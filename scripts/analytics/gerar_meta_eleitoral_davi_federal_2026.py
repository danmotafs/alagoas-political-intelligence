import os
import json
import pandas as pd
from datetime import datetime


# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DATA_FINAL_DIR = os.path.join(BASE_DIR, "data", "final")
DATA_DASHBOARD_DIR = os.path.join(BASE_DIR, "data", "dashboard")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(DATA_FINAL_DIR, exist_ok=True)
os.makedirs(DATA_DASHBOARD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


# ============================================================
# META ELEITORAL OPERACIONAL
# ============================================================

META_VOTOS_DAVI_2026 = 60000


# ============================================================
# CENÁRIOS DE CONVERSÃO
# ============================================================
# Conforme curadoria:
# O objetivo é converter parte dos eleitores do vereador em votos para Davi.
# Portanto, o potencial nunca pode ultrapassar a própria votação do vereador.
#
# Cenário conservador: 10%
# Cenário intermediário: 15%
# Cenário máximo operacional: 20%
# ============================================================

TAXA_CONVERSAO_CONSERVADORA = 0.10
TAXA_CONVERSAO_INTERMEDIARIA = 0.15
TAXA_CONVERSAO_MAXIMA = 0.20


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_coluna(nome: str) -> str:
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

    nome = nome.replace(" ", "_")
    nome = nome.replace("-", "_")
    nome = nome.replace("/", "_")

    while "__" in nome:
        nome = nome.replace("__", "_")

    return nome


def encontrar_coluna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
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


def carregar_base_vereadores() -> pd.DataFrame:
    candidatos_arquivo = [
        os.path.join(DATA_FINAL_DIR, "inteligencia_vereadores_alagoas_2024.csv"),
        os.path.join(DATA_FINAL_DIR, "base_vereadores_alagoas_2024.csv"),
        os.path.join(DATA_FINAL_DIR, "inteligencia_municipal_vereadores.csv"),
    ]

    for caminho in candidatos_arquivo:
        if os.path.exists(caminho):
            print(f"Base de vereadores encontrada: {caminho}")
            return pd.read_csv(caminho, sep=None, engine="python", encoding="utf-8-sig")

    raise FileNotFoundError(
        "Nenhuma base de vereadores foi encontrada em data/final."
    )


def classificar_potencial_por_votos(votos_vereador: float) -> str:
    """
    Classificação objetiva baseada apenas na votação nominal do vereador.
    Não calcula apoio político; apenas porte eleitoral bruto.
    """
    if votos_vereador >= 5000:
        return "MUITO_ALTO"
    elif votos_vereador >= 3000:
        return "ALTO"
    elif votos_vereador >= 1500:
        return "MEDIO"
    elif votos_vereador >= 700:
        return "BAIXO"
    else:
        return "RESIDUAL"


def classificar_grupo_politico(valor) -> str:
    """
    Padroniza grupo político conforme curadoria:
    - GRUPO CALHEIROS
    - GRUPO LIRA
    - GRUPO JHC
    - SEM GRUPO
    """
    if pd.isna(valor):
        return "SEM GRUPO"

    texto = str(valor).strip().upper()

    if texto == "" or texto in ["NAO_CLASSIFICADO", "NÃO CLASSIFICADO", "NAN", "NONE"]:
        return "SEM GRUPO"

    if "CALHEIROS" in texto or "RENAN" in texto or "MDB" in texto:
        return "GRUPO CALHEIROS"

    if "LIRA" in texto or "ARTHUR" in texto or "ARTHUR LIRA" in texto or "PP" in texto:
        return "GRUPO LIRA"

    if "JHC" in texto or "PL" in texto:
        return "GRUPO JHC"

    if "SEM" in texto:
        return "SEM GRUPO"

    return "SEM GRUPO"


def calcular_score_politico(row: pd.Series) -> float:
    """
    Score político documentado para o painel.

    O score vai de 0 a 100 e combina:
    - 40 pontos: força eleitoral do vereador no município
    - 30 pontos: relação com Davi, se houver campo preenchido
    - 20 pontos: status de articulação, se houver campo preenchido
    - 10 pontos: grupo político classificado

    Este score não representa previsão eleitoral.
    É apenas uma métrica operacional de priorização/curadoria.
    """

    score = 0

    votos = row.get("votos_vereador_2024", 0)

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

    relacao = str(row.get("relacao_davi", "")).strip().lower()

    if "aliado_forte" in relacao or "aliado forte" in relacao:
        score += 30
    elif "aliado_eventual" in relacao or "aliado eventual" in relacao:
        score += 20
    elif "neutro" in relacao:
        score += 12
    elif "adversario" in relacao or "adversário" in relacao:
        score += 0
    else:
        score += 8

    status = str(row.get("status_articulacao", "")).strip().lower()

    if "confirmado" in status or "fechado" in status:
        score += 20
    elif "negociacao" in status or "negociação" in status:
        score += 14
    elif "indefinido" in status:
        score += 6
    else:
        score += 6

    grupo = str(row.get("grupo_politico_padronizado", "")).strip().upper()

    if grupo in ["GRUPO CALHEIROS", "GRUPO LIRA", "GRUPO JHC"]:
        score += 10
    else:
        score += 4

    return round(min(score, 100), 2)


def gerar_insight(row: pd.Series) -> str:
    vereador = row["vereador"]
    municipio = row["municipio"]
    votos = int(row["votos_vereador_2024"])
    conservador = int(row["votos_potenciais_davi_10pct"])
    maximo = int(row["votos_potenciais_davi_20pct"])
    pct_meta_max = row["percentual_meta_davi_20pct"]

    return (
        f"{vereador}, em {municipio}, recebeu {votos:,} votos em 2024. "
        f"Pela regra de conversão validada na curadoria, pode representar entre "
        f"{conservador:,} votos potenciais para Davi no cenário conservador de 10% "
        f"e {maximo:,} votos no cenário máximo operacional de 20%. "
        f"No teto de conversão, isso equivale a {pct_meta_max:.2f}% da meta de 60 mil votos."
    ).replace(",", ".")


# ============================================================
# PROCESSAMENTO PRINCIPAL
# ============================================================

def main():
    print("=" * 70)
    print("GERAÇÃO DA META ELEITORAL FEDERAL 2026 — DAVI MAIA")
    print("=" * 70)

    df = carregar_base_vereadores()

    print(f"Linhas carregadas: {len(df)}")
    print(f"Colunas disponíveis: {list(df.columns)}")

    col_municipio = encontrar_coluna(df, [
        "municipio",
        "nm_municipio",
        "nome_municipio",
        "cidade",
    ])

    col_vereador = encontrar_coluna(df, [
        "vereador",
        "nome_vereador",
        "candidato",
        "nome_candidato",
        "nm_candidato",
        "lideranca",
        "nome",
    ])

    col_nome_urna = encontrar_coluna(df, [
        "nome_urna",
        "nm_urna_candidato",
        "nome_urna_candidato",
    ])

    col_partido = encontrar_coluna(df, [
        "partido",
        "sg_partido",
        "sigla_partido",
    ])

    col_votos = encontrar_coluna(df, [
        "votos",
        "qt_votos",
        "votos_nominais",
        "votacao",
        "total_votos",
        "votos_vereador",
    ])

    col_grupo = encontrar_coluna(df, [
        "grupo_politico",
        "grupo",
        "bloco_politico",
    ])

    col_relacao = encontrar_coluna(df, [
        "relacao_davi",
        "relação_davi",
        "relacao_com_davi",
    ])

    col_score_articulacao = encontrar_coluna(df, [
        "score_articulacao",
        "score_articulação",
    ])

    col_prioridade = encontrar_coluna(df, [
        "prioridade_final",
        "prioridade",
    ])

    col_eleitorado = encontrar_coluna(df, [
        "eleitorado_2024",
        "eleitorado",
    ])

    col_percentual_municipio = encontrar_coluna(df, [
        "percentual_votos_municipio",
        "percentual_votos_no_municipio",
    ])

    if col_municipio is None:
        raise ValueError("Não foi possível identificar a coluna de município.")

    if col_vereador is None:
        raise ValueError("Não foi possível identificar a coluna de vereador/candidato.")

    if col_votos is None:
        raise ValueError("Não foi possível identificar a coluna de votos.")

    print()
    print("Mapeamento de colunas:")
    print(f"Município: {col_municipio}")
    print(f"Vereador: {col_vereador}")
    print(f"Nome urna: {col_nome_urna if col_nome_urna else 'não identificado'}")
    print(f"Partido: {col_partido if col_partido else 'não identificado'}")
    print(f"Votos: {col_votos}")
    print(f"Grupo político: {col_grupo if col_grupo else 'não identificado'}")
    print(f"Relação Davi: {col_relacao if col_relacao else 'não identificado'}")
    print(f"Score articulação: {col_score_articulacao if col_score_articulacao else 'não identificado'}")
    print(f"Prioridade: {col_prioridade if col_prioridade else 'não identificado'}")
    print(f"Eleitorado: {col_eleitorado if col_eleitorado else 'não identificado'}")
    print(f"Percentual votos município: {col_percentual_municipio if col_percentual_municipio else 'não identificado'}")

    base = pd.DataFrame()

    base["municipio"] = df[col_municipio].astype(str).str.strip()
    base["vereador"] = df[col_vereador].astype(str).str.strip()
    base["nome_urna"] = df[col_nome_urna].astype(str).str.strip() if col_nome_urna else base["vereador"]
    base["partido"] = df[col_partido].astype(str).str.strip() if col_partido else ""
    base["votos_vereador_2024"] = df[col_votos].apply(converter_numero).round(0).astype(int)

    if col_grupo:
        base["grupo_politico_original"] = df[col_grupo].astype(str).str.strip()
    else:
        base["grupo_politico_original"] = "SEM GRUPO"

    base["grupo_politico_padronizado"] = base["grupo_politico_original"].apply(classificar_grupo_politico)

    if col_relacao:
        base["relacao_davi"] = df[col_relacao].astype(str).str.strip()
    else:
        base["relacao_davi"] = "nao_informado"

    if col_score_articulacao:
        base["score_articulacao_original"] = df[col_score_articulacao].apply(converter_numero)
    else:
        base["score_articulacao_original"] = 0

    if col_prioridade:
        base["prioridade_final"] = df[col_prioridade].astype(str).str.strip()
    else:
        base["prioridade_final"] = ""

    if col_eleitorado:
        base["eleitorado_2024"] = df[col_eleitorado].apply(converter_numero).round(0).astype(int)
    else:
        base["eleitorado_2024"] = 0

    if col_percentual_municipio:
        base["percentual_votos_municipio"] = df[col_percentual_municipio].apply(converter_numero)
    else:
        base["percentual_votos_municipio"] = 0

    # Remove linhas inválidas
    base = base[base["municipio"].notna()]
    base = base[base["vereador"].notna()]
    base = base[base["votos_vereador_2024"] > 0].copy()

    # ========================================================
    # CÁLCULO CORRIGIDO DE CONVERSÃO DE VOTOS
    # ========================================================
    # Regra:
    # votos do vereador * 10%, 15% ou 20%.
    # O potencial nunca pode ser maior que os votos do vereador.
    # ========================================================

    base["taxa_conversao_conservadora"] = TAXA_CONVERSAO_CONSERVADORA
    base["taxa_conversao_intermediaria"] = TAXA_CONVERSAO_INTERMEDIARIA
    base["taxa_conversao_maxima"] = TAXA_CONVERSAO_MAXIMA

    base["votos_potenciais_davi_10pct"] = (
        base["votos_vereador_2024"] * TAXA_CONVERSAO_CONSERVADORA
    ).round(0).astype(int)

    base["votos_potenciais_davi_15pct"] = (
        base["votos_vereador_2024"] * TAXA_CONVERSAO_INTERMEDIARIA
    ).round(0).astype(int)

    base["votos_potenciais_davi_20pct"] = (
        base["votos_vereador_2024"] * TAXA_CONVERSAO_MAXIMA
    ).round(0).astype(int)

    # Segurança: impede qualquer valor acima dos votos do vereador
    base["votos_potenciais_davi_10pct"] = base[
        ["votos_potenciais_davi_10pct", "votos_vereador_2024"]
    ].min(axis=1)

    base["votos_potenciais_davi_15pct"] = base[
        ["votos_potenciais_davi_15pct", "votos_vereador_2024"]
    ].min(axis=1)

    base["votos_potenciais_davi_20pct"] = base[
        ["votos_potenciais_davi_20pct", "votos_vereador_2024"]
    ].min(axis=1)

    base["meta_votos_davi_2026"] = META_VOTOS_DAVI_2026

    base["percentual_meta_davi_10pct"] = (
        base["votos_potenciais_davi_10pct"] / META_VOTOS_DAVI_2026 * 100
    ).round(4)

    base["percentual_meta_davi_15pct"] = (
        base["votos_potenciais_davi_15pct"] / META_VOTOS_DAVI_2026 * 100
    ).round(4)

    base["percentual_meta_davi_20pct"] = (
        base["votos_potenciais_davi_20pct"] / META_VOTOS_DAVI_2026 * 100
    ).round(4)

    base["potencial_eleitoral_bruto"] = base["votos_vereador_2024"].apply(classificar_potencial_por_votos)

    base["score_politico_calculado"] = base.apply(calcular_score_politico, axis=1)

    base["metodologia_score_politico"] = (
        "Score 0-100: até 40 pontos por força eleitoral do vereador; "
        "até 30 por relação com Davi; até 20 por status de articulação; "
        "até 10 por grupo político classificado."
    )

    base["metodologia_conversao_votos"] = (
        "Potencial calculado como percentual dos votos nominais do vereador em 2024. "
        "Cenários: 10% conservador, 15% intermediário e 20% máximo operacional."
    )

    base["insight_estrategico"] = base.apply(gerar_insight, axis=1)

    # Ordena pela votação nominal e potencial máximo matemático
    base = base.sort_values(
        by=["votos_potenciais_davi_20pct", "votos_vereador_2024"],
        ascending=[False, False]
    ).reset_index(drop=True)

    base["ranking_potencial_transferencia"] = range(1, len(base) + 1)

    # Acumulados por cenário
    base["votos_acumulados_10pct"] = base["votos_potenciais_davi_10pct"].cumsum()
    base["votos_acumulados_15pct"] = base["votos_potenciais_davi_15pct"].cumsum()
    base["votos_acumulados_20pct"] = base["votos_potenciais_davi_20pct"].cumsum()

    base["percentual_meta_acumulado_10pct"] = (
        base["votos_acumulados_10pct"] / META_VOTOS_DAVI_2026 * 100
    ).round(2)

    base["percentual_meta_acumulado_15pct"] = (
        base["votos_acumulados_15pct"] / META_VOTOS_DAVI_2026 * 100
    ).round(2)

    base["percentual_meta_acumulado_20pct"] = (
        base["votos_acumulados_20pct"] / META_VOTOS_DAVI_2026 * 100
    ).round(2)

    base["atinge_meta_10pct_ate_aqui"] = base["votos_acumulados_10pct"] >= META_VOTOS_DAVI_2026
    base["atinge_meta_15pct_ate_aqui"] = base["votos_acumulados_15pct"] >= META_VOTOS_DAVI_2026
    base["atinge_meta_20pct_ate_aqui"] = base["votos_acumulados_20pct"] >= META_VOTOS_DAVI_2026

    def qtd_para_meta(coluna_flag):
        subset = base[base[coluna_flag] == True]
        if len(subset) == 0:
            return None
        return int(subset.iloc[0]["ranking_potencial_transferencia"])

    qtd_meta_10 = qtd_para_meta("atinge_meta_10pct_ate_aqui")
    qtd_meta_15 = qtd_para_meta("atinge_meta_15pct_ate_aqui")
    qtd_meta_20 = qtd_para_meta("atinge_meta_20pct_ate_aqui")

    # ========================================================
    # RESUMO MUNICIPAL
    # ========================================================

    resumo_municipal = (
        base.groupby("municipio", as_index=False)
        .agg(
            vereadores_mapeados=("vereador", "count"),
            votos_vereadores_2024=("votos_vereador_2024", "sum"),
            votos_potenciais_davi_10pct=("votos_potenciais_davi_10pct", "sum"),
            votos_potenciais_davi_15pct=("votos_potenciais_davi_15pct", "sum"),
            votos_potenciais_davi_20pct=("votos_potenciais_davi_20pct", "sum"),
            maior_potencial_individual_20pct=("votos_potenciais_davi_20pct", "max"),
            score_politico_medio=("score_politico_calculado", "mean"),
            eleitorado_2024=("eleitorado_2024", "max"),
        )
    )

    resumo_municipal["meta_votos_davi_2026"] = META_VOTOS_DAVI_2026

    resumo_municipal["percentual_meta_davi_10pct"] = (
        resumo_municipal["votos_potenciais_davi_10pct"] / META_VOTOS_DAVI_2026 * 100
    ).round(4)

    resumo_municipal["percentual_meta_davi_15pct"] = (
        resumo_municipal["votos_potenciais_davi_15pct"] / META_VOTOS_DAVI_2026 * 100
    ).round(4)

    resumo_municipal["percentual_meta_davi_20pct"] = (
        resumo_municipal["votos_potenciais_davi_20pct"] / META_VOTOS_DAVI_2026 * 100
    ).round(4)

    resumo_municipal["score_politico_medio"] = resumo_municipal["score_politico_medio"].round(2)

    resumo_municipal = resumo_municipal.sort_values(
        by=["votos_potenciais_davi_20pct", "eleitorado_2024"],
        ascending=[False, False]
    ).reset_index(drop=True)

    resumo_municipal["ranking_municipal_potencial"] = range(1, len(resumo_municipal) + 1)

    # ========================================================
    # RESUMO POR GRUPO POLÍTICO
    # ========================================================

    resumo_grupo = (
        base.groupby("grupo_politico_padronizado", as_index=False)
        .agg(
            vereadores_mapeados=("vereador", "count"),
            municipios_distintos=("municipio", "nunique"),
            votos_vereadores_2024=("votos_vereador_2024", "sum"),
            votos_potenciais_davi_10pct=("votos_potenciais_davi_10pct", "sum"),
            votos_potenciais_davi_15pct=("votos_potenciais_davi_15pct", "sum"),
            votos_potenciais_davi_20pct=("votos_potenciais_davi_20pct", "sum"),
            score_politico_medio=("score_politico_calculado", "mean"),
        )
    )

    resumo_grupo["percentual_meta_davi_20pct"] = (
        resumo_grupo["votos_potenciais_davi_20pct"] / META_VOTOS_DAVI_2026 * 100
    ).round(4)

    resumo_grupo["score_politico_medio"] = resumo_grupo["score_politico_medio"].round(2)

    resumo_grupo = resumo_grupo.sort_values(
        by="votos_potenciais_davi_20pct",
        ascending=False
    ).reset_index(drop=True)

    # ========================================================
    # RESUMO GERAL
    # ========================================================

    total_10 = int(base["votos_potenciais_davi_10pct"].sum())
    total_15 = int(base["votos_potenciais_davi_15pct"].sum())
    total_20 = int(base["votos_potenciais_davi_20pct"].sum())

    resumo_geral = {
        "data_geracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "meta_votos_davi_2026": META_VOTOS_DAVI_2026,
        "total_vereadores_mapeados": int(len(base)),
        "total_municipios_mapeados": int(base["municipio"].nunique()),
        "votos_vereadores_2024_total": int(base["votos_vereador_2024"].sum()),
        "votos_potenciais_davi_10pct_total": total_10,
        "votos_potenciais_davi_15pct_total": total_15,
        "votos_potenciais_davi_20pct_total": total_20,
        "percentual_meta_total_10pct": round(total_10 / META_VOTOS_DAVI_2026 * 100, 2),
        "percentual_meta_total_15pct": round(total_15 / META_VOTOS_DAVI_2026 * 100, 2),
        "percentual_meta_total_20pct": round(total_20 / META_VOTOS_DAVI_2026 * 100, 2),
        "qtd_vereadores_para_meta_10pct": qtd_meta_10,
        "qtd_vereadores_para_meta_15pct": qtd_meta_15,
        "qtd_vereadores_para_meta_20pct": qtd_meta_20,
        "metodologia": (
            "A meta operacional de Davi Maia foi fixada em 60.000 votos. "
            "A contribuição de cada vereador é calculada exclusivamente como percentual "
            "dos votos nominais obtidos pelo vereador em 2024: 10%, 15% e 20%. "
            "O cenário de 20% é o teto operacional, conforme curadoria. "
            "Nenhum vereador pode contribuir, na estimativa, com mais votos do que recebeu."
        ),
        "metodologia_score_politico": (
            "Score 0-100: até 40 pontos por força eleitoral do vereador; "
            "até 30 pontos por relação com Davi; até 20 pontos por status de articulação; "
            "até 10 pontos por grupo político classificado."
        ),
        "grupos_politicos_validos": [
            "GRUPO CALHEIROS",
            "GRUPO LIRA",
            "GRUPO JHC",
            "SEM GRUPO",
        ],
    }

    # ========================================================
    # EXPORTAÇÕES
    # ========================================================

    saida_detalhada_csv = os.path.join(DATA_FINAL_DIR, "meta_eleitoral_davi_federal_2026.csv")
    saida_municipal_csv = os.path.join(DATA_FINAL_DIR, "resumo_meta_eleitoral_municipios_davi_2026.csv")
    saida_grupo_csv = os.path.join(DATA_FINAL_DIR, "resumo_meta_eleitoral_grupos_politicos_davi_2026.csv")
    saida_json = os.path.join(DATA_DASHBOARD_DIR, "meta_eleitoral_davi_federal_2026.json")
    saida_md = os.path.join(REPORTS_DIR, "meta_eleitoral_davi_federal_2026.md")

    base.to_csv(saida_detalhada_csv, index=False, encoding="utf-8-sig")
    resumo_municipal.to_csv(saida_municipal_csv, index=False, encoding="utf-8-sig")
    resumo_grupo.to_csv(saida_grupo_csv, index=False, encoding="utf-8-sig")

    dashboard_payload = {
        "resumo_geral": resumo_geral,
        "top_vereadores": base.head(100).to_dict(orient="records"),
        "resumo_municipal": resumo_municipal.to_dict(orient="records"),
        "resumo_grupo_politico": resumo_grupo.to_dict(orient="records"),
    }

    with open(saida_json, "w", encoding="utf-8") as f:
        json.dump(dashboard_payload, f, ensure_ascii=False, indent=2)

    with open(saida_md, "w", encoding="utf-8") as f:
        f.write("# Meta Eleitoral Federal 2026 — Davi Maia\n\n")
        f.write(f"Data de geração: {resumo_geral['data_geracao']}\n\n")

        f.write("## Premissa Central\n\n")
        f.write("A meta operacional de Davi Maia foi ajustada para **60.000 votos**.\n\n")
        f.write(
            "A contribuição potencial de cada vereador é calculada como uma fração "
            "dos votos nominais recebidos pelo próprio vereador em 2024.\n\n"
        )

        f.write("Cenários utilizados:\n\n")
        f.write("- Conservador: 10% dos votos do vereador\n")
        f.write("- Intermediário: 15% dos votos do vereador\n")
        f.write("- Máximo operacional: 20% dos votos do vereador\n\n")

        f.write("## Resumo Geral\n\n")
        f.write(f"- Vereadores mapeados: {len(base):,}\n".replace(",", "."))
        f.write(f"- Municípios mapeados: {base['municipio'].nunique():,}\n".replace(",", "."))
        f.write(f"- Votos totais dos vereadores em 2024: {int(base['votos_vereador_2024'].sum()):,}\n".replace(",", "."))
        f.write(f"- Potencial 10%: {total_10:,} votos\n".replace(",", "."))
        f.write(f"- Potencial 15%: {total_15:,} votos\n".replace(",", "."))
        f.write(f"- Potencial 20%: {total_20:,} votos\n".replace(",", "."))
        f.write(f"- Cobertura da meta no cenário 10%: {resumo_geral['percentual_meta_total_10pct']:.2f}%\n")
        f.write(f"- Cobertura da meta no cenário 15%: {resumo_geral['percentual_meta_total_15pct']:.2f}%\n")
        f.write(f"- Cobertura da meta no cenário 20%: {resumo_geral['percentual_meta_total_20pct']:.2f}%\n\n")

        f.write("## Quantidade de Vereadores Necessários para Atingir a Meta\n\n")
        f.write(f"- Cenário 10%: {qtd_meta_10 if qtd_meta_10 else 'meta não atingida'}\n")
        f.write(f"- Cenário 15%: {qtd_meta_15 if qtd_meta_15 else 'meta não atingida'}\n")
        f.write(f"- Cenário 20%: {qtd_meta_20 if qtd_meta_20 else 'meta não atingida'}\n\n")

        f.write("## Metodologia do Score Político\n\n")
        f.write(
            "O score político calculado vai de 0 a 100 e combina: "
            "força eleitoral do vereador, relação com Davi, status de articulação "
            "e grupo político classificado.\n\n"
        )

        f.write("Grupos políticos válidos:\n\n")
        f.write("- GRUPO CALHEIROS\n")
        f.write("- GRUPO LIRA\n")
        f.write("- GRUPO JHC\n")
        f.write("- SEM GRUPO\n\n")

        f.write("## Top 20 por Potencial Máximo Operacional\n\n")
        f.write("| Ranking | Município | Vereador | Partido | Votos 2024 | 10% | 15% | 20% | % Meta 20% | Grupo |\n")
        f.write("|---:|---|---|---|---:|---:|---:|---:|---:|---|\n")

        for _, row in base.head(20).iterrows():
            f.write(
                f"| {int(row['ranking_potencial_transferencia'])} "
                f"| {row['municipio']} "
                f"| {row['vereador']} "
                f"| {row['partido']} "
                f"| {int(row['votos_vereador_2024'])} "
                f"| {int(row['votos_potenciais_davi_10pct'])} "
                f"| {int(row['votos_potenciais_davi_15pct'])} "
                f"| {int(row['votos_potenciais_davi_20pct'])} "
                f"| {row['percentual_meta_davi_20pct']:.2f}% "
                f"| {row['grupo_politico_padronizado']} |\n"
            )

    print()
    print("=" * 70)
    print("ARQUIVOS GERADOS")
    print("=" * 70)
    print(saida_detalhada_csv)
    print(saida_municipal_csv)
    print(saida_grupo_csv)
    print(saida_json)
    print(saida_md)

    print()
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    print(f"Meta operacional de Davi: {META_VOTOS_DAVI_2026:,} votos".replace(",", "."))
    print(f"Vereadores mapeados: {len(base):,}".replace(",", "."))
    print(f"Municípios mapeados: {base['municipio'].nunique():,}".replace(",", "."))
    print(f"Votos totais dos vereadores em 2024: {int(base['votos_vereador_2024'].sum()):,}".replace(",", "."))
    print(f"Potencial total 10%: {total_10:,} votos ({resumo_geral['percentual_meta_total_10pct']:.2f}% da meta)".replace(",", "."))
    print(f"Potencial total 15%: {total_15:,} votos ({resumo_geral['percentual_meta_total_15pct']:.2f}% da meta)".replace(",", "."))
    print(f"Potencial total 20%: {total_20:,} votos ({resumo_geral['percentual_meta_total_20pct']:.2f}% da meta)".replace(",", "."))

    print()
    print("Quantidade de vereadores necessários para atingir 60.000 votos:")
    print(f"Cenário 10%: {qtd_meta_10 if qtd_meta_10 else 'meta não atingida'}")
    print(f"Cenário 15%: {qtd_meta_15 if qtd_meta_15 else 'meta não atingida'}")
    print(f"Cenário 20%: {qtd_meta_20 if qtd_meta_20 else 'meta não atingida'}")

    print("=" * 70)


if __name__ == "__main__":
    main()