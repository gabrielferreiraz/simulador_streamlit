"""
Módulo da view para a página de Dashboard de Análise (Insights).
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Optional

from src.db import simulation_repository as sim_repo
from src.db.user_repository import get_user_by_id

def show():
    """
    Renderiza a página de Dashboard de Análise com consultas otimizadas e controle de acesso.
    """
    st.title("Dashboard de Análise de Simulações")

    user_role = st.session_state.get("user_role")
    user_id = st.session_state.get("user_id")

    # --- 1. Controle de Acesso ---
    if user_role == "Consultor":
        st.warning("Acesso negado. Esta página está disponível apenas para Supervisores e Administradores.")
        st.stop()

    team_id: Optional[int] = None
    if user_role == "Supervisor":
        user_data = get_user_by_id(user_id)
        if user_data and user_data["team_id"]:
            team_id = user_data["team_id"]
            st.info(f"Visualizando insights para a sua equipe.")
        else:
            st.error("Você é um Supervisor, mas não está associado a uma equipe. Contate um Administrador.")
            st.stop()

    # --- 2. Carregamento de Dados (Otimizado) ---
    with st.spinner("Carregando dados do dashboard..."):
        # Uma única chamada para cada tipo de dado, com o filtro de equipe aplicado no BD
        general_metrics = sim_repo.get_general_metrics(team_id=team_id)
        simulacoes_por_dia_df = sim_repo.get_simulations_per_day(team_id=team_id)
        credit_dist_df = sim_repo.get_credit_distribution(team_id=team_id)
        simulacoes_por_consultor_df = sim_repo.get_simulations_by_consultant(team_id=team_id)
        
        # Gráfico de equipes é apenas para Admins
        team_stats_df = pd.DataFrame()
        if user_role == "Admin":
            team_stats_df = sim_repo.get_team_simulation_stats()

    total_simulacoes, media_credito, media_prazo = general_metrics
    if total_simulacoes == 0:
        st.info("Nenhum dado de simulação encontrado para o filtro atual.")
        st.stop()

    # --- 3. Renderização das Métricas e Gráficos ---
    st.markdown("#### Métricas Gerais")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Simulações", f"{total_simulacoes}")
    col2.metric("Média de Crédito", f"R$ {media_credito:,.2f}")
    col3.metric("Média de Prazo", f"{media_prazo:.0f} meses")

    st.markdown("---")
    st.markdown("#### Análises Visuais")

    col_a, col_b = st.columns(2)

    with col_a:
        if not simulacoes_por_dia_df.empty:
            fig_daily = px.bar(simulacoes_por_dia_df, x='data', y='simulacoes',
                               title='Simulações por Dia',
                               labels={'data': 'Data', 'simulacoes': 'Nº de Simulações'},
                               color_discrete_sequence=['#4CAF50'])
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("Sem dados para o gráfico de simulações por dia.")

        if user_role == "Admin" and not team_stats_df.empty:
            fig_teams = px.bar(team_stats_df, x='equipe', y='simulacoes', color='equipe',
                               title='Simulações por Equipe',
                               labels={'equipe': 'Equipe', 'simulacoes': 'Nº de Simulações'},
                               color_discrete_sequence=px.colors.sequential.Viridis)
            st.plotly_chart(fig_teams, use_container_width=True)

    with col_b:
        if not credit_dist_df.empty:
            fig_hist = px.histogram(credit_dist_df, x='valor_credito', nbins=20,
                                  title='Distribuição de Crédito Simulado',
                                  labels={'valor_credito': 'Valor do Crédito (R$)'},
                                  color_discrete_sequence=['#66BB6A'])
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Sem dados para o gráfico de distribuição de crédito.")

        if not simulacoes_por_consultor_df.empty:
            title = 'Distribuição por Consultor' + (' da Equipe' if user_role == "Supervisor" else '')
            fig_pie = px.pie(simulacoes_por_consultor_df, names='consultor', values='simulacoes',
                             title=title,
                             color_discrete_sequence=px.colors.sequential.Greens_r)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sem dados para o gráfico de simulações por consultor.")

