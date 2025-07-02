import streamlit as st
import logging
from src.db.database import init_db, get_db
from src.db.user_repository import UserRepository
from src.auth.auth_service import AuthService
from src.db.audit_repository import AuditRepository
from src.utils.style_utils import apply_dark_theme, hide_main_page_from_sidebar, hide_all_pages_except_login
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, NoResultFound

# Configura o logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    
    user_repo = UserRepository()
    audit_repo = AuditRepository()
    auth_service = AuthService(user_repo, audit_repo)

    with get_db() as db:
        try:
            # Tenta buscar o usuário mestre
            user_repo.get_by_email(db, master_email)
            logging.info("Master admin user already exists.")
        except NoResultFound:
            # Se não existir, cria o usuário mestre
            try:
                master_password = st.secrets["MASTER_PASSWORD"]
            except KeyError:
                st.error("Senha mestra não encontrada nos segredos da aplicação. Adicione MASTER_PASSWORD ao seu arquivo .streamlit/secrets.toml")
                st.stop()
                
            master_password_hash = auth_service.hash_password(master_password)
            try:
                user_repo.add(
                    db,
                    nome="Admin Master",
                    tipo_consultor="N/A",
                    telefone="",
                    email=master_email,
                    foto_bytes=None,
                    role="Admin",
                    password_hash=master_password_hash
                )
                db.commit() # Commit explícito para o setup inicial
                logging.info("Master admin user created successfully.")
            except IntegrityError:
                logging.warning("Master admin user was created by another process concurrently.")
            except SQLAlchemyError as e:
                logging.error(f"Erro de banco de dados ao criar usuário mestre: {e}", exc_info=True)
                st.error(f"Erro de banco de dados ao criar usuário mestre: {e}")
                st.stop()
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco de dados ao verificar usuário mestre: {e}", exc_info=True)
            st.error(f"Erro de banco de dados ao verificar usuário mestre: {e}")
            st.stop()

# Inicializa o banco de dados e o admin mestre
try:
    init_db() # Cria as tabelas se não existirem
    setup_initial_admin()
except Exception as e:
    logging.critical(f"Erro crítico na inicialização da aplicação: {e}", exc_info=True)
    st.error(f"Erro crítico na inicialização da aplicação: {e}")
    st.stop()

# Verifica se o usuário está autenticado. Se não estiver, redireciona para o login e esconde outras páginas.
user_repo_for_auth_check = UserRepository()
audit_repo_for_auth_check = AuditRepository()
auth_service_for_check = AuthService(user_repo_for_auth_check, audit_repo_for_auth_check)

if not auth_service_for_check.check_password():
    hide_all_pages_except_login()
    st.switch_page("pages/00_Login.py")

# Se o usuário estiver autenticado, a execução continua normalmente para a página principal
st.switch_page("pages/simulador.py")
