# pages/1_📊_Simulador.py
from src.utils.page_setup import setup_page
from src.view import simulator_page

# Configura a página (título, ícone, tema, verificação de login e barra lateral)
setup_page("Simulador Servopa", "📊")

# Renderiza o conteúdo específico da página
simulator_page.show()