"""
Refatorado: Módulo da view principal da área Administrativa.

Esta view atua como um controlador principal, instanciando o AdminService
e passando-o para as sub-views (gerenciamento de usuários e equipes).
Isso completa o padrão de desacoplamento, garantindo que toda a seção
de administração siga uma arquitetura limpa e centralizada.
"""
import streamlit as st

# Importações da nova arquitetura
from src.view.admin.admin_service import AdminService
from src.db.user_repository import UserRepository
from src.db.team_repository import TeamRepository
from src.db.audit_repository import AuditRepository
from src.auth.auth_service import AuthService
from src.db import get_db # Importa o gerenciador de sessão do SQLAlchemy
from src.view.admin import user_management_view, team_management_view
from src.config import config

def show():
    """Renderiza a página de administração, orquestrando as sub-views."""
    st.title("Painel de Administração")

    # Apenas Admins podem acessar esta página. A verificação é feita em setup_page.
    if st.session_state.get("user_role") != config.ROLE_ADMIN:
        st.error("Acesso negado. Você não tem permissão para visualizar esta página.")
        return

    # --- Injeção de Dependência ---
    # A sessão do DB é gerenciada pelo context manager get_db()
    with get_db() as db:
        try:
            # Instancia os repositórios e o serviço de autenticação
            user_repo = UserRepository()
            team_repo = TeamRepository()
            audit_repo = AuditRepository()
            auth_service = AuthService(user_repo, audit_repo)

            # Instancia o serviço que orquestra toda a lógica da página
            service = AdminService(
                user_repo,
                team_repo,
                audit_repo,
                auth_service
            )
        except Exception as e:
            st.error("Ocorreu um erro crítico ao inicializar os serviços da página de administração.")
            st.error(f"Detalhes: {e}")
            return

        # --- Navegação em Abas ---
        tab1, tab2 = st.tabs(["Gerenciar Usuários", "Gerenciar Equipes"])

        with tab1:
            # Passa a instância do serviço e a sessão do DB para a sub-view de usuários
            user_management_view.show_user_management(service, db)

        with tab2:
            # Passa a instância do serviço e a sessão do DB para a sub-view de equipes
            team_management_view.show_team_management(service, db)
