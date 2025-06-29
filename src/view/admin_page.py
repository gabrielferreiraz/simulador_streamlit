# src/view/admin_page.py
import streamlit as st
from src.view.admin import user_management_view, team_management_view

def show():
    """
    Renderiza o Painel de Administração, que agora atua como um orquestrador
    para as visualizações de gerenciamento de usuários e equipes.
    """
    st.title("Painel de Administração")

    # Verificação de permissão de alto nível.
    # Verificações mais granulares são feitas dentro de cada módulo.
    if st.session_state.get("user_role") not in ["Admin", "Supervisor"]:
        st.error("Acesso negado. Você não tem permissão para acessar esta página.")
        return

    # Inicializa o estado para controle de confirmação de deleção
    if 'confirming_delete_user' not in st.session_state:
        st.session_state.confirming_delete_user = None
    if 'confirming_delete_team' not in st.session_state:
        st.session_state.confirming_delete_team = None

    tab_users, tab_teams = st.tabs(["Gerenciar Usuários", "Gerenciar Equipes"])

    with tab_users:
        # Chama a visualização de gerenciamento de usuários
        user_management_view.show()

    with tab_teams:
        # Chama a visualização de gerenciamento de equipes
        team_management_view.show()
