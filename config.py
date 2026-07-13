# ============================================================
# CONFIGURAÇÕES DO DASHBOARD DE GOVERNANÇA DE FIDCs
# Preencha apenas as variáveis abaixo
# ============================================================

# ID da sua planilha no Google Sheets
# (está na URL: docs.google.com/spreadsheets/d/SEU_ID/edit)
GOOGLE_SHEETS_ID = "1aQMCdPXkRS1TULe-9Iw0JLxi5I7nOpvkEC5TZOnekwc"

# CNPJs dos fundos para destacar no comparativo
CNPJS_DESTAQUE = [
    "50901127000150",  # IOX 90 FIC FIDC
]

# ============================================================
# NÃO ALTERE DAQUI PARA BAIXO
# ============================================================

# URLs da CVM
URL_CVM_BASE = "https://dados.cvm.gov.br/dados/FIDC/DOC/INF_MENSAL/DADOS"

# Tabelas do Informe Mensal que vamos processar
TABELAS_FIDC = [
    "inf_mensal_fidc_tab_I",
    "inf_mensal_fidc_tab_II",
    "inf_mensal_fidc_tab_III",
    "inf_mensal_fidc_tab_IV",
    "inf_mensal_fidc_tab_V",
    "inf_mensal_fidc_tab_VI",
    "inf_mensal_fidc_tab_VII",
]

# Nomes das abas no Google Sheets
GOOGLE_SHEET_NAME_GERAL = "GERAL_TODOS_FUNDOS"
GOOGLE_SHEET_NAME_RANKINGS = "RANKINGS"
GOOGLE_SHEET_NAME_COMPARATIVO = "COMPARATIVO_TOP5"
GOOGLE_SHEET_NAME_FUNDO = "FUNDO_SELECIONADO"
