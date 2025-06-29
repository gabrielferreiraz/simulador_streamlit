import sqlite3
import os

DB_FILE = "simulations.db"

def get_db_connection():
    """Retorna uma conexão com o banco de dados."""
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    return con

def init_db():
    """Inicializa o banco de dados e cria as tabelas se não existirem."""
    try:
        with get_db_connection() as con:
            cur = con.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS simulations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
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
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    supervisor_id INTEGER,
                    FOREIGN KEY (supervisor_id) REFERENCES users (id) ON DELETE SET NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    tipo_consultor TEXT,
                    telefone TEXT,
                    email TEXT UNIQUE,
                    foto BLOB,
                    role TEXT NOT NULL DEFAULT 'Consultor',
                    team_id INTEGER,
                    password TEXT NOT NULL,
                    FOREIGN KEY (team_id) REFERENCES teams (id) ON DELETE SET NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id INTEGER,
                    action_type TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                )
            ''')
            con.commit()
            print("Database tables initialized successfully.")
    except sqlite3.Error as e:
        print(f"Error initializing the database: {e}")
        raise e
