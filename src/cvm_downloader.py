"""
Download e extração dos dados de FIDC do Portal Dados Abertos CVM
"""

import requests
import zipfile
import io
import pandas as pd
from datetime import datetime
from config import URL_CVM_BASE

def baixar_zip_cvm(ano, mes):
    """Baixa o ZIP do Informe Mensal de FIDC da CVM"""
    url = f"{URL_CVM_BASE}/inf_mensal_fidc_{ano}{mes:02d}.zip"
    print(f"Baixando: {url}")
    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            return io.BytesIO(resp.content)
        else:
            print(f"HTTP {resp.status_code} para {ano}{mes:02d}")
            return None
    except Exception as e:
        print(f"Erro ao baixar: {e}")
        return None

def extrair_tabelas_do_zip(zip_bytes):
    """Extrai todos os CSVs do ZIP e retorna um dict {nome_tabela: DataFrame}"""
    tabelas = {}
    try:
        with zipfile.ZipFile(zip_bytes) as z:
            for nome in z.namelist():
                if not nome.endswith(('.csv', '.txt')):
                    continue
                nome_tabela = nome.split('/')[-1].replace('.csv', '').replace('.txt', '')
                try:
                    df = pd.read_csv(
                        z.open(nome), sep=';', encoding='latin1',
                        dtype=str, low_memory=False
                    )
                    df.columns = df.columns.str.strip()
                    tabelas[nome_tabela] = df
                    print(f"  OK {nome_tabela}: {len(df)} linhas, {len(df.columns)} colunas")
                except Exception as e:
                    print(f"  Erro ao ler {nome}: {e}")
    except Exception as e:
        print(f"Erro ao extrair ZIP: {e}")
    return tabelas

def encontrar_ultima_competencia():
    """Tenta baixar o mes atual - 2 (delay da CVM). Se falhar, tenta anteriores."""
    hoje = datetime.now()
    for tentativa in range(4):
        mes = hoje.month - 2 - tentativa
        ano = hoje.year
        if mes <= 0:
            mes += 12
            ano -= 1
        zip_bytes = baixar_zip_cvm(ano, mes)
        if zip_bytes:
            print(f"Competencia encontrada: {mes:02d}/{ano}")
            return zip_bytes, ano, mes
    raise Exception("Nao foi possivel baixar dados da CVM apos 4 tentativas")

def carregar_dados_cvm():
    """Funcao principal: baixa e extrai dados da CVM"""
    print("CVM FIDC - Download de Dados")

    zip_bytes, ano, mes = encontrar_ultima_competencia()
    tabelas = extrair_tabelas_do_zip(zip_bytes)

    print(f"Total de tabelas carregadas: {len(tabelas)}")
    return tabelas, f"{mes:02d}/{ano}"
