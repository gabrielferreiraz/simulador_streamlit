# src/utils/page_setup.py
import streamlit as st
from src.auth.auth_service import AuthService
from src.db import get_db
from src.db.user_repository import UserRepository
from src.db.audit_repository import AuditRepository
from src.utils.style_utils import (
    apply_dark_theme, 
    hide_insights_link_for_consultor, 
    hide_admin_link_for_consultor, 
    hide_all_pages_except_login,
    hide_main_page_from_sidebar
)
from src.config import config as cfg

def setup_page(page_title: str, page_icon: str, hide_sidebar: bool = False):
    """
    Configura uma página padrão da aplicação.
    Isso inclui o título, ícone, tema e a barra lateral.
    A verificação de autenticação é feita no main.py para garantir que apenas
    a página de login seja acessível antes da autenticação.
    """
    st.set_page_config(layout="wide", page_title=page_title, page_icon=page_icon)
    apply_dark_theme()

    # Instancia os repositórios e o serviço de autenticação
    # Estes serão singletons para a execução do script Streamlit
    user_repo = UserRepository()
    audit_repo = AuditRepository()
    auth_service = AuthService(user_repo, audit_repo)

    # Esconde links da barra lateral com base no cargo do usuário
    user_role = st.session_state.get(cfg.SESSION_STATE_USER_ROLE)
    if user_role == cfg.ROLE_CONSULTOR:
        hide_insights_link_for_consultor()
        hide_admin_link_for_consultor()

    # Inicializa o estado para o logout
    if cfg.SESSION_STATE_DO_LOGOUT not in st.session_state:
        st.session_state[cfg.SESSION_STATE_DO_LOGOUT] = False

    # Se o sinal de logout foi ativado, executa o logout e reseta o sinal
    if st.session_state[cfg.SESSION_STATE_DO_LOGOUT]:
        with get_db() as db:
            auth_service.logout_user(db)
        st.session_state[cfg.SESSION_STATE_DO_LOGOUT] = False

    if not hide_sidebar:
        with st.sidebar:
            st.write(f"Bem-vindo, {st.session_state.get(cfg.SESSION_STATE_USER_NAME, 'Usuário')}!")
            st.write(f"Cargo: {st.session_state.get(cfg.SESSION_STATE_USER_ROLE, 'N/A')}")
            st.button("Sair", on_click=lambda: st.session_state.update({cfg.SESSION_STATE_DO_LOGOUT: True}), use_container_width=True)