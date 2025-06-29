# src/utils/page_setup.py
import streamlit as st
from src.auth.auth_service import check_password, logout_user
from src.utils.style_utils import apply_dark_theme

def setup_page(page_title: str, page_icon: str, hide_sidebar: bool = False):
    """
    Configura uma página padrão da aplicação.
    Isso inclui o título, ícone, tema, verificação de autenticação e a barra lateral.
    """
    st.set_page_config(layout="wide", page_title=page_title, page_icon=page_icon)
    apply_dark_theme()

    if not check_password():
        st.warning("Por favor, faça o login para acessar esta página.")
        st.page_link("main.py", label="Ir para a página de Login", icon="🏠")
        st.stop()

    if not hide_sidebar:
        with st.sidebar:
            st.title("Navegação")
            st.write(f"Bem-vindo, {st.session_state.get('user_name', 'Usuário')}!")
            st.write(f"Cargo: {st.session_state.get('user_role', 'N/A')}")
            
            # Adiciona um link para cada página
            st.page_link("pages/1_📊_Simulador.py", label="Simulador", icon="📊")
            st.page_link("pages/2_📈_Insights.py", label="Insights", icon="📈")
            
            # Mostra o link de Admin apenas para usuários autorizados
            if st.session_state.get("user_role") in ["Admin", "Supervisor"]:
                st.page_link("pages/3_⚙️_Administrador.py", label="Usuários e Equipe", icon="⚙️")

            st.button("Sair", on_click=logout_user, use_container_width=True)
