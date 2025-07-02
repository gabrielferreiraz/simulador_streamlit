"""
Refatorado: Módulo de repositório para operações de usuários usando SQLAlchemy.

Este repositório agora interage com o banco de dados através do ORM SQLAlchemy,
utilizando objetos de sessão para todas as operações. Ele retorna instâncias
dos modelos SQLAlchemy diretamente, e lida com as exceções do SQLAlchemy,
proporcionando uma camada de acesso a dados mais robusta e orientada a objetos.
"""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError, NoResultFound

from src.db.models import User, Team, Simulation # Importa os modelos SQLAlchemy
from src.db.data_models import UserStats # Dataclass que ainda é usado para retorno de estatísticas

logger = logging.getLogger(__name__)

class UserRepository:
    """Gerencia todas as operações de banco de dados para a entidade User."""

    def add(
        self,
        db: Session,
        nome: str,
        email: str,
        password_hash: str,
        role: str,
        tipo_consultor: Optional[str] = None,
        telefone: Optional[str] = None,
        foto_bytes: Optional[bytes] = None,
    ) -> User:
        """
        Adiciona um novo usuário ao banco de dados.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            nome (str): Nome do usuário.
            email (str): E-mail do usuário (deve ser único).
            password_hash (str): Hash da senha do usuário.
            role (str): Papel do usuário ('Admin', 'Supervisor', 'Consultor').
            tipo_consultor (Optional[str]): Tipo de consultor (e.g., "Interno", "Externo").
            telefone (Optional[str]): Telefone de contato.
            foto_bytes (Optional[bytes]): Foto do usuário como bytes.

        Returns:
            User: O objeto User criado.

        Raises:
            IntegrityError: Se o nome ou e-mail já existirem.
        """
        new_user = User(
            nome=nome,
            tipo_consultor=tipo_consultor,
            telefone=telefone,
            email=email,
            foto=foto_bytes,
            role=role,
            password=password_hash
        )
        try:
            db.add(new_user)
            db.flush() # Garante que o ID seja gerado antes do commit
            logger.info(f"Usuário '{nome}' (ID: {new_user.id}) adicionado com sucesso.")
            return new_user
        except IntegrityError as e:
            logger.warning(f"Falha ao adicionar usuário. Conflito de integridade para nome '{nome}' ou e-mail '{email}'.")
            raise e # Re-lança a exceção do SQLAlchemy

    def get_all_with_team_info(self, db: Session) -> List[User]:
        """
        Busca todos os usuários com informações de suas equipes.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.

        Returns:
            List[User]: Uma lista de objetos User, com a relação `team` carregada.
        """
        # Carrega a relação 'team' para evitar N+1 queries
        stmt = select(User).order_by(User.nome).options(selectinload(User.team))
        users = db.execute(stmt).scalars().all()
        return users

    def get_by_id(self, db: Session, user_id: int) -> User:
        """
        Busca um usuário pelo ID.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            user_id (int): O ID do usuário.

        Returns:
            User: O objeto User encontrado.

        Raises:
            NoResultFound: Se o usuário não for encontrado.
        """
        stmt = select(User).where(User.id == user_id)
        user = db.execute(stmt).scalar_one_or_none()
        if user is None:
            raise NoResultFound(f"Usuário com ID {user_id} não encontrado.")
        return user

    def get_by_email(self, db: Session, email: str) -> User:
        """
        Busca um usuário pelo e-mail.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            email (str): O e-mail do usuário.

        Returns:
            User: O objeto User encontrado.

        Raises:
            NoResultFound: Se o usuário não for encontrado.
        """
        stmt = select(User).where(User.email == email)
        user = db.execute(stmt).scalar_one_or_none()
        if user is None:
            raise NoResultFound(f"Usuário com e-mail {email} não encontrado.")
        return user

    def update(self, db: Session, user: User) -> User:
        """
        Atualiza os dados de um usuário existente a partir de um objeto User.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            user (User): O objeto User com os dados atualizados. O ID deve estar presente.

        Returns:
            User: O objeto User atualizado.

        Raises:
            NoResultFound: Se o usuário a ser atualizado não existir.
            IntegrityError: Se a atualização violar uma restrição de unicidade.
        """
        existing_user = db.get(User, user.id)
        if existing_user is None:
            raise NoResultFound(f"Usuário com ID {user.id} não encontrado para atualização.")

        try:
            # Atualiza os atributos do objeto existente
            existing_user.nome = user.nome
            existing_user.tipo_consultor = user.tipo_consultor
            existing_user.telefone = user.telefone
            existing_user.email = user.email
            existing_user.foto = user.foto
            existing_user.role = user.role
            existing_user.password = user.password # Assume que o hash já foi feito se a senha mudou
            existing_user.team_id = user.team_id

            db.flush() # Garante que as validações de integridade sejam checadas
            logger.info(f"Usuário ID {user.id} ({user.nome}) atualizado com sucesso.")
            return existing_user
        except IntegrityError as e:
            logger.warning(f"Falha ao atualizar usuário ID {user.id}. Conflito de integridade.")
            raise e

    def delete(self, db: Session, user_id: int):
        """
        Deleta um usuário do sistema.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            user_id (int): O ID do usuário a ser deletado.

        Raises:
            NoResultFound: Se o usuário a ser deletado não existir.
        """
        user_to_delete = db.get(User, user_id)
        if user_to_delete is None:
            raise NoResultFound(f"Usuário com ID {user_id} não encontrado para exclusão.")
        db.delete(user_to_delete)
        logger.info(f"Usuário ID {user_id} deletado com sucesso.")

    def get_simulation_stats(self, db: Session, user_id: int) -> UserStats:
        """
        Calcula estatísticas de simulação para um usuário específico.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            user_id (int): O ID do usuário.

        Returns:
            UserStats: Um objeto UserStats com as estatísticas.
        """
        # Usando SQLAlchemy Core para agregação para maior flexibilidade
        stmt = select(
            func.count(Simulation.id).label("total_simulacoes"),
            func.coalesce(func.avg(Simulation.valor_credito), 0).label("media_credito"),
            func.coalesce(func.sum(Simulation.valor_credito), 0).label("total_credito")
        ).where(Simulation.user_id == user_id)

        result = db.execute(stmt).fetchone()
        
        if result:
            return UserStats(
                total_simulacoes=result.total_simulacoes,
                media_credito=result.media_credito,
                total_credito=result.total_credito
            )
        return UserStats() # Retorna estatísticas zeradas se não houver dados
