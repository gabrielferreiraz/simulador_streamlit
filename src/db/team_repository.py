"""
Módulo de repositório para todas as operações de banco de dados relacionadas a equipes.
"""
import sqlite3
import pandas as pd
import logging
from typing import List, Tuple, Optional

from .database import get_db_connection

# Configura o logger para este módulo
logger = logging.getLogger(__name__)

def create_team(name: str, supervisor_id: int) -> Tuple[bool, str]:
    """
    Cria uma nova equipe e a associa a um supervisor.
    A operação é transacional: se qualquer passo falhar, tudo é revertido.

    Args:
        name (str): O nome da nova equipe (deve ser único).
        supervisor_id (int): O ID do usuário supervisor.

    Returns:
        Tuple[bool, str]: (True, "Mensagem de sucesso") ou (False, "Mensagem de erro").
    """
    if not name or not name.strip():
        return False, "O nome da equipe não pode ser vazio."
    if supervisor_id is None:
        return False, "É obrigatório selecionar um supervisor para criar uma equipe."

    try:
        with get_db_connection() as con:
            cur = con.cursor()
            cur.execute("BEGIN")  # Inicia a transação
            
            # 1. Cria a equipe
            cur.execute("INSERT INTO teams (name, supervisor_id) VALUES (?, ?)", (name, supervisor_id))
            team_id = cur.lastrowid
            
            # 2. Associa o supervisor à nova equipe
            cur.execute("UPDATE users SET team_id = ? WHERE id = ?", (team_id, supervisor_id))
            
            con.commit()  # Finaliza a transação
        logger.info(f"Equipe '{name}' (ID: {team_id}) criada com sucesso, supervisionada por usuário ID {supervisor_id}.")
        return True, "Equipe criada com sucesso!"
    except sqlite3.IntegrityError:
        con.rollback()
        logger.warning(f"Falha ao criar equipe. O nome '{name}' já existe.")
        return False, f"Erro: O nome de equipe '{name}' já existe."
    except sqlite3.Error as e:
        con.rollback()
        logger.error(f"Erro de banco de dados ao criar equipe '{name}': {e}", exc_info=True)
        return False, "Ocorreu um erro no banco de dados ao criar a equipe."

def get_all_teams() -> pd.DataFrame:
    """
    Busca todas as equipes e os nomes de seus supervisores.

    Returns:
        pd.DataFrame: DataFrame com colunas [id, name, supervisor_id, supervisor_name],
                      ou um DataFrame vazio em caso de erro.
    """
    sql = """
        SELECT t.id, t.name, t.supervisor_id, u.nome as supervisor_name
        FROM teams t
        LEFT JOIN users u ON t.supervisor_id = u.id 
        ORDER BY t.name
    """
    try:
        with get_db_connection() as con:
            df = pd.read_sql_query(sql, con)
        return df
    except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
        logger.error(f"Falha ao buscar todas as equipes: {e}", exc_info=True)
        return pd.DataFrame()

def update_team_members(team_id: int, member_ids: List[int]) -> Tuple[bool, str]:
    """
    Atualiza os membros de uma equipe de forma transacional.

    Args:
        team_id (int): O ID da equipe a ser atualizada.
        member_ids (List[int]): A lista completa de IDs dos membros da equipe.

    Returns:
        Tuple[bool, str]: (True, "Mensagem de sucesso") ou (False, "Mensagem de erro").
    """
    try:
        with get_db_connection() as con:
            cur = con.cursor()
            cur.execute("BEGIN")
            
            # 1. Remove todos os usuários da equipe (exceto o supervisor, que é fixo)
            cur.execute("""
                UPDATE users SET team_id = NULL 
                WHERE team_id = ? AND id NOT IN (SELECT supervisor_id FROM teams WHERE id = ?)
            """, (team_id, team_id))
            
            # 2. Adiciona os novos membros selecionados
            if member_ids:
                placeholders = ', '.join('?' for _ in member_ids)
                sql = f"UPDATE users SET team_id = ? WHERE id IN ({placeholders})"
                params = [team_id] + member_ids
                cur.execute(sql, params)
                
            con.commit()
        logger.info(f"Membros da equipe ID {team_id} atualizados com sucesso.")
        return True, "Membros da equipe atualizados com sucesso."
    except sqlite3.Error as e:
        con.rollback()
        logger.error(f"Erro de banco de dados ao atualizar membros da equipe ID {team_id}: {e}", exc_info=True)
        return False, "Ocorreu um erro no banco de dados ao atualizar os membros."

def delete_team(team_id: int) -> Tuple[bool, str]:
    """
    Deleta uma equipe. A associação dos membros é tratada por 'ON DELETE SET NULL'.

    Args:
        team_id (int): O ID da equipe a ser deletada.

    Returns:
        Tuple[bool, str]: (True, "Mensagem de sucesso") ou (False, "Mensagem de erro").
    """
    sql = "DELETE FROM teams WHERE id = ?"
    try:
        with get_db_connection() as con:
            cur = con.execute(sql, (team_id,))
            con.commit()
            if cur.rowcount == 0:
                logger.warning(f"Tentativa de deletar equipe ID {team_id}, mas a equipe não foi encontrada.")
                return False, "Equipe não encontrada."
        logger.info(f"Equipe ID {team_id} deletada com sucesso.")
        return True, "Equipe deletada com sucesso!"
    except sqlite3.Error as e:
        logger.error(f"Erro de banco de dados ao deletar equipe ID {team_id}: {e}", exc_info=True)
        return False, "Ocorreu um erro no banco de dados ao deletar a equipe."
