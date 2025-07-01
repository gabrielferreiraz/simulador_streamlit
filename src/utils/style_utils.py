"""Módulo de utilitários para estilização e formatação."""
import re
import streamlit as st

def apply_dark_theme():
    """Aplica um tema escuro personalizado via CSS."""
    with open("src/styles/dark.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def hide_main_page_from_sidebar():
    """Oculta a página principal (main.py) da barra lateral de navegação."""
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] .st-emotion-cache-1v0mbdj > ul > li:first-child {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

def format_currency(value: float | None) -> str:
    """
    Formata um valor numérico como uma string de moeda brasileira (BRL).

    Args:
        value (float | None): O valor a ser formatado.

    Returns:
        str: A string formatada, por exemplo, "R$ 1.234,56".
             Retorna "R$ 0,00" se o valor for None ou inválido.
    """
    if value is None:
        return "R$ 0,00"
    try:
        return f"R$ {value:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"

def sanitize_text_for_pdf(text: str) -> str:
    """
    Sanitiza o texto para ser usado com segurança em FPDF.
    Converte para 'latin-1' e substitui caracteres não suportados.

    Args:
        text (str): O texto de entrada.

    Returns:
        str: O texto sanitizado.
    """
    if not isinstance(text, str):
        text = str(text)
    return text.encode('latin-1', 'replace').decode('latin-1')

def sanitize_filename(filename: str) -> str:
    """
    Sanitiza uma string para que ela seja um nome de arquivo seguro.
    Remove caracteres inválidos e substitui espaços.

    Args:
        filename (str): O nome de arquivo proposto.

    Returns:
        str: Um nome de arquivo seguro.
    """
    if not isinstance(filename, str):
        filename = str(filename)
    # Remove caracteres que não são letras, números, _, -, .
    filename = re.sub(r'[^\w\s-.]', '', filename).strip()
    # Substitui espaços e hífens múltiplos por um único underscore
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename
