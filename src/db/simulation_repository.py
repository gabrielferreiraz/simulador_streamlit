"""
Módulo de repositório para todas as operações de banco de dados relacionadas a simulações.
"""
import sqlite3
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, Any, Optional, Tuple

from .database import get_db_connection

# Configura o logger para este módulo
logger = logging.getLogger(__name__)

def log_simulation(user_id: int, inputs: Dict[str, Any], results: Dict[str, Any], nome_cliente: str):
    """
    Registra uma simulação completa no banco de dados de forma segura.

    Args:
        user_id (int): ID do usuário que realizou a simulação.
        inputs (Dict[str, Any]): Dicionário com os dados de entrada da simulação.
        results (Dict[str, Any]): Dicionário com os resultados do cálculo.
        nome_cliente (str): Nome do cliente associado à simulação.
    """
    sql = """
        INSERT INTO simulations (
            timestamp, user_id, nome_cliente,
            valor_credito, prazo_meses, taxa_administracao_total, opcao_plano_light, 
            opcao_seguro_prestamista, percentual_lance_ofertado, percentual_lance_embutido, 
            qtd_parcelas_lance_ofertado, opcao_diluir_lance, assembleia_atual, 
            credito_disponivel, nova_parcela_pos_lance, saldo_devedor_base_final, 
            valor_lance_recurso_proprio, credito_contratado, valor_parcela_inicial, 
            valor_lance_ofertado_total, valor_lance_embutido, total_parcelas_pagas_no_lance, 
            prazo_restante_final, percentual_parcela_base, percentual_lance_recurso_proprio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        with get_db_connection() as con:
            params = (
                datetime.now().isoformat(), user_id, nome_cliente,
                inputs.get('valor_credito'), inputs.get('prazo_meses'), inputs.get('taxa_administracao_total'),
                inputs.get('opcao_plano_light'), inputs.get('opcao_seguro_prestamista'), inputs.get('percentual_lance_ofertado'),
                inputs.get('percentual_lance_embutido'), inputs.get('qtd_parcelas_lance_ofertado'), inputs.get('opcao_diluir_lance'),
                inputs.get('assembleia_atual'), results.get('credito_disponivel'), results.get('nova_parcela_pos_lance'),
                results.get('saldo_devedor_base_final'), results.get('valor_lance_recurso_proprio'), results.get('credito_contratado'),
                results.get('valor_parcela_inicial'), results.get('valor_lance_ofertado_total'), results.get('valor_lance_embutido'),
                results.get('total_parcelas_pagas_no_lance'), results.get('prazo_restante_final'), results.get('percentual_parcela_base'),
                results.get('percentual_lance_recurso_proprio')
            )
            con.execute(sql, params)
            con.commit()
            logger.info(f"Simulação para o cliente '{nome_cliente}' pelo usuário ID {user_id} registrada com sucesso.")
    except sqlite3.Error as e:
        logger.error(f"Falha ao registrar simulação para o usuário ID {user_id}: {e}", exc_info=True)

def get_last_simulation_by_user(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Busca a simulação mais recente de um usuário específico.

    Args:
        user_id (int): O ID do usuário.

    Returns:
        Optional[Dict[str, Any]]: Um dicionário com os dados da simulação ou None.
    """
    sql = "SELECT * FROM simulations WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1"
    try:
        with get_db_connection() as con:
            last_sim_row = con.execute(sql, (user_id,)).fetchone()
        return dict(last_sim_row) if last_sim_row else None
    except sqlite3.Error as e:
        logger.error(f"Falha ao buscar a última simulação do usuário ID {user_id}: {e}", exc_info=True)
        return None

def get_general_metrics(team_id: Optional[int] = None) -> Tuple[int, float, float]:
    """
    Busca métricas gerais (total, média de crédito, média de prazo) para todos os usuários
    ou para uma equipe específica.

    Args:
        team_id (Optional[int]): O ID da equipe para filtrar os resultados. Se None, busca para todos.

    Returns:
        Tuple[int, float, float]: (total_simulações, média_crédito, média_prazo).
    """
    base_sql = "SELECT COUNT(s.id), AVG(s.valor_credito), AVG(s.prazo_meses) FROM simulations s"
    params = []
    if team_id:
        base_sql += " JOIN users u ON s.user_id = u.id WHERE u.team_id = ?"
        params.append(team_id)
    
    try:
        with get_db_connection() as con:
            metrics = con.execute(base_sql, params).fetchone()
        if metrics and metrics[0] is not None:
            return metrics[0], metrics[1] or 0, metrics[2] or 0
        return 0, 0.0, 0.0
    except sqlite3.Error as e:
        logger.error(f"Falha ao buscar métricas gerais (team_id: {team_id}): {e}", exc_info=True)
        return 0, 0.0, 0.0

def get_simulations_per_day(team_id: Optional[int] = None) -> pd.DataFrame:
    """
    Busca o número de simulações por dia, com filtro opcional por equipe.

    Args:
        team_id (Optional[int]): O ID da equipe para filtrar.

    Returns:
        pd.DataFrame: DataFrame com colunas 'data' e 'simulacoes'.
    """
    sql = "SELECT DATE(s.timestamp) as data, COUNT(s.id) as simulacoes FROM simulations s"
    params = ()
    if team_id:
        sql += " JOIN users u ON s.user_id = u.id WHERE u.team_id = ?"
        params = (team_id,)
    sql += " GROUP BY data ORDER BY data"
    
    try:
        with get_db_connection() as con:
            return pd.read_sql_query(sql, con, params=params)
    except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
        logger.error(f"Falha ao buscar simulações por dia (team_id: {team_id}): {e}", exc_info=True)
        return pd.DataFrame()

def get_credit_distribution(team_id: Optional[int] = None) -> pd.DataFrame:
    """
    Busca a coluna de valor_credito para o histograma, com filtro opcional por equipe.

    Args:
        team_id (Optional[int]): O ID da equipe para filtrar.

    Returns:
        pd.DataFrame: DataFrame com a coluna 'valor_credito'.
    """
    sql = "SELECT s.valor_credito FROM simulations s"
    params = ()
    if team_id:
        sql += " JOIN users u ON s.user_id = u.id WHERE u.team_id = ?"
        params = (team_id,)
        
    try:
        with get_db_connection() as con:
            return pd.read_sql_query(sql, con, params=params)
    except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
        logger.error(f"Falha ao buscar distribuição de crédito (team_id: {team_id}): {e}", exc_info=True)
        return pd.DataFrame()

def get_simulations_by_consultant(team_id: Optional[int] = None) -> pd.DataFrame:
    """
    Busca a contagem de simulações por consultor, com filtro opcional por equipe.

    Args:
        team_id (Optional[int]): O ID da equipe para filtrar.

    Returns:
        pd.DataFrame: DataFrame com 'consultor' e 'simulacoes'.
    """
    sql = """
        SELECT COALESCE(u.nome, 'Usuário Removido') as consultor, COUNT(s.id) as simulacoes
        FROM simulations s
        LEFT JOIN users u ON s.user_id = u.id
    """
    params = ()
    if team_id:
        sql += " WHERE u.team_id = ?"
        params = (team_id,)
    sql += " GROUP BY consultor ORDER BY simulacoes DESC"
    
    try:
        with get_db_connection() as con:
            return pd.read_sql_query(sql, con, params=params)
    except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
        logger.error(f"Falha ao buscar simulações por consultor (team_id: {team_id}): {e}", exc_info=True)
        return pd.DataFrame()

def get_team_simulation_stats() -> pd.DataFrame:
    """
    Agrega estatísticas de simulação por equipe. Apenas para Admins.

    Returns:
        pd.DataFrame: DataFrame com 'equipe' e 'simulacoes'.
    """
    sql = """
        SELECT COALESCE(t.name, 'Sem Equipe') as equipe, COUNT(s.id) as simulacoes
        FROM simulations s
        LEFT JOIN users u ON s.user_id = u.id
        LEFT JOIN teams t ON u.team_id = t.id
        GROUP BY equipe
        ORDER BY simulacoes DESC
    """
    try:
        with get_db_connection() as con:
            return pd.read_sql_query(sql, con)
    except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
        logger.error(f"Falha ao calcular estatísticas por equipe: {e}", exc_info=True)
        return pd.DataFrame()
