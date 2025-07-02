"""
Módulo para configuração e gerenciamento da conexão com o banco de dados usando SQLAlchemy.

Define o motor do banco de dados (Engine) e uma fábrica de sessões (SessionLocal)
para interagir com o banco de forma transacional e segura.
"""
import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Iterator

from src.db.models import Base

logger = logging.getLogger(__name__)

# URL do banco de dados SQLite
# Lê do ambiente ou usa um valor padrão
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./simulations.db")

# Cria o motor do banco de dados
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Cria uma fábrica de sessões. Cada instância de SessionLocal será uma sessão de banco de dados.
# O `autocommit=False` e `autoflush=False` são padrões para sessões transacionais.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db() -> Iterator[Session]:
    """
    Fornece uma sessão de banco de dados como um gerenciador de contexto.

    Garante que a sessão seja fechada ao final do bloco `with`, e que as
    transações sejam confirmadas (commit) em caso de sucesso ou revertidas
    (rollback) em caso de erro.

    Yields:
        sqlalchemy.orm.Session: Uma sessão de banco de dados.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Erro de banco de dados: {e}", exc_info=True)
        raise # Re-lança a exceção para que a camada superior possa tratá-la
    finally:
        db.close()

def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas definidas nos modelos.
    Esta função deve ser chamada apenas uma vez para configurar o esquema inicial.
    Em um ambiente de produção, migrações (Alembic) seriam usadas para gerenciar
    alterações de esquema.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Banco de dados inicializado (tabelas criadas/verificadas).")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Inicializando o banco de dados com SQLAlchemy...")
    init_db()
    print("Banco de dados pronto.")