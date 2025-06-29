# pages/2_📈_Insights.py
from src.utils.page_setup import setup_page
from src.view import insights_page

# Configura a página (título, ícone, tema, verificação de login e barra lateral)
setup_page("Dashboard de Insights", "📈")

# Renderiza o conteúdo específico da página
insights_page.show()