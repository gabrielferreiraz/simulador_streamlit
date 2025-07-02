import streamlit as st
from src.auth.auth_service import AuthService
from src.db import get_db
from src.db.user_repository import UserRepository
from src.db.audit_repository import AuditRepository
from src.schemas.auth import LoginInput # Importa o esquema Pydantic
from pydantic import ValidationError # Importa ValidationError

# Configuração da página deve ser a primeira chamada do Streamlit
st.set_page_config(page_title="Login", page_icon="🔑", layout="centered")

# Instancia os repositórios e o serviço de autenticação
# Estes serão singletons para a execução do script Streamlit
user_repo = UserRepository()
audit_repo = AuditRepository()
auth_service = AuthService(user_repo, audit_repo)

# Se o usuário já está autenticado, redireciona para a página principal
if auth_service.check_password():
    st.switch_page("pages/simulador.py")

def login_page():
    """Renderiza a página e o formulário de login."""
    st.title("Login - Simulador Servopa")
    st.markdown("Por favor, faça login para acessar o sistema.")

    with st.form("login_form"):
        email = st.text_input(
            "E-mail", 
            key="login_email",
            placeholder="seu.email@servopa.com.br"
        )
        password = st.text_input(
            "Senha", 
            type="password", 
            key="login_password",
            placeholder="Sua senha"
        )
        submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            login_data = {"email": email, "password": password}
            try:
                # Valida os dados com Pydantic
                validated_login_data = LoginInput(**login_data)

                with get_db() as db:
                    success, message = auth_service.login_user(db, validated_login_data.email, validated_login_data.password)
                    if success:
                        st.success("Login bem-sucedido! Redirecionando...")
                        st.switch_page("pages/simulador.py")
                        st.stop()
                    else:
                        st.error(message)
            except ValidationError as e:
                st.error(f"Erro de validação: {e}")
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado: {e}")

# Renderiza a página de login
login_page()
