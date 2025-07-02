from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class UserStats:
    """Representa as estatísticas de simulação de um usuário."""
    total_simulacoes: int = 0
    media_credito: float = 0.0
    total_credito: float = 0.0


@dataclass
class GeneralMetrics:
    """Representa as métricas gerais de simulação."""
    total_simulacoes: int = 0
    media_credito: float = 0.0
    media_prazo: float = 0.0


# --- Modelos para a Lógica de Cálculo ---

@dataclass
class SimulationInput:
    """Contrato de dados para os inputs da simulação."""
    valor_credito: float
    prazo_meses: int
    taxa_administracao_total: float
    TAXA_SEGURO_AUTO: float
    TAXA_SEGURO_IMOVEL: float
    assembleia_atual: int = 1
    opcao_plano_light: int = 1
    opcao_seguro_prestamista: int = 0
    percentual_lance_ofertado: float = 0.0
    percentual_lance_embutido: float = 0.0
    qtd_parcelas_lance_ofertado: int = 0
    opcao_diluir_lance: int = 1

    def __post_init__(self):
        """Validação automática dos dados de entrada."""
        if self.valor_credito <= 0 or self.prazo_meses <= 0 or self.taxa_administracao_total < 0:
            raise ValueError("Crédito, prazo e taxa devem ser valores positivos.")
        if self.assembleia_atual > self.prazo_meses:
            raise ValueError("A assembleia do lance não pode ser maior que o prazo do plano.")
        if self.percentual_lance_embutido > self.percentual_lance_ofertado:
            raise ValueError("O lance embutido não pode ser maior que o lance ofertado total.")


@dataclass
class SimulationResult:
    """Contrato de dados para os resultados da simulação."""
    credito_disponivel: float
    nova_parcela_pos_lance: float
    saldo_devedor_base_final: float
    valor_lance_recurso_proprio: float
    credito_contratado: float
    valor_parcela_inicial: float
    valor_lance_ofertado_total: float
    valor_lance_embutido: float
    total_parcelas_pagas_no_lance: float
    prazo_restante_final: float
    percentual_parcela_base: float
    percentual_lance_recurso_proprio: float
    # Adiciona os inputs para facilitar o log
    inputs: SimulationInput = field(repr=False)