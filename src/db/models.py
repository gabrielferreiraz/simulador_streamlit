"""
Definição dos modelos SQLAlchemy para o banco de dados.

Estes modelos representam as tabelas do banco de dados e suas relações,
permitindo a interação com o banco de forma orientada a objetos através do ORM.
"""
from sqlalchemy import Column, Integer, String, Float, LargeBinary, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False, unique=True)
    tipo_consultor = Column(String)
    telefone = Column(String)
    email = Column(String, nullable=False, unique=True)
    foto = Column(LargeBinary)
    role = Column(String, nullable=False, default='Consultor')
    team_id = Column(Integer, ForeignKey('teams.id', ondelete='SET NULL'))
    password = Column(String, nullable=False) # Armazenará o hash da senha

    # Relação com Team: um usuário pertence a uma equipe
    team = relationship("Team", back_populates="users", foreign_keys=[team_id])
    # Relação com Team: um usuário pode ser supervisor de uma equipe
    supervised_teams = relationship("Team", back_populates="supervisor", foreign_keys='Team.supervisor_id')

    simulations = relationship("Simulation", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, nome='{self.nome}', email='{self.email}')>"

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    supervisor_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))

    # Relação com User: uma equipe tem vários usuários
    users = relationship("User", back_populates="team", foreign_keys='User.team_id')
    # Relação com User: uma equipe tem um supervisor
    supervisor = relationship("User", back_populates="supervised_teams", foreign_keys=[supervisor_id])

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"

class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    nome_cliente = Column(String)
    valor_credito = Column(Float)
    prazo_meses = Column(Integer)
    taxa_administracao_total = Column(Float)
    opcao_plano_light = Column(Integer)
    opcao_seguro_prestamista = Column(Integer)
    percentual_lance_ofertado = Column(Float)
    percentual_lance_embutido = Column(Float)
    qtd_parcelas_lance_ofertado = Column(Integer)
    opcao_diluir_lance = Column(Integer)
    assembleia_atual = Column(Integer)
    credito_disponivel = Column(Float)
    nova_parcela_pos_lance = Column(Float)
    saldo_devedor_base_final = Column(Float)
    valor_lance_recurso_proprio = Column(Float)
    credito_contratado = Column(Float)
    valor_parcela_inicial = Column(Float)
    valor_lance_ofertado_total = Column(Float)
    valor_lance_embutido = Column(Float)
    total_parcelas_pagas_no_lance = Column(Float)
    prazo_restante_final = Column(Float)
    percentual_parcela_base = Column(Float)
    percentual_lance_recurso_proprio = Column(Float)

    user = relationship("User", back_populates="simulations")

    def __repr__(self):
        return f"<Simulation(id={self.id}, user_id={self.user_id}, cliente='{self.nome_cliente}')>"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    action_type = Column(String, nullable=False)
    details = Column(Text)

    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action_type}')>"