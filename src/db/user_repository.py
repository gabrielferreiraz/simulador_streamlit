"""
Módulo de repositório para todas as operações de banco de dados relacionadas a usuários.
"""
import sqlite3
import pandas as pd
import logging
from typing import List, Tuple, Optional, Any, Dict

from .database import get_db_connection

# Configura o logger para este módulo
logger = logging.getLogger(__name__)

def add_user(
    nome: str,
    tipo_consultor: str,
    telefone: str,
    email: str,
    foto_bytes: Optional[bytes],
    role: str,
    password_hash: str
) -> Tuple[bool, str]:
    """
    Adiciona um novo usuário ao banco de dados.

    Args:
        nome (str): Nome do usuário.
        tipo_consultor (str): Tipo de consultor (e.g., "Interno", "Externo").
        telefone (str): Telefone de contato.
        email (str): E-mail do usuário (deve ser único).
        foto_bytes (Optional[bytes]): Foto do usuário como bytes.
        role (str): Papel do usuário ('Admin', 'Supervisor', 'Consultor').
        password_hash (str): Hash da senha do usuário.

    Returns:
        Tuple[bool, str]: (True, "Mensagem de sucesso") ou (False, "Mensagem de erro").
    """
    if not all([nome, email, password_hash, role]):
        return False, "Nome, e-mail, senha e papel são campos obrigatórios."

    sql = "INSERT INTO users (nome, tipo_consultor, telefone, email, foto, role, password) VALUES (?, ?, ?, ?, ?, ?, ?)"
    params = (nome, tipo_consultor, telefone, email, foto_bytes, role, password_hash)
    
    try:
        with get_db_connection() as con:
            con.execute(sql, params)
            con.commit()
        logger.info(f"Usuário '{nome}' (role: {role}) adicionado com sucesso.")
        return True, "Usuário adicionado com sucesso!"
    except sqlite3.IntegrityError:
        logger.warning(f"Falha ao adicionar usuário. Nome '{nome}' ou e-mail '{email}' já existem.")
        return False, f"Erro: O nome de usuário '{nome}' ou e-mail '{email}' já existe."
    except sqlite3.Error as e:
        logger.error(f"Erro de banco de dados ao adicionar usuário '{nome}': {e}", exc_info=True)
        return False, "Ocorreu um erro no banco de dados ao adicionar o usuário."

def get_all_users() -> pd.DataFrame:
    """
    Busca todos os usuários e informações de suas equipes para exibição no painel de admin.

    Returns:
        pd.DataFrame: Um DataFrame com os dados dos usuários ou um DataFrame vazio em caso de erro.
    """
    sql = """
        SELECT u.id, u.nome, u.role, u.tipo_consultor, u.team_id, t.name as team_name 
        FROM users u 
        LEFT JOIN teams t ON u.team_id = t.id 
        ORDER BY u.nome
    """
    try:
        with get_db_connection() as con:
            df = pd.read_sql_query(sql, con)
        return df
    except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
        logger.error(f"Falha ao buscar todos os usuários: {e}", exc_info=True)
        return pd.DataFrame()

def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    """
    Busca um usuário específico pelo seu ID.

    Args:
        user_id (int): O ID do usuário.

    Returns:
        Optional[sqlite3.Row]: Um objeto Row com os dados do usuário ou None se não for encontrado ou em caso de erro.
    """
    sql = "SELECT * FROM users WHERE id = ?"
    try:
        with get_db_connection() as con:
            user_data = con.execute(sql, (user_id,)).fetchone()
        return user_data
    except sqlite3.Error as e:
        logger.error(f"Falha ao buscar usuário por ID ({user_id}): {e}", exc_info=True)
        return None

def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    """
    Busca um usuário específico pelo seu e-mail.

    Args:
        email (str): O e-mail do usuário.

    Returns:
        Optional[sqlite3.Row]: Um objeto Row com os dados do usuário ou None se não for encontrado ou em caso de erro.
    """
    if not email:
        return None
    sql = "SELECT * FROM users WHERE email = ?"
    try:
        with get_db_connection() as con:
            user_data = con.execute(sql, (email,)).fetchone()
        return user_data
    except sqlite3.Error as e:
        logger.error(f"Falha ao buscar usuário por e-mail ({email}): {e}", exc_info=True)
        return None

def update_user(
    user_id: int,
    nome: str,
    tipo: str,
    telefone: str,
    email: str,
    foto_bytes: Optional[bytes],
    role: str,
    password_hash: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Atualiza os dados de um usuário existente.

    Args:
        user_id (int): ID do usuário a ser atualizado.
        nome (str): Novo nome.
        tipo (str): Novo tipo de consultor.
        telefone (str): Novo telefone.
        email (str): Novo e-mail.
        foto_bytes (Optional[bytes]): Novos bytes da foto, ou None para não alterar.
        role (str): Novo papel.
        password_hash (Optional[str]): Novo hash de senha, ou None para não alterar.

    Returns:
        Tuple[bool, str]: (True, "Mensagem de sucesso") ou (False, "Mensagem de erro").
    """
    sql_parts = ["nome=?", "tipo_consultor=?", "telefone=?", "email=?", "role=?"]
    params: List[Any] = [nome, tipo, telefone, email, role]

    if foto_bytes is not None:
        sql_parts.append("foto=?")
        params.append(foto_bytes)
    if password_hash:
        sql_parts.append("password=?")
        params.append(password_hash)
    
    params.append(user_id)
    sql = f"UPDATE users SET {', '.join(sql_parts)} WHERE id=?"

    try:
        with get_db_connection() as con:
            con.execute(sql, tuple(params))
            con.commit()
        logger.info(f"Usuário ID {user_id} ({nome}) atualizado com sucesso.")
        return True, "Usuário atualizado com sucesso!"
    except sqlite3.IntegrityError:
        logger.warning(f"Falha ao atualizar usuário ID {user_id}. Nome '{nome}' ou e-mail '{email}' já existem.")
        return False, f"Erro: O nome de usuário '{nome}' ou e-mail '{email}' já existe."
    except sqlite3.Error as e:
        logger.error(f"Erro de banco de dados ao atualizar usuário ID {user_id}: {e}", exc_info=True)
        return False, "Ocorreu um erro no banco de dados ao atualizar o usuário."

def delete_user(user_id: int) -> Tuple[bool, str]:
    """
    Deleta um usuário do sistema.

    Args:
        user_id (int): O ID do usuário a ser deletado.

    Returns:
        Tuple[bool, str]: (True, "Mensagem de sucesso") ou (False, "Mensagem de erro").
    """
    sql = "DELETE FROM users WHERE id = ?"
    try:
        with get_db_connection() as con:
            cur = con.execute(sql, (user_id,))
            con.commit()
            if cur.rowcount == 0:
                logger.warning(f"Tentativa de deletar usuário ID {user_id}, mas o usuário não foi encontrado.")
                return False, "Usuário não encontrado."
        logger.info(f"Usuário ID {user_id} deletado com sucesso.")
        return True, "Usuário deletado com sucesso!"
    except sqlite3.Error as e:
        logger.error(f"Erro de banco de dados ao deletar usuário ID {user_id}: {e}", exc_info=True)
        return False, "Ocorreu um erro no banco de dados ao deletar o usuário."

def get_user_simulation_stats(user_id: int) -> Dict[str, float]:
    """
    Calcula estatísticas de simulação (total, média, soma) para um usuário específico.

    Args:
        user_id (int): O ID do usuário.

    Returns:
        Dict[str, float]: Um dicionário com as estatísticas. Retorna zeros se não houver dados.
    """
    sql = "SELECT COUNT(id) as total_simulacoes, AVG(valor_credito) as media_credito, SUM(valor_credito) as total_credito FROM simulations WHERE user_id = ?"
    default_stats = {'total_simulacoes': 0, 'media_credito': 0, 'total_credito': 0}
    try:
        with get_db_connection() as con:
            stats = con.execute(sql, (user_id,)).fetchone()
        if stats and stats['total_simulacoes'] > 0:
            return dict(stats)
        return default_stats
    except sqlite3.Error as e:
        logger.error(f"Erro ao buscar estatísticas do usuário ID {user_id}: {e}", exc_info=True)
        return default_stats

def get_user_detailed_simulations(user_id: int) -> pd.DataFrame:
    """
    Retorna um DataFrame com as simulações detalhadas de um usuário.

    Args:
        user_id (int): O ID do usuário.

    Returns:
        pd.DataFrame: Um DataFrame com os detalhes da simulação ou um DataFrame vazio em caso de erro.
    """
    sql = "SELECT timestamp, valor_credito, nova_parcela_pos_lance FROM simulations WHERE user_id = ? ORDER BY timestamp DESC"
    try:
        with get_db_connection() as con:
            df = pd.read_sql_query(sql, con, params=(user_id,))
        return df
    except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
        logger.error(f"Falha ao buscar simulações detalhadas do usuário ID {user_id}: {e}", exc_info=True)
        return pd.DataFrame()
