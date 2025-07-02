"""
Refatorado: Módulo da view para a página do Simulador.

Esta view agora delega toda a lógica de negócio e acesso a dados para uma
classe de serviço (`SimulatorPageService`), tornando o código da UI mais limpo,
declarativo e focado exclusivamente na renderização dos componentes do Streamlit.
O tratamento de erros é feito de forma centralizada no serviço, e a view apenas
exibe as mensagens de erro resultantes.
"""
import streamlit as st
import logging
from typing import Dict, Any, Optional

# Importações da nova arquitetura
from src.db.data_models import SimulationInput, SimulationResult
from src.calculations.simulation_calculator import realizar_calculo_simulacao
from src.calculations.exceptions import CalculationError, InvalidInputError
from src.db import get_db # Importa o gerenciador de sessão do SQLAlchemy
from src.db.user_repository import UserRepository
from src.db.simulation_repository import SimulationRepository
from src.db.audit_repository import AuditRepository
from src.config import config
from src.reports.pdf_generator import create_creative_pdf_to_buffer
from src.utils.style_utils import format_currency, sanitize_filename
from src.utils.cached_data import (
    get_cached_general_metrics,
    get_cached_simulations_per_day,
    get_cached_credit_distribution,
    get_cached_simulations_by_consultant,
    get_cached_team_simulation_stats
) # Importa as funções cacheadas para invalidá-las

from sqlalchemy.exc import SQLAlchemyError, NoResultFound, IntegrityError # Exceções do SQLAlchemy

logger = logging.getLogger(__name__)

# --- Camada de Serviço da View ---
class SimulatorPageService:
    """Encapsula a lógica de negócio e estado da página do simulador."""
    def __init__(self, user_repo: UserRepository, sim_repo: SimulationRepository, audit_repo: AuditRepository):
        self.user_repo = user_repo
        self.sim_repo = sim_repo
        self.audit_repo = audit_repo

    def get_initial_inputs(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Busca a última simulação do usuário para pré-popular o formulário."""
        try:
            last_sim = self.sim_repo.get_last_by_user(db, user_id)
            if last_sim:
                st.toast("Carregamos os dados da sua última simulação.")
                # Converte o modelo SQLAlchemy Simulation de volta para um dicionário para o formulário
                return {
                    'cliente_nome': last_sim.nome_cliente or "",
                    'valor_credito': last_sim.valor_credito,
                    'prazo_meses': last_sim.prazo_meses,
                    # As taxas são armazenadas como decimais, convertemos para porcentagem para a UI
                    'taxa_administracao_total': (last_sim.taxa_administracao_total or 0.0) * 100.0,
                    'percentual_lance_ofertado': (last_sim.percentual_lance_ofertado or 0.0) * 100.0,
                    'percentual_lance_embutido': (last_sim.percentual_lance_embutido or 0.0) * 100.0,
                    'qtd_parcelas_lance_ofertado': last_sim.qtd_parcelas_lance_ofertado,
                    'opcao_plano_light': last_sim.opcao_plano_light or 1,
                    'opcao_seguro_prestamista': last_sim.opcao_seguro_prestamista or 0,
                    'opcao_diluir_lance': last_sim.opcao_diluir_lance or 1,
                    'assembleia_atual': last_sim.assembleia_atual or 1,
                }
        except SQLAlchemyError as e:
            logger.error(f"Falha ao buscar última simulação para o usuário {user_id}: {e}")
            st.toast("Não foi possível carregar sua última simulação.", icon="⚠️")
        
        # Retorna valores padrão se não houver simulação anterior ou em caso de erro
        return {
            'cliente_nome': "", 'valor_credito': None, 'prazo_meses': None,
            'taxa_administracao_total': None, 'opcao_plano_light': 1,
            'opcao_seguro_prestamista': 0, 'percentual_lance_ofertado': None,
            'percentual_lance_embutido': None, 'qtd_parcelas_lance_ofertado': None,
            'opcao_diluir_lance': 1, 'assembleia_atual': 1,
        }

    def run_simulation(self, db: Session, user_id: int, form_inputs: Dict[str, Any]) -> Optional[SimulationResult]:
        """
        Orquestra a validação, cálculo, e persistência da simulação.
        Retorna o resultado ou None em caso de falha.
        """
        try:
            # 1. Validar campos obrigatórios da UI
            required_fields = {'valor_credito': "Crédito (R$)", 'prazo_meses': "Qtd Meses", 'taxa_administracao_total': "Taxa (%)"}
            missing = [label for field, label in required_fields.items() if form_inputs.get(field) is None]
            if missing:
                st.error(f"Por favor, preencha os campos obrigatórios: {', '.join(missing)}.")
                return None

            # 2. Construir o dataclass de input (validação acontece no __post_init__)
            sim_input = SimulationInput(
                valor_credito=float(form_inputs['valor_credito']),
                prazo_meses=int(form_inputs['prazo_meses']),
                taxa_administracao_total=float(form_inputs['taxa_administracao_total']) / 100.0,
                percentual_lance_ofertado=float(form_inputs.get('percentual_lance_ofertado') or 0.0) / 100.0,
                percentual_lance_embutido=float(form_inputs.get('percentual_lance_embutido') or 0.0) / 100.0,
                qtd_parcelas_lance_ofertado=int(form_inputs.get('qtd_parcelas_lance_ofertado') or 0),
                assembleia_atual=int(form_inputs.get('assembleia_atual') or 1),
                opcao_plano_light=form_inputs.get('opcao_plano_light', 1),
                opcao_seguro_prestamista=form_inputs.get('opcao_seguro_prestamista', 0),
                opcao_diluir_lance=form_inputs.get('opcao_diluir_lance', 1),
                TAXA_SEGURO_AUTO=config.TAXA_SEGURO_AUTO,
                TAXA_SEGURO_IMOVEL=config.TAXA_SEGURO_IMOVEL,
            )

            # 3. Realizar o cálculo
            result = realizar_calculo_simulacao(sim_input)

            # 4. Logar a simulação e o evento de auditoria
            self.sim_repo.log(db, user_id, form_inputs['cliente_nome'], sim_input.__dict__, result.__dict__)
            self.audit_repo.log_event(db, "SIMULATION_GENERATED", user_id, f"Cliente: {form_inputs['cliente_nome']}")
            
            st.toast("Simulação gerada e registrada com sucesso!")

            # Invalida o cache de métricas relacionadas a simulações
            get_cached_general_metrics.clear()
            get_cached_simulations_per_day.clear()
            get_cached_credit_distribution.clear()
            get_cached_simulations_by_consultant.clear()
            get_cached_team_simulation_stats.clear()

            return result

        except (InvalidInputError, ValueError, CalculationError) as e:
            st.error(f"Erro na Simulação: {e}")
        except SQLAlchemyError as e:
            st.error(f"Erro no Banco de Dados: {e}")
            logger.critical(f"Erro de banco de dados ao rodar simulação: {e}", exc_info=True)
        except Exception as e:
            st.error("Ocorreu um erro inesperado. A equipe de TI foi notificada.")
            logger.critical(f"Erro inesperado na simulação: {e}", exc_info=True)
        
        return None

# --- Renderização da Página (View) ---

def _show_results(results: SimulationResult):
    """Mostra a seção de resultados formatados."""
    st.divider()
    st.header("Resultados da Simulação")

    tab1, tab2 = st.tabs(["Resumo Principal", "Detalhes do Cálculo"])
    with tab1:
        st.subheader("Principais Valores")
        col1, col2 = st.columns(2)
        col1.metric("Crédito Disponível", format_currency(results.credito_disponivel))
        col2.metric("Nova Parcela Pós-Lance", format_currency(results.nova_parcela_pos_lance))
        col1.metric("Saldo Devedor", format_currency(results.saldo_devedor_base_final))
        col2.metric("Lance Pago (Rec. Próprio)", format_currency(results.valor_lance_recurso_proprio))

    with tab2:
        st.subheader("Detalhes e Valores Intermediários")
        col3, col4 = st.columns(2)
        col3.metric("Crédito Contratado", format_currency(results.credito_contratado))
        col4.metric("Valor da Parcela Inicial", format_currency(results.valor_parcela_inicial))
        col3.metric("Lance Ofertado Total", format_currency(results.valor_lance_ofertado_total))
        col4.metric("Lance Embutido", format_currency(results.valor_lance_embutido))
        col3.metric("Parcelas Pagas", f"{int(results.total_parcelas_pagas_no_lance)} unid.")
        col4.metric("Parcelas Restantes", f"{int(results.prazo_restante_final)} unid.")
        col3.metric("% Parcela Inicial", f"{results.percentual_parcela_base:.4%}")
        col4.metric("% Lance Pago (Rec. Próprio)", f"{results.percentual_lance_recurso_proprio:.2%}")

    st.divider()
    st.subheader("Exportar Simulação em PDF")
    
    dados_pdf = {
        "Crédito Disponível": format_currency(results.credito_disponivel),
        "Saldo Devedor": format_currency(results.saldo_devedor_base_final),
        "Qtd de Parcelas a Pagar": f"{int(results.prazo_restante_final)}",
        "Valor da Nova Parcela": format_currency(results.nova_parcela_pos_lance),
        "Qtd Parcelas Pagas": f"{int(results.total_parcelas_pagas_no_lance)}"
    }
    
    with st.spinner("Preparando PDF..."):
        pdf_data = create_creative_pdf_to_buffer(
            st.session_state.simulation_inputs['cliente_nome'], 
            st.session_state.get("user_name", "Consultor"), 
            dados_pdf
        )

    if pdf_data:
        safe_name = sanitize_filename(st.session_state.simulation_inputs.get('cliente_nome', 'cliente'))
        file_name = f"simulacao_servopa_{safe_name}_credito_{int(results.credito_contratado)}.pdf"
        st.download_button("📥 Baixar PDF da Simulação", pdf_data, file_name, "application/pdf", use_container_width=True)
    else:
        st.error("Ocorreu um erro ao gerar o PDF.")

def show():
    """Renderiza a página do Simulador de Lances."""
    st.title("Simulador de Lances Servopa")

    # Injeção de Dependência
    # A sessão do DB é gerenciada pelo context manager get_db()
    with get_db() as db:
        service = SimulatorPageService(UserRepository(), SimulationRepository(), AuditRepository())

        # Inicialização do estado da sessão
        if 'simulation_inputs' not in st.session_state:
            user_id = st.session_state.get("user_id")
            st.session_state.simulation_inputs = service.get_initial_inputs(db, user_id) if user_id else {}
            st.session_state.simulation_results = None

        # --- Formulário de Inputs ---
        with st.container(border=True):
            st.subheader("Dados para a Simulação")
            inputs = st.session_state.simulation_inputs
            
            inputs['cliente_nome'] = st.text_input("Nome do Cliente", value=inputs.get('cliente_nome'))
            
            with st.expander("Parâmetros da Simulação", expanded=True):
                col1, col2, col3 = st.columns(3)
                inputs['valor_credito'] = col1.number_input("Crédito (R$)", value=inputs.get('valor_credito'), step=1000.0, format="%.2f")
                inputs['prazo_meses'] = col2.number_input("Qtd Meses", value=inputs.get('prazo_meses'), step=1, min_value=1)
                inputs['taxa_administracao_total'] = col3.number_input("Taxa (%)", value=inputs.get('taxa_administracao_total'), step=0.1, format="%.2f")

                col1, col2 = st.columns(2)
                inputs['opcao_plano_light'] = col1.selectbox("Plano Light", options=list(config.PLANO_LIGHT_OPTIONS.keys()), format_func=lambda x: config.PLANO_LIGHT_OPTIONS[x], index=list(config.PLANO_LIGHT_OPTIONS.keys()).index(inputs.get('opcao_plano_light', 1)))
                inputs['opcao_seguro_prestamista'] = col2.selectbox("Seguro Prestamista", options=list(config.SEGURO_PRESTAMISTA_OPTIONS.keys()), format_func=lambda x: config.SEGURO_PRESTAMISTA_OPTIONS[x], index=list(config.SEGURO_PRESTAMISTA_OPTIONS.keys()).index(inputs.get('opcao_seguro_prestamista', 0)))

                st.subheader("Valores do Lance (Opcional)")
                col1, col2, col3 = st.columns(3)
                inputs['percentual_lance_ofertado'] = col1.number_input("% Ofertado", value=inputs.get('percentual_lance_ofertado'), step=0.1, format="%.2f")
                inputs['percentual_lance_embutido'] = col2.number_input("% Embutido", value=inputs.get('percentual_lance_embutido'), step=0.1, format="%.2f")
                inputs['qtd_parcelas_lance_ofertado'] = col3.number_input("Qtd Parcelas Ofertado", value=inputs.get('qtd_parcelas_lance_ofertado'), step=1, min_value=0)

                col1, col2 = st.columns(2)
                inputs['opcao_diluir_lance'] = col1.radio("Diluir Lance?", options=list(config.DILUIR_LANCE_OPTIONS.keys()), format_func=lambda x: config.DILUIR_LANCE_OPTIONS[x], index=list(config.DILUIR_LANCE_OPTIONS.keys()).index(inputs.get('opcao_diluir_lance', 1)))
                inputs['assembleia_atual'] = col2.number_input("Lance na Assembleia", value=inputs.get('assembleia_atual'), step=1, min_value=1)

        if st.button("Gerar Simulação", type="primary", use_container_width=True):
            with st.spinner("Calculando..."):
                user_id = st.session_state.get("user_id")
                results = service.run_simulation(db, user_id, st.session_state.simulation_inputs)
                st.session_state.simulation_results = results

        # Mostra os resultados se eles existirem e forem válidos
        if st.session_state.get('simulation_results'):
            _show_results(st.session_state.simulation_results)