"""
Gera rankings comparativos e listas Top 10 para o dashboard
"""

import pandas as pd

def gerar_ranking_pl(df, top_n=10):
    """Top N FIDCs por Patrimônio Líquido"""
    if 'pl' not in df.columns:
        return pd.DataFrame()
    ranking = df.nlargest(top_n, 'pl')[
        ['cnpj_fundo', 'nome_fundo', 'pl', 'pdd_pct']
    ].copy()
    ranking['posicao'] = range(1, len(ranking) + 1)
    ranking['pl'] = ranking['pl'].apply(lambda x: round(x, 2))
    return ranking[['posicao', 'cnpj_fundo', 'nome_fundo', 'pl', 'pdd_pct']]

def gerar_ranking_cdi(df, top_n=10):
    """Top N FIDCs por %CDI (maior prêmio)"""
    col = 'pct_cdi'
    if col not in df.columns:
        return pd.DataFrame()
    ranking = df.nlargest(top_n, col)[
        ['cnpj_fundo', 'nome_fundo', col, 'pl', 'pdd_pct']
    ].copy()
    ranking['posicao'] = range(1, len(ranking) + 1)
    return ranking[['posicao', 'cnpj_fundo', 'nome_fundo', col, 'pl']]

def gerar_ranking_pdd(df, top_n=10):
    """Top N FIDCs com MENOR PDD (melhor qualidade)"""
    col = 'pdd_pct'
    if col not in df.columns:
        return pd.DataFrame()
    ranking = df.nsmallest(top_n, col)[
        ['cnpj_fundo', 'nome_fundo', col, 'pl']
    ].copy()
    ranking['posicao'] = range(1, len(ranking) + 1)
    return ranking[['posicao', 'cnpj_fundo', 'nome_fundo', col, 'pl']]

def gerar_ranking_concentracao(df, top_n=10):
    """Top N FIDCs com MENOR concentração (mais diversificados)"""
    col = 'top5_pct'
    if col not in df.columns:
        return pd.DataFrame()
    ranking = df.nsmallest(top_n, col)[
        ['cnpj_fundo', 'nome_fundo', 'top1_pct', 'top3_pct', col, 'num_operacoes', 'pl']
    ].copy()
    ranking['posicao'] = range(1, len(ranking) + 1)
    return ranking[['posicao', 'cnpj_fundo', 'nome_fundo', col, 'num_operacoes']]

def gerar_ranking_pl_destaque(df, cnpj_destaque, top_n=10):
    """Mostra a posição do fundo destaque no ranking de PL"""
    ranking = df.nlargest(top_n, 'pl')[['cnpj_fundo', 'nome_fundo', 'pl']].copy()
    ranking['posicao'] = range(1, len(ranking) + 1)

    # Verifica se o destaque está no top N
    if cnpj_destaque in ranking['cnpj_fundo'].values:
        linha = ranking[ranking['cnpj_fundo'] == cnpj_destaque].iloc[0]
        return f"{int(linha['posicao'])}º lugar - PL: R$ {linha['pl']:,.2f}"
    return f"Fora do Top {top_n}"

def gerar_posicao_indicador(df, cnpj_destaque, coluna, label):
    """Retorna a posição do fundo em um ranking específico"""
    if coluna not in df.columns:
        return f"{label}: N/D"

    ranking = df.sort_values(coluna, ascending=False)
    ranking['posicao'] = range(1, len(ranking) + 1)

    if cnpj_destaque in ranking['cnpj_fundo'].values:
        linha = ranking[ranking['cnpj_fundo'] == cnpj_destaque].iloc[0]
        total = len(ranking)
        return f"{label}: {int(linha['posicao'])}º entre {total} FIDCs"
    return f"{label}: Fundo não encontrado"

def gerar_todos_rankings(df_geral):
    """Gera todos os rankings e retorna dict de DataFrames"""
    print("🏆 Gerando rankings...")
    rankings = {
        'TOP10_PL': gerar_ranking_pl(df_geral, 10),
        'TOP10_PCT_CDI': gerar_ranking_cdi(df_geral, 10),
        'TOP10_MENOR_PDD': gerar_ranking_pdd(df_geral, 10),
        'TOP10_MENOR_CONCENTRACAO': gerar_ranking_concentracao(df_geral, 10),
    }
    for nome, df in rankings.items():
        if not df.empty:
            print(f"  ✅ {nome}: {len(df)} registros")
        else:
            print(f"  ⚠️  {nome}: vazio")
    return rankings

def gerar_comparativo_top5(df_geral, cnpj_referencia='50901127000150'):
    """Gera comparativo entre o fundo de referência e os Top 5 FIDCs"""
    print(f"📊 Gerando comparativo Top 5...")

    fundo_ref = df_geral[df_geral['cnpj_fundo'] == cnpj_referencia]
    top5 = df_geral.nlargest(5, 'pl')

    comparativo = pd.concat([fundo_ref, top5]).drop_duplicates(subset='cnpj_fundo')

    cols_desejadas = [
        'cnpj_fundo', 'nome_fundo', 'pl', 'carteira',
        'pdd', 'pdd_pct', 'rentabilidade', 'cdi',
        'pct_cdi', 'premio_pp', 'top1_pct', 'top3_pct',
        'top5_pct', 'num_operacoes', 'vl_recompra'
    ]
    cols_existentes = [c for c in cols_desejadas if c in comparativo.columns]
    if not cols_existentes:
        return pd.DataFrame()

    comparativo = comparativo[cols_existentes].copy()

    if not top5.empty:
        media = {}
        for col in cols_existentes:
            if col not in ['cnpj_fundo', 'nome_fundo'] and \
               pd.api.types.is_numeric_dtype(top5[col]):
                media[col] = top5[col].mean()
        media['cnpj_fundo'] = 'MEDIA'
        media['nome_fundo'] = 'Média Top 5'
        comparativo = pd.concat(
            [comparativo, pd.DataFrame([media])],
            ignore_index=True
        )

    print(f"  ✅ Comparativo com {len(comparativo)} fundos")
    return comparativo

def buscar_fundo_por_cnpj_ou_nome(df_geral, busca):
    """Busca um fundo por CNPJ ou parte do nome"""
    busca = str(busca).strip()
    if not busca:
        return pd.DataFrame()

    cnpj_limpo = ''.join(f for f in busca if f.isdigit())
    if len(cnpj_limpo) >= 8:
        resultado = df_geral[df_geral['cnpj_fundo'].str.contains(cnpj_limpo, na=False)]
        if not resultado.empty:
            return resultado

    if 'nome_fundo' in df_geral.columns:
        resultado = df_geral[
            df_geral['nome_fundo'].str.contains(busca, case=False, na=False)
        ]
        return resultado

    return pd.DataFrame()
