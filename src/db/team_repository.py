"""
Refatorado: Módulo de repositório para operações de equipes usando SQLAlchemy.

Este repositório agora interage com o banco de dados através do ORM SQLAlchemy,
utilizando objetos de sessão para todas as operações. Ele retorna instâncias
dos modelos SQLAlchemy diretamente, e lida com as exceções do SQLAlchemy,
proporcionando uma camada de acesso a dados mais robusta e orientada a objetos.
"""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound

from src.db.models import Team, User # Importa os modelos SQLAlchemy
from src.db.data_models import TeamWithSupervisor # Dataclass que ainda é usado para retorno

logger = logging.getLogger(__name__)

class TeamRepository:
    """Gerencia todas as operações de banco de dados para a entidade Team."""

    def create(self, db: Session, name: str, supervisor_id: int) -> Team:
        """
        Cria uma nova equipe e a associa a um supervisor de forma transacional.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            name (str): O nome da nova equipe (deve ser único).
            supervisor_id (int): O ID do usuário supervisor.

        Returns:
            Team: O objeto Team criado.

        Raises:
            IntegrityError: Se o nome da equipe já existir.
            NoResultFound: Se o supervisor não for encontrado.
        """
        # Verifica se o supervisor existe
        supervisor = db.get(User, supervisor_id)
        if not supervisor:
            raise NoResultFound(f"Supervisor com ID {supervisor_id} não encontrado.")

        new_team = Team(name=name, supervisor_id=supervisor_id)
        try:
            db.add(new_team)
            db.flush() # Garante que o ID seja gerado e a integridade verificada

            # Associa o supervisor à nova equipe (se ele não tiver uma equipe já)
            # Esta lógica pode ser mais complexa dependendo das regras de negócio
            # Aqui, estamos apenas garantindo que o supervisor_id da equipe seja setado
            # e que o team_id do usuário supervisor seja atualizado.
            supervisor.team_id = new_team.id
            db.flush()

            logger.info(f"Equipe '{name}' (ID: {new_team.id}) criada, supervisionada por usuário ID {supervisor_id}.")
            return new_team
        except IntegrityError as e:
            logger.warning(f"Falha ao criar equipe. O nome '{name}' já existe.")
            raise e

    def get_all_with_supervisor_info(self, db: Session) -> List[TeamWithSupervisor]:
        """
        Busca todas as equipes com os nomes de seus supervisores.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.

        Returns:
            List[TeamWithSupervisor]: Uma lista de objetos TeamWithSupervisor.
        """
        stmt = select(Team).options(selectinload(Team.supervisor)).order_by(Team.name)
        teams = db.execute(stmt).scalars().all()
        
        # Converte para TeamWithSupervisor dataclass
        return [
            TeamWithSupervisor(
                id=team.id,
                name=team.name,
                supervisor_id=team.supervisor_id,
                supervisor_name=team.supervisor.nome if team.supervisor else None
            ) for team in teams
        ]

    def get_by_id(self, db: Session, team_id: int) -> Team:
        """
        Busca uma equipe pelo seu ID.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            team_id (int): O ID da equipe.

        Returns:
            Team: O objeto Team encontrado.

        Raises:
            NoResultFound: Se a equipe não for encontrada.
        """
        stmt = select(Team).where(Team.id == team_id)
        team = db.execute(stmt).scalar_one_or_none()
        if team is None:
            raise NoResultFound(f"Equipe com ID {team_id} não encontrada.")
        return team

    def update_members(self, db: Session, team_id: int, member_ids: List[int]):
        """
        Atualiza os membros de uma equipe.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            team_id (int): O ID da equipe a ser atualizada.
            member_ids (List[int]): A lista completa de IDs dos membros da equipe.

        Raises:
            NoResultFound: Se a equipe não for encontrada.
        """
        team = db.get(Team, team_id)
        if not team:
            raise NoResultFound(f"Equipe com ID {team_id} não encontrada para atualização de membros.")

        # Desassocia todos os usuários da equipe, exceto o supervisor
        db.query(User).filter(
            User.team_id == team_id,
            User.id != team.supervisor_id # Não desassocia o supervisor
        ).update({'team_id': None})

        # Associa os novos membros
        if member_ids:
            db.query(User).filter(User.id.in_(member_ids)).update({'team_id': team_id})
        
        db.flush()
        logger.info(f"Membros da equipe ID {team_id} atualizados.")

    def delete(self, db: Session, team_id: int):
        """
        Deleta uma equipe.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            team_id (int): O ID da equipe a ser deletada.

        Raises:
            NoResultFound: Se a equipe a ser deletada não existir.
        """
        team_to_delete = db.get(Team, team_id)
        if team_to_delete is None:
            raise NoResultFound(f"Equipe com ID {team_id} não encontrada para exclusão.")
        db.delete(team_to_delete)
        logger.info(f"Equipe ID {team_id} deletada com sucesso.")
