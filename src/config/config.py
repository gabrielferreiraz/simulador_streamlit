"""
Módulo para centralizar todas as configurações e constantes da aplicação.
"""

# --- Constantes de Negócio ---
TAXA_SEGURO_AUTO = 0.000599
TAXA_SEGURO_IMOVEL = 0.000392

# --- Mapeamentos para Widgets da UI ---
PLANO_LIGHT_OPTIONS = {
    1: "100%", 2: "50%", 3: "60%", 4: "70%", 5: "80%", 6: "90%"
}
SEGURO_PRESTAMISTA_OPTIONS = {
    0: "Sem Seguro", 1: "Auto", 2: "Imóvel"
}
DILUIR_LANCE_OPTIONS = {
    1: "Sim - Diluir Lance", 3: "Não - Diluir Lance"
}

# --- Constantes de Autenticação e Permissão ---
USER_ROLES = ["Consultor", "Supervisor", "Admin"]
ROLE_ADMIN = "Admin"
ROLE_SUPERVISOR = "Supervisor"
ROLE_CONSULTOR = "Consultor"

CONSULTOR_TYPES = ["Interno", "Externo"]

# --- Chaves do st.session_state ---
# Usar constantes evita erros de digitação ao acessar o estado da sessão.
SESSION_STATE_AUTHENTICATED = "authenticated"
SESSION_STATE_USER_ID = "user_id"
SESSION_STATE_USER_NAME = "user_name"
SESSION_STATE_USER_ROLE = "user_role"
SESSION_STATE_SIMULATION_INPUTS = "simulation_inputs"
SESSION_STATE_SIMULATION_RESULTS = "simulation_results"
SESSION_STATE_CONFIRMING_DELETE_USER = "confirming_delete_user"
SESSION_STATE_CONFIRMING_DELETE_TEAM = "confirming_delete_team"
SESSION_STATE_DO_LOGOUT = "do_logout"