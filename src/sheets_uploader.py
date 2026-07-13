"""
Upload dos dados processados para o Google Sheets
"""

import os
import json
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def autenticar_google():
    """Autentica usando credenciais da variável de ambiente"""
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if not creds_json:
        raise ValueError(
            "❌ Variável GOOGLE_CREDENTIALS não encontrada.\n"
            "Configure o secret no GitHub Actions com o JSON da conta de serviço."
        )
    creds = Credentials.from_service_account_info(
        json.loads(creds_json),
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return build('sheets', 'v4', credentials=creds)

def escrever_aba(service, spreadsheet_id, nome_aba, df, cabecalho_extra=None):
    """Escreve um DataFrame em uma aba específica do Google Sheets"""
    try:
        planilha = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        abas = [a['properties']['title'] for a in planilha['sheets']]

        if nome_aba not in abas:
            body = {'requests': [{
                'addSheet': {'properties': {'title': nome_aba}}
            }]}
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()

        valores = []
        if cabecalho_extra:
            valores.append(cabecalho_extra)
        valores.append(df.columns.tolist())

        for _, row in df.iterrows():
            linha = []
            for col in df.columns:
                val = row[col]
                if pd.isna(val) or val is None:
                    linha.append('')
                elif isinstance(val, float):
                    linha.append(round(val, 4))
                else:
                    linha.append(str(val))
            valores.append(linha)

        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=f"'{nome_aba}'!A:ZZ"
        ).execute()

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{nome_aba}'!A1",
            valueInputOption='USER_ENTERED',
            body={'values': valores}
        ).execute()

        print(f"  ✅ Aba '{nome_aba}': {len(valores)} linhas escritas")

    except HttpError as e:
        print(f"  ⚠️  Erro ao escrever aba '{nome_aba}': {e}")

def atualizar_planilha(spreadsheet_id, df_geral, rankings, comparativo):
    """Função principal de upload"""
    print("\n📤 Atualizando Google Sheets...")
    service = autenticar_google()

    escrever_aba(service, spreadsheet_id, 'GERAL_TODOS_FUNDOS', df_geral)

    for nome_ranking, df_rank in rankings.items():
        escrever_aba(service, spreadsheet_id, nome_ranking, df_rank)

    if not comparativo.empty:
        escrever_aba(service, spreadsheet_id, 'COMPARATIVO_TOP5', comparativo)

    print("\n✅ Planilha atualizada com sucesso!")
    return True
