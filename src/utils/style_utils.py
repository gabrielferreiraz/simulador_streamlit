import streamlit as st
import os

def format_currency(value):
    """Formats a number as Brazilian Real currency without depending on locale."""
    if value is None:
        value = 0
    # Formata o número com duas casas decimais, separador de milhar e vírgula decimal
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def load_css(file_path):
    """Lê um arquivo CSS e o injeta no cabeçalho da página Streamlit."""
    try:
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo de estilo não encontrado em: {file_path}")

def apply_dark_theme():
    """Aplica o tema escuro padrão da aplicação."""
    # Constrói o caminho absoluto para o arquivo CSS
    script_dir = os.path.dirname(os.path.abspath(__file__))
    css_file_path = os.path.join(script_dir, '..', 'styles', 'dark.css')
    load_css(css_file_path)

def hide_main_page_from_sidebar():
    """Injeta CSS para esconder o link para a página 'main' (login) na barra lateral."""
    st.markdown("""
    <style>
        /* Esconde o link para a página de Login (00_Login.py) */
        div[data-testid="stSidebarNav"] li:has(a[href="/00_Login"]) {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def hide_insights_link_for_consultor():
    """Injeta CSS para esconder o link para a página 'Insights' na barra lateral."""
    st.markdown("""
    <style>
        /* Esconde o link da página de Insights */
        div[data-testid="stSidebarNav"] a[href="/2_%F0%9F%93%88_Insights"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

def hide_admin_link_for_consultor():
    """Injeta CSS para esconder o link para a página 'Administrador' na barra lateral."""
    st.markdown("""
    <style>
        /* Esconde o link da página de Administrador */
        div[data-testid="stSidebarNav"] a[href="/administrador"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

def hide_all_pages_except_login():
    """Injeta CSS para esconder todos os links de página na barra lateral, exceto o de login."""
    st.markdown("""
    <style>
        /* Esconde todos os links de página na barra lateral, exceto o de login */
        div[data-testid="stSidebarNav"] li:not(:has(a[href="/pages/00_Login"])) {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

