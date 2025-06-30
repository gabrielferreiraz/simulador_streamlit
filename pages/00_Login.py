

import streamlit as st
from src.db.user_repository import get_user_by_email
from src.auth.auth_service import check_password, login_user, hash_password

# Configuração da página deve ser a primeira chamada do Streamlit
st.set_page_config(page_title="Login", page_icon="🔑", layout="centered")

# Se o usuário já está autenticado, redireciona para o simulador
if check_password():
    st.switch_page("pages/simulador.py")

# --- Página de Login ---
def login_page():
    """Renderiza o formulário de login."""
    st.title("Login - Simulador Servopa")
    st.markdown("Por favor, faça login para acessar o sistema.")

    with st.form("login_form"):
        email = st.text_input("E-mail", key="login_email")
        password = st.text_input("Senha", type="password", key="login_password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            success, message = login_user(email, password)
            if success:
                st.switch_page("pages/simulador.py")
                st.stop()
            else:
                st.error(message)

# Renderiza a página de login
login_page()
