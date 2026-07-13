"""
Processa os dados brutos da CVM e calcula indicadores de governança
para TODOS os FIDCs disponíveis.
"""
import pandas as pd
import numpy as np

def processar_tab_i(df):
    """TAB_I: Balanço Patrimonial - PL, Carteira, PDD"""
    if df is None or df.empty:
        return pd.DataFrame()
    cols = df.columns.tolist()

    # Busca flexível de colunas (nomes exatos ou aproximados)
    col_cnpj = 'CNPJ_FUNDO' if 'CNPJ_FUNDO' in cols else \
               ([c for c in cols if 'CNPJ' in c.upper() and 'FUND' in c.upper()] or [None])[0]
    col_nome = 'DENOM_SOCIAL' if 'DENOM_SOCIAL' in cols else \
               ([c for c in cols if 'DENOM' in c.upper()] or [None])[0]
    col_pl = 'VL_PATRIMONIO_LIQUIDO' if 'VL_PATRIMONIO_LIQUIDO' in cols else \
             ([c for c in cols if 'PATRIMONIO' in c.upper() and 'LIQUID' in c.upper()] or [None])[0]
    col_carteira = 'VL_CARTEIRA' if 'VL_CARTEIRA' in cols else \
                   ([c for c in cols if 'CARTEIRA' in c.upper()] or [None])[0]
    col_pdd = 'VL_PDD' if 'VL_PDD' in cols else \
              ([c for c in cols if 'PDD' in c.upper()] or [None])[0]

    if not col_cnpj:
        print(f"  TAB_I: CNPJ nao encontrado! Colunas: {cols[:15]}...")
        return pd.DataFrame()

    rename_map = {}
    if col_cnpj: rename_map[col_cnpj] = 'cnpj_fundo'
    if col_nome: rename_map[col_nome] = 'nome_fundo'
    if col_pl: rename_map[col_pl] = 'pl'
    if col_carteira: rename_map[col_carteira] = 'carteira'
    if col_pdd: rename_map[col_pdd] = 'pdd'

    df_proc = df[list(rename_map.keys())].rename(columns=rename_map).copy()
    for col in ['pl', 'carteira', 'pdd']:
        if col in df_proc.columns:
            df_proc[col] = pd.to_numeric(df_proc[col], errors='coerce').fillna(0)

    if 'carteira' in df_proc.columns and 'pdd' in df_proc.columns:
        df_proc['pdd_pct'] = np.where(
            df_proc['carteira'] > 0,
            (df_proc['pdd'] / df_proc['carteira'] * 100).round(2),
            0
        )
    else:
        df_proc['pdd_pct'] = 0

    if 'cnpj_fundo' in df_proc.columns:
        df_proc['cnpj_fundo'] = (
            df_proc['cnpj_fundo'].astype(str)
            .str.replace(r'\D', '', regex=True).str.zfill(14)
        )

    print(f"  TAB_I: {len(df_proc)} fundos, colunas: {list(df_proc.columns)}")
    return df_proc

def processar_tab_vi(df):
    """TAB_VI: Resultado - Rentabilidade e %CDI"""
    if df is None or df.empty:
        return pd.DataFrame()
    cols = df.columns.tolist()
    col_cnpj = [c for c in cols if 'CNPJ' in c.upper()]
    col_rent = [c for c in cols if 'RENTAB' in c.upper()]
    col_cdi = [c for c in cols if 'CDI' in c.upper()]
    if not col_cnpj or not col_rent:
        return pd.DataFrame()
    rename_map = {col_cnpj[0]: 'cnpj_fundo'}
    if col_rent:
        rename_map[col_rent[0]] = 'rentabilidade'
    if col_cdi:
        rename_map[col_cdi[0]] = 'cdi'
    df_proc = df[list(rename_map.keys())].rename(columns=rename_map).copy()
    for col in ['rentabilidade', 'cdi']:
        if col in df_proc.columns:
            df_proc[col] = pd.to_numeric(df_proc[col], errors='coerce').fillna(0)
    if 'rentabilidade' in df_proc.columns and 'cdi' in df_proc.columns:
        df_proc['pct_cdi'] = np.where(
            df_proc['cdi'] > 0,
            (df_proc['rentabilidade'] / df_proc['cdi'] * 100).round(0),
            0
        )
        df_proc['premio_pp'] = (df_proc['pct_cdi'] - 100).round(0)
    else:
        df_proc['pct_cdi'] = 0
        df_proc['premio_pp'] = 0
    if 'cnpj_fundo' in df_proc.columns:
        df_proc['cnpj_fundo'] = (
            df_proc['cnpj_fundo'].astype(str)
            .str.replace(r'\D', '', regex=True).str.zfill(14)
        )
    return df_proc

def processar_tab_ii(df):
    """TAB_II: Carteira Detalhada - Concentracao por devedor"""
    if df is None or df.empty:
        return pd.DataFrame()
    cols = df.columns.tolist()
    col_cnpj = [c for c in cols if 'CNPJ' in c.upper() and 'FUNDO' in c.upper()]
    col_valor = [c for c in cols if 'VL_' in c.upper() or 'VALOR' in c.upper()]
    if not col_cnpj or not col_valor:
        return pd.DataFrame()
    df_proc = df[[col_cnpj[0], col_valor[0]]].copy()
    df_proc = df_proc.rename(columns={col_cnpj[0]: 'cnpj_fundo', col_valor[0]: 'vl_operacao'})
    df_proc['cnpj_fundo'] = (
        df_proc['cnpj_fundo'].astype(str)
        .str.replace(r'\D', '', regex=True).str.zfill(14)
    )
    df_proc['vl_operacao'] = pd.to_numeric(df_proc['vl_operacao'], errors='coerce').fillna(0)

    def calc_concentracao(grupo):
        total = grupo['vl_operacao'].sum()
        if total == 0:
            return pd.Series({'top1_pct': 0, 'top3_pct': 0, 'top5_pct': 0,
                              'num_operacoes': 0, 'carteira_total': 0})
        ordenado = grupo.sort_values('vl_operacao', ascending=False)
        return pd.Series({
            'top1_pct': round(ordenado.iloc[0]['vl_operacao'] / total * 100, 1),
            'top3_pct': round(ordenado.head(3)['vl_operacao'].sum() / total * 100, 1),
            'top5_pct': round(ordenado.head(5)['vl_operacao'].sum() / total * 100, 1),
            'num_operacoes': len(grupo),
            'carteira_total': round(total, 2),
        })
    conc = df_proc.groupby('cnpj_fundo').apply(calc_concentracao).reset_index()
    return conc

def processar_tab_v(df):
    """TAB_V: Movimentacao - Recompra"""
    if df is None or df.empty:
        return pd.DataFrame()
    cols = df.columns.tolist()
    col_cnpj = [c for c in cols if 'CNPJ' in c.upper() and 'FUNDO' in c.upper()]
    col_recompra = [c for c in cols if 'RECOMPRA' in c.upper()]
    if not col_cnpj:
        return pd.DataFrame()
    if col_recompra:
        df_proc = df[[col_cnpj[0], col_recompra[0]]].copy()
        df_proc = df_proc.rename(columns={
            col_cnpj[0]: 'cnpj_fundo', col_recompra[0]: 'vl_recompra'
        })
    else:
        df_proc = df[[col_cnpj[0]]].copy()
        df_proc = df_proc.rename(columns={col_cnpj[0]: 'cnpj_fundo'})
        df_proc['vl_recompra'] = 0
    df_proc['cnpj_fundo'] = (
        df_proc['cnpj_fundo'].astype(str)
        .str.replace(r'\D', '', regex=True).str.zfill(14)
    )
    df_proc['vl_recompra'] = pd.to_numeric(df_proc['vl_recompra'], errors='coerce').fillna(0)
    return df_proc.groupby('cnpj_fundo')['vl_recompra'].sum().reset_index()

def processar_tab_vii(df):
    """TAB_VII: Concentracao por Cedente/Sacado"""
    if df is None or df.empty:
        return pd.DataFrame()
    cols = df.columns.tolist()
    col_cnpj = [c for c in cols if 'CNPJ' in c.upper() and 'FUNDO' in c.upper()]
    if not col_cnpj:
        return pd.DataFrame()
    df_proc = df[[col_cnpj[0]]].copy()
    df_proc = df_proc.rename(columns={col_cnpj[0]: 'cnpj_fundo'})
    df_proc['cnpj_fundo'] = (
        df_proc['cnpj_fundo'].astype(str)
        .str.replace(r'\D', '', regex=True).str.zfill(14)
    )
    return df_proc.groupby('cnpj_fundo').size().reset_index(name='num_cedentes')

def processar_tab_iv(df):
    """TAB_IV: Prazos dos Ativos"""
    if df is None or df.empty:
        return pd.DataFrame()
    cols = df.columns.tolist()
    col_cnpj = [c for c in cols if 'CNPJ' in c.upper() and 'FUNDO' in c.upper()]
    if not col_cnpj:
        return pd.DataFrame()
    df_proc = df[[col_cnpj[0]]].copy()
    df_proc = df_proc.rename(columns={col_cnpj[0]: 'cnpj_fundo'})
    df_proc['cnpj_fundo'] = (
        df_proc['cnpj_fundo'].astype(str)
        .str.replace(r'\D', '', regex=True).str.zfill(14)
    )
    return df_proc.groupby('cnpj_fundo').size().reset_index(name='num_prazos')

def _get_tabela(tabelas, nome_base):
    """Tenta encontrar a tabela pelo nome base, aceitando sufixo _YYYYMM ou _YYYY não numérico"""
    # Tenta nome exato primeiro
    if nome_base in tabelas:
        return tabelas[nome_base]
    # Tenta encontrar qualquer chave que COMECE com o nome base
    for chave in tabelas:
        if chave.startswith(nome_base):
            print(f"  Encontrada tabela via fallback: {chave}")
            return tabelas[chave]
    print(f"  Tabela {nome_base} NAO encontrada! Chaves disponiveis: {[k for k in tabelas.keys() if nome_base.split('_')[-1] in k]}")
    return None

def consolidar_fundos(tabelas, competencia):
    """Consolida dados de TODOS os fundos a partir de todas as tabelas"""
    print("Consolidando dados de todos os FIDCs...")
    print(f"  Tabelas disponiveis: {list(tabelas.keys())}")

    tab_i = processar_tab_i(_get_tabela(tabelas, 'inf_mensal_fidc_tab_I'))
    tab_vi = processar_tab_vi(_get_tabela(tabelas, 'inf_mensal_fidc_tab_VI'))
    tab_ii = processar_tab_ii(_get_tabela(tabelas, 'inf_mensal_fidc_tab_II'))
    tab_v = processar_tab_v(_get_tabela(tabelas, 'inf_mensal_fidc_tab_V'))

    base = tab_i.copy() if not tab_i.empty else pd.DataFrame()
    print(f"  TAB_I processada: {len(base)} fundos")

    if not base.empty:
        base['competencia'] = competencia
        if not tab_vi.empty and 'cnpj_fundo' in tab_vi.columns:
            cols_vi = [c for c in tab_vi.columns if c not in ['nome_fundo']]
            base = base.merge(tab_vi[cols_vi], on='cnpj_fundo', how='left', suffixes=('', '_vi'))
        if not tab_ii.empty and 'cnpj_fundo' in tab_ii.columns:
            base = base.merge(tab_ii, on='cnpj_fundo', how='left', suffixes=('', '_ii'))
        if not tab_v.empty and 'cnpj_fundo' in tab_v.columns:
            base = base.merge(tab_v, on='cnpj_fundo', how='left', suffixes=('', '_v'))
        for col in base.columns:
            if col not in ['cnpj_fundo', 'nome_fundo', 'competencia']:
                base[col] = base[col].fillna(0)
        if 'pl' in base.columns:
            antes = len(base)
            base = base[base['pl'] > 0]
            print(f"  Fundos com PL > 0: {len(base)} (removidos {antes - len(base)} sem PL)")
    else:
        print("  TAB_I esta vazia!")
        chave_tab_i = [k for k in tabelas.keys() if 'tab_I' in k]
        print(f"  Chaves contendo 'tab_I': {chave_tab_i}")
        if chave_tab_i:
            print(f"  Colunas da primeira tabela encontrada: {list(tabelas[chave_tab_i[0]].columns)}")

    print(f"  {len(base)} fundos processados com sucesso")
    return base
