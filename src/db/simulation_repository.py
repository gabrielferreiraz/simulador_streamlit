"""
Refatorado: Módulo de repositório para operações de simulações usando SQLAlchemy.

Este repositório agora interage com o banco de dados através do ORM SQLAlchemy,
utilizando objetos de sessão para todas as operações. Ele retorna instâncias
dos modelos SQLAlchemy diretamente, e lida com as exceções do SQLAlchemy,
proporcionando uma camada de acesso a dados mais robusta e orientada a objetos.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from src.db.models import Simulation # Importa o modelo SQLAlchemy

logger = logging.getLogger(__name__)

class SimulationRepository:
    """Gerencia as operações de banco de dados para a entidade Simulation."""

    def log(self, db: Session, user_id: int, nome_cliente: str, inputs: Dict[str, Any], results: Dict[str, Any]) -> Simulation:
        """
        Registra uma simulação completa no banco de dados.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            user_id (int): ID do usuário que realizou a simulação.
            nome_cliente (str): Nome do cliente associado à simulação.
            inputs (Dict[str, Any]): Dicionário com os dados de entrada da simulação.
            results (Dict[str, Any]): Dicionário com os resultados do cálculo.

        Returns:
            Simulation: O objeto Simulation criado.
        """
        new_simulation = Simulation(
            timestamp=datetime.now(),
            user_id=user_id,
            nome_cliente=nome_cliente,
            valor_credito=inputs.get('valor_credito'),
            prazo_meses=inputs.get('prazo_meses'),
            taxa_administracao_total=inputs.get('taxa_administracao_total'),
            opcao_plano_light=inputs.get('opcao_plano_light'),
            opcao_seguro_prestamista=inputs.get('opcao_seguro_prestamista'),
            percentual_lance_ofertado=inputs.get('percentual_lance_ofertado'),
            percentual_lance_embutido=inputs.get('percentual_lance_embutido'),
            qtd_parcelas_lance_ofertado=inputs.get('qtd_parcelas_lance_ofertado'),
            opcao_diluir_lance=inputs.get('opcao_diluir_lance'),
            assembleia_atual=inputs.get('assembleia_atual'),
            credito_disponivel=results.get('credito_disponivel'),
            nova_parcela_pos_lance=results.get('nova_parcela_pos_lance'),
            saldo_devedor_base_final=results.get('saldo_devedor_base_final'),
            valor_lance_recurso_proprio=results.get('valor_lance_recurso_proprio'),
            credito_contratado=results.get('credito_contratado'),
            valor_parcela_inicial=results.get('valor_parcela_inicial'),
            valor_lance_ofertado_total=results.get('valor_lance_ofertado_total'),
            valor_lance_embutido=results.get('valor_lance_embutido'),
            total_parcelas_pagas_no_lance=results.get('total_parcelas_pagas_no_lance'),
            prazo_restante_final=results.get('prazo_restante_final'),
            percentual_parcela_base=results.get('percentual_parcela_base'),
            percentual_lance_recurso_proprio=results.get('percentual_lance_recurso_proprio')
        )
        db.add(new_simulation)
        db.flush() # Garante que o ID seja gerado
        logger.info(f"Simulação para '{nome_cliente}' (usuário ID {user_id}) registrada com ID {new_simulation.id}.")
        return new_simulation

    def get_by_id(self, db: Session, simulation_id: int) -> Simulation:
        """
        Busca uma simulação pelo seu ID.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            simulation_id (int): O ID da simulação.

        Returns:
            Simulation: O objeto Simulation encontrado.

        Raises:
            NoResultFound: Se a simulação não for encontrada.
        """
        stmt = select(Simulation).where(Simulation.id == simulation_id)
        simulation = db.execute(stmt).scalar_one_or_none()
        if simulation is None:
            raise NoResultFound(f"Simulação com ID {simulation_id} não encontrada.")
        return simulation

    def get_last_by_user(self, db: Session, user_id: int) -> Optional[Simulation]:
        """
        Busca a simulação mais recente de um usuário específico.

        Args:
            db (Session): A sessão do banco de dados SQLAlchemy.
            user_id (int): O ID do usuário.

        Returns:
            Optional[Simulation]: O objeto Simulation mais recente ou None se não houver.
        """
        stmt = select(Simulation).where(Simulation.user_id == user_id).order_by(Simulation.timestamp.desc()).limit(1)
        return db.execute(stmt).scalar_one_or_none()
