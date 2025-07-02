"""
Refatorado: Módulo de serviço de autenticação.

Este serviço agora é uma classe que recebe os repositórios de usuário e auditoria
por injeção de dependência. Ele utiliza bcrypt para hashing de senhas e interage
com o banco de dados através dos repositórios, garantindo uma separação clara
de responsabilidades e facilitando a testabilidade.
"""
import logging
from typing import Tuple, Optional

import bcrypt
import streamlit as st
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.db.user_repository import UserRepository
from src.db.audit_repository import AuditRepository
from src.config import config as cfg

logger = logging.getLogger(__name__)

class AuthService:
    """Gerencia a autenticação e autorização de usuários."""

    def __init__(self, user_repo: UserRepository, audit_repo: AuditRepository):
        self.user_repo = user_repo
        self.audit_repo = audit_repo

    def hash_password(self, password: str) -> str:
        """
        Gera o hash de uma senha usando bcrypt.

        Args:
            password (str): A senha em texto plano a ser hasheada.

        Returns:
            str: O hash da senha codificado em UTF-8.
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
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

    def check_password(self) -> bool:
        """
        Verifica se o usuário na sessão atual do Streamlit está autenticado.

        Returns:
            bool: True se o usuário estiver autenticado, False caso contrário.
        """
        return st.session_state.get(cfg.SESSION_STATE_AUTHENTICATED, False)

    def login_user(self, db: Session, email: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Tenta autenticar um usuário e, em caso de sucesso, atualiza o estado da sessão.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            email (str): O e-mail do usuário.
            password (str): A senha do usuário.

        Returns:
            Tuple[bool, Optional[str]]: Uma tupla contendo (True, None) em caso de sucesso,
                                         ou (False, mensagem_de_erro) em caso de falha.
        """
        if not email or not password:
            return False, "E-mail e senha são obrigatórios."

        try:
            user = self.user_repo.get_by_email(db, email)
        except NoResultFound:
            self.audit_repo.log_event(db, "LOGIN_FAILURE", None, f"Tentativa de login para e-mail não registrado: {email}.")
            logger.warning(f"Falha no login: e-mail não encontrado '{email}'.")
            return False, "E-mail ou senha inválidos."
        except Exception as e:
            logger.error(f"Erro de banco de dados ao buscar usuário por e-mail: {e}", exc_info=True)
            return False, "Ocorreu um erro no sistema. Tente novamente mais tarde."

        if self.verify_password(password, user.password):
            st.session_state[cfg.SESSION_STATE_AUTHENTICATED] = True
            st.session_state[cfg.SESSION_STATE_USER_ID] = user.id
            st.session_state[cfg.SESSION_STATE_USER_NAME] = user.nome
            st.session_state[cfg.SESSION_STATE_USER_ROLE] = user.role
            
            self.audit_repo.log_event(db, "LOGIN_SUCCESS", user.id, f"Usuário {user.nome} ({user.email}) logado com sucesso.")
            logger.info(f"Usuário '{user.nome}' (ID: {user.id}) autenticado com sucesso.")
            return True, None
        else:
            self.audit_repo.log_event(db, "LOGIN_FAILURE", user.id, f"Tentativa de login com senha incorreta para o usuário {user.nome} ({user.email}).")
            logger.warning(f"Falha no login: senha incorreta para o usuário '{user.nome}' (ID: {user.id}).")
            return False, "E-mail ou senha inválidos."

    def logout_user(self, db: Session):
        """
        Desconecta o usuário, registra o evento e limpa completamente o estado da sessão.
        """
        user_id = st.session_state.get(cfg.SESSION_STATE_USER_ID)
        user_name = st.session_state.get(cfg.SESSION_STATE_USER_NAME, "N/A")

        if user_id:
            self.audit_repo.log_event(db, "LOGOUT", user_id, f"Usuário {user_name} (ID: {user_id}) desconectado.")
            logger.info(f"Usuário '{user_name}' (ID: {user_id}) desconectado.")

        # Lista de chaves para limpar para garantir uma sessão limpa
        keys_to_clear = [
            cfg.SESSION_STATE_AUTHENTICATED, cfg.SESSION_STATE_USER_ID, 
            cfg.SESSION_STATE_USER_NAME, cfg.SESSION_STATE_USER_ROLE,
            cfg.SESSION_STATE_SIMULATION_INPUTS, cfg.SESSION_STATE_SIMULATION_RESULTS,
            cfg.SESSION_STATE_CONFIRMING_DELETE_USER, cfg.SESSION_STATE_CONFIRMING_DELETE_TEAM,
            cfg.SESSION_STATE_DO_LOGOUT
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
                
        st.info("Você foi desconectado com segurança.")
        st.switch_page("pages/00_Login.py")