"""
Módulo responsável pela lógica de negócio principal: o cálculo da simulação de consórcio.
"""
import logging
import numpy as np
from typing import Dict, Any, Union

# Configura o logger para este módulo
logger = logging.getLogger(__name__)

def realizar_calculo_simulacao(inputs: Dict[str, Any]) -> Dict[str, Union[str, float, int]]:
    """
    Realiza todos os cálculos da simulação de consórcio com validação de entrada robusta.

    Args:
        inputs (Dict[str, Any]): Um dicionário contendo todos os parâmetros de entrada, como:
            - valor_credito (float)
            - prazo_meses (int)
            - taxa_administracao_total (float)
            - e outras chaves de configuração.

    Returns:
        Dict[str, Union[str, float, int]]: Um dicionário contendo o status ("success" ou "error"),
                                           os resultados calculados ou uma mensagem de erro.
    
    Raises:
        ValueError: Se os inputs essenciais forem inválidos (e.g., negativos, zero onde não permitido).
        TypeError: Se os inputs não forem do tipo numérico esperado.
    """
    try:
        # --- 1. Desempacotar e Validar Inputs Essenciais ---
        valor_credito = float(inputs['valor_credito'])
        prazo_meses = int(inputs['prazo_meses'])
        taxa_administracao_total = float(inputs['taxa_administracao_total'])
        assembleia_atual = int(inputs.get('assembleia_atual', 1))

        if valor_credito <= 0 or prazo_meses <= 0 or taxa_administracao_total < 0:
            raise ValueError("Crédito, prazo e taxa devem ser valores positivos.")
        if assembleia_atual > prazo_meses:
            raise ValueError("A assembleia do lance não pode ser maior que o prazo do plano.")

        # --- 2. Desempacotar Inputs Opcionais com Valores Padrão ---
        opcao_plano_light = inputs.get('opcao_plano_light', 1)
        opcao_seguro_prestamista = inputs.get('opcao_seguro_prestamista', 0)
        percentual_lance_ofertado = float(inputs.get('percentual_lance_ofertado', 0))
        percentual_lance_embutido = float(inputs.get('percentual_lance_embutido', 0))
        qtd_parcelas_lance_ofertado = int(inputs.get('qtd_parcelas_lance_ofertado', 0))
        opcao_diluir_lance = inputs.get('opcao_diluir_lance', 1)
        TAXA_SEGURO_AUTO = float(inputs['TAXA_SEGURO_AUTO'])
        TAXA_SEGURO_IMOVEL = float(inputs['TAXA_SEGURO_IMOVEL'])

        # --- 3. Cálculos Iniciais ---
        credito_contratado = valor_credito
        fator_taxa_total = 1 + taxa_administracao_total
        taxa_amortizacao_mensal = fator_taxa_total / prazo_meses
        valor_total_a_pagar = valor_credito * fator_taxa_total

        # --- 4. Seguro e Plano Light ---
        flag_seguro_auto = 1 if opcao_seguro_prestamista == 1 else 0
        flag_seguro_imovel = 1 if opcao_seguro_prestamista == 2 else 0
        
        mapa_plano_light = {1: 1.0, 2: 0.5, 3: 0.6, 4: 0.7, 5: 0.8, 6: 0.9}
        fator_plano_light = mapa_plano_light.get(opcao_plano_light, 1.0)
        percentual_parcela_base = taxa_amortizacao_mensal * fator_plano_light

        # --- 5. Parcela Inicial ---
        valor_seguro_auto = (TAXA_SEGURO_AUTO * valor_total_a_pagar) * flag_seguro_auto
        valor_seguro_imovel = (TAXA_SEGURO_IMOVEL * valor_total_a_pagar) * flag_seguro_imovel
        valor_parcela_inicial = (valor_credito * percentual_parcela_base) + valor_seguro_auto + valor_seguro_imovel

        # --- 6. Cálculos Pós-Assembleia (Pré-Lance) ---
        prazo_restante_inicial = prazo_meses - assembleia_atual
        valor_pago_ate_assembleia = assembleia_atual * percentual_parcela_base
        saldo_devedor_faturado_inicial = fator_taxa_total - valor_pago_ate_assembleia
        
        if prazo_restante_inicial <= 0:
            # Se o lance for na última parcela, não há recálculo
            taxa_amortizacao_mensal_pos_assembleia = 0
        else:
            taxa_amortizacao_mensal_pos_assembleia = saldo_devedor_faturado_inicial / prazo_restante_inicial
        
        valor_parcela_base_pos_assembleia = valor_credito * taxa_amortizacao_mensal_pos_assembleia

        # --- 7. Cálculos do Lance ---
        valor_lance_ofertado_total = qtd_parcelas_lance_ofertado * valor_parcela_base_pos_assembleia
        
        if valor_parcela_base_pos_assembleia > 0:
            qtd_parcelas_lance_embutido_float = (valor_credito * percentual_lance_embutido) / valor_parcela_base_pos_assembleia
        else:
            qtd_parcelas_lance_embutido_float = 0
            
        qtd_parcelas_lance_embutido = np.round(qtd_parcelas_lance_embutido_float, 0)
        valor_lance_embutido = qtd_parcelas_lance_embutido * valor_parcela_base_pos_assembleia
        percentual_lance_recurso_proprio = percentual_lance_ofertado - percentual_lance_embutido
        valor_lance_recurso_proprio = valor_lance_ofertado_total - valor_lance_embutido

        # --- 8. Diluição do Lance e Prazo Final ---
        flag_diluir_lance_sim = 1 if opcao_diluir_lance == 1 else 0
        flag_diluir_lance_nao = 1 if opcao_diluir_lance == 3 else 0
        
        parcelas_pagas_no_lance_embutido = qtd_parcelas_lance_embutido * flag_diluir_lance_sim
        parcelas_pagas_no_lance_ofertado = qtd_parcelas_lance_ofertado * flag_diluir_lance_nao
        
        total_parcelas_pagas_no_lance = assembleia_atual + parcelas_pagas_no_lance_embutido + parcelas_pagas_no_lance_ofertado
        prazo_restante_final = prazo_meses - total_parcelas_pagas_no_lance

        # --- 9. Saldo Devedor e Nova Parcela ---
        valor_pago_total_com_lance = (qtd_parcelas_lance_ofertado * taxa_amortizacao_mensal_pos_assembleia) + (valor_pago_ate_assembleia * valor_credito)
        saldo_devedor_base_final = valor_total_a_pagar - valor_pago_total_com_lance
        
        if prazo_restante_final > 0:
            nova_parcela_base = saldo_devedor_base_final / prazo_restante_final
        else:
            nova_parcela_base = 0
            
        valor_seguro_auto_final = (TAXA_SEGURO_AUTO * saldo_devedor_base_final) * flag_seguro_auto
        valor_seguro_imovel_final = (TAXA_SEGURO_IMOVEL * saldo_devedor_base_final) * flag_seguro_imovel
        
        nova_parcela_pos_lance = nova_parcela_base + valor_seguro_auto_final + valor_seguro_imovel_final
        credito_disponivel = credito_contratado - valor_lance_embutido

        return {
            "status": "success",
            "credito_disponivel": credito_disponivel,
            "nova_parcela_pos_lance": nova_parcela_pos_lance,
            "saldo_devedor_base_final": saldo_devedor_base_final,
            "valor_lance_recurso_proprio": valor_lance_recurso_proprio,
            "credito_contratado": credito_contratado,
            "valor_parcela_inicial": valor_parcela_inicial,
            "valor_lance_ofertado_total": valor_lance_ofertado_total,
            "valor_lance_embutido": valor_lance_embutido,
            "total_parcelas_pagas_no_lance": total_parcelas_pagas_no_lance,
            "prazo_restante_final": prazo_restante_final,
            "percentual_parcela_base": percentual_parcela_base,
            "percentual_lance_recurso_proprio": percentual_lance_recurso_proprio,
        }
    except (ValueError, TypeError) as e:
        logger.error(f"Erro de validação nos dados de entrada da simulação: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro nos dados de entrada: {e}"}
    except ZeroDivisionError as e:
        logger.error(f"Erro de divisão por zero durante o cálculo da simulação. Inputs: {inputs}", exc_info=True)
        return {"status": "error", "message": "Erro no cálculo: O prazo não pode ser zero. Verifique os campos e tente novamente."}
    except KeyError as e:
        logger.error(f"Chave obrigatória ausente nos inputs da simulação: {e}", exc_info=True)
        return {"status": "error", "message": f"Erro de configuração: O campo obrigatório '{e}' não foi fornecido."}
    except Exception as e:
        logger.critical(f"Um erro inesperado ocorreu durante o cálculo da simulação: {e}", exc_info=True)
        return {"status": "error", "message": f"Ocorreu um erro inesperado no sistema. A equipe de TI foi notificada."}
