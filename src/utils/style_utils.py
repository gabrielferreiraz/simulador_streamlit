"""Módulo de utilitários para estilização e formatação com CSS."""
import re
import streamlit as st

def apply_dark_theme():
    """Aplica um tema escuro personalizado lendo o arquivo CSS."""
    try:
        with open("src/styles/dark.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo de estilo 'dark.css' não encontrado.")

def hide_main_page_from_sidebar():
    """Oculta o link para a página principal (main.py) na barra lateral."""
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] .st-emotion-cache-1v0mbdj > ul > li:first-child {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

def hide_insights_link_for_consultor():
    """Oculta o link para a página de Insights se o usuário for um Consultor."""
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] .st-emotion-cache-1v0mbdj > ul > li > a[href*="insights"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

def hide_admin_link_for_consultor():
    """Oculta o link para a página de Administrador se o usuário for um Consultor."""
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] .st-emotion-cache-1v0mbdj > ul > li > a[href*="administrador"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

def hide_all_pages_except_login():
    """Oculta todos os links de página na barra lateral, útil para a tela de login."""
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] .st-emotion-cache-1v0mbdj > ul {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

def format_currency(value: float | None) -> str:
    """Formata um valor numérico como uma string de moeda brasileira (BRL)."""
    if value is None:
        return "R$ 0,00"
    try:
        # Converte para R$ 1.234,56
        return f"R$ {value:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"

def sanitize_text_for_pdf(text: str) -> str:
    """Sanitiza o texto para ser usado com segurança em FPDF."""
    if not isinstance(text, str):
        text = str(text)
    return text.encode('latin-1', 'replace').decode('latin-1')

def sanitize_filename(filename: str) -> str:
    """Sanitiza uma string para que ela seja um nome de arquivo seguro."""
    if not isinstance(filename, str):
        filename = str(filename)
    filename = re.sub(r'[^\w\s-.]', '', filename).strip()
    return re.sub(r'[-\s]+', '_', filename)