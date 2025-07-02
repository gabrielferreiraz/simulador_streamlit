"""
Refatorado: Módulo de repositório para operações de auditoria usando SQLAlchemy.

Este repositório agora interage com o banco de dados através do ORM SQLAlchemy,
utilizando objetos de sessão para todas as operações. Ele retorna instâncias
dos modelos SQLAlchemy diretamente, e lida com as exceções do SQLAlchemy,
proporcionando uma camada de acesso a dados mais robusta e orientada a objetos.
"""
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select

from src.db.models import AuditLog # Importa o modelo SQLAlchemy

logger = logging.getLogger(__name__)

class AuditRepository:
    """Gerencia as operações de banco de dados para a entidade AuditLog."""

    def log_event(self, db: Session, action_type: str, user_id: Optional[int] = None, details: Optional[str] = None):
        """
        Registra um novo evento de auditoria no banco de dados.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            action_type (str): O tipo de ação sendo registrada (ex: 'LOGIN_SUCCESS').
            user_id (Optional[int]): O ID do usuário associado ao evento.
            details (Optional[str]): Detalhes adicionais sobre o evento.
        """
        new_log = AuditLog(
            timestamp=datetime.now(),
            user_id=user_id,
            action_type=action_type,
            details=details
        )
        try:
            db.add(new_log)
            db.flush() # Garante que o log seja persistido mesmo que a transação falhe mais tarde
            logger.info(f"Evento de auditoria registrado: {action_type} para usuário ID {user_id}")
        except Exception as e:
            # Loga o erro, mas não propaga a exceção para não quebrar a funcionalidade principal
            # que gerou o evento de auditoria. A transação será revertida pelo get_db().
            logger.error(f"Falha ao registrar evento de auditoria: {e}", exc_info=True)

    def get_all_logs(self, db: Session, limit: int = 100) -> List[AuditLog]:
        """
        Busca os eventos de auditoria mais recentes.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            limit (int): O número máximo de logs a serem retornados.

        Returns:
            List[AuditLog]: Uma lista de objetos AuditLog.
        """
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
        return db.execute(stmt).scalars().all()