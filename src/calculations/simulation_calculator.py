import numpy as np

def realizar_calculo_simulacao(inputs):
    """
    Realiza todos os cálculos da simulação de consórcio.

    Args:
        inputs (dict): Um dicionário contendo todos os parâmetros de entrada.

    Returns:
        dict: Um dicionário contendo todos os resultados calculados ou um status de erro.
    """
    try:
        # --- Desempacotar Inputs ---
        valor_credito = inputs['valor_credito']
        prazo_meses = inputs['prazo_meses']
        taxa_administracao_total = inputs['taxa_administracao_total']
        opcao_plano_light = inputs['opcao_plano_light']
        opcao_seguro_prestamista = inputs['opcao_seguro_prestamista']
        percentual_lance_ofertado = inputs['percentual_lance_ofertado']
        percentual_lance_embutido = inputs['percentual_lance_embutido']
        qtd_parcelas_lance_ofertado = inputs['qtd_parcelas_lance_ofertado']
        opcao_diluir_lance = inputs['opcao_diluir_lance']
        assembleia_atual = inputs['assembleia_atual']
        TAXA_SEGURO_AUTO = inputs['TAXA_SEGURO_AUTO']
        TAXA_SEGURO_IMOVEL = inputs['TAXA_SEGURO_IMOVEL']

        # --- Cálculos Iniciais ---
        credito_contratado = valor_credito
        fator_taxa_total = 1 + taxa_administracao_total
        taxa_amortizacao_mensal = np.round(fator_taxa_total / prazo_meses, 6) if prazo_meses > 0 else 0
        valor_total_a_pagar = valor_credito * fator_taxa_total

        # --- Seguro ---
        flag_seguro_auto = 1 if opcao_seguro_prestamista == 1 else 0
        flag_seguro_imovel = 1 if opcao_seguro_prestamista == 2 else 0

        # --- Plano Light ---
        mapa_plano_light = {1: 1.0, 2: 0.5, 3: 0.6, 4: 0.7, 5: 0.8, 6: 0.9}
        fator_plano_light = mapa_plano_light.get(opcao_plano_light, 1.0)
        percentual_parcela_base = np.round(taxa_amortizacao_mensal * fator_plano_light, 8)

        # --- Parcela Inicial ---
        valor_seguro_auto = (TAXA_SEGURO_AUTO * valor_total_a_pagar) * flag_seguro_auto
        valor_seguro_imovel = (TAXA_SEGURO_IMOVEL * valor_total_a_pagar) * flag_seguro_imovel
        valor_parcela_inicial = (valor_credito * percentual_parcela_base) + valor_seguro_auto + valor_seguro_imovel

        # --- Cálculos Pós-Assembleia (Pré-Lance) ---
        prazo_restante_inicial = prazo_meses - assembleia_atual if prazo_meses >= assembleia_atual else 0
        valor_pago_ate_assembleia = np.round((assembleia_atual * percentual_parcela_base * valor_credito) / credito_contratado, 6) if credito_contratado > 0 else 0
        saldo_devedor_faturado_inicial = fator_taxa_total - valor_pago_ate_assembleia
        taxa_amortizacao_mensal_pos_assembleia = np.round(saldo_devedor_faturado_inicial / prazo_restante_inicial, 6) if prazo_restante_inicial > 0 else 0
        valor_parcela_base_pos_assembleia = np.round(valor_credito * taxa_amortizacao_mensal_pos_assembleia, 6)

        # --- Cálculos do Lance ---
        valor_lance_ofertado_total = qtd_parcelas_lance_ofertado * valor_parcela_base_pos_assembleia
        qtd_parcelas_lance_embutido_float = ((valor_credito * fator_taxa_total) * percentual_lance_embutido) / valor_parcela_base_pos_assembleia if valor_parcela_base_pos_assembleia > 0 else 0
        qtd_parcelas_lance_embutido = np.round(qtd_parcelas_lance_embutido_float, 0)
        valor_lance_embutido = qtd_parcelas_lance_embutido * valor_parcela_base_pos_assembleia
        percentual_lance_recurso_proprio = percentual_lance_ofertado - percentual_lance_embutido
        valor_lance_recurso_proprio = valor_lance_ofertado_total - valor_lance_embutido

        # --- Diluição do Lance ---
        flag_diluir_lance_sim = 1 if opcao_diluir_lance == 1 else 0
        flag_diluir_lance_nao = 1 if opcao_diluir_lance == 3 else 0
        
        parcelas_pagas_lance_embutido = qtd_parcelas_lance_embutido
        parcelas_pagas_lance_ofertado = qtd_parcelas_lance_ofertado

        total_parcelas_pagas_no_lance = 1 + (parcelas_pagas_lance_embutido * flag_diluir_lance_sim) + (parcelas_pagas_lance_ofertado * flag_diluir_lance_nao) + (assembleia_atual - 1)
        prazo_restante_final = prazo_meses - total_parcelas_pagas_no_lance

        # --- Saldo Devedor e Nova Parcela ---
        valor_pago_total_com_lance = (qtd_parcelas_lance_ofertado * taxa_amortizacao_mensal_pos_assembleia) + valor_pago_ate_assembleia
        saldo_devedor_faturado_final = fator_taxa_total - valor_pago_total_com_lance
        saldo_devedor_base_final = saldo_devedor_faturado_final * credito_contratado
        
        taxa_amortizacao_mensal_final = np.round(saldo_devedor_faturado_final / prazo_restante_final, 6) if prazo_restante_final > 0 else 0
        
        valor_seguro_auto_final = (TAXA_SEGURO_AUTO * saldo_devedor_base_final) * flag_seguro_auto
        valor_seguro_imovel_final = (TAXA_SEGURO_IMOVEL * saldo_devedor_base_final) * flag_seguro_imovel
        
        nova_parcela_pos_lance = (taxa_amortizacao_mensal_final * credito_contratado) + valor_seguro_auto_final + valor_seguro_imovel_final if credito_contratado > 0 else 0
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
    except (ZeroDivisionError, ValueError) as e:
        return {"status": "error", "message": f"Erro no Cálculo: Um dos valores de entrada está causando uma divisão por zero. Verifique os campos e tente novamente. Detalhe: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Um erro inesperado ocorreu: {e}"}