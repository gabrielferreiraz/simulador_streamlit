"""
Refatorado: Módulo de cálculo da simulação de consórcio.

Este módulo agora contém uma lógica de negócio pura e isolada. A função
principal opera com `dataclasses` de entrada e saída, garantindo contratos
de dados fortes. A validação é feita no `__post_init__` do dataclass de
entrada e os erros são comunicados através de exceções customizadas, tornando
o código mais limpo, testável e reutilizável.
"""
import logging

from src.db.data_models import SimulationInput, SimulationResult
from src.calculations.exceptions import CalculationError

logger = logging.getLogger(__name__)

def realizar_calculo_simulacao(inputs: SimulationInput) -> SimulationResult:
    """
    Realiza todos os cálculos da simulação de consórcio.

    Args:
        inputs (SimulationInput): Um objeto com todos os parâmetros de entrada validados.

    Returns:
        SimulationResult: Um objeto com todos os resultados do cálculo.
    
    Raises:
        CalculationError: Se ocorrer um erro durante o cálculo (ex: divisão por zero).
    """
    try:
        # --- 1. Cálculos Iniciais (os inputs já estão validados) ---
        fator_taxa_total = 1 + inputs.taxa_administracao_total
        taxa_amortizacao_mensal = fator_taxa_total / inputs.prazo_meses
        valor_total_a_pagar = inputs.valor_credito * fator_taxa_total

        # --- 2. Seguro e Plano Light ---
        flag_seguro_auto = 1 if inputs.opcao_seguro_prestamista == 1 else 0
        flag_seguro_imovel = 1 if inputs.opcao_seguro_prestamista == 2 else 0
        
        mapa_plano_light = {1: 1.0, 2: 0.5, 3: 0.6, 4: 0.7, 5: 0.8, 6: 0.9}
        fator_plano_light = mapa_plano_light.get(inputs.opcao_plano_light, 1.0)
        percentual_parcela_base = taxa_amortizacao_mensal * fator_plano_light

        # --- 3. Parcela Inicial ---
        valor_seguro_auto = (inputs.TAXA_SEGURO_AUTO * valor_total_a_pagar) * flag_seguro_auto
        valor_seguro_imovel = (inputs.TAXA_SEGURO_IMOVEL * valor_total_a_pagar) * flag_seguro_imovel
        valor_parcela_inicial = (inputs.valor_credito * percentual_parcela_base) + valor_seguro_auto + valor_seguro_imovel

        # --- 4. Cálculos Pós-Assembleia (Pré-Lance) ---
        prazo_restante_inicial = inputs.prazo_meses - inputs.assembleia_atual
        valor_pago_ate_assembleia = inputs.assembleia_atual * percentual_parcela_base
        saldo_devedor_faturado_inicial = fator_taxa_total - valor_pago_ate_assembleia
        
        taxa_amortizacao_mensal_pos_assembleia = saldo_devedor_faturado_inicial / prazo_restante_inicial if prazo_restante_inicial > 0 else 0
        valor_parcela_base_pos_assembleia = inputs.valor_credito * taxa_amortizacao_mensal_pos_assembleia

        # --- 5. Cálculos do Lance ---
        valor_lance_ofertado_total = inputs.qtd_parcelas_lance_ofertado * valor_parcela_base_pos_assembleia
        qtd_parcelas_lance_embutido_float = (inputs.valor_credito * inputs.percentual_lance_embutido) / valor_parcela_base_pos_assembleia if valor_parcela_base_pos_assembleia > 0 else 0
        qtd_parcelas_lance_embutido = round(qtd_parcelas_lance_embutido_float, 0)
        valor_lance_embutido = qtd_parcelas_lance_embutido * valor_parcela_base_pos_assembleia
        percentual_lance_recurso_proprio = inputs.percentual_lance_ofertado - inputs.percentual_lance_embutido
        valor_lance_recurso_proprio = valor_lance_ofertado_total - valor_lance_embutido

        # --- 6. Diluição do Lance e Prazo Final ---
        flag_diluir_lance_sim = 1 if inputs.opcao_diluir_lance == 1 else 0
        flag_diluir_lance_nao = 1 if inputs.opcao_diluir_lance == 3 else 0
        
        parcelas_pagas_no_lance_embutido = qtd_parcelas_lance_embutido * flag_diluir_lance_sim
        parcelas_pagas_no_lance_ofertado = inputs.qtd_parcelas_lance_ofertado * flag_diluir_lance_nao
        
        total_parcelas_pagas_no_lance = inputs.assembleia_atual + parcelas_pagas_no_lance_embutido + parcelas_pagas_no_lance_ofertado
        prazo_restante_final = inputs.prazo_meses - total_parcelas_pagas_no_lance

        # --- 7. Saldo Devedor e Nova Parcela ---
        valor_pago_total_com_lance = (inputs.qtd_parcelas_lance_ofertado * taxa_amortizacao_mensal_pos_assembleia) + (valor_pago_ate_assembleia * inputs.valor_credito)
        saldo_devedor_base_final = valor_total_a_pagar - valor_pago_total_com_lance
        
        nova_parcela_base = saldo_devedor_base_final / prazo_restante_final if prazo_restante_final > 0 else 0
        valor_seguro_auto_final = (inputs.TAXA_SEGURO_AUTO * saldo_devedor_base_final) * flag_seguro_auto
        valor_seguro_imovel_final = (inputs.TAXA_SEGURO_IMOVEL * saldo_devedor_base_final) * flag_seguro_imovel
        
        nova_parcela_pos_lance = nova_parcela_base + valor_seguro_auto_final + valor_seguro_imovel_final
        credito_disponivel = inputs.valor_credito - valor_lance_embutido

        return SimulationResult(
            credito_disponivel=credito_disponivel,
            nova_parcela_pos_lance=nova_parcela_pos_lance,
            saldo_devedor_base_final=saldo_devedor_base_final,
            valor_lance_recurso_proprio=valor_lance_recurso_proprio,
            credito_contratado=inputs.valor_credito,
            valor_parcela_inicial=valor_parcela_inicial,
            valor_lance_ofertado_total=valor_lance_ofertado_total,
            valor_lance_embutido=valor_lance_embutido,
            total_parcelas_pagas_no_lance=total_parcelas_pagas_no_lance,
            prazo_restante_final=prazo_restante_final,
            percentual_parcela_base=percentual_parcela_base,
            percentual_lance_recurso_proprio=percentual_lance_recurso_proprio,
            inputs=inputs
        )

    except ZeroDivisionError as e:
        logger.error(f"Erro de divisão por zero no cálculo. Inputs: {inputs}", exc_info=True)
        raise CalculationError("Erro no cálculo: O prazo restante ou outro divisor foi zero.") from e
    except Exception as e:
        logger.critical(f"Erro inesperado no cálculo da simulação: {e}", exc_info=True)
        raise CalculationError("Ocorreu um erro inesperado no sistema de cálculo.") from e