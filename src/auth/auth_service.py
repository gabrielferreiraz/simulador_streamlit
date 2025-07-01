"""Módulo para serviços de autenticação, como hashing e verificação de senhas."""

import bcrypt
import streamlit as st
import logging
from typing import Tuple, Optional

from src.db.user_repository import get_user_by_email
from src.db.audit_repository import log_audit_event

# Configura o logger para este módulo
logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """
    Gera o hash de uma senha usando bcrypt.

    Args:
        password (str): A senha em texto plano a ser hasheada.

    Returns:
        str: O hash da senha codificado em UTF-8.
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde a um hash.

    Args:
        password (str): A senha em texto plano.
        hashed_password (str): O hash da senha armazenado.

    Returns:
        bool: True se a senha corresponder ao hash, False caso contrário.
    """
    if not password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except (ValueError, TypeError):
        logger.warning("Tentativa de verificação de senha com hash inválido ou malformado.")
        return False

def check_password() -> bool:
    """
    Verifica se o usuário na sessão atual do Streamlit está autenticado.

    Returns:
        bool: True se o usuário estiver autenticado, False caso contrário.
    """
    return st.session_state.get("authenticated", False)

def login_user(email: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Tenta autenticar um usuário e, em caso de sucesso, atualiza o estado da sessão.

    Args:
        email (str): O e-mail do usuário.
        password (str): A senha do usuário.

    Returns:
        Tuple[bool, Optional[str]]: Uma tupla contendo (True, None) em caso de sucesso,
                                     ou (False, mensagem_de_erro) em caso de falha.
    """
    if not email or not password:
        return False, "E-mail e senha são obrigatórios."

    user_data = get_user_by_email(email)
    if not user_data:
        log_audit_event(None, "LOGIN_FAILURE", f"Tentativa de login para e-mail não registrado: {email}.")
        logger.warning(f"Falha no login: e-mail não encontrado '{email}'.")
        return False, "E-mail ou senha inválidos."

    # user_data: (id, nome, tipo_consultor, telefone, email, foto, role, team_id, password)
    user_id, user_name, _, _, user_email, _, user_role, _, stored_password_hash = user_data

    if verify_password(password, stored_password_hash):
        st.session_state["authenticated"] = True
        st.session_state["user_id"] = user_id
        st.session_state["user_name"] = user_name
        st.session_state["user_role"] = user_role
        
        log_audit_event(user_id, "LOGIN_SUCCESS", f"Usuário {user_name} ({user_email}) logado com sucesso.")
        logger.info(f"Usuário '{user_name}' (ID: {user_id}) autenticado com sucesso.")
        return True, None
    else:
        log_audit_event(user_id, "LOGIN_FAILURE", f"Tentativa de login com senha incorreta para o usuário {user_name} ({user_email}).")
        logger.warning(f"Falha no login: senha incorreta para o usuário '{user_name}' (ID: {user_id}).")
        return False, "E-mail ou senha inválidos."

def logout_user():
    """
    Desconecta o usuário, registra o evento e limpa completamente o estado da sessão.
    """
    user_id = st.session_state.get("user_id")
    user_name = st.session_state.get("user_name", "N/A")

    if user_id:
        log_audit_event(user_id, "LOGOUT", f"Usuário {user_name} (ID: {user_id}) desconectado.")
        logger.info(f"Usuário '{user_name}' (ID: {user_id}) desconectado.")

    # Lista de chaves para limpar para garantir uma sessão limpa
    keys_to_clear = [
        "authenticated", "user_id", "user_name", "user_role",
        "simulation_inputs", "simulation_results",
        "confirming_delete_user", "confirming_delete_team"
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            
    st.info("Você foi desconectado com segurança.")
    st.switch_page("pages/00_Login.py")
