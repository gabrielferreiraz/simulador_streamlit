# src/view/simulator_page.py
import streamlit as st
from src.calculations.simulation_calculator import realizar_calculo_simulacao
from src.reports.pdf_generator import create_creative_pdf_to_buffer
from src.db.simulation_repository import log_simulation, get_last_simulation_by_user
from src.db.audit_repository import log_audit_event
from src.config import config
import locale

# Set locale for currency formatting
# Try various common Brazilian Portuguese locales, then fallback to a generic UTF-8
for loc in ['pt_BR.UTF-8', 'pt_BR', 'Portuguese_Brazil.1252', 'pt_PT.UTF-8', 'en_US.UTF-8']:
    try:
        locale.setlocale(locale.LC_ALL, loc)
        break
    except locale.Error:
        continue

def format_currency(value):
    """Formats a number as Brazilian Real currency."""
    if value is None:
        value = 0
    return locale.currency(value, grouping=True, symbol='R$')

def initialize_session_state():
    """Inicializa o st.session_state com valores padrão ou da última simulação."""
    if 'simulation_inputs' in st.session_state:
        return

    user_id = st.session_state.get("user_id")
    last_sim = get_last_simulation_by_user(user_id) if user_id else None

    defaults = {
        'valor_credito': 250000.0,
        'prazo_meses': 240,
        'taxa_administracao_total': 18.5,
        'opcao_plano_light': 1,
        'opcao_seguro_prestamista': 0,
        'percentual_lance_ofertado': 30.0,
        'percentual_lance_embutido': 0.0,
        'qtd_parcelas_lance_ofertado': 180,
        'opcao_diluir_lance': 1,
        'assembleia_atual': 1,
        'cliente_nome': "João da Silva"
    }

    if last_sim:
        st.session_state.simulation_inputs = {
            'valor_credito': last_sim.get('valor_credito', defaults['valor_credito']),
            'prazo_meses': last_sim.get('prazo_meses', defaults['prazo_meses']),
            'taxa_administracao_total': last_sim.get('taxa_administracao_total', defaults['taxa_administracao_total']) * 100,
            'opcao_plano_light': last_sim.get('opcao_plano_light', defaults['opcao_plano_light']),
            'opcao_seguro_prestamista': last_sim.get('opcao_seguro_prestamista', defaults['opcao_seguro_prestamista']),
            'percentual_lance_ofertado': last_sim.get('percentual_lance_ofertado', defaults['percentual_lance_ofertado']) * 100,
            'percentual_lance_embutido': last_sim.get('percentual_lance_embutido', defaults['percentual_lance_embutido']) * 100,
            'qtd_parcelas_lance_ofertado': int(last_sim.get('qtd_parcelas_lance_ofertado', defaults['qtd_parcelas_lance_ofertado'])),
            'opcao_diluir_lance': last_sim.get('opcao_diluir_lance', defaults['opcao_diluir_lance']),
            'assembleia_atual': last_sim.get('assembleia_atual', defaults['assembleia_atual']),
            'cliente_nome': defaults['cliente_nome'] # Nome do cliente não é salvo intencionalmente
        }
        st.toast("Carregamos os dados da sua última simulação.")
    else:
        st.session_state.simulation_inputs = defaults

    st.session_state.simulation_results = None

def show():
    """Renderiza a página do Simulador de Lances."""
    st.title("Simulador de Lances Servopa")
    
    initialize_session_state()

    # --- Formulário de Inputs ---
    with st.container(border=True):
        st.subheader("Dados para a Simulação")
        
        # Dados do Cliente
        st.session_state.simulation_inputs['cliente_nome'] = st.text_input(
            "Nome do Cliente", 
            value=st.session_state.simulation_inputs['cliente_nome'],
            help="Nome do cliente para quem a simulação será gerada."
        )
        
        # Parâmetros da Simulação
        with st.expander("Parâmetros da Simulação", expanded=True):
            st.subheader("Dados do Crédito")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.session_state.simulation_inputs['valor_credito'] = st.number_input("Crédito (R$)", value=st.session_state.simulation_inputs['valor_credito'], step=1000.0, format="%.2f")
                st.caption(f"Valor: **{format_currency(st.session_state.simulation_inputs['valor_credito'])}**")
            st.session_state.simulation_inputs['prazo_meses'] = col2.number_input("Qtd Meses", value=st.session_state.simulation_inputs['prazo_meses'], step=1)
            st.session_state.simulation_inputs['taxa_administracao_total'] = col3.number_input("Taxa (%)", value=st.session_state.simulation_inputs['taxa_administracao_total'], step=0.1, format="%.2f")

            st.subheader("Opções do Plano")
            col1, col2 = st.columns(2)
            st.session_state.simulation_inputs['opcao_plano_light'] = col1.selectbox("Plano Light", options=list(config.PLANO_LIGHT_OPTIONS.keys()), format_func=lambda x: config.PLANO_LIGHT_OPTIONS[x], index=list(config.PLANO_LIGHT_OPTIONS.keys()).index(st.session_state.simulation_inputs['opcao_plano_light']))
            st.session_state.simulation_inputs['opcao_seguro_prestamista'] = col2.selectbox("Seguro Prestamista", options=list(config.SEGURO_PRESTAMISTA_OPTIONS.keys()), format_func=lambda x: config.SEGURO_PRESTAMISTA_OPTIONS[x], index=list(config.SEGURO_PRESTAMISTA_OPTIONS.keys()).index(st.session_state.simulation_inputs['opcao_seguro_prestamista']))

            st.subheader("Valores do Lance")
            col1, col2, col3 = st.columns(3)
            st.session_state.simulation_inputs['percentual_lance_ofertado'] = col1.number_input("% Ofertado", value=st.session_state.simulation_inputs['percentual_lance_ofertado'], step=0.1, format="%.2f")
            st.session_state.simulation_inputs['percentual_lance_embutido'] = col2.number_input("% Embutido", value=st.session_state.simulation_inputs['percentual_lance_embutido'], step=0.1, format="%.2f")
            st.session_state.simulation_inputs['qtd_parcelas_lance_ofertado'] = col3.number_input("Qtd Parcelas Ofertado", value=st.session_state.simulation_inputs['qtd_parcelas_lance_ofertado'], step=1)

            st.subheader("Configurações da Assembleia")
            col1, col2 = st.columns(2)
            st.session_state.simulation_inputs['opcao_diluir_lance'] = col1.radio("Diluir Lance?", options=list(config.DILUIR_LANCE_OPTIONS.keys()), format_func=lambda x: config.DILUIR_LANCE_OPTIONS[x], index=list(config.DILUIR_LANCE_OPTIONS.keys()).index(st.session_state.simulation_inputs['opcao_diluir_lance']))
            st.session_state.simulation_inputs['assembleia_atual'] = col2.number_input("Lance na Assembleia", value=st.session_state.simulation_inputs['assembleia_atual'], step=1)

    # --- Botão de Ação ---
    if st.button("Gerar Simulação", type="primary", use_container_width=True):
        with st.spinner("Calculando..."):
            # Prepara os inputs para a função de cálculo
            inputs_calculo = st.session_state.simulation_inputs.copy()
            inputs_calculo['taxa_administracao_total'] /= 100
            inputs_calculo['percentual_lance_ofertado'] /= 100
            inputs_calculo['percentual_lance_embutido'] /= 100
            inputs_calculo['TAXA_SEGURO_AUTO'] = config.TAXA_SEGURO_AUTO
            inputs_calculo['TAXA_SEGURO_IMOVEL'] = config.TAXA_SEGURO_IMOVEL
            
            resultados = realizar_calculo_simulacao(inputs_calculo)
            st.session_state.simulation_results = resultados

            # Log da simulação no banco de dados
            if resultados["status"] == "success":
                log_simulation(st.session_state["user_id"], inputs_calculo, resultados)
                log_audit_event(st.session_state["user_id"], "SIMULATION_GENERATED", f"Simulation generated for client {st.session_state.simulation_inputs['cliente_nome']}.")
                st.toast("Simulação gerada e registrada com sucesso!")
            else:
                st.error(f"Erro no cálculo: {resultados['message']}")

    # --- Exibição dos Resultados ---
    if st.session_state.simulation_results and st.session_state.simulation_results["status"] == "success":
        resultados = st.session_state.simulation_results
        st.divider()
        st.header("Resultados da Simulação")

        tab1, tab2 = st.tabs(["Resumo Principal", "Detalhes do Cálculo"])
        with tab1:
            st.subheader("Principais Valores")
            col1, col2 = st.columns(2)
            col1.metric(label="Crédito Disponível", value=format_currency(resultados['credito_disponivel']))
            col2.metric(label="Nova Parcela Pós-Lance", value=format_currency(resultados['nova_parcela_pos_lance']))
            col1.metric(label="Saldo Devedor", value=format_currency(resultados['saldo_devedor_base_final']))
            col2.metric(label="Lance Pago (Rec. Próprio)", value=format_currency(resultados['valor_lance_recurso_proprio']))

        with tab2:
            st.subheader("Detalhes e Valores Intermediários")
            col3, col4 = st.columns(2)
            col3.metric(label="Crédito Contratado", value=format_currency(resultados['credito_contratado']))
            col4.metric(label="Valor da Parcela Inicial", value=format_currency(resultados['valor_parcela_inicial']))
            col3.metric(label="Lance Ofertado Total", value=format_currency(resultados['valor_lance_ofertado_total']))
            col4.metric(label="Lance Embutido", value=format_currency(resultados['valor_lance_embutido']))
            col3.metric(label="Parcelas Pagas", value=f"{int(resultados['total_parcelas_pagas_no_lance'])} unid.")
            col4.metric(label="Parcelas Restantes", value=f"{int(resultados['prazo_restante_final'])} unid.")
            col3.metric(label="% Parcela Inicial", value=f"{resultados['percentual_parcela_base']:.4%}")
            col4.metric(label="% Lance Pago (Rec. Próprio)", value=f"{resultados['percentual_lance_recurso_proprio']:.2%}")

        st.divider()
        st.subheader("Exportar Simulação em PDF")
        
        dados_pdf = {
            "Crédito Disponível": format_currency(resultados['credito_disponivel']),
            "Saldo Devedor": format_currency(resultados['saldo_devedor_base_final']),
            "Qtd de Parcelas a Pagar": f"{int(resultados['prazo_restante_final'])}",
            "Valor da Nova Parcela": format_currency(resultados['nova_parcela_pos_lance']),
            "Qtd Parcelas Pagas": f"{int(resultados['total_parcelas_pagas_no_lance'])}"
        }
        
        with st.spinner("Preparando PDF..."):
            pdf_data = create_creative_pdf_to_buffer(
                st.session_state.simulation_inputs['cliente_nome'], 
                st.session_state.get("user_name", "Consultor"), 
                dados_pdf
            )

        safe_filename = st.session_state.simulation_inputs['cliente_nome'].strip().replace(' ', '_').lower() or "simulacao_servopa"
        
        st.download_button(
            label="📥 Baixar PDF da Simulação",
            data=pdf_data,
            file_name=f"{safe_filename}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
