# pages/3_⚙️_Administrador.py
from src.utils.page_setup import setup_page
from src.view import admin_page
import streamlit as st

# Configura a página (título, ícone, tema, verificação de login e barra lateral)
setup_page("Administrador", "⚙️")

# Renderiza o conteúdo específico da página
admin_page.show()


