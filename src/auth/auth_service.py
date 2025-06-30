import bcrypt
import streamlit as st
from src.db.user_repository import get_user_by_email
from src.db.audit_repository import log_audit_event

def hash_password(password: str) -> str:
    """Gera o hash de uma senha."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    if not password or not hashed_password:
        return False
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def check_password() -> bool:
    """Verifica se o usuário na sessão atual está autenticado."""
    return st.session_state.get("authenticated", False)

def login_user(email: str, password: str) -> tuple[bool, str | None]:
    """Tenta autenticar um usuário e atualiza o estado da sessão.
    Retorna (True, None) em caso de sucesso ou (False, mensagem_de_erro) em caso de falha.
    """
    user_data = get_user_by_email(email)
    if user_data:
        # user_data: (id, nome, tipo_consultor, telefone, email, foto, role, team_id, password)
        stored_password = user_data[8]
        if verify_password(password, stored_password):
            st.session_state["authenticated"] = True
            st.session_state["user_id"] = user_data[0]
            st.session_state["user_name"] = user_data[1]
            st.session_state["user_role"] = user_data[6]
            log_audit_event(user_data[0], "LOGIN_SUCCESS", f"User {user_data[1]} ({user_data[4]}) logged in.")
            return True, None
        else:
            log_audit_event(None, "LOGIN_FAILURE", f"Failed login for email: {email} (incorrect password).")
            return False, "Senha incorreta."
    else:
        log_audit_event(None, "LOGIN_FAILURE", f"Failed login for email: {email} (email not found).")
        return False, "E-mail não encontrado."

def logout_user():
    """Desconecta o usuário e limpa o estado da sessão."""
    user_id = st.session_state.get("user_id")
    user_name = st.session_state.get("user_name")
    if user_id:
        log_audit_event(user_id, "LOGOUT", f"User {user_name} ({user_id}) logged out.")
    
    # Limpa todas as chaves relacionadas ao usuário
    keys_to_clear = ["authenticated", "user_id", "user_name", "user_role"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            
    st.info("Você foi desconectado.")
    st.switch_page("pages/00_Login.py")
