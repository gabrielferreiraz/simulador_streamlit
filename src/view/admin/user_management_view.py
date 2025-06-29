# src/view/admin/user_management_view.py
import streamlit as st
import io
from src.db.user_repository import add_user, get_all_users, get_user_by_id, update_user, delete_user, get_user_simulation_stats, get_user_detailed_simulations
from src.db.audit_repository import log_audit_event
from src.auth.auth_service import hash_password
from src.config import config
import pandas as pd

def show():
    """Renderiza a aba de gerenciamento de usuários."""
    if st.session_state.get("user_role") != "Admin":
        st.warning("Apenas usuários com permissão de administrador podem gerenciar usuários.")
        return

    st.subheader("Gerenciamento de Consultores e Supervisores")
    with st.expander("Adicionar Novo Usuário", expanded=False):
        render_add_user_form()

    st.divider()
    st.subheader("Lista de Usuários")
    users_df = get_all_users()
    if users_df.empty:
        st.info("Nenhum usuário cadastrado.")
    else:
        st.dataframe(users_df, use_container_width=True, hide_index=True)
        st.divider()
        st.subheader("Editar ou Deletar Usuário")
        render_edit_user_section(users_df)

def render_add_user_form():
    new_role_selection = st.selectbox("Cargo", config.USER_ROLES, key="new_user_role_selection")
    with st.form("add_user_form", clear_on_submit=True):
        new_nome = st.text_input("Nome Completo", key="new_user_nome")
        new_tipo = st.selectbox("Tipo de Consultor", config.CONSULTOR_TYPES, key="new_user_tipo") if new_role_selection == "Consultor" else None
        new_telefone = st.text_input("Telefone", key="new_user_telefone")
        new_email = st.text_input("Email", key="new_user_email")
        new_password = st.text_input("Senha", type="password", key="new_user_password")
        new_foto = st.file_uploader("Foto do Perfil", type=['png', 'jpg', 'jpeg'], key="new_user_foto")
        submitted = st.form_submit_button("Adicionar Usuário")
        if submitted:
            if not (new_nome and new_email and new_password):
                st.warning("Nome, E-mail e Senha são obrigatórios.")
                return
            foto_bytes = new_foto.getvalue() if new_foto else None
            hashed_password = hash_password(new_password)
            success, message = add_user(new_nome, new_tipo, new_telefone, new_email, foto_bytes, new_role_selection, hashed_password)
            if success:
                st.success(message)
                log_audit_event(st.session_state.get("user_id"), "USER_CREATED", f"User {new_nome} created.")
                st.rerun()
            else:
                st.error(message)

def render_edit_user_section(users_df):
    st.info("Selecione um usuário para visualizar seus detalhes, editar informações ou removê-lo do sistema.")
    user_options = {row['id']: row['nome'] for _, row in users_df.iterrows()}
    selected_user_id = st.selectbox("Selecione um usuário", options=list(user_options.keys()), format_func=lambda x: user_options[x], key="edit_delete_user_select", index=None, placeholder="Escolha um usuário...")

    if not selected_user_id:
        return

    user_data = get_user_by_id(selected_user_id)
    if not user_data:
        st.error("Usuário não encontrado."); return

    uid, nome, tipo, telefone, email, foto_bytes, role, team_id, _ = user_data
    
    if st.session_state.get('confirming_delete_user') == uid:
        with st.warning(f"**Atenção!** Você está prestes a deletar o usuário **{nome}**. Esta ação é irreversível."):
            col1, col2 = st.columns(2)
            col1.button("Confirmar Deleção", on_click=handle_user_delete, args=(uid, nome), use_container_width=True, type="primary")
            col2.button("Cancelar", on_click=lambda: st.session_state.update(confirming_delete_user=None), use_container_width=True)
        return

    col_edit_photo, col_edit_details = st.columns([1, 2])
    with col_edit_photo:
        render_user_stats(uid, foto_bytes)
    with col_edit_details:
        render_edit_user_form(uid, nome, tipo, telefone, email, role, foto_bytes)

    st.divider()
    st.subheader("Simulações Realizadas por Este Usuário")
    render_user_simulations(uid)

def render_edit_user_form(uid, nome, tipo, telefone, email, role, foto_bytes):
    st.markdown("##### Editar Informações")
    with st.form(f"edit_user_form_{uid}"):
        edited_nome = st.text_input("Nome", value=nome)
        edited_role = st.selectbox("Cargo", config.USER_ROLES, index=config.USER_ROLES.index(role))
        edited_tipo = st.selectbox("Tipo", config.CONSULTOR_TYPES, index=config.CONSULTOR_TYPES.index(tipo) if tipo in config.CONSULTOR_TYPES else 0) if edited_role == "Consultor" else None
        edited_telefone = st.text_input("Telefone", value=telefone or "")
        edited_email = st.text_input("Email", value=email or "")
        edited_password = st.text_input("Nova Senha", type="password", placeholder="Deixe em branco para não alterar")
        edited_foto_file = st.file_uploader("Trocar Foto", type=['png', 'jpg', 'jpeg'])
        
        col_buttons_user = st.columns(2)
        edit_submitted = col_buttons_user[0].form_submit_button("Salvar Alterações", use_container_width=True)
        delete_submitted = col_buttons_user[1].form_submit_button("Deletar Usuário", type="primary", use_container_width=True)

        if edit_submitted:
            handle_user_update(uid, edited_nome, edited_tipo, edited_telefone, edited_email, edited_foto_file, foto_bytes, edited_role, edited_password)
        if delete_submitted:
            st.session_state.confirming_delete_user = uid
            st.rerun()

def handle_user_update(uid, nome, tipo, telefone, email, new_foto_file, old_foto_bytes, role, password):
    updated_foto_bytes = new_foto_file.getvalue() if new_foto_file else old_foto_bytes
    hashed_password = hash_password(password) if password else None
    success, message = update_user(uid, nome, tipo, telefone, email, updated_foto_bytes, role, hashed_password)
    if success:
        st.success(message)
        log_audit_event(st.session_state.get("user_id"), "USER_UPDATED", f"User {nome} ({uid}) updated.")
        st.rerun()
    else:
        st.error(message)

def handle_user_delete(uid, nome):
    success, message = delete_user(uid)
    if success:
        st.success(message)
        log_audit_event(st.session_state.get("user_id"), "USER_DELETED", f"User {nome} ({uid}) deleted.")
        st.session_state.confirming_delete_user = None
        st.rerun()
    else:
        st.error(message)

def render_user_stats(user_id, foto_bytes):
    st.markdown("##### Foto e Estatísticas")
    if foto_bytes:
        st.image(io.BytesIO(foto_bytes), width=150, caption="Foto Atual")
    else:
        st.image("https://via.placeholder.com/150", width=150, caption="Sem foto")
    stats = get_user_simulation_stats(user_id)
    st.metric("Total de Simulações", f"{stats['total_simulacoes']} sims.")
    st.metric("Média de Crédito Simulado", f"R$ {stats['media_credito']:,.2f}")
    st.metric("Valor Total Simulado", f"R$ {stats['total_credito']:,.2f}")

def render_user_simulations(user_id):
    user_simulations_df = get_user_detailed_simulations(user_id)
    if user_simulations_df.empty:
        st.info("Nenhuma simulação encontrada para este usuário.")
    else:
        user_simulations_df['timestamp'] = pd.to_datetime(user_simulations_df['timestamp']).dt.strftime('%d/%m/%Y %H:%M:%S')
        user_simulations_df.columns = ["Data/Hora", "Crédito Simulado (R$)", "Nova Parcela (R$)"]
        st.dataframe(user_simulations_df, use_container_width=True, hide_index=True)
