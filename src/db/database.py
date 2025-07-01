"""
Módulo para inicialização e conexão com o banco de dados SQLite.
"""
import sqlite3
import logging
from typing import List, Tuple

# Configura o logger para este módulo
logger = logging.getLogger(__name__)

DB_FILE = "simulations.db"

def get_db_connection() -> sqlite3.Connection:
    """
    Estabelece e retorna uma conexão com o banco de dados SQLite.

    A conexão é configurada para usar o objeto `sqlite3.Row` para acesso
    por nome de coluna e para impor chaves estrangeiras (foreign keys).

    Returns:
        sqlite3.Connection: Um objeto de conexão com o banco de dados.
    
    Raises:
        sqlite3.Error: Se a conexão com o banco de dados falhar.
    """
    try:
        con = sqlite3.connect(DB_FILE, timeout=10)  # Timeout para evitar locks
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON;")
        return con
    except sqlite3.Error as e:
        logger.critical(f"Falha crítica ao conectar ao banco de dados '{DB_FILE}': {e}", exc_info=True)
        raise

def _execute_scripts(cursor: sqlite3.Cursor, scripts: List[str]):
    """Executa uma lista de scripts SQL."""
    for script in scripts:
        cursor.execute(script)

def init_db():
    """
    Inicializa o banco de dados. Cria as tabelas e os índices necessários
    se eles ainda não existirem.
    """
    try:
        with get_db_connection() as con:
            cur = con.cursor()

            # --- Criação de Tabelas ---
            table_scripts = [
                '''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    supervisor_id INTEGER,
                    FOREIGN KEY (supervisor_id) REFERENCES users (id) ON DELETE SET NULL
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    tipo_consultor TEXT,
                    telefone TEXT,
                    email TEXT NOT NULL UNIQUE,
                    foto BLOB,
                    role TEXT NOT NULL DEFAULT 'Consultor' CHECK(role IN ('Admin', 'Supervisor', 'Consultor')),
                    team_id INTEGER,
                    password TEXT NOT NULL,
                    FOREIGN KEY (team_id) REFERENCES teams (id) ON DELETE SET NULL
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS simulations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    nome_cliente TEXT,
                    valor_credito REAL,
                    prazo_meses INTEGER,
                    taxa_administracao_total REAL,
                    opcao_plano_light INTEGER,
                    opcao_seguro_prestamista INTEGER,
                    percentual_lance_ofertado REAL,
                    percentual_lance_embutido REAL,
                    qtd_parcelas_lance_ofertado INTEGER,
                    opcao_diluir_lance INTEGER,
                    assembleia_atual INTEGER,
                    credito_disponivel REAL,
                    nova_parcela_pos_lance REAL,
                    saldo_devedor_base_final REAL,
                    valor_lance_recurso_proprio REAL,
                    credito_contratado REAL,
                    valor_parcela_inicial REAL,
                    valor_lance_ofertado_total REAL,
                    valor_lance_embutido REAL,
                    total_parcelas_pagas_no_lance REAL,
                    prazo_restante_final REAL,
                    percentual_parcela_base REAL,
                    percentual_lance_recurso_proprio REAL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id INTEGER,
                    action_type TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                )
                '''
            ]
            _execute_scripts(cur, table_scripts)

            # --- Criação de Índices para Performance ---
            index_scripts = [
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);",
                "CREATE INDEX IF NOT EXISTS idx_users_team_id ON users (team_id);",
                "CREATE INDEX IF NOT EXISTS idx_simulations_user_id ON simulations (user_id);",
                "CREATE INDEX IF NOT EXISTS idx_simulations_timestamp ON simulations (timestamp);"
            ]
            _execute_scripts(cur, index_scripts)

            # --- Migrações de Esquema (Ex: Adicionar colunas) ---
            cur.execute("PRAGMA table_info(simulations);")
            columns = [col['name'] for col in cur.fetchall()]
            if 'nome_cliente' not in columns:
                cur.execute("ALTER TABLE simulations ADD COLUMN nome_cliente TEXT;")
                logger.info("Coluna 'nome_cliente' adicionada à tabela 'simulations' via migração.")

            con.commit()
            logger.info("Banco de dados inicializado e verificado com sucesso.")
    except sqlite3.Error as e:
        logger.critical(f"Erro crítico ao inicializar o banco de dados: {e}", exc_info=True)
        raise e
