"""
Refatorado: Módulo da view para Gerenciamento de Equipes.

Seguindo o mesmo padrão da view de usuários, esta interface é declarativa
e delega toda a lógica para o AdminService. Ela é responsável apenas por
renderizar os formulários e tabelas, e exibir os resultados ou erros
fornecidos pelo serviço, resultando em um código de UI limpo e de fácil manutenção.
"""
import streamlit as st
import pandas as pd

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError

from src.view.admin.admin_service import AdminService
from src.utils.cached_data import get_cached_all_users_with_team_info, get_cached_available_supervisors, get_cached_all_teams_with_supervisor_info

def show_team_management(service: AdminService, db: Session):
    """Renderiza a UI para gerenciamento de equipes."""
    st.header("Gerenciamento de Equipes")

    try:
        # Usa funções cacheadas para leitura de dados
        all_users = get_cached_all_users_with_team_info()
        available_supervisors = get_cached_available_supervisors()
    except SQLAlchemyError as e:
        st.error(f"Erro ao carregar dados de usuários e equipes: {e}")
        return

    # --- Formulário para Criar Nova Equipe ---
    with st.expander("Criar Nova Equipe", expanded=False):
        with st.form("new_team_form", clear_on_submit=True):
            team_name = st.text_input("Nome da Equipe")
            supervisor_options = {user.id: user.nome for user in available_supervisors}
            selected_supervisor_id = st.selectbox("Selecione um Supervisor", options=list(supervisor_options.keys()), format_func=lambda x: supervisor_options[x])

            submitted = st.form_submit_button("Criar Equipe")
            if submitted:
                if not team_name or not selected_supervisor_id:
                    st.error("Nome da equipe e supervisor são obrigatórios.")
                else:
                    try:
                        service.create_team(db, team_name, selected_supervisor_id)
                        st.success(f"Equipe '{team_name}' criada com sucesso!")
                        st.rerun()
                    except IntegrityError as e:
                        st.error(f"Erro ao criar equipe: O nome da equipe já existe. Detalhes: {e}")
                    except NoResultFound as e:
                        st.error(f"Erro ao criar equipe: {e}")
                    except SQLAlchemyError as e:
                        st.error(f"Erro de banco de dados ao criar equipe: {e}")

    st.divider()

    # --- Lista de Equipes ---
    st.subheader("Equipes Formadas")
    try:
        # Usa função cacheada para obter as equipes
        teams = get_cached_all_teams_with_supervisor_info()
        if not teams:
            st.info("Nenhuma equipe formada.")
            return

        # Converte os objetos TeamWithSupervisor (dataclass) para dicionários para o DataFrame
        teams_data = []
        for team in teams:
            teams_data.append(team.__dict__)

        df_teams = pd.DataFrame(teams_data)
        df_teams_display = df_teams[['id', 'name', 'supervisor_name']]
        df_teams_display.rename(columns={'id': 'ID', 'name': 'Nome da Equipe', 'supervisor_name': 'Supervisor'}, inplace=True)
        st.dataframe(df_teams_display, use_container_width=True, hide_index=True)

        # --- Ações de Gerenciamento de Equipe ---
        st.subheader("Gerenciar Membros e Excluir Equipe")
        team_options = {team.id: team.name for team in teams}
        selected_team_id = st.selectbox("Selecione uma equipe para gerenciar", options=list(team_options.keys()), format_func=lambda x: team_options[x])

        if selected_team_id:
            # Filtra usuários que podem ser membros (não são supervisores de outras equipes)
            # all_users já foi carregado no início da função
            assigned_supervisor_ids = {team.supervisor_id for team in teams if team.id != selected_team_id}
            available_members = [user for user in all_users if user.id not in assigned_supervisor_ids or (user.team_id == selected_team_id and user.id != df_teams.loc[df_teams['id'] == selected_team_id, 'supervisor_id'].values[0])]
            member_options = {user.id: user.nome for user in available_members}
            
            # Filtra membros que já estão na equipe selecionada
            current_member_ids = [user.id for user in all_users if user.team_id == selected_team_id and user.id != df_teams.loc[df_teams['id'] == selected_team_id, 'supervisor_id'].values[0]]

            with st.form(f"manage_team_{selected_team_id}"):
                st.write(f"Editando membros da equipe: **{team_options[selected_team_id]}**")
                selected_member_ids = st.multiselect("Membros da Equipe", options=list(member_options.keys()), format_func=lambda x: member_options[x], default=current_member_ids)
                
                col1, col2 = st.columns([1, 5])
                if col1.form_submit_button("Salvar Membros"):
                    try:
                        service.update_team_members(db, selected_team_id, selected_member_ids)
                        st.success("Membros da equipe atualizados com sucesso!")
                        st.rerun()
                    except NoResultFound as e:
                        st.error(f"Erro ao atualizar membros: {e}")
                    except SQLAlchemyError as e:
                        st.error(f"Erro de banco de dados ao atualizar membros: {e}")

                if col2.form_submit_button("Excluir Equipe", type="primary"):
                    try:
                        service.delete_team(db, selected_team_id)
                        st.success("Equipe excluída com sucesso!")
                        st.rerun()
                    except NoResultFound as e:
                        st.error(f"Erro ao excluir equipe: {e}")
                    except SQLAlchemyError as e:
                        st.error(f"Erro de banco de dados ao excluir equipe: {e}")

    except SQLAlchemyError as e:
        st.error(f"Não foi possível carregar as equipes: {e}")
