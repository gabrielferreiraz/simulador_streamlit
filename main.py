import streamlit as st
import logging
import locale
from src.db.database import init_db
from src.db.user_repository import add_user, get_user_by_email
from src.auth.auth_service import hash_password
from src.utils.style_utils import apply_dark_theme, hide_main_page_from_sidebar

# Configura o logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configura a localidade para o Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    st.error("Localidade 'pt_BR.UTF-8' não encontrada. A formatação de moeda pode não funcionar.")
    # Tenta uma alternativa ou define um padrão seguro
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        pass # Mantém a localidade padrão se tudo falhar

st.set_page_config(layout="centered", page_title="Simulador Servopa", page_icon="🔑")

# Carrega Font Awesome
st.markdown(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    """,
    unsafe_allow_html=True
)

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
        logging.info("Master admin user created successfully.")

# Inicializa o banco de dados e o admin mestre
try:
    init_db()
    setup_initial_admin()
except Exception as e:
    logging.error(f"Erro crítico na inicialização da aplicação: {e}")
    st.error(f"Erro crítico na inicialização da aplicação: {e}")
    st.stop()

st.switch_page("pages/00_Login.py")
