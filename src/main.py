#!/usr/bin/env python3
"""
Dashboard de Governança de FIDCs - Automatizado
Pipeline: CVM → Processamento → Rankings → Google Sheets
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import GOOGLE_SHEETS_ID, CNPJS_DESTAQUE
from src.cvm_downloader import carregar_dados_cvm
from src.processador import consolidar_fundos
from src.rankings import (
    gerar_todos_rankings,
    gerar_comparativo_top5,
    gerar_posicao_indicador,
)
from src.sheets_uploader import atualizar_planilha

def main():
    print("=" * 60)
    print("DASHBOARD DE GOVERNANCA DE FIDCs")
    print("   Automatizacao CVM > Google Sheets > Looker Studio")
    print("=" * 60)

    # 1. Baixar dados da CVM
    print("\nETAPA 1/4 - Baixando dados da CVM...")
    tabelas, competencia = carregar_dados_cvm()

    # 2. Processar todos os fundos
    print(f"\nETAPA 2/4 - Processando indicadores ({competencia})...")
    df_geral = consolidar_fundos(tabelas, competencia)

    if df_geral.empty:
        print("Nenhum fundo encontrado. Abortando.")
        return

    print(f"\nTotal de {len(df_geral)} FIDCs processados")

    # 3. Gerar rankings
    print(f"\nETAPA 3/4 - Gerando rankings...")
    rankings = gerar_todos_rankings(df_geral)
    comparativo = gerar_comparativo_top5(df_geral, CNPJS_DESTAQUE[0])

    if not df_geral.empty:
        print(f"\nPosicao do IOX90 no mercado:")
        for col, label in [('pct_cdi', 'CDI'), ('pdd_pct', 'PDD'), ('pl', 'PL')]:
            posicao = gerar_posicao_indicador(df_geral, CNPJS_DESTAQUE[0], col, label)
            print(f"   {posicao}")

    # 4. Atualizar Google Sheets
    print(f"\nETAPA 4/4 - Enviando para Google Sheets...")
    if not GOOGLE_SHEETS_ID or GOOGLE_SHEETS_ID == "SEU_ID_AQUI":
        print("GOOGLE_SHEETS_ID nao configurado. Configure em config.py")
        print(f"Dados prontos: {len(df_geral)} fundos, {len(rankings)} rankings")
        if not comparativo.empty:
            print(f"Comparativo Top 5: {len(comparativo)} linhas")
        return

    atualizar_planilha(GOOGLE_SHEETS_ID, df_geral, rankings, comparativo)

    print("\n" + "=" * 60)
    print("Pipeline concluida!")
    print(f"Competencia: {competencia}")
    print(f"Fundos: {len(df_geral)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
