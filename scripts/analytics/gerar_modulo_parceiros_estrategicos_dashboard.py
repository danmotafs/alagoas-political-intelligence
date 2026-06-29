import os
import json
import math
from datetime import datetime

import pandas as pd


BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

ARQUIVO_CRUZAMENTO = os.path.join(
    BASE_DIR,
    "data",
    "final",
    "parceiros",
    "consolidado_cruzamento_parceiros_vereadores_2024.csv",
)

ARQUIVO_TERRITORIAL = os.path.join(
    BASE_DIR,
    "data",
    "dashboard",
    "parceiros",
    "consolidado_parceiros_territorial.json",
)

SAIDA_JSON = os.path.join(
    BASE_DIR,
    "data",
    "dashboard",
    "parceiros",
    "modulo_parceiros_estrategicos_v1.json",
)

SAIDA_CSV_TOP = os.path.join(
    BASE_DIR,
    "data",
    "final",
    "parceiros",
    "top_convergencias_parceiros_estrategicos_v1.csv",
)

META_DAVI = 60000


def detectar_encoding(caminho):
    encodings = ["utf-8-sig", "utf-8", "latin-1", "ISO-8859-1", "cp1252"]

    for encoding in encodings:
        try:
            with open(caminho, "r", encoding=encoding) as f:
                f.readline()
            return encoding
        except UnicodeDecodeError:
            continue

    return "latin-1"


def detectar_sep(caminho, encoding):
    with open(caminho, "r", encoding=encoding, errors="replace") as f:
        primeira_linha = f.readline()

    if ";" in primeira_linha:
        return ";"

    if "," in primeira_linha:
        return ","

    return ";"


def ler_csv(caminho):
    encoding = detectar_encoding(caminho)
    sep = detectar_sep(caminho, encoding)

    return pd.read_csv(
        caminho,
        sep=sep,
        encoding=encoding,
        dtype=str,
        low_memory=False,
        on_bad_lines="skip",
    )


def converter_int(valor):
    try:
        if pd.isna(valor):
            return 0

        texto = str(valor).strip()

        if texto == "":
            return 0

        texto = texto.replace(".", "").replace(",", ".")
        return int(float(texto))
    except Exception:
        return 0


def converter_float(valor):
    try:
        if pd.isna(valor):
            return 0.0

        texto = str(valor).strip()

        if texto == "":
            return 0.0

        texto = texto.replace(",", ".")
        return float(texto)
    except Exception:
        return 0.0


def limpar_json(obj):
    if isinstance(obj, dict):
        return {k: limpar_json(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [limpar_json(v) for v in obj]

    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj

    if pd.isna(obj) if not isinstance(obj, (str, int, float, bool, dict, list, type(None))) else False:
        return None

    return obj


def carregar_territorial():
    if not os.path.exists(ARQUIVO_TERRITORIAL):
        return {}

    with open(ARQUIVO_TERRITORIAL, "r", encoding="utf-8") as f:
        return json.load(f)


def preparar_cruzamento():
    if not os.path.exists(ARQUIVO_CRUZAMENTO):
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_CRUZAMENTO}")

    df = ler_csv(ARQUIVO_CRUZAMENTO)

    colunas_numericas = [
        "votos_parceiro_local",
        "votos_vereador_local",
        "indice_convergencia",
        "potencial_davi_10pct_local",
        "potencial_davi_15pct_local",
        "potencial_davi_20pct_local",
    ]

    for col in colunas_numericas:
        if col in df.columns:
            if col == "indice_convergencia":
                df[col] = df[col].apply(converter_float)
            else:
                df[col] = df[col].apply(converter_int)

    return df


def gerar_resumo_geral(df):
    if df.empty:
        return {
            "parceiros_processados": 0,
            "total_cruzamentos_qualificados": 0,
            "municipios_com_convergencia": 0,
            "vereadores_convergentes": 0,
            "locais_convergentes": 0,
            "potencial_local_bruto_20pct": 0,
            "potencial_vereadores_unicos_20pct": 0,
            "percentual_meta_davi_potencial_unico_20pct": 0,
        }

    parceiros = df["nome_parceiro"].nunique() if "nome_parceiro" in df.columns else 0
    municipios = df["municipio"].nunique() if "municipio" in df.columns else 0
    vereadores = df["vereador"].nunique() if "vereador" in df.columns else 0
    locais = df["local_votacao_parceiro"].nunique() if "local_votacao_parceiro" in df.columns else 0

    potencial_local_bruto_20 = int(df["potencial_davi_20pct_local"].sum()) if "potencial_davi_20pct_local" in df.columns else 0

    vereadores_unicos = (
        df.sort_values(
            by=["indice_convergencia", "votos_vereador_local"],
            ascending=[False, False],
        )
        .drop_duplicates(subset=["nome_parceiro", "vereador", "partido_vereador"], keep="first")
        .copy()
    )

    potencial_unico_20 = int(vereadores_unicos["potencial_davi_20pct_local"].sum()) if "potencial_davi_20pct_local" in vereadores_unicos.columns else 0

    percentual_meta = round((potencial_unico_20 / META_DAVI) * 100, 2) if META_DAVI else 0

    return {
        "parceiros_processados": int(parceiros),
        "total_cruzamentos_qualificados": int(len(df)),
        "municipios_com_convergencia": int(municipios),
        "vereadores_convergentes": int(vereadores),
        "locais_convergentes": int(locais),
        "potencial_local_bruto_20pct": potencial_local_bruto_20,
        "potencial_vereadores_unicos_20pct": potencial_unico_20,
        "percentual_meta_davi_potencial_unico_20pct": percentual_meta,
        "observacao": (
            "O potencial por vereadores únicos é a métrica conservadora. "
            "O potencial local bruto pode repetir o mesmo vereador em mais de um local de votação."
        ),
    }


def gerar_resumo_por_parceiro(df):
    if df.empty:
        return []

    registros = []

    for parceiro, grupo in df.groupby("nome_parceiro"):
        vereadores_unicos = (
            grupo.sort_values(
                by=["indice_convergencia", "votos_vereador_local"],
                ascending=[False, False],
            )
            .drop_duplicates(subset=["vereador", "partido_vereador"], keep="first")
            .copy()
        )

        potencial_unico_20 = int(vereadores_unicos["potencial_davi_20pct_local"].sum())

        top_municipio = ""
        if "municipio" in grupo.columns and not grupo.empty:
            top_municipio = (
                grupo.groupby("municipio")["votos_parceiro_local"]
                .sum()
                .sort_values(ascending=False)
                .index[0]
            )

        top_local = ""
        if "local_votacao_parceiro" in grupo.columns and not grupo.empty:
            top_local = (
                grupo.groupby("local_votacao_parceiro")["votos_parceiro_local"]
                .sum()
                .sort_values(ascending=False)
                .index[0]
            )

        registros.append(
            {
                "nome_parceiro": parceiro,
                "total_cruzamentos": int(len(grupo)),
                "municipios_com_convergencia": int(grupo["municipio"].nunique()) if "municipio" in grupo.columns else 0,
                "vereadores_convergentes": int(grupo["vereador"].nunique()) if "vereador" in grupo.columns else 0,
                "locais_convergentes": int(grupo["local_votacao_parceiro"].nunique()) if "local_votacao_parceiro" in grupo.columns else 0,
                "potencial_vereadores_unicos_20pct": potencial_unico_20,
                "percentual_meta_davi_20pct": round((potencial_unico_20 / META_DAVI) * 100, 2),
                "principal_municipio": top_municipio,
                "principal_local_votacao": top_local,
                "maior_indice_convergencia": round(float(grupo["indice_convergencia"].max()), 2),
                "classificacao_principal": grupo.sort_values(by="indice_convergencia", ascending=False).iloc[0].get("classificacao_convergencia", ""),
            }
        )

    return sorted(registros, key=lambda x: x["potencial_vereadores_unicos_20pct"], reverse=True)


def gerar_top_convergencias(df):
    if df.empty:
        return []

    colunas = [
        "ranking_convergencia",
        "nome_parceiro",
        "municipio",
        "local_votacao_parceiro",
        "regiao_estimada",
        "vereador",
        "partido_vereador",
        "votos_parceiro_local",
        "votos_vereador_local",
        "indice_convergencia",
        "classificacao_convergencia",
        "potencial_davi_10pct_local",
        "potencial_davi_15pct_local",
        "potencial_davi_20pct_local",
        "acao_recomendada",
    ]

    colunas_existentes = [col for col in colunas if col in df.columns]

    top = (
        df.sort_values(
            by=["indice_convergencia", "votos_parceiro_local", "votos_vereador_local"],
            ascending=[False, False, False],
        )
        .head(100)
        .copy()
    )

    top = top[colunas_existentes]

    return top.to_dict(orient="records")


def gerar_vereadores_prioritarios(df):
    if df.empty:
        return []

    vereadores = (
        df.sort_values(
            by=["indice_convergencia", "votos_vereador_local"],
            ascending=[False, False],
        )
        .drop_duplicates(subset=["nome_parceiro", "vereador", "partido_vereador"], keep="first")
        .copy()
    )

    colunas = [
        "nome_parceiro",
        "municipio",
        "vereador",
        "partido_vereador",
        "local_votacao_parceiro",
        "votos_parceiro_local",
        "votos_vereador_local",
        "indice_convergencia",
        "classificacao_convergencia",
        "potencial_davi_20pct_local",
        "acao_recomendada",
    ]

    colunas_existentes = [col for col in colunas if col in vereadores.columns]

    return vereadores[colunas_existentes].head(100).to_dict(orient="records")


def gerar_resumo_municipios(df):
    if df.empty:
        return []

    municipio = (
        df.groupby(["nome_parceiro", "municipio"], as_index=False)
        .agg(
            cruzamentos=("vereador", "count"),
            vereadores_convergentes=("vereador", "nunique"),
            locais_convergentes=("local_votacao_parceiro", "nunique"),
            votos_parceiro_nos_locais=("votos_parceiro_local", "sum"),
            votos_vereadores_nos_locais=("votos_vereador_local", "sum"),
            potencial_davi_20pct_local=("potencial_davi_20pct_local", "sum"),
            maior_indice_convergencia=("indice_convergencia", "max"),
        )
    )

    municipio = municipio.sort_values(
        by=["maior_indice_convergencia", "votos_parceiro_nos_locais"],
        ascending=[False, False],
    )

    return municipio.head(100).to_dict(orient="records")


def gerar_json_dashboard(df, territorial):
    resumo_geral = gerar_resumo_geral(df)
    resumo_parceiros = gerar_resumo_por_parceiro(df)
    top_convergencias = gerar_top_convergencias(df)
    vereadores_prioritarios = gerar_vereadores_prioritarios(df)
    resumo_municipios = gerar_resumo_municipios(df)

    dados = {
        "metadata": {
            "titulo": "Parceiros Estratégicos — Davi Maia 2026",
            "versao": "v1",
            "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "descricao": (
                "Módulo de inteligência para cruzar a força eleitoral dos parceiros de Davi "
                "com os redutos dos vereadores alagoanos. A primeira parceira processada é Gabi Gonçalves."
            ),
            "observacao_metodologica": (
                "A convergência é calculada pelo cruzamento entre votação do parceiro em 2022 "
                "e votação dos vereadores em 2024, usando município, zona e local de votação quando disponíveis. "
                "Foram excluídos casos residuais com baixa presença do parceiro ou do vereador."
            ),
        },
        "resumo_geral": resumo_geral,
        "resumo_por_parceiro": resumo_parceiros,
        "top_convergencias": top_convergencias,
        "vereadores_prioritarios": vereadores_prioritarios,
        "resumo_municipios": resumo_municipios,
        "territorial_parceiros": territorial.get("parceiros_processados", []),
    }

    return limpar_json(dados)


def main():
    print("=" * 80)
    print("GERANDO MÓDULO — PARCEIROS ESTRATÉGICOS PARA DASHBOARD")
    print("=" * 80)

    df = preparar_cruzamento()
    territorial = carregar_territorial()

    print(f"Cruzamentos carregados: {len(df):,}".replace(",", "."))

    dados = gerar_json_dashboard(df, territorial)

    with open(SAIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2, allow_nan=False)

    top = pd.DataFrame(dados["top_convergencias"])
    top.to_csv(SAIDA_CSV_TOP, index=False, encoding="utf-8-sig")

    print()
    print("Arquivos gerados:")
    print(SAIDA_JSON)
    print(SAIDA_CSV_TOP)

    print()
    print("Resumo geral:")
    resumo = dados["resumo_geral"]

    print(f"Parceiros processados: {resumo['parceiros_processados']}")
    print(f"Cruzamentos qualificados: {resumo['total_cruzamentos_qualificados']}")
    print(f"Municípios com convergência: {resumo['municipios_com_convergencia']}")
    print(f"Vereadores convergentes: {resumo['vereadores_convergentes']}")
    print(f"Potencial vereadores únicos 20%: {resumo['potencial_vereadores_unicos_20pct']}")
    print(f"% da meta Davi: {resumo['percentual_meta_davi_potencial_unico_20pct']}%")

    print("=" * 80)


if __name__ == "__main__":
    main()