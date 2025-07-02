"""
Módulo para funções de recuperação de dados cacheadas com Streamlit.

Estas funções são decoradas com `@st.cache_data` para otimizar o desempenho
da aplicação, evitando consultas repetidas ao banco de dados para dados que
não mudam frequentemente. Elas obtêm sua própria sessão de banco de dados
para garantir que o cache funcione corretamente.
"""
import streamlit as st
from typing import List, Optional
import pandas as pd # Importa pandas

from sqlalchemy.orm import Session

from src.db import get_db
from src.db.user_repository import UserRepository
from src.db.team_repository import TeamRepository
from src.db.models import User, Team
from src.db.data_models import TeamWithSupervisor, GeneralMetrics
from src.reports.metrics_service import MetricsService

# Instâncias dos repositórios para uso nas funções cacheadas
# Estas instâncias são criadas uma vez por execução de script Streamlit
_user_repo = UserRepository()
_team_repo = TeamRepository()
_metrics_service = MetricsService()

@st.cache_data(ttl=3600) # Cache por 1 hora
def get_cached_all_users_with_team_info() -> List[User]:
    """
    Retorna todos os usuários com informações de equipe, utilizando cache.
    """
    with get_db() as db:
        return _user_repo.get_all_with_team_info(db)

@st.cache_data(ttl=3600) # Cache por 1 hora
def get_cached_all_teams_with_supervisor_info() -> List[TeamWithSupervisor]:
    """
    Retorna todas as equipes com informações de supervisor, utilizando cache.
    """
    with get_db() as db:
        return _team_repo.get_all_with_supervisor_info(db)

@st.cache_data(ttl=3600) # Cache por 1 hora
def get_cached_available_supervisors() -> List[User]:
    """
    Retorna usuários que são supervisores e não estão gerenciando uma equipe, utilizando cache.
    """
    with get_db() as db:
        all_users = _user_repo.get_all_with_team_info(db)
        teams = _team_repo.get_all_with_supervisor_info(db)
        assigned_supervisor_ids = {team.supervisor_id for team in teams if team.supervisor_id is not None}
        
        available = [
            user for user in all_users 
            if user.role == 'Supervisor' and user.id not in assigned_supervisor_ids
        ]
        return available

@st.cache_data(ttl=600) # Cache por 10 minutos
def get_cached_general_metrics(team_id: Optional[int] = None) -> GeneralMetrics:
    """
    Retorna métricas gerais de simulação, utilizando cache.
    """
    with get_db() as db:
        return _metrics_service.get_general_metrics(db, team_id)

@st.cache_data(ttl=600) # Cache por 10 minutos
def get_cached_simulations_per_day(team_id: Optional[int] = None) -> pd.DataFrame:
    """
    Retorna o número de simulações por dia, utilizando cache.
    """
    with get_db() as db:
        return _metrics_service.get_simulations_per_day(db, team_id)

@st.cache_data(ttl=600) # Cache por 10 minutos
def get_cached_credit_distribution(team_id: Optional[int] = None) -> pd.DataFrame:
    """
    Retorna a distribuição de crédito, utilizando cache.
    """
    with get_db() as db:
        return _metrics_service.get_credit_distribution(db, team_id)

@st.cache_data(ttl=600) # Cache por 10 minutos
def get_cached_simulations_by_consultant(team_id: Optional[int] = None) -> pd.DataFrame:
    """
    Retorna a contagem de simulações por consultor, utilizando cache.
    """
    with get_db() as db:
        return _metrics_service.get_simulations_by_consultant(db, team_id)

@st.cache_data(ttl=600) # Cache por 10 minutos
def get_cached_team_simulation_stats() -> pd.DataFrame:
    """
    Retorna estatísticas de simulação por equipe, utilizando cache.
    """
    with get_db() as db:
        return _metrics_service.get_team_simulation_stats(db)