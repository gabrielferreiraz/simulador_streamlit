"""
Refatorado: Módulo de serviço para calcular e agregar métricas para relatórios e insights.

Este serviço agora utiliza SQLAlchemy para interagir com o banco de dados,
proporcionando uma forma mais robusta e orientada a objetos de buscar e agregar dados.
Ele é o único lugar que deve usar a biblioteca `pandas` para manipulação de dados,
preparando-os para serem consumidos pela UI (gráficos).
"""
import pandas as pd
import logging
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from src.db.models import User, Team, Simulation # Importa os modelos SQLAlchemy
from src.db.data_models import GeneralMetrics

logger = logging.getLogger(__name__)

class MetricsService:
    """Fornece métodos para calcular métricas de negócio a partir dos dados brutos."""

    def get_general_metrics(self, db: Session, team_id: Optional[int] = None) -> GeneralMetrics:
        """
        Busca métricas gerais (total, média de crédito, média de prazo).
        """
        try:
            stmt = select(
                func.count(Simulation.id).label("total_simulacoes"),
                func.coalesce(func.avg(Simulation.valor_credito), 0).label("media_credito"),
                func.coalesce(func.avg(Simulation.prazo_meses), 0).label("media_prazo")
            )
            if team_id:
                stmt = stmt.join(User, Simulation.user_id == User.id).where(User.team_id == team_id)
            
            result = db.execute(stmt).fetchone()
            
            if result:
                return GeneralMetrics(
                    total_simulacoes=result.total_simulacoes,
                    media_credito=result.media_credito,
                    media_prazo=result.media_prazo
                )
            return GeneralMetrics()
        except SQLAlchemyError as e:
            logger.error(f"Falha ao buscar métricas gerais (team_id: {team_id}): {e}", exc_info=True)
            raise # Re-lança a exceção para a camada superior

    def get_simulations_per_day(self, db: Session, team_id: Optional[int] = None) -> pd.DataFrame:
        """
        Busca o número de simulações por dia para gráficos.
        """
        try:
            stmt = select(
                func.strftime("%Y-%m-%d", Simulation.timestamp).label("data"),
                func.count(Simulation.id).label("simulacoes")
            )
            if team_id:
                stmt = stmt.join(User, Simulation.user_id == User.id).where(User.team_id == team_id)
            stmt = stmt.group_by(func.strftime("%Y-%m-%d", Simulation.timestamp)).order_by("data")
            
            rows = db.execute(stmt).fetchall()
            return pd.DataFrame(rows, columns=["data", "simulacoes"])
        except SQLAlchemyError as e:
            logger.error(f"Falha ao buscar simulações por dia (team_id: {team_id}): {e}", exc_info=True)
            return pd.DataFrame({'data': [], 'simulacoes': []}) # Retorna DF vazio com schema

    def get_credit_distribution(self, db: Session, team_id: Optional[int] = None) -> pd.DataFrame:
        """
        Busca a distribuição de crédito para o histograma.
        """
        try:
            stmt = select(Simulation.valor_credito)
            if team_id:
                stmt = stmt.join(User, Simulation.user_id == User.id).where(User.team_id == team_id)
            
            rows = db.execute(stmt).fetchall()
            return pd.DataFrame(rows, columns=['valor_credito'])
        except SQLAlchemyError as e:
            logger.error(f"Falha ao buscar distribuição de crédito (team_id: {team_id}): {e}", exc_info=True)
            return pd.DataFrame({'valor_credito': []})

    def get_simulations_by_consultant(self, db: Session, team_id: Optional[int] = None) -> pd.DataFrame:
        """
        Busca a contagem de simulações por consultor.
        """
        try:
            stmt = select(
                func.coalesce(User.nome, 'Usuário Removido').label("consultor"),
                func.count(Simulation.id).label("simulacoes")
            ).join(User, Simulation.user_id == User.id, isouter=True)
            
            if team_id:
                stmt = stmt.where(User.team_id == team_id)
            
            stmt = stmt.group_by("consultor").order_by(func.count(Simulation.id).desc())
            
            rows = db.execute(stmt).fetchall()
            return pd.DataFrame(rows, columns=["consultor", "simulacoes"])
        except SQLAlchemyError as e:
            logger.error(f"Falha ao buscar simulações por consultor (team_id: {team_id}): {e}", exc_info=True)
            return pd.DataFrame({'consultor': [], 'simulacoes': []})

    def get_team_simulation_stats(self, db: Session) -> pd.DataFrame:
        """
        Agrega estatísticas de simulação por equipe.
        """
        try:
            stmt = select(
                func.coalesce(Team.name, 'Sem Equipe').label("equipe"),
                func.count(Simulation.id).label("simulacoes")
            ).join(User, Simulation.user_id == User.id)
            stmt = stmt.join(Team, User.team_id == Team.id, isouter=True)
            stmt = stmt.group_by("equipe").order_by(func.count(Simulation.id).desc())
            
            rows = db.execute(stmt).fetchall()
            return pd.DataFrame(rows, columns=["equipe", "simulacoes"])
        except SQLAlchemyError as e:
            logger.error(f"Falha ao calcular estatísticas por equipe: {e}", exc_info=True)
            return pd.DataFrame({'equipe': [], 'simulacoes': []})