"""
Módulo de serviço para a página de Administração.

Encapsula toda a lógica de negócio para gerenciamento de usuários e equipes,
servindo como uma camada intermediária entre a UI e os repositórios de dados.
Isso mantém a UI limpa e focada na apresentação, enquanto a lógica de negócio
é centralizada, testável e reutilizável.
"""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound

from src.auth.auth_service import AuthService
from src.db.models import User, Team # Importa os modelos SQLAlchemy
from src.db.user_repository import UserRepository
from src.db.team_repository import TeamRepository
from src.db.audit_repository import AuditRepository
from src.db.data_models import UserStats, TeamWithSupervisor # Dataclasses para retorno de dados
from src.schemas.user import UserCreate, UserUpdate # Importa os esquemas Pydantic

logger = logging.getLogger(__name__)

class AdminService:
    """Orquestra as operações de administração."""

    def __init__(self, user_repo: UserRepository, team_repo: TeamRepository, audit_repo: AuditRepository, auth_service: AuthService):
        self.user_repo = user_repo
        self.team_repo = team_repo
        self.audit_repo = audit_repo
        self.auth_service = auth_service

    # --- Operações de Usuário ---

    def get_all_users_with_team_info(self, db: Session) -> List[User]:
        """Retorna todos os usuários com informações de suas equipes (modelos SQLAlchemy)."""
        return self.user_repo.get_all_with_team_info(db)

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Busca um usuário por ID."""
        try:
            return self.user_repo.get_by_id(db, user_id)
        except NoResultFound:
            return None

    def create_user(self, db: Session, user_data: UserCreate) -> User:
        """Cria um novo usuário a partir de um esquema Pydantic validado."""
        password_hash = self.auth_service.hash_password(user_data.password)
        user = self.user_repo.add(
            db, 
            nome=user_data.nome, 
            email=user_data.email, 
            password_hash=password_hash, 
            role=user_data.role,
            tipo_consultor=user_data.tipo_consultor, 
            telefone=user_data.telefone, 
            foto_bytes=None # A foto será tratada separadamente na view
        )
        self.audit_repo.log_event(db, "USER_CREATED", details=f"User '{user_data.nome}' (ID: {user.id}) created.")
        return user

    def update_user(self, db: Session, user_id: int, user_data: UserUpdate, foto_bytes: Optional[bytes] = None):
        """Atualiza os dados de um usuário a partir de um esquema Pydantic validado."""
        user = self.user_repo.get_by_id(db, user_id)
        
        if user_data.nome: user.nome = user_data.nome
        if user_data.email: user.email = user_data.email
        if user_data.role: user.role = user_data.role
        if user_data.tipo_consultor: user.tipo_consultor = user_data.tipo_consultor
        if user_data.telefone: user.telefone = user_data.telefone
        if foto_bytes is not None: user.foto = foto_bytes

        if user_data.password:
            user.password = self.auth_service.hash_password(user_data.password)
            
        self.user_repo.update(db, user)
        self.audit_repo.log_event(db, "USER_UPDATED", details=f"User '{user.nome}' (ID: {user.id}) updated.")

    def delete_user(self, db: Session, user_id: int):
        """Deleta um usuário."""
        self.user_repo.delete(db, user_id)
        self.audit_repo.log_event(db, "USER_DELETED", details=f"User ID {user_id} deleted.")

    # --- Operações de Equipe ---

    def get_all_teams_with_supervisor_info(self, db: Session) -> List[TeamWithSupervisor]:
        """Retorna todas as equipes com informações de seus supervisores (dataclass)."""
        return self.team_repo.get_all_with_supervisor_info(db)

    def get_available_supervisors(self, db: Session) -> List[User]:
        """Retorna usuários que são supervisores e não estão gerenciando uma equipe."""
        all_users = self.user_repo.get_all_with_team_info(db) # Retorna modelos User
        teams = self.team_repo.get_all_with_supervisor_info(db) # Retorna dataclasses TeamWithSupervisor
        assigned_supervisor_ids = {team.supervisor_id for team in teams if team.supervisor_id is not None}
        
        available = [
            user for user in all_users 
            if user.role == 'Supervisor' and user.id not in assigned_supervisor_ids
        ]
        return available

    def create_team(self, db: Session, name: str, supervisor_id: int):
        """Cria uma nova equipe."""
        team = self.team_repo.create(db, name, supervisor_id)
        self.audit_repo.log_event(db, "TEAM_CREATED", details=f"Team '{name}' (ID: {team.id}) created.")

    def update_team_members(self, db: Session, team_id: int, member_ids: List[int]):
        """Atualiza os membros de uma equipe."""
        self.team_repo.update_members(db, team_id, member_ids)
        self.audit_repo.log_event(db, "TEAM_MEMBERS_UPDATED", details=f"Members for team ID {team_id} updated.")

    def delete_team(self, db: Session, team_id: int):
        """Deleta uma equipe."""
        self.team_repo.delete(db, team_id)
        self.audit_repo.log_event(db, "TEAM_DELETED", details=f"Team ID {team_id} deleted.")