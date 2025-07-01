"""
Módulo da view para a aba de Gerenciamento de Usuários no painel de administração.
"""
import streamlit as st
import io
import pandas as pd
from typing import Optional, Dict, Any

from src.db import user_repository as user_repo, team_repository as team_repo
from src.db.audit_repository import log_audit_event
from src.auth.auth_service import hash_password
from src.config import config

# --- Funções de Segurança e Permissão ---

def can_manage_user(manager_role: str, manager_id: int, manager_team_id: Optional[int], target_user_data: Dict[str, Any]) -> bool:
    """Verifica se o usuário logado pode gerenciar o usuário alvo."""
    if manager_role == "Admin":
        return True
    if manager_role == "Supervisor":
        # Supervisor não pode gerenciar a si mesmo, outros supervisores ou admins
        if target_user_data['id'] == manager_id or target_user_data['role'] in ["Admin", "Supervisor"]:
            return False
        # Supervisor só pode gerenciar membros de sua própria equipe
        return target_user_data['team_id'] == manager_team_id
    return False

def get_allowed_roles(manager_role: str) -> list[str]:
    """Retorna a lista de cargos que um gerente pode atribuir."""
    if manager_role == "Admin":
        return config.USER_ROLES
    return ["Consultor"] # Supervisor só pode criar/editar consultores

# --- Renderização da Lista de Usuários ---

def render_user_list():
    """Renderiza a lista de usuários com filtros e controle de acesso."""
    st.subheader("Lista de Usuários Cadastrados")

    manager_role = st.session_state.get("user_role")
    manager_team_id = user_repo.get_user_by_id(st.session_state.get("user_id"))['team_id']

    users_df = user_repo.get_all_users()
    if users_df.empty:
        st.info("Nenhum usuário cadastrado.")
        return

    # Filtra o DataFrame com base na permissão do usuário logado
    if manager_role == "Supervisor":
        users_df = users_df[users_df['team_id'] == manager_team_id]
        if users_df.empty:
            st.info("Nenhum usuário encontrado em sua equipe.")
            return

    # Lógica de filtros da UI
    with st.expander("Opções de Filtro", expanded=True):
        # ... (código dos widgets de filtro permanece o mesmo)
        col_role, col_name, col_team = st.columns(3)
        filter_role = col_role.selectbox("Filtrar por Cargo", ["Todos"] + config.USER_ROLES)
        filter_name = col_name.text_input("Filtrar por Nome")
        
        teams_df = team_repo.get_all_teams()
        team_options = {"Todos": "Todos", **{row['id']: row['name'] for _, row in teams_df.iterrows()}}
        filter_team = col_team.selectbox("Filtrar por Equipe", options=list(team_options.keys()), format_func=lambda x: team_options[x])

    # Aplica filtros
    filtered_df = users_df.copy()
    if filter_role != "Todos":
        filtered_df = filtered_df[filtered_df['role'] == filter_role]
    if filter_name:
        filtered_df = filtered_df[filtered_df['nome'].str.contains(filter_name, case=False, na=False)]
    if filter_team != "Todos":
        filtered_df = filtered_df[filtered_df['team_id'] == filter_team]

    if filtered_df.empty:
        st.info("Nenhum usuário encontrado com os filtros aplicados.")
    else:
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# --- Renderização da Gestão de Usuários (Adicionar/Editar/Deletar) ---

def show():
    """Renderiza a aba de gestão de usuários (adicionar, editar, deletar)."""
    st.subheader("Gestão de Consultores e Supervisores")
    
    with st.expander("Adicionar Novo Usuário", expanded=False):
        render_add_user_form()

    st.divider()
    st.subheader("Editar ou Deletar Usuário")
    
    users_df = user_repo.get_all_users()
    if users_df.empty:
        st.info("Nenhum usuário cadastrado para editar ou deletar.")
        return
        
    manager_role = st.session_state.get("user_role")
    manager_id = st.session_state.get("user_id")
    manager_team_id = user_repo.get_user_by_id(manager_id)['team_id']

    # Filtra a lista de usuários que o gerente pode ver/editar
    if manager_role == "Supervisor":
        users_df = users_df[users_df['team_id'] == manager_team_id]

    user_options = {row['id']: row['nome'] for _, row in users_df.iterrows()}
    selected_user_id = st.selectbox(
        "Selecione um usuário para gerenciar", 
        options=list(user_options.keys()), 
        format_func=lambda x: user_options.get(x, "Inválido"), 
        index=None, 
        placeholder="Escolha um usuário..."
    )

    if not selected_user_id:
        return

    user_data = user_repo.get_user_by_id(selected_user_id)
    if not user_data:
        st.error("Usuário não encontrado."); return

    # Verificação final de permissão
    if not can_manage_user(manager_role, manager_id, manager_team_id, user_data):
        st.error("Acesso negado. Você não tem permissão para gerenciar este usuário.")
        return

    # Lógica de deleção e edição
    if st.session_state.get('confirming_delete_user') == selected_user_id:
        render_delete_confirmation(user_data)
    else:
        render_user_details_and_form(user_data)

# --- Sub-componentes de Renderização ---

def render_add_user_form():
    manager_role = st.session_state.get("user_role")
    allowed_roles = get_allowed_roles(manager_role)
    
    with st.form("add_user_form", clear_on_submit=True):
        new_role = st.selectbox("Cargo", allowed_roles, key="new_user_role")
        new_nome = st.text_input("Nome Completo")
        new_tipo = st.selectbox("Tipo de Consultor", config.CONSULTOR_TYPES) if new_role == "Consultor" else "N/A"
        new_telefone = st.text_input("Telefone")
        new_email = st.text_input("Email")
        new_password = st.text_input("Senha", type="password")
        new_foto = st.file_uploader("Foto do Perfil", type=['png', 'jpg', 'jpeg'])
        
        submitted = st.form_submit_button("Adicionar Usuário")
        if submitted:
            if not all([new_nome, new_email, new_password]):
                st.warning("Nome, E-mail e Senha são obrigatórios."); return
            
            foto_bytes = new_foto.getvalue() if new_foto else None
            hashed_password = hash_password(new_password)
            
            success, message = user_repo.add_user(new_nome, new_tipo, new_telefone, new_email, foto_bytes, new_role, hashed_password)
            if success:
                st.success(message)
                log_audit_event(st.session_state.get("user_id"), "USER_CREATED", f"User {new_nome} created.")
                st.rerun()
            else:
                st.error(message)

def render_delete_confirmation(user_data):
    with st.warning(f"**Atenção!** Você está prestes a deletar o usuário **{user_data['nome']}**. Esta ação é irreversível."):
        col1, col2 = st.columns(2)
        col1.button("Confirmar Deleção", on_click=handle_user_delete, args=(user_data['id'], user_data['nome']), use_container_width=True, type="primary")
        col2.button("Cancelar", on_click=lambda: st.session_state.update(confirming_delete_user=None), use_container_width=True)

def render_user_details_and_form(user_data):
    col_edit_photo, col_edit_details = st.columns([1, 2])
    with col_edit_photo:
        render_user_stats(user_data['id'], user_data['foto'])
    with col_edit_details:
        render_edit_user_form(user_data)

    st.divider()
    st.subheader("Simulações Realizadas por Este Usuário")
    render_user_simulations(user_data['id'])

def render_edit_user_form(user_data):
    manager_role = st.session_state.get("user_role")
    allowed_roles = get_allowed_roles(manager_role)
    
    with st.form(f"edit_user_form_{user_data['id']}"):
        edited_nome = st.text_input("Nome", value=user_data['nome'])
        
        current_role_index = allowed_roles.index(user_data['role']) if user_data['role'] in allowed_roles else 0
        edited_role = st.selectbox("Cargo", allowed_roles, index=current_role_index)
        
        edited_tipo = "N/A"
        if edited_role == "Consultor":
            current_tipo_index = config.CONSULTOR_TYPES.index(user_data['tipo_consultor']) if user_data['tipo_consultor'] in config.CONSULTOR_TYPES else 0
            edited_tipo = st.selectbox("Tipo", config.CONSULTOR_TYPES, index=current_tipo_index)

        edited_telefone = st.text_input("Telefone", value=user_data['telefone'] or "")
        edited_email = st.text_input("Email", value=user_data['email'] or "")
        edited_password = st.text_input("Nova Senha", type="password", placeholder="Deixe em branco para não alterar")
        edited_foto_file = st.file_uploader("Trocar Foto", type=['png', 'jpg', 'jpeg'])
        
        col_buttons_user = st.columns(2)
        edit_submitted = col_buttons_user[0].form_submit_button("Salvar Alterações", use_container_width=True)
        delete_submitted = col_buttons_user[1].form_submit_button("Deletar Usuário", type="primary", use_container_width=True)

        if edit_submitted:
            handle_user_update(user_data, edited_nome, edited_tipo, edited_telefone, edited_email, edited_foto_file, edited_role, edited_password)
        if delete_submitted:
            st.session_state.confirming_delete_user = user_data['id']
            st.rerun()

def render_user_stats(user_id, foto_bytes):
    st.markdown("##### Foto e Estatísticas")
    if foto_bytes:
        st.image(io.BytesIO(foto_bytes), width=150, caption="Foto Atual")
    else:
        st.image("https://via.placeholder.com/150", width=150, caption="Sem foto")
    stats = user_repo.get_user_simulation_stats(user_id)
    st.metric("Total de Simulações", f"{stats['total_simulacoes']} sims.")
    st.metric("Média de Crédito", f"R$ {stats['media_credito']:,.2f}")
    st.metric("Total Simulado", f"R$ {stats['total_credito']:,.2f}")

def render_user_simulations(user_id):
    sims_df = user_repo.get_user_detailed_simulations(user_id)
    if sims_df.empty:
        st.info("Nenhuma simulação encontrada para este usuário.")
    else:
        sims_df['timestamp'] = pd.to_datetime(sims_df['timestamp']).dt.strftime('%d/%m/%Y %H:%M:%S')
        sims_df.columns = ["Data/Hora", "Crédito (R$)", "Nova Parcela (R$)"]
        st.dataframe(sims_df, use_container_width=True, hide_index=True)

# --- Funções de Manipulação (Handlers) ---

def handle_user_update(user_data, nome, tipo, telefone, email, new_foto_file, role, password):
    foto_bytes = new_foto_file.getvalue() if new_foto_file else user_data['foto']
    hashed_password = hash_password(password) if password else None
    
    success, message = user_repo.update_user(user_data['id'], nome, tipo, telefone, email, foto_bytes, role, hashed_password)
    if success:
        st.success(message)
        log_audit_event(st.session_state.get("user_id"), "USER_UPDATED", f"User {nome} ({user_data['id']}) updated.")
        st.rerun()
    else:
        st.error(message)

def handle_user_delete(user_id, user_name):
    if user_id == st.session_state.get("user_id"):
        st.error("Ação n��o permitida: você não pode deletar a si mesmo."); return

    success, message = user_repo.delete_user(user_id)
    if success:
        st.success(message)
        log_audit_event(st.session_state.get("user_id"), "USER_DELETED", f"User {user_name} ({user_id}) deleted.")
        st.session_state.confirming_delete_user = None
        st.rerun()
    else:
        st.error(message)
