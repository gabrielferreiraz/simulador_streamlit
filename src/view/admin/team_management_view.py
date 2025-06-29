# src/view/admin/team_management_view.py
import streamlit as st
from src.db.team_repository import create_team, get_all_teams, update_team_members, delete_team
from src.db.user_repository import get_all_users
from src.db.audit_repository import log_audit_event

def show():
    """Renderiza a aba de gerenciamento de equipes."""
    st.subheader("Gerenciamento de Equipes")
    st.info("Crie e gerencie equipes, atribuindo supervisores e membros.")

    with st.expander("Criar Nova Equipe", expanded=False):
        render_create_team_form()

    st.divider()
    st.subheader("Lista de Equipes")
    teams_df = get_all_teams()
    if teams_df.empty:
        st.info("Nenhuma equipe cadastrada.")
    else:
        st.dataframe(teams_df, use_container_width=True, hide_index=True)
        st.divider()
        st.subheader("Gerenciar Membros da Equipe")
        render_manage_team_members_section(teams_df)

def render_create_team_form():
    with st.form("add_team_form", clear_on_submit=True):
        new_team_name = st.text_input("Nome da Equipe")
        all_users = get_all_users()
        if all_users.empty:
            st.warning("Nenhum usuário cadastrado para ser supervisor.")
            supervisors_df = pd.DataFrame(columns=['id', 'nome'])
        else:
            supervisors_df = all_users[all_users['role'] == 'Supervisor']
        
        supervisor_options = {row['id']: row['nome'] for _, row in supervisors_df.iterrows()}
        
        selected_supervisor_id = st.selectbox(
            "Selecionar Supervisor", 
            options=list(supervisor_options.keys()), 
            format_func=lambda x: supervisor_options[x], 
            index=None, 
            placeholder="Escolha um supervisor..."
        )
        
        team_submitted = st.form_submit_button("Criar Equipe")
        if team_submitted:
            if not (new_team_name and selected_supervisor_id):
                st.warning("Nome da equipe e supervisor são obrigatórios.")
                return
            success, message = create_team(new_team_name, selected_supervisor_id)
            if success:
                st.success(message)
                log_audit_event(st.session_state.get("user_id"), "TEAM_CREATED", f"Team {new_team_name} created.")
                st.rerun()
            else:
                st.error(message)

def render_manage_team_members_section(teams_df):
    team_options = {row['id']: row['name'] for _, row in teams_df.iterrows()}
    selected_team_id = st.selectbox("Selecione uma equipe", options=list(team_options.keys()), key="manage_team_select", index=None, placeholder="Escolha uma equipe...")

    if not selected_team_id:
        return

    if st.session_state.get('confirming_delete_team') == selected_team_id:
        team_name = team_options[selected_team_id]
        with st.warning(f"**Atenção!** Você está prestes a deletar a equipe **{team_name}**. Os membros ficarão sem equipe. Esta ação é irreversível."):
            col1, col2 = st.columns(2)
            col1.button("Confirmar Deleção da Equipe", on_click=handle_team_delete, args=(selected_team_id, team_name), use_container_width=True, type="primary")
            col2.button("Cancelar", on_click=lambda: st.session_state.update(confirming_delete_team=None), use_container_width=True)
        return

    with st.form(f"edit_team_members_form_{selected_team_id}"):
        team_supervisor_id = teams_df.loc[teams_df['id'] == selected_team_id, 'supervisor_id'].iloc[0]
        all_supervisor_ids = teams_df['supervisor_id'].dropna().unique().tolist()
        users_df = get_all_users()
        available_members_df = users_df[
            (users_df['role'].isin(['Consultor', 'Supervisor'])) &
            (~users_df['id'].isin([sid for sid in all_supervisor_ids if sid != team_supervisor_id])) &
            (users_df['team_id'].isna() | (users_df['team_id'] == selected_team_id)) &
            (users_df['id'] != team_supervisor_id)
        ]
        member_options = {row['id']: row['nome'] for _, row in available_members_df.iterrows()}
        current_member_ids = users_df.loc[users_df['team_id'] == selected_team_id, 'id'].tolist()
        filtered_current_member_ids = [mid for mid in current_member_ids if mid in member_options]
        
        selected_member_ids = st.multiselect("Selecionar Membros", options=list(member_options.keys()), default=filtered_current_member_ids, format_func=lambda x: member_options.get(x, "Membro Inválido"))
        
        col_buttons_team = st.columns(2)
        update_submitted = col_buttons_team[0].form_submit_button("Atualizar Membros", use_container_width=True)
        delete_submitted = col_buttons_team[1].form_submit_button("Deletar Equipe", type="primary", use_container_width=True)

        if update_submitted:
            handle_team_update(selected_team_id, selected_member_ids, team_options[selected_team_id])
        if delete_submitted:
            st.session_state.confirming_delete_team = selected_team_id
            st.rerun()

def handle_team_update(team_id, member_ids, team_name):
    success, message = update_team_members(team_id, member_ids)
    if success:
        st.success(message)
        log_audit_event(st.session_state.get("user_id"), "TEAM_MEMBERS_UPDATED", f"Team {team_name} members updated.")
        st.rerun()
    else:
        st.error(message)

def handle_team_delete(team_id, team_name):
    success, message = delete_team(team_id)
    if success:
        st.success(message)
        log_audit_event(st.session_state.get("user_id"), "TEAM_DELETED", f"Team {team_name} ({team_id}) deleted.")
        st.session_state.confirming_delete_team = None
        st.rerun()
    else:
        st.error(message)
