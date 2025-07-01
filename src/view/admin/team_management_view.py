"""
Módulo da view para a aba de Gerenciamento de Equipes no painel de administração.
"""
import streamlit as st
from typing import Dict, Any

from src.db import team_repository as team_repo, user_repository as user_repo
from src.db.audit_repository import log_audit_event

# --- Funções de Segurança e Permissão ---

def can_manage_team(manager_role: str, manager_team_id: int, target_team_id: int) -> bool:
    """Verifica se o usuário logado pode gerenciar a equipe alvo."""
    if manager_role == "Admin":
        return True
    if manager_role == "Supervisor":
        return manager_team_id == target_team_id
    return False

# --- Renderização Principal ---

def show():
    """Renderiza a aba de gerenciamento de equipes com controle de acesso."""
    st.subheader("Gerenciamento de Equipes")
    
    manager_role = st.session_state.get("user_role")
    
    if manager_role == "Admin":
        st.info("Crie e gerencie equipes, atribuindo supervisores e membros.")
        with st.expander("Criar Nova Equipe", expanded=False):
            render_create_team_form()
        st.divider()

    st.subheader("Lista de Equipes")
    teams_df = team_repo.get_all_teams()
    
    if teams_df.empty:
        st.info("Nenhuma equipe cadastrada."); return

    # Filtra as equipes que o usuário pode ver
    if manager_role == "Supervisor":
        user_data = user_repo.get_user_by_id(st.session_state.get("user_id"))
        teams_df = teams_df[teams_df['id'] == user_data['team_id']]
        if teams_df.empty:
            st.warning("Você não está associado a nenhuma equipe."); return
    
    st.dataframe(teams_df, use_container_width=True, hide_index=True)
    st.divider()
    
    st.subheader("Gerenciar Membros da Equipe")
    render_manage_team_members_section(teams_df)

# --- Sub-componentes de Renderização ---

def render_create_team_form():
    """Renderiza o formulário para criar uma nova equipe (apenas para Admins)."""
    all_users = user_repo.get_all_users()
    # Supervisores disponíveis são aqueles com o cargo e que ainda não supervisionam uma equipe
    existing_supervisor_ids = team_repo.get_all_teams()['supervisor_id'].dropna().unique()
    supervisors_df = all_users[(all_users['role'] == 'Supervisor') & (~all_users['id'].isin(existing_supervisor_ids))]
    
    if supervisors_df.empty:
        st.warning("Não há supervisores disponíveis. Crie um usuário 'Supervisor' que não esteja em outra equipe."); return

    with st.form("add_team_form", clear_on_submit=True):
        new_team_name = st.text_input("Nome da Equipe")
        supervisor_options = {row['id']: row['nome'] for _, row in supervisors_df.iterrows()}
        selected_supervisor_id = st.selectbox("Selecionar Supervisor", options=list(supervisor_options.keys()), format_func=lambda x: supervisor_options.get(x), index=None)
        
        if st.form_submit_button("Criar Equipe"):
            if not all([new_team_name, selected_supervisor_id]):
                st.warning("Nome da equipe e supervisor são obrigatórios."); return
            
            success, message = team_repo.create_team(new_team_name, selected_supervisor_id)
            if success:
                st.success(message)
                log_audit_event(st.session_state.get("user_id"), "TEAM_CREATED", f"Team {new_team_name} created.")
                st.rerun()
            else:
                st.error(message)

def render_manage_team_members_section(teams_df):
    """Renderiza a seção para editar ou deletar uma equipe."""
    team_options = {row['id']: row['name'] for _, row in teams_df.iterrows()}
    selected_team_id = st.selectbox("Selecione uma equipe para gerenciar", options=list(team_options.keys()), index=None)

    if not selected_team_id:
        return

    manager_role = st.session_state.get("user_role")
    manager_team_id = user_repo.get_user_by_id(st.session_state.get("user_id"))['team_id']

    if not can_manage_team(manager_role, manager_team_id, selected_team_id):
        st.error("Acesso negado. Você não tem permissão para gerenciar esta equipe.")
        return

    if st.session_state.get('confirming_delete_team') == selected_team_id:
        render_delete_confirmation(selected_team_id, team_options[selected_team_id])
    else:
        render_edit_team_form(selected_team_id, teams_df)

def render_delete_confirmation(team_id, team_name):
    with st.warning(f"**Atenção!** Você está prestes a deletar a equipe **{team_name}**. Os membros ficarão sem equipe. Esta ação é irreversível."):
        col1, col2 = st.columns(2)
        col1.button("Confirmar Deleção da Equipe", on_click=handle_team_delete, args=(team_id, team_name), use_container_width=True, type="primary")
        col2.button("Cancelar", on_click=lambda: st.session_state.update(confirming_delete_team=None), use_container_width=True)

def render_edit_team_form(team_id, teams_df):
    with st.form(f"edit_team_members_form_{team_id}"):
        users_df = user_repo.get_all_users()
        # Membros disponíveis são consultores sem equipe ou que já estão nesta equipe
        available_members_df = users_df[(users_df['role'] == 'Consultor') & (users_df['team_id'].isna() | (users_df['team_id'] == team_id))]
        member_options = {row['id']: row['nome'] for _, row in available_members_df.iterrows()}
        
        current_member_ids = users_df[users_df['team_id'] == team_id]['id'].tolist()
        # O supervisor da equipe não deve ser listado como um membro selecionável
        supervisor_id = teams_df.loc[teams_df['id'] == team_id, 'supervisor_id'].iloc[0]
        current_member_ids = [mid for mid in current_member_ids if mid != supervisor_id]

        selected_member_ids = st.multiselect("Selecionar Membros (Consultores)", options=list(member_options.keys()), default=current_member_ids, format_func=lambda x: member_options.get(x))
        
        col_buttons_team = st.columns(2)
        update_submitted = col_buttons_team[0].form_submit_button("Atualizar Membros", use_container_width=True)
        
        # Apenas Admins podem deletar equipes
        delete_visible = st.session_state.get("user_role") == "Admin"
        delete_submitted = False
        if delete_visible:
            delete_submitted = col_buttons_team[1].form_submit_button("Deletar Equipe", type="primary", use_container_width=True)

        if update_submitted:
            handle_team_update(team_id, selected_member_ids, team_options[team_id])
        if delete_submitted:
            st.session_state.confirming_delete_team = team_id
            st.rerun()

# --- Funções de Manipulação (Handlers) ---

def handle_team_update(team_id, member_ids, team_name):
    success, message = team_repo.update_team_members(team_id, member_ids)
    if success:
        st.success(message)
        log_audit_event(st.session_state.get("user_id"), "TEAM_MEMBERS_UPDATED", f"Team {team_name} members updated.")
        st.rerun()
    else:
        st.error(message)

def handle_team_delete(team_id, team_name):
    success, message = team_repo.delete_team(team_id)
    if success:
        st.success(message)
        log_audit_event(st.session_state.get("user_id"), "TEAM_DELETED", f"Team {team_name} ({team_id}) deleted.")
        st.session_state.confirming_delete_team = None
        st.rerun()
    else:
        st.error(message)

