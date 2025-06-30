# src/utils/page_setup.py
import streamlit as st
from src.auth.auth_service import check_password, logout_user
from src.utils.style_utils import apply_dark_theme, hide_insights_link_for_consultor, hide_admin_link_for_consultor, hide_all_pages_except_login

def setup_page(page_title: str, page_icon: str, hide_sidebar: bool = False):
    """
    Configura uma página padrão da aplicação.
    Isso inclui o título, ícone, tema, verificação de autenticação e a barra lateral.
    """
    st.set_page_config(layout="wide", page_title=page_title, page_icon=page_icon)
    apply_dark_theme()

    if not check_password():
        st.warning("Por favor, faça o login para acessar esta página.")
        st.page_link("pages/00_Login.py", label="Ir para a página de Login", icon="🏠")
        hide_all_pages_except_login() # Esconde todas as páginas, exceto a de login
        st.stop()

    # Esconde o link de Insights e Administrador para Consultores
    if st.session_state.get("user_role") == "Consultor":
        hide_insights_link_for_consultor()
        hide_admin_link_for_consultor()

    # Inicializa o estado para o logout
    if 'do_logout' not in st.session_state:
        st.session_state.do_logout = False

    # Se o sinal de logout foi ativado, executa o logout e reseta o sinal
    if st.session_state.do_logout:
        logout_user()
        st.session_state.do_logout = False # Reseta o sinal

    if not hide_sidebar:
        with st.sidebar:
            st.write(f"Bem-vindo, {st.session_state.get('user_name', 'Usuário')}!")
            st.write(f"Cargo: {st.session_state.get('user_role', 'N/A')}")
            # O botão agora apenas define um estado, o logout é tratado fora do callback
            st.button("Sair", on_click=lambda: st.session_state.update(do_logout=True), use_container_width=True)
