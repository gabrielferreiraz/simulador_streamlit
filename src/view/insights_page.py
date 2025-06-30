import streamlit as st
import pandas as pd
import plotly.express as px
from src.db import simulation_repository as sim_repo
from src.db.user_repository import get_user_by_id # Importar para obter o team_id do supervisor

def show():
    """Renderiza a página de Dashboard de Análise com consultas otimizadas e controle de acesso."""
    user_role = st.session_state.get("user_role")
    user_id = st.session_state.get("user_id")

    st.title("Dashboard de Análise de Simulações")

    # --- Controle de Acesso --- #
    if user_role == "Consultor":
        st.error("Acesso negado. Consultores não têm permissão para visualizar os insights.")
        return

    team_id = None
    if user_role == "Supervisor":
        user_data = get_user_by_id(user_id)
        if user_data and user_data[7]: # user_data[7] é o team_id
            team_id = user_data[7]
            st.info(f"Visualizando insights para a equipe: **{user_data[1]}**") # user_data[1] é o nome do supervisor
        else:
            st.warning("Você é um supervisor, mas não está associado a uma equipe. Não é possível exibir insights.")
            return

    # --- Métricas Gerais --- #
    with st.spinner("Carregando métricas..."):
        if user_role == "Admin":
            total_simulacoes, media_credito, media_prazo = sim_repo.get_general_metrics()
        elif user_role == "Supervisor":
            total_simulacoes, media_credito, media_prazo = sim_repo.get_general_metrics_by_team(team_id)

    if total_simulacoes == 0:
        st.warning("Nenhum dado de simulação foi encontrado ainda. Gere uma simulação para ver os insights.")
        return

    st.markdown("#### Métricas Gerais")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Simulações", f"{total_simulacoes}")
    col2.metric("Média de Crédito", f"R$ {media_credito or 0:,.2f}")
    col3.metric("Média de Prazo", f"{media_prazo or 0:.0f} meses")

    st.markdown("---")
    st.markdown("#### Análises Visuais")

    # Gráficos em colunas para melhor layout
    col_a, col_b = st.columns(2)

    with col_a:
        with st.spinner("Carregando gráfico de simulações por dia..."):
            if user_role == "Admin":
                simulacoes_por_dia_df = sim_repo.get_simulations_per_day()
            elif user_role == "Supervisor":
                simulacoes_por_dia_df = sim_repo.get_simulations_per_day_by_team(team_id)
        if not simulacoes_por_dia_df.empty:
            fig_daily = px.bar(simulacoes_por_dia_df, x='data', y='simulacoes',
                               title='Simulações por Dia',
                               labels={'data': 'Data', 'simulacoes': 'Simulações'},
                               color_discrete_sequence=['#4CAF50'])
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("Sem dados para o gráfico de simulações por dia.")

        with st.spinner("Carregando gráfico de simulações por equipe..."):
            if user_role == "Admin":
                team_stats_df = sim_repo.get_team_simulation_stats()
                if not team_stats_df.empty:
                    fig_teams = px.bar(team_stats_df, x='equipe', y='simulacoes', color='equipe',
                                       title='Simulações por Equipe',
                                       labels={'equipe': 'Equipe', 'simulacoes': 'Simulações'},
                                       color_discrete_sequence=px.colors.sequential.Viridis)
                    st.plotly_chart(fig_teams, use_container_width=True)
                else:
                    st.info("Sem dados para o gráfico de simulações por equipe.")
            elif user_role == "Supervisor":
                st.info("Supervisores não visualizam o gráfico de simulações por equipe.")

    with col_b:
        with st.spinner("Carregando gráfico de distribuição de crédito..."):
            if user_role == "Admin":
                credit_dist_df = sim_repo.get_credit_distribution()
            elif user_role == "Supervisor":
                credit_dist_df = sim_repo.get_credit_distribution_by_team(team_id)
        if not credit_dist_df.empty:
            fig_hist = px.histogram(credit_dist_df, x='valor_credito', nbins=20,
                                  title='Distribuição de Crédito Simulado',
                                  labels={'valor_credito': 'Valor do Crédito (R$)'},
                                  color_discrete_sequence=['#66BB6A'])
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Sem dados para o gráfico de distribuição de crédito.")

        with st.spinner("Carregando gráfico de simulações por consultor..."):
            if user_role == "Admin":
                simulacoes_por_consultor_df = sim_repo.get_simulations_by_consultant()
                if not simulacoes_por_consultor_df.empty:
                    fig_pie = px.pie(simulacoes_por_consultor_df, names='consultor', values='simulacoes',
                                         title='Distribuição de Simulações por Consultor',
                                         color_discrete_sequence=px.colors.sequential.Greens_r)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("Sem dados para o gráfico de simulações por consultor.")
            elif user_role == "Supervisor":
                simulacoes_por_consultor_df = sim_repo.get_simulations_by_consultant_by_team(team_id)
                if not simulacoes_por_consultor_df.empty:
                    fig_pie = px.pie(simulacoes_por_consultor_df, names='consultor', values='simulacoes',
                                         title='Distribuição de Simulações por Consultor da Equipe',
                                         color_discrete_sequence=px.colors.sequential.Greens_r)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("Sem dados para o gráfico de simulações por consultor da equipe.")

