import sqlite3
import pandas as pd
import logging
from .database import get_db_connection

def add_user(nome, tipo_consultor, telefone, email, foto_bytes, role, password_hash):
    """Adiciona um novo usuário ao banco de dados com uma senha já hasheada."""
    if not nome or not nome.strip():
        return False, "Nome do usuário não pode ser vazio."
    if not email or not email.strip():
        return False, "E-mail não pode ser vazio."
    if not password_hash:
        return False, "Senha (hash) não pode ser vazia."

    sql = "INSERT INTO users (nome, tipo_consultor, telefone, email, foto, role, password) VALUES (?, ?, ?, ?, ?, ?, ?)"
    try:
        with get_db_connection() as con:
            con.execute(sql, (nome, tipo_consultor, telefone, email, foto_bytes, role, password_hash))
            con.commit()
        return True, "Usuário adicionado com sucesso!"
    except sqlite3.IntegrityError:
        return False, f"Erro: O nome de usuário '{nome}' ou e-mail '{email}' já existe."
    except sqlite3.Error as e:
        return False, f"Erro ao adicionar usuário: {e}"

def get_all_users():
    """Busca todos os usuários para exibição no painel de admin."""
    sql = "SELECT u.id, u.nome, u.role, u.tipo_consultor, u.team_id, t.name as team_name FROM users u LEFT JOIN teams t ON u.team_id = t.id ORDER BY u.nome"
    try:
        with get_db_connection() as con:
            df = pd.read_sql_query(sql, con)
        return df
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar usuários: {e}")
        return pd.DataFrame()

def get_user_by_id(user_id):
    """Busca um usuário específico pelo seu ID."""
    sql = "SELECT * FROM users WHERE id = ?"
    try:
        with get_db_connection() as con:
            user_data = con.execute(sql, (user_id,)).fetchone()
        return user_data if user_data else None
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar usuário por ID: {e}")
        return None

def get_user_by_email(email):
    """Busca um usuário específico pelo seu e-mail."""
    sql = "SELECT * FROM users WHERE email = ?"
    try:
        with get_db_connection() as con:
            user_data = con.execute(sql, (email,)).fetchone()
        return user_data
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar usuário por e-mail: {e}")
        return None

def update_user(user_id, nome, tipo, telefone, email, foto_bytes, role, password_hash=None):
    """Atualiza os dados de um usuário."""
    try:
        with get_db_connection() as con:
            sql = "UPDATE users SET nome=?, tipo_consultor=?, telefone=?, email=?, role=?"
            params = [nome, tipo, telefone, email, role]
            if foto_bytes is not None:
                sql += ", foto=?"
                params.append(foto_bytes)
            if password_hash:
                sql += ", password=?"
                params.append(password_hash)
            sql += " WHERE id=?"
            params.append(user_id)
            con.execute(sql, tuple(params))
            con.commit()
        return True, "Usuário atualizado com sucesso!"
    except sqlite3.IntegrityError:
        return False, f"Erro: O nome de usuário '{nome}' ou e-mail '{email}' já existe."
    except sqlite3.Error as e:
        return False, f"Erro ao atualizar usuário: {e}"

def delete_user(user_id):
    """Deleta um usuário do sistema."""
    sql = "DELETE FROM users WHERE id = ?"
    try:
        with get_db_connection() as con:
            con.execute(sql, (user_id,))
            con.commit()
        return True, "Usuário deletado com sucesso!"
    except sqlite3.Error as e:
        return False, f"Erro ao deletar usuário: {e}"

def get_user_simulation_stats(user_id):
    """Calcula estatísticas de simulação para um usuário."""
    sql = "SELECT COUNT(id) as total_simulacoes, AVG(valor_credito) as media_credito, SUM(valor_credito) as total_credito FROM simulations WHERE user_id = ?"
    try:
        with get_db_connection() as con:
            stats = con.execute(sql, (user_id,)).fetchone()
        # Retorna um dicionário com valores padrão se não houver estatísticas
        return {
            'total_simulacoes': stats['total_simulacoes'] or 0,
            'media_credito': stats['media_credito'] or 0,
            'total_credito': stats['total_credito'] or 0
        }
    except sqlite3.Error as e:
        logging.error(f"Erro ao buscar estatísticas do usuário: {e}")
        return {'total_simulacoes': 0, 'media_credito': 0, 'total_credito': 0}

def get_user_detailed_simulations(user_id):
    """Retorna um DataFrame com as simulações detalhadas de um usuário."""
    sql = "SELECT timestamp, valor_credito, nova_parcela_pos_lance FROM simulations WHERE user_id = ? ORDER BY timestamp DESC"
    try:
        with get_db_connection() as con:
            df = pd.read_sql_query(sql, con, params=(user_id,))
        return df
    except sqlite3.Error as e:
        logging.error(f"Falha ao buscar simulações detalhadas do usuário: {e}")
        return pd.DataFrame()
