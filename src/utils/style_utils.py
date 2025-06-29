
import streamlit as st

def load_css(file_path):
    """Lê um arquivo CSS e o injeta no cabeçalho da página Streamlit."""
    try:
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo de estilo não encontrado em: {file_path}")

def apply_dark_theme():
    """Aplica o tema escuro padrão da aplicação."""
    load_css("src/styles/dark.css")

def hide_main_page_from_sidebar():
    """Injeta CSS para esconder o link para a página 'main' na barra lateral."""
    st.markdown("""
    <style>
        div[data-testid="stSidebarNav"] ul {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

