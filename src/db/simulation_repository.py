import sqlite3
import pandas as pd
from datetime import datetime
import logging
from .database import get_db_connection

def log_simulation(user_id, inputs, resultados, nome_cliente):
    """Registra uma simulação completa no banco de dados."""
    now = datetime.now().isoformat()
    sql = """
        INSERT INTO simulations (
            timestamp, user_id, valor_credito, prazo_meses, taxa_administracao_total,
            opcao_plano_light, opcao_seguro_prestamista, percentual_lance_ofertado,
            percentual_lance_embutido, qtd_parcelas_lance_ofertado, opcao_diluir_lance,
            assembleia_atual, credito_disponivel, nova_parcela_pos_lance,
            saldo_devedor_base_final, valor_lance_recurso_proprio, credito_contratado,
            valor_parcela_inicial, valor_lance_ofertado_total, valor_lance_embutido,
            total_parcelas_pagas_no_lance, prazo_restante_final, percentual_parcela_base,
            percentual_lance_recurso_proprio, nome_cliente
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        now, user_id, inputs['valor_credito'], inputs['prazo_meses'], inputs['taxa_administracao_total'],
        inputs['opcao_plano_light'], inputs['opcao_seguro_prestamista'], inputs['percentual_lance_ofertado'],
        inputs['percentual_lance_embutido'], inputs['qtd_parcelas_lance_ofertado'], inputs['opcao_diluir_lance'],
        inputs['assembleia_atual'], resultados['credito_disponivel'], resultados['nova_parcela_pos_lance'],
        resultados['saldo_devedor_base_final'], resultados['valor_lance_recurso_proprio'], resultados['credito_contratado'],
        resultados['valor_parcela_inicial'], resultados['valor_lance_ofertado_total'], resultados['valor_lance_embutido'],
        resultados['total_parcelas_pagas_no_lance'], resultados['prazo_restante_final'], resultados['percentual_parcela_base'],
        resultados['percentual_lance_recurso_proprio'], nome_cliente
    )
    try:
        with get_db_connection() as con:
            con.execute(sql, params)
            con.commit()
    except sqlite3.Error as e:
        logging.error(f"Falha ao registrar o log no banco de dados: {e}")

def get_last_simulation_by_user(user_id):
    """Busca a simulação mais recente de um usuário específico."""
    sql = "SELECT *, nome_cliente FROM simulations WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1"
    try:
        with get_db_connection() as con:
            last_sim = con.execute(sql, (user_id,)).fetchone()
        return dict(last_sim) if last_sim else None
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar a última simulação do usuário: {e}")
        return None

def get_general_metrics():
    """Busca métricas gerais (total, média de crédito, média de prazo) via SQL."""
    sql = "SELECT COUNT(id), AVG(valor_credito), AVG(prazo_meses) FROM simulations"
    try:
        with get_db_connection() as con:
            metrics = con.execute(sql).fetchone()
        return metrics if metrics else (0, 0, 0)
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar métricas gerais: {e}")
        return 0, 0, 0

def get_general_metrics_by_team(team_id):
    """Busca métricas gerais (total, média de crédito, média de prazo) para uma equipe específica."""
    sql = """
        SELECT COUNT(s.id), AVG(s.valor_credito), AVG(s.prazo_meses)
        FROM simulations s
        JOIN users u ON s.user_id = u.id
        WHERE u.team_id = ?
    """
    try:
        with get_db_connection() as con:
            metrics = con.execute(sql, (team_id,)).fetchone()
        return metrics if metrics else (0, 0, 0)
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar métricas gerais por equipe: {e}")
        return 0, 0, 0

def get_simulations_per_day():
    """Busca o número de simulações por dia via SQL."""
    sql = "SELECT DATE(timestamp) as data, COUNT(id) as simulacoes FROM simulations GROUP BY data ORDER BY data"
    try:
        with get_db_connection() as con:
            return pd.read_sql_query(sql, con)
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar simulações por dia: {e}")
        return pd.DataFrame()

def get_simulations_per_day_by_team(team_id):
    """Busca o número de simulações por dia para uma equipe específica."""
    sql = """
        SELECT DATE(s.timestamp) as data, COUNT(s.id) as simulacoes
        FROM simulations s
        JOIN users u ON s.user_id = u.id
        WHERE u.team_id = ?
        GROUP BY data ORDER BY data
    """
    try:
        with get_db_connection() as con:
            return pd.read_sql_query(sql, con, params=(team_id,))
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar simulações por dia para equipe: {e}")
        return pd.DataFrame()

def get_credit_distribution():
    """Busca a coluna de valor_credito para o histograma."""
    sql = "SELECT valor_credito FROM simulations"
    try:
        with get_db_connection() as con:
            return pd.read_sql_query(sql, con)
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar distribuição de crédito: {e}")
        return pd.DataFrame()

def get_credit_distribution_by_team(team_id):
    """Busca a coluna de valor_credito para o histograma para uma equipe específica."""
    sql = """
        SELECT s.valor_credito
        FROM simulations s
        JOIN users u ON s.user_id = u.id
        WHERE u.team_id = ?
    """
    try:
        with get_db_connection() as con:
            return pd.read_sql_query(sql, con, params=(team_id,))
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar distribuição de crédito para equipe: {e}")
        return pd.DataFrame()

def get_simulations_by_consultant():
    """Busca a contagem de simulações por consultor, tratando usuários removidos."""
    sql = """
        SELECT COALESCE(u.nome, 'Usuário Removido') as consultor, COUNT(s.id) as simulacoes
        FROM simulations s
        LEFT JOIN users u ON s.user_id = u.id
        GROUP BY consultor
        ORDER BY simulacoes DESC
    """
    try:
        with get_db_connection() as con:
            return pd.read_sql_query(sql, con)
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar simulações por consultor: {e}")
        return pd.DataFrame()

def get_simulations_by_consultant_by_team(team_id):
    """Busca a contagem de simulações por consultor para uma equipe específica."""
    sql = """
        SELECT COALESCE(u.nome, 'Usuário Removido') as consultor, COUNT(s.id) as simulacoes
        FROM simulations s
        JOIN users u ON s.user_id = u.id
        WHERE u.team_id = ?
        GROUP BY consultor
        ORDER BY simulacoes DESC
    """
    try:
        with get_db_connection() as con:
            return pd.read_sql_query(sql, con, params=(team_id,))
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar simulações por consultor para equipe: {e}")
        return pd.DataFrame()

def get_team_simulation_stats():
    """Agrega estatísticas de simulação por equipe via SQL."""
    sql = """
        SELECT
            COALESCE(t.name, 'Sem Equipe') as equipe,
            COUNT(s.id) as simulacoes
        FROM simulations s
        LEFT JOIN users u ON s.user_id = u.id
        LEFT JOIN teams t ON u.team_id = t.id
        GROUP BY equipe
        ORDER BY simulacoes DESC
    """
    try:
        with get_db_connection() as con:
            return pd.read_sql_query(sql, con)
    except sqlite3.Error as e:
        logging.error(f"Falha ao calcular estatísticas por equipe: {e}")
        return pd.DataFrame()