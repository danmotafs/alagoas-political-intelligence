import os
import json
import shutil
import pandas as pd
from datetime import datetime


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DATA_FINAL_DIR = os.path.join(BASE_DIR, "data", "final")
DATA_DASHBOARD_DIR = os.path.join(BASE_DIR, "data", "dashboard")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(DATA_FINAL_DIR, exist_ok=True)
os.makedirs(DATA_DASHBOARD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

META_DAVI_2026 = 60000

TAXA_CONSERVADORA = 0.10
TAXA_INTERMEDIARIA = 0.15
TAXA_MAXIMA = 0.20

ARQUIVO_VEREADORES = os.path.join(DATA_FINAL_DIR, "inteligencia_vereadores_alagoas_2024.csv")
ARQUIVO_DASHBOARD_V2 = os.path.join(DATA_DASHBOARD_DIR, "base_dashboard_v2.json")

SAIDA_VEREADORES_CORRIGIDA = os.path.join(DATA_FINAL_DIR, "inteligencia_vereadores_alagoas_2024_corrigida.csv")
SAIDA_META_DETALHADA = os.path.join(DATA_FINAL_DIR, "meta_eleitoral_davi_federal_2026.csv")
SAIDA_META_MUNICIPIOS = os.path.join(DATA_FINAL_DIR, "resumo_meta_eleitoral_municipios_davi_2026.csv")
SAIDA_META_DASHBOARD = os.path.join(DATA_DASHBOARD_DIR, "meta_eleitoral_davi_federal_2026.json")
SAIDA_RELATORIO = os.path.join(REPORTS_DIR, "correcao_contribuicao_vereadores_dashboard_v2.md")


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_coluna(nome):
    if nome is None:
        return ""

    nome = str(nome).strip().lower()

    substituicoes = {
        "á": "a", "à": "a", "ã": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
    }

    for origem, destino in substituicoes.items():
        nome = nome.replace(origem, destino)

    nome = nome.replace(" ", "_").replace("-", "_").replace("/", "_")

    while "__" in nome:
        nome = nome.replace("__", "_")

    return nome


def encontrar_coluna(df, candidatos):
    mapa = {normalizar_coluna(col): col for col in df.columns}

    for candidato in candidatos:
        candidato_norm = normalizar_coluna(candidato)
        if candidato_norm in mapa:
            return mapa[candidato_norm]

    return None


def converter_numero(valor):
    if pd.isna(valor):
        return 0

    texto = str(valor).strip()

    if texto == "":
        return 0

    texto = texto.replace(".", "")
    texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return 0


def classificar_grupo_politico(valor):
    if pd.isna(valor):
        return "SEM GRUPO"

    texto = str(valor).strip().upper()

    if texto in ["", "NAN", "NONE", "NAO_CLASSIFICADO", "NÃO CLASSIFICADO", "NÃO_CLASSIFICADO"]:
        return "SEM GRUPO"

    if "CALHEIROS" in texto or "RENAN" in texto:
        return "GRUPO CALHEIROS"

    if "LIRA" in texto or "ARTHUR" in texto:
        return "GRUPO LIRA"

    if "JHC" in texto:
        return "GRUPO JHC"

    if "SEM" in texto:
        return "SEM GRUPO"

    # Cuidado: partido sozinho não é grupo político suficiente.
    # Se a base ainda não tiver curadoria política, classificamos como SEM GRUPO.
    return "SEM GRUPO"


def classificar_potencial_eleitoral(votos):
    if votos >= 5000:
        return "MUITO_ALTO"
    if votos >= 3000:
        return "ALTO"
    if votos >= 1500:
        return "MEDIO"
    if votos >= 700:
        return "BAIXO"
    return "RESIDUAL"


def calcular_score_politico(row):
    """
    Score operacional 0-100 para priorização.

    40 pontos: porte eleitoral do vereador
    25 pontos: participação percentual no município
    20 pontos: prioridade estratégica municipal
    15 pontos: grupo político classificado

    O score não é previsão de voto.
    É apenas índice de priorização para o dashboard.
    """

    score = 0

    votos = row.get("votos", 0)
    percentual_municipio = row.get("percentual_votos_municipio_corrigido", 0)
    prioridade = str(row.get("prioridade_final", "")).strip().upper()
    grupo = str(row.get("grupo_politico_padronizado", "")).strip().upper()

    # 1) Porte eleitoral — até 40 pontos
    if votos >= 5000:
        score += 40
    elif votos >= 3000:
        score += 34
    elif votos >= 1500:
        score += 26
    elif votos >= 700:
        score += 18
    elif votos > 0:
        score += 10

    # 2) Peso dentro do município — até 25 pontos
    if percentual_municipio >= 10:
        score += 25
    elif percentual_municipio >= 7:
        score += 20
    elif percentual_municipio >= 4:
        score += 15
    elif percentual_municipio >= 2:
        score += 10
    elif percentual_municipio > 0:
        score += 5

    # 3) Prioridade territorial — até 20 pontos
    if "ALTISSIMA" in prioridade or "ALTÍSSIMA" in prioridade:
        score += 20
    elif "ALTA" in prioridade:
        score += 16
    elif "MEDIA" in prioridade or "MÉDIA" in prioridade:
        score += 10
    elif "BAIXA" in prioridade:
        score += 5
    else:
        score += 5

    # 4) Grupo político classificado — até 15 pontos
    if grupo in ["GRUPO CALHEIROS", "GRUPO LIRA", "GRUPO JHC"]:
        score += 15
    else:
        score += 5

    return round(min(score, 100), 2)


def formatar_int(valor):
    try:
        return int(round(float(valor)))
    except Exception:
        return 0


def gerar_tooltip_vereador(row):
    vereador = row["vereador"]
    municipio = row["municipio"]
    votos = formatar_int(row["votos"])
    votos_10 = formatar_int(row["contribuicao_davi_10pct"])
    votos_15 = formatar_int(row["contribuicao_davi_15pct"])
    votos_20 = formatar_int(row["contribuicao_davi_20pct"])
    pct_meta_20 = row["percentual_meta_davi_20pct"]

    return (
        f"{vereador}, em {municipio}, recebeu {votos:,} votos em 2024. "
        f"Pela metodologia corrigida, a contribuição potencial para Davi é calculada "
        f"como conversão de parte desses próprios eleitores: {votos_10:,} votos no cenário "
        f"conservador de 10%, {votos_15:,} no cenário intermediário de 15% e {votos_20:,} "
        f"no teto operacional de 20%. No cenário máximo, isso representa "
        f"{pct_meta_20:.2f}% da meta de 60.000 votos."
    ).replace(",", ".")


# ============================================================
# PROCESSAMENTO PRINCIPAL
# ============================================================

def main():
    print("=" * 80)
    print("CORREÇÃO DOS CÁLCULOS DE CONTRIBUIÇÃO — DASHBOARD V2")
    print("=" * 80)

    if not os.path.exists(ARQUIVO_VEREADORES):
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_VEREADORES}")

    df = pd.read_csv(ARQUIVO_VEREADORES, sep=None, engine="python", encoding="utf-8-sig")

    print(f"Base carregada: {ARQUIVO_VEREADORES}")
    print(f"Linhas carregadas: {len(df)}")
    print(f"Colunas disponíveis: {list(df.columns)}")

    col_municipio = encontrar_coluna(df, ["municipio", "nm_municipio", "cidade"])
    col_vereador = encontrar_coluna(df, ["vereador", "nome_vereador", "candidato", "nome_candidato"])
    col_nome_urna = encontrar_coluna(df, ["nome_urna", "nome_urna_candidato"])
    col_partido = encontrar_coluna(df, ["partido", "sg_partido", "sigla_partido"])
    col_nome_partido = encontrar_coluna(df, ["nome_partido", "nm_partido"])
    col_votos = encontrar_coluna(df, ["votos", "qt_votos", "votos_nominais", "total_votos"])
    col_eleitorado = encontrar_coluna(df, ["eleitorado_2024", "eleitorado"])
    col_prioridade = encontrar_coluna(df, ["prioridade_final", "prioridade"])
    col_grupo = encontrar_coluna(df, ["grupo_politico", "grupo", "bloco_politico"])
    col_percentual_municipio = encontrar_coluna(df, ["percentual_votos_municipio", "percentual_votos_no_municipio"])
    col_rank = encontrar_coluna(df, ["rank_vereador_municipio", "ranking_vereador_municipio"])

    obrigatorias = {
        "municipio": col_municipio,
        "vereador": col_vereador,
        "votos": col_votos,
    }

    faltantes = [nome for nome, col in obrigatorias.items() if col is None]
    if faltantes:
        raise ValueError(f"Colunas obrigatórias não identificadas: {faltantes}")

    print()
    print("Mapeamento de colunas:")
    print(f"Município: {col_municipio}")
    print(f"Vereador: {col_vereador}")
    print(f"Nome urna: {col_nome_urna if col_nome_urna else 'não identificado'}")
    print(f"Partido: {col_partido if col_partido else 'não identificado'}")
    print(f"Nome partido: {col_nome_partido if col_nome_partido else 'não identificado'}")
    print(f"Votos: {col_votos}")
    print(f"Eleitorado: {col_eleitorado if col_eleitorado else 'não identificado'}")
    print(f"Prioridade: {col_prioridade if col_prioridade else 'não identificado'}")
    print(f"Grupo político: {col_grupo if col_grupo else 'não identificado'}")
    print(f"Percentual município: {col_percentual_municipio if col_percentual_municipio else 'não identificado'}")
    print(f"Rank vereador município: {col_rank if col_rank else 'não identificado'}")

    base = df.copy()

    base["municipio"] = base[col_municipio].astype(str).str.strip()
    base["vereador"] = base[col_vereador].astype(str).str.strip()
    base["nome_urna"] = base[col_nome_urna].astype(str).str.strip() if col_nome_urna else base["vereador"]
    base["partido"] = base[col_partido].astype(str).str.strip() if col_partido else ""
    base["nome_partido"] = base[col_nome_partido].astype(str).str.strip() if col_nome_partido else ""
    base["votos"] = base[col_votos].apply(converter_numero).round(0).astype(int)

    if col_eleitorado:
        base["eleitorado_2024"] = base[col_eleitorado].apply(converter_numero).round(0).astype(int)
    else:
        base["eleitorado_2024"] = 0

    if col_prioridade:
        base["prioridade_final"] = base[col_prioridade].astype(str).str.strip()
    else:
        base["prioridade_final"] = ""

    if col_grupo:
        base["grupo_politico_original"] = base[col_grupo].astype(str).str.strip()
    else:
        base["grupo_politico_original"] = "SEM GRUPO"

    if col_rank:
        base["rank_vereador_municipio"] = base[col_rank].apply(converter_numero).round(0).astype(int)
    else:
        base["rank_vereador_municipio"] = 0

    # Mantém apenas registros com votação válida
    base = base[base["votos"] > 0].copy()

    # Percentual de votos do vereador no município.
    # Caso a coluna original esteja com escala errada, recalculamos a partir do total municipal.
    total_votos_municipio = base.groupby("municipio")["votos"].transform("sum")
    base["total_votos_vereadores_municipio"] = total_votos_municipio
    base["percentual_votos_municipio_corrigido"] = (
        base["votos"] / base["total_votos_vereadores_municipio"] * 100
    ).round(4)

    # Grupo político padronizado
    base["grupo_politico_padronizado"] = base["grupo_politico_original"].apply(classificar_grupo_politico)

    # ========================================================
    # CÁLCULO CORRIGIDO DE CONTRIBUIÇÃO
    # ========================================================
    # Regra curada:
    # contribuição = votos do vereador * percentual de conversão
    # teto = 20%
    # ========================================================

    base["meta_votos_davi_2026"] = META_DAVI_2026

    base["taxa_conversao_conservadora"] = TAXA_CONSERVADORA
    base["taxa_conversao_intermediaria"] = TAXA_INTERMEDIARIA
    base["taxa_conversao_maxima"] = TAXA_MAXIMA

    base["contribuicao_davi_10pct"] = (base["votos"] * TAXA_CONSERVADORA).round(0).astype(int)
    base["contribuicao_davi_15pct"] = (base["votos"] * TAXA_INTERMEDIARIA).round(0).astype(int)
    base["contribuicao_davi_20pct"] = (base["votos"] * TAXA_MAXIMA).round(0).astype(int)

    # Garantia matemática: jamais ultrapassar a votação do próprio vereador.
    base["contribuicao_davi_10pct"] = base[["contribuicao_davi_10pct", "votos"]].min(axis=1)
    base["contribuicao_davi_15pct"] = base[["contribuicao_davi_15pct", "votos"]].min(axis=1)
    base["contribuicao_davi_20pct"] = base[["contribuicao_davi_20pct", "votos"]].min(axis=1)

    base["percentual_meta_davi_10pct"] = (base["contribuicao_davi_10pct"] / META_DAVI_2026 * 100).round(4)
    base["percentual_meta_davi_15pct"] = (base["contribuicao_davi_15pct"] / META_DAVI_2026 * 100).round(4)
    base["percentual_meta_davi_20pct"] = (base["contribuicao_davi_20pct"] / META_DAVI_2026 * 100).round(4)

    base["potencial_eleitoral_vereador"] = base["votos"].apply(classificar_potencial_eleitoral)
    base["score_politico_calculado"] = base.apply(calcular_score_politico, axis=1)

    base["metodologia_contribuicao"] = (
        "Contribuição corrigida: votos nominais do vereador em 2024 multiplicados por "
        "10%, 15% e 20%. O cenário de 20% é o teto operacional. Nenhum vereador pode "
        "contribuir, na estimativa, com mais votos do que recebeu."
    )

    base["metodologia_score_politico"] = (
        "Score 0-100: até 40 pontos por porte eleitoral; até 25 por percentual de votos "
        "no município; até 20 por prioridade territorial; até 15 por grupo político classificado."
    )

    base["tooltip_contribuicao_corrigida"] = base.apply(gerar_tooltip_vereador, axis=1)

    # Compatibilidade com nomes antigos que podem estar sendo usados no dashboard.
    # Estes campos substituem os cálculos antigos inflados.
    base["potencial_transferencia_conservador_10pct"] = base["contribuicao_davi_10pct"]
    base["potencial_transferencia_moderado_15pct"] = base["contribuicao_davi_15pct"]
    base["potencial_transferencia_maximo_20pct"] = base["contribuicao_davi_20pct"]

    # Campos antigos preservados, mas agora com valores corrigidos.
    # Atenção: os nomes antigos 35pct/50pct deixam de ser recomendados para exibição.
    if "potencial_transferencia_conservador_20pct" in base.columns:
        base["potencial_transferencia_conservador_20pct"] = base["contribuicao_davi_20pct"]

    if "potencial_transferencia_moderado_35pct" in base.columns:
        base["potencial_transferencia_moderado_35pct"] = base["contribuicao_davi_15pct"]

    if "potencial_transferencia_alto_50pct" in base.columns:
        base["potencial_transferencia_alto_50pct"] = base["contribuicao_davi_20pct"]

    # Ordenação geral
    base = base.sort_values(
        by=["contribuicao_davi_20pct", "votos"],
        ascending=[False, False]
    ).reset_index(drop=True)

    base["ranking_contribuicao_davi"] = range(1, len(base) + 1)

    base["acumulado_davi_10pct"] = base["contribuicao_davi_10pct"].cumsum()
    base["acumulado_davi_15pct"] = base["contribuicao_davi_15pct"].cumsum()
    base["acumulado_davi_20pct"] = base["contribuicao_davi_20pct"].cumsum()

    base["percentual_meta_acumulado_10pct"] = (base["acumulado_davi_10pct"] / META_DAVI_2026 * 100).round(2)
    base["percentual_meta_acumulado_15pct"] = (base["acumulado_davi_15pct"] / META_DAVI_2026 * 100).round(2)
    base["percentual_meta_acumulado_20pct"] = (base["acumulado_davi_20pct"] / META_DAVI_2026 * 100).round(2)

    def qtd_para_meta(coluna):
        atingiu = base[base[coluna] >= META_DAVI_2026]
        if len(atingiu) == 0:
            return None
        return int(atingiu.iloc[0]["ranking_contribuicao_davi"])

    qtd_meta_10 = qtd_para_meta("acumulado_davi_10pct")
    qtd_meta_15 = qtd_para_meta("acumulado_davi_15pct")
    qtd_meta_20 = qtd_para_meta("acumulado_davi_20pct")

    # ========================================================
    # RESUMO MUNICIPAL
    # ========================================================

    idx_lideranca = base.groupby("municipio")["contribuicao_davi_20pct"].idxmax()
    liderancas = base.loc[idx_lideranca, [
        "municipio",
        "vereador",
        "nome_urna",
        "partido",
        "votos",
        "contribuicao_davi_10pct",
        "contribuicao_davi_15pct",
        "contribuicao_davi_20pct",
        "percentual_meta_davi_20pct",
        "grupo_politico_padronizado",
        "tooltip_contribuicao_corrigida",
    ]].copy()

    liderancas = liderancas.rename(columns={
        "vereador": "principal_lideranca",
        "nome_urna": "principal_lideranca_nome_urna",
        "partido": "principal_lideranca_partido",
        "votos": "principal_lideranca_votos",
        "contribuicao_davi_10pct": "principal_lideranca_contribuicao_10pct",
        "contribuicao_davi_15pct": "principal_lideranca_contribuicao_15pct",
        "contribuicao_davi_20pct": "principal_lideranca_contribuicao_20pct",
        "percentual_meta_davi_20pct": "principal_lideranca_percentual_meta_20pct",
        "grupo_politico_padronizado": "principal_lideranca_grupo_politico",
        "tooltip_contribuicao_corrigida": "principal_lideranca_tooltip",
    })

    resumo_municipal = (
        base.groupby("municipio", as_index=False)
        .agg(
            vereadores=("vereador", "count"),
            total_de_votos=("votos", "sum"),
            eleitorado_2024=("eleitorado_2024", "max"),
            contribuicao_davi_10pct=("contribuicao_davi_10pct", "sum"),
            contribuicao_davi_15pct=("contribuicao_davi_15pct", "sum"),
            contribuicao_davi_20pct=("contribuicao_davi_20pct", "sum"),
            score_politico_medio=("score_politico_calculado", "mean"),
        )
    )

    resumo_municipal["score_politico_medio"] = resumo_municipal["score_politico_medio"].round(2)
    resumo_municipal["percentual_meta_davi_10pct"] = (resumo_municipal["contribuicao_davi_10pct"] / META_DAVI_2026 * 100).round(4)
    resumo_municipal["percentual_meta_davi_15pct"] = (resumo_municipal["contribuicao_davi_15pct"] / META_DAVI_2026 * 100).round(4)
    resumo_municipal["percentual_meta_davi_20pct"] = (resumo_municipal["contribuicao_davi_20pct"] / META_DAVI_2026 * 100).round(4)

    resumo_municipal = resumo_municipal.merge(liderancas, on="municipio", how="left")

    resumo_municipal = resumo_municipal.sort_values(
        by=["contribuicao_davi_20pct", "eleitorado_2024"],
        ascending=[False, False]
    ).reset_index(drop=True)

    resumo_municipal["ranking_municipal_contribuicao"] = range(1, len(resumo_municipal) + 1)

    # Compatibilidade visual com a seção "Força Política dos Vereadores"
    resumo_municipal["potencial_corrigido"] = resumo_municipal["contribuicao_davi_20pct"]
    resumo_municipal["potencial_label"] = "Teto 20%"
    resumo_municipal["tooltip_potencial_corrigido"] = (
        "Potencial municipal corrigido: soma do teto operacional de 20% dos votos nominais "
        "dos vereadores mapeados no município. Não representa previsão de votos nem apoio confirmado."
    )

    # ========================================================
    # RESUMO GERAL
    # ========================================================

    total_votos_vereadores = int(base["votos"].sum())
    total_10 = int(base["contribuicao_davi_10pct"].sum())
    total_15 = int(base["contribuicao_davi_15pct"].sum())
    total_20 = int(base["contribuicao_davi_20pct"].sum())

    resumo_geral = {
        "data_geracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "meta_votos_davi_2026": META_DAVI_2026,
        "vereadores_mapeados": int(len(base)),
        "municipios_mapeados": int(base["municipio"].nunique()),
        "votos_vereadores_2024_total": total_votos_vereadores,
        "potencial_bruto_10pct": total_10,
        "potencial_bruto_15pct": total_15,
        "potencial_bruto_20pct": total_20,
        "percentual_meta_10pct": round(total_10 / META_DAVI_2026 * 100, 2),
        "percentual_meta_15pct": round(total_15 / META_DAVI_2026 * 100, 2),
        "percentual_meta_20pct": round(total_20 / META_DAVI_2026 * 100, 2),
        "qtd_vereadores_para_meta_10pct": qtd_meta_10,
        "qtd_vereadores_para_meta_15pct": qtd_meta_15,
        "qtd_vereadores_para_meta_20pct": qtd_meta_20,
        "metodologia": (
            "A contribuição de cada vereador foi corrigida para representar apenas uma fração "
            "dos votos nominais obtidos pelo próprio vereador em 2024. Cenários: 10%, 15% e 20%. "
            "O cenário de 20% é o teto operacional. Os valores são potencial bruto, não previsão "
            "de voto nem apoio confirmado."
        ),
    }

    # ========================================================
    # EXPORTA CSV E JSON PRÓPRIOS
    # ========================================================

    base.to_csv(SAIDA_VEREADORES_CORRIGIDA, index=False, encoding="utf-8-sig")
    base.to_csv(SAIDA_META_DETALHADA, index=False, encoding="utf-8-sig")
    resumo_municipal.to_csv(SAIDA_META_MUNICIPIOS, index=False, encoding="utf-8-sig")

    payload_meta = {
        "resumo_geral": resumo_geral,
        "ranking_vereadores": base.head(500).to_dict(orient="records"),
        "ranking_municipios": resumo_municipal.to_dict(orient="records"),
    }

    with open(SAIDA_META_DASHBOARD, "w", encoding="utf-8") as f:
        json.dump(payload_meta, f, ensure_ascii=False, indent=2)

    # ========================================================
    # ATUALIZA BASE DO DASHBOARD V2
    # ========================================================

    if os.path.exists(ARQUIVO_DASHBOARD_V2):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dashboard = ARQUIVO_DASHBOARD_V2.replace(".json", f"_backup_{timestamp}.json")
        shutil.copy2(ARQUIVO_DASHBOARD_V2, backup_dashboard)

        with open(ARQUIVO_DASHBOARD_V2, "r", encoding="utf-8") as f:
            dashboard = json.load(f)

        dashboard["meta_eleitoral_davi_2026"] = payload_meta
        dashboard["contribuicao_vereadores_corrigida"] = {
            "resumo_geral": resumo_geral,
            "municipios": resumo_municipal.to_dict(orient="records"),
            "vereadores_top_500": base.head(500).to_dict(orient="records"),
            "metodologia": resumo_geral["metodologia"],
        }

        # Chaves de compatibilidade: se o JS buscar esses nomes, os dados já estarão corrigidos.
        dashboard["forca_politica_vereadores_corrigida"] = resumo_municipal.to_dict(orient="records")
        dashboard["ranking_contribuicao_davi_corrigido"] = base.head(500).to_dict(orient="records")

        with open(ARQUIVO_DASHBOARD_V2, "w", encoding="utf-8") as f:
            json.dump(dashboard, f, ensure_ascii=False, indent=2)

        dashboard_atualizado = True
    else:
        backup_dashboard = None
        dashboard_atualizado = False

    # ========================================================
    # RELATÓRIO
    # ========================================================

    with open(SAIDA_RELATORIO, "w", encoding="utf-8") as f:
        f.write("# Correção dos Cálculos de Contribuição dos Vereadores — Dashboard V2\n\n")
        f.write(f"Data de geração: {resumo_geral['data_geracao']}\n\n")

        f.write("## Regra corrigida\n\n")
        f.write("A contribuição potencial de cada vereador foi recalculada como percentual dos votos nominais obtidos em 2024.\n\n")
        f.write("- Cenário conservador: 10%\n")
        f.write("- Cenário intermediário: 15%\n")
        f.write("- Cenário máximo operacional: 20%\n\n")

        f.write("## Meta\n\n")
        f.write(f"- Meta operacional Davi Maia 2026: {META_DAVI_2026:,} votos\n\n".replace(",", "."))

        f.write("## Resultado geral\n\n")
        f.write(f"- Vereadores mapeados: {len(base):,}\n".replace(",", "."))
        f.write(f"- Municípios mapeados: {base['municipio'].nunique():,}\n".replace(",", "."))
        f.write(f"- Votos totais dos vereadores em 2024: {total_votos_vereadores:,}\n".replace(",", "."))
        f.write(f"- Potencial bruto 10%: {total_10:,} votos\n".replace(",", "."))
        f.write(f"- Potencial bruto 15%: {total_15:,} votos\n".replace(",", "."))
        f.write(f"- Potencial bruto 20%: {total_20:,} votos\n\n".replace(",", "."))

        f.write("## Vereadores necessários para atingir a meta\n\n")
        f.write(f"- Cenário 10%: {qtd_meta_10 if qtd_meta_10 else 'meta não atingida'}\n")
        f.write(f"- Cenário 15%: {qtd_meta_15 if qtd_meta_15 else 'meta não atingida'}\n")
        f.write(f"- Cenário 20%: {qtd_meta_20 if qtd_meta_20 else 'meta não atingida'}\n\n")

        f.write("## Arquivos gerados\n\n")
        f.write(f"- {SAIDA_VEREADORES_CORRIGIDA}\n")
        f.write(f"- {SAIDA_META_DETALHADA}\n")
        f.write(f"- {SAIDA_META_MUNICIPIOS}\n")
        f.write(f"- {SAIDA_META_DASHBOARD}\n")
        f.write(f"- {SAIDA_RELATORIO}\n")

        if dashboard_atualizado:
            f.write(f"- Dashboard V2 atualizado: {ARQUIVO_DASHBOARD_V2}\n")
            f.write(f"- Backup do Dashboard V2: {backup_dashboard}\n")
        else:
            f.write("- Dashboard V2 não atualizado porque base_dashboard_v2.json não foi encontrado.\n")

    # ========================================================
    # LOG FINAL
    # ========================================================

    print()
    print("=" * 80)
    print("RESULTADO DA CORREÇÃO")
    print("=" * 80)
    print(f"Meta Davi Maia 2026: {META_DAVI_2026:,} votos".replace(",", "."))
    print(f"Vereadores mapeados: {len(base):,}".replace(",", "."))
    print(f"Municípios mapeados: {base['municipio'].nunique():,}".replace(",", "."))
    print(f"Votos totais dos vereadores 2024: {total_votos_vereadores:,}".replace(",", "."))
    print(f"Potencial bruto 10%: {total_10:,} votos ({resumo_geral['percentual_meta_10pct']:.2f}% da meta)".replace(",", "."))
    print(f"Potencial bruto 15%: {total_15:,} votos ({resumo_geral['percentual_meta_15pct']:.2f}% da meta)".replace(",", "."))
    print(f"Potencial bruto 20%: {total_20:,} votos ({resumo_geral['percentual_meta_20pct']:.2f}% da meta)".replace(",", "."))
    print()
    print("Vereadores necessários para atingir 60.000 votos:")
    print(f"Cenário 10%: {qtd_meta_10 if qtd_meta_10 else 'meta não atingida'}")
    print(f"Cenário 15%: {qtd_meta_15 if qtd_meta_15 else 'meta não atingida'}")
    print(f"Cenário 20%: {qtd_meta_20 if qtd_meta_20 else 'meta não atingida'}")
    print()
    print("Arquivos gerados:")
    print(SAIDA_VEREADORES_CORRIGIDA)
    print(SAIDA_META_DETALHADA)
    print(SAIDA_META_MUNICIPIOS)
    print(SAIDA_META_DASHBOARD)
    print(SAIDA_RELATORIO)

    if dashboard_atualizado:
        print()
        print("base_dashboard_v2.json atualizado com sucesso.")
        print(f"Backup criado em: {backup_dashboard}")
    else:
        print()
        print("Atenção: base_dashboard_v2.json não encontrado. O dashboard não foi atualizado.")

    print("=" * 80)


if __name__ == "__main__":
    main()