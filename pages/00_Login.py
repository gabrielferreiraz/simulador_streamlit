
# main.py - Ponto de Entrada e Página de Login
import streamlit as st
from src.db.database import init_db
from src.db.user_repository import add_user, get_user_by_email
from src.auth.auth_service import check_password, login_user, hash_password
from src.utils.style_utils import apply_dark_theme, hide_main_page_from_sidebar

# Configuração da página deve ser a primeira chamada do Streamlit
st.set_page_config(layout="centered", page_title="Login - Simulador Servopa", page_icon="🔑")

# Aplica o tema escuro e esconde a navegação da página principal
apply_dark_theme()
hide_main_page_from_sidebar()

def setup_initial_admin():
    """Verifica e cria o usuário mestre, se necessário."""
    master_email = "reoboteconsorciosti@gmail.com"
    if not get_user_by_email(master_email):
        try:
            master_password = st.secrets["MASTER_PASSWORD"]
        except KeyError:
            st.error("Senha mestra não encontrada nos segredos da aplicação. Adicione MASTER_PASSWORD ao seu arquivo .streamlit/secrets.toml")
            st.stop()
            
        master_password_hash = hash_password(master_password)
        add_user(
            nome="Admin Master",
            tipo_consultor="N/A",
            telefone="",
            email=master_email,
            foto_bytes=None,
            role="Admin",
            password_hash=master_password_hash
        )
        print("Master admin user created successfully.")

# Inicializa o banco de dados e o admin mestre
try:
    init_db()
    setup_initial_admin()
except Exception as e:
    st.error(f"Erro crítico na inicialização da aplicação: {e}")
    st.stop()

# --- Lógica de Navegação e Estado ---

# Se o usuário já está autenticado, redireciona para o simulador
if check_password():
    st.switch_page("pages/1_📊_Simulador.py")

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
            if login_user(email, password):
                st.switch_page("pages/1_📊_Simulador.py")

# Renderiza a página de login
login_page()
