import sqlite3
import pandas as pd
import logging
from .database import get_db_connection

def create_team(name, supervisor_id):
    if not name or not name.strip():
        return False, "Nome da equipe não pode ser vazio."
    if supervisor_id is None:
        return False, "Supervisor é obrigatório para criar uma equipe."

    try:
        with get_db_connection() as con:
            cur = con.cursor()
            # Remove supervisor from any existing team
            cur.execute("UPDATE users SET team_id = NULL WHERE id = ?", (supervisor_id,))
            cur.execute("INSERT INTO teams (name, supervisor_id) VALUES (?, ?)", (name, supervisor_id))
            team_id = cur.lastrowid
            cur.execute("UPDATE users SET team_id = ? WHERE id = ?", (team_id, supervisor_id))
            con.commit()
        return True, "Equipe criada com sucesso!"
    except sqlite3.IntegrityError:
        return False, f"Erro: O nome de equipe '{name}' já existe."
    except sqlite3.Error as e:
        return False, f"Erro ao criar equipe: {e}"

def get_all_teams():
    try:
        with get_db_connection() as con:
            df = pd.read_sql_query("""
                SELECT t.id, t.name, t.supervisor_id, u.nome as supervisor_name
                FROM teams t
                LEFT JOIN users u ON t.supervisor_id = u.id ORDER BY t.name
            """, con)
        return df
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar equipes: {e}")
        return pd.DataFrame()

def update_team_members(team_id, member_ids):
    try:
        with get_db_connection() as con:
            cur = con.cursor()
            # Remove all users from this team first
            cur.execute("UPDATE users SET team_id = NULL WHERE team_id = ?", (team_id,))
            if member_ids:
                placeholders = ', '.join('?' for _ in member_ids)
                cur.execute(f"UPDATE users SET team_id = ? WHERE id IN ({placeholders})", [team_id] + member_ids)
            con.commit()
        return True, "Membros da equipe atualizados."
    except sqlite3.Error as e:
        return False, f"Erro ao atualizar membros: {e}"

def delete_team(team_id):
    try:
        with get_db_connection() as con:
            cur = con.cursor()
            # Set team_id to NULL for all users in this team
            cur.execute("UPDATE users SET team_id = NULL WHERE team_id = ?", (team_id,))
            cur.execute("DELETE FROM teams WHERE id = ?", (team_id,))
            con.commit()
        return True, "Equipe deletada com sucesso!"
    except sqlite3.Error as e:
        return False, f"Erro ao deletar equipe: {e}"