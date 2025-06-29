
# src/config/config.py

"""
Módulo para centralizar todas as configurações da aplicação.
"""

# Taxas de seguro (exemplo de configuração que pode ser movida para .env ou secrets.toml no futuro)
TAXA_SEGURO_AUTO = 0.000599
TAXA_SEGURO_IMOVEL = 0.000392

# Mapeamentos para opções do Selectbox (melhora a legibilidade)
PLANO_LIGHT_OPTIONS = {
    1: "100%", 2: "50%", 3: "60%", 4: "70%", 5: "80%", 6: "90%"
}

SEGURO_PRESTAMISTA_OPTIONS = {
    0: "Sem Seguro", 1: "Auto", 2: "Imóvel"
}

DILUIR_LANCE_OPTIONS = {
    1: "Sim - Diluir Lance", 3: "Não - Diluir Lance"
}

USER_ROLES = ["Consultor", "Supervisor", "Admin"]
CONSULTOR_TYPES = ["Interno", "Externo"]
