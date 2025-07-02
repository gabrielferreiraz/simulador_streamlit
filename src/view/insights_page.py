"""
Refatorado: Módulo da view para a página de Insights.

Esta view foi refatorada para ser uma consumidora do MetricsService.
Ela não tem mais conhecimento sobre como as métricas são calculadas ou de onde
vêm os dados. A view simplesmente solicita os dados agregados (sejam DataFrames
ou objetos de métricas) ao serviço e os renderiza nos componentes do Streamlit,
como gráficos e cartões. O tratamento de erros de banco de dados é encapsulado,
tornando a UI mais robusta.
"""
import streamlit as st
import plotly.express as px
import logging

# Importações da nova arquitetura
from src.config import config
from src.utils.cached_data import (
    get_cached_general_metrics,
    get_cached_simulations_per_day,
    get_cached_credit_distribution,
    get_cached_simulations_by_consultant,
    get_cached_team_simulation_stats,
    get_cached_all_teams_with_supervisor_info
)

from sqlalchemy.exc import SQLAlchemyError # Exceções do SQLAlchemy

logger = logging.getLogger(__name__)

def show():
    """Renderiza a página de insights e dashboards."""
    st.title("Insights e Desempenho")

    # --- Filtros ---
    st.sidebar.header("Filtros de Análise")
    selected_team_id = None
    # O filtro de equipe só aparece para Admin e Supervisor
    if st.session_state.get("user_role") in [config.ROLE_ADMIN, config.ROLE_SUPERVISOR]:
        try:
            teams = get_cached_all_teams_with_supervisor_info()
            team_options = {team.id: team.name for team in teams}
            team_options[0] = "Todas as Equipes" # Adiciona a opção para ver todos
            
            selected_team_name = st.sidebar.selectbox(
                "Filtrar por Equipe", 
                options=list(team_options.values()),
                index=0
            )
            # Converte o nome da equipe de volta para ID
            selected_team_id = [id for id, name in team_options.items() if name == selected_team_name][0]
            if selected_team_id == 0:
                selected_team_id = None # O serviço espera None para buscar todos

        except SQLAlchemyError as e:
            st.sidebar.error(f"Erro ao carregar equipes: {e}")
            logger.error(f"Erro de DB ao carregar filtro de equipes: {e}")

    try:
        # --- Métricas Gerais ---
        st.header("Visão Geral")
        metrics = get_cached_general_metrics(team_id=selected_team_id)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Simulações", f"{metrics.total_simulacoes:,}".replace(",", "."))
        col2.metric("Média de Crédito", f"R$ {metrics.media_credito:,.2f}".replace(",", "X").replace(".", ",".replace("X", ".")))
        col3.metric("Média de Prazo", f"{metrics.media_prazo:.1f} meses")

        st.divider()

        # --- Gráficos ---
        st.header("Análise Gráfica")
        df_sim_per_day = get_cached_simulations_per_day(team_id=selected_team_id)
        if not df_sim_per_day.empty:
            fig_line = px.line(df_sim_per_day, x='data', y='simulacoes', title='Simulações Realizadas por Dia', labels={'data': 'Data', 'simulacoes': 'Nº de Simulações'})
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Não há dados de simulações por dia para exibir.")

        col1, col2 = st.columns(2)
        with col1:
            df_credit_dist = get_cached_credit_distribution(team_id=selected_team_id)
            if not df_credit_dist.empty:
                fig_hist = px.histogram(df_credit_dist, x='valor_credito', nbins=20, title='Distribuição de Valores de Crédito', labels={'valor_credito': 'Valor do Crédito (R$)'})
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("Não há dados de distribuição de crédito para exibir.")

        with col2:
            df_by_consultant = get_cached_simulations_by_consultant(team_id=selected_team_id)
            if not df_by_consultant.empty:
                fig_bar = px.bar(df_by_consultant.head(10), x='consultor', y='simulacoes', title='Top 10 Consultores por Nº de Simulações', labels={'consultor': 'Consultor', 'simulacoes': 'Nº de Simulações'})
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Não há dados de simulações por consultor para exibir.")

        # Gráfico de pizza para Admins
        if st.session_state.get("user_role") == config.ROLE_ADMIN:
            st.subheader("Desempenho por Equipe")
            df_team_stats = get_cached_team_simulation_stats()
            if not df_team_stats.empty:
                fig_pie = px.pie(df_team_stats, names='equipe', values='simulacoes', title='Distribuição de Simulações por Equipe')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Não há dados de simulações por equipe para exibir.")

    except SQLAlchemyError as e:
        st.error(f"Ocorreu um erro ao carregar as métricas: {e}")
        logger.error(f"Erro de DB ao carregar página de insights: {e}", exc_info=True)