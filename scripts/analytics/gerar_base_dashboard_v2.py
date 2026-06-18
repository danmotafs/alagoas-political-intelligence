from pathlib import Path
import json
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_CSV = BASE_DIR / "data" / "final" / "inteligencia_politica_territorial_enriquecida.csv"
INPUT_VEREADORES_MUNICIPAIS = BASE_DIR / "data" / "final" / "inteligencia_municipal_vereadores.csv"

OUTPUT_DIR = BASE_DIR / "data" / "dashboard"
OUTPUT_JSON = OUTPUT_DIR / "base_dashboard_v2.json"


COLUNAS_SAIDA = [
    "rank",
    "municipio",
    "populacao_estimada_2024",
    "eleitorado_2024",
    "participacao_eleitorado_pct",
    "indice_estrategico_pct",
    "prioridade_politica",
    "prefeito",
    "vice_prefeito",
    "partido",
    "votos_prefeito",
    "percentual_prefeito",
    "segundo_colocado",
    "partido_segundo_colocado",
    "votos_segundo_colocado",
    "percentual_segundo_colocado",
    "margem_vitoria_votos",
    "margem_vitoria_pct",
    "visitado_pre_campanha",
    "quantidade_visitas",
    "ultima_visita",
    "status_visitacao",
    "capital_politico_prefeito",
    "grupo_politico",
    "relacao_davi",
    "grupo_politico_classificacao",
    "relacao_davi_classificacao",
    "peso_politico",
    "status_articulacao",
    "observacoes",
    "score_articulacao",
    "prioridade_final",
    "recomendacao_estrategica",
]


COLUNAS_NUMERICAS = [
    "rank",
    "populacao_estimada_2024",
    "eleitorado_2024",
    "participacao_eleitorado_pct",
    "indice_estrategico_pct",
    "votos_prefeito",
    "percentual_prefeito",
    "votos_segundo_colocado",
    "percentual_segundo_colocado",
    "margem_vitoria_votos",
    "margem_vitoria_pct",
    "quantidade_visitas",
    "score_articulacao",
]


COLUNAS_NUMERICAS_VEREADORES = [
    "rank_municipal",
    "vereadores_eleitos",
    "total_votos_vereadores",
    "media_votos_vereador",
    "principal_lideranca_votos",
    "potencial_transferencia_conservador",
    "potencial_transferencia_moderado",
    "potencial_transferencia_alto",
    "indice_influencia_municipal",
]


def limpar_texto(valor):
    if pd.isna(valor):
        return ""

    valor = str(valor).strip()

    if valor.lower() in ["nan", "none", "null"]:
        return ""

    return valor


def carregar_base() -> pd.DataFrame:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)

    colunas_existentes = [col for col in COLUNAS_SAIDA if col in df.columns]
    df = df[colunas_existentes].copy()

    return df


def normalizar_booleano_visitado(valor) -> bool:
    if pd.isna(valor):
        return False

    texto = str(valor).strip().lower()

    if texto in ["sim", "s", "true", "1", "visitado", "visitado_pre_campanha"]:
        return True

    return False


def preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
    for coluna in COLUNAS_NUMERICAS:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)

    for coluna in df.columns:
        if coluna not in COLUNAS_NUMERICAS:
            df[coluna] = df[coluna].apply(limpar_texto)

    if "visitado_pre_campanha" in df.columns:
        df["visitado_pre_campanha"] = df["visitado_pre_campanha"].apply(
            normalizar_booleano_visitado
        )

    if "status_visitacao" not in df.columns and "visitado_pre_campanha" in df.columns:
        df["status_visitacao"] = df["visitado_pre_campanha"].apply(
            lambda x: "Visitado" if x else "Não visitado"
        )

    return df


def carregar_vereadores_municipais_df() -> pd.DataFrame:
    if not INPUT_VEREADORES_MUNICIPAIS.exists():
        print("\nAviso: base municipal de vereadores não encontrada.")
        print(f"Arquivo esperado: {INPUT_VEREADORES_MUNICIPAIS}")
        return pd.DataFrame()

    df = pd.read_csv(INPUT_VEREADORES_MUNICIPAIS)

    for coluna in COLUNAS_NUMERICAS_VEREADORES:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)

    for coluna in df.columns:
        if coluna not in COLUNAS_NUMERICAS_VEREADORES:
            df[coluna] = df[coluna].apply(limpar_texto)

    if "rank_municipal" in df.columns:
        df = df.sort_values("rank_municipal", ascending=True)
    elif "total_votos_vereadores" in df.columns:
        df = df.sort_values("total_votos_vereadores", ascending=False)

    return df


def gerar_indicadores_vereadores(df_vereadores: pd.DataFrame) -> dict:
    if df_vereadores.empty:
        return {
            "vereadores_mapeados": 0,
            "votos_vereadores_total": 0,
            "potencial_transferencia_conservador_total": 0,
            "potencial_transferencia_moderado_total": 0,
            "potencial_transferencia_alto_total": 0,
        }

    vereadores_mapeados = (
        int(df_vereadores["vereadores_eleitos"].sum())
        if "vereadores_eleitos" in df_vereadores.columns
        else 0
    )

    votos_vereadores_total = (
        int(df_vereadores["total_votos_vereadores"].sum())
        if "total_votos_vereadores" in df_vereadores.columns
        else 0
    )

    potencial_conservador = (
        int(df_vereadores["potencial_transferencia_conservador"].sum())
        if "potencial_transferencia_conservador" in df_vereadores.columns
        else 0
    )

    potencial_moderado = (
        int(df_vereadores["potencial_transferencia_moderado"].sum())
        if "potencial_transferencia_moderado" in df_vereadores.columns
        else 0
    )

    potencial_alto = (
        int(df_vereadores["potencial_transferencia_alto"].sum())
        if "potencial_transferencia_alto" in df_vereadores.columns
        else 0
    )

    return {
        "vereadores_mapeados": vereadores_mapeados,
        "votos_vereadores_total": votos_vereadores_total,
        "potencial_transferencia_conservador_total": potencial_conservador,
        "potencial_transferencia_moderado_total": potencial_moderado,
        "potencial_transferencia_alto_total": potencial_alto,
    }


def gerar_indicadores(df: pd.DataFrame, df_vereadores: pd.DataFrame) -> dict:
    total_municipios = int(df["municipio"].nunique()) if "municipio" in df.columns else int(len(df))

    eleitorado_total = int(df["eleitorado_2024"].sum()) if "eleitorado_2024" in df.columns else 0
    populacao_total = int(df["populacao_estimada_2024"].sum()) if "populacao_estimada_2024" in df.columns else 0

    if "visitado_pre_campanha" in df.columns:
        municipios_visitados = int(df[df["visitado_pre_campanha"] == True]["municipio"].nunique())
    elif "status_visitacao" in df.columns:
        municipios_visitados = int(df[df["status_visitacao"].str.lower() == "visitado"]["municipio"].nunique())
    else:
        municipios_visitados = 0

    cobertura_territorial_pct = round((municipios_visitados / total_municipios) * 100, 2) if total_municipios else 0

    prefeitos_mapeados = int(df["prefeito"].replace("", pd.NA).dropna().nunique()) if "prefeito" in df.columns else 0
    partidos_mapeados = int(df["partido"].replace("", pd.NA).dropna().nunique()) if "partido" in df.columns else 0

    indicadores = {
        "total_municipios": total_municipios,
        "eleitorado_total": eleitorado_total,
        "populacao_total": populacao_total,
        "municipios_visitados": municipios_visitados,
        "cobertura_territorial_pct": cobertura_territorial_pct,
        "prefeitos_mapeados": prefeitos_mapeados,
        "partidos_mapeados": partidos_mapeados,
    }

    indicadores.update(gerar_indicadores_vereadores(df_vereadores))

    return indicadores


def gerar_ranking(df: pd.DataFrame) -> dict:
    ranking_estrategico = []

    if "indice_estrategico_pct" in df.columns:
        ranking_estrategico = (
            df.sort_values("indice_estrategico_pct", ascending=False)
            .head(20)
            .to_dict(orient="records")
        )

    maior_eleitorado = []
    if "eleitorado_2024" in df.columns:
        maior_eleitorado = (
            df.sort_values("eleitorado_2024", ascending=False)
            .head(10)
            .to_dict(orient="records")
        )

    menor_margem = []
    if "margem_vitoria_pct" in df.columns:
        menor_margem = (
            df[df["margem_vitoria_pct"] > 0]
            .sort_values("margem_vitoria_pct", ascending=True)
            .head(10)
            .to_dict(orient="records")
        )

    maior_score_articulacao = []
    if "score_articulacao" in df.columns:
        maior_score_articulacao = (
            df.sort_values("score_articulacao", ascending=False)
            .head(10)
            .to_dict(orient="records")
        )

    nao_visitados_prioritarios = []
    if "visitado_pre_campanha" in df.columns and "indice_estrategico_pct" in df.columns:
        nao_visitados_prioritarios = (
            df[df["visitado_pre_campanha"] == False]
            .sort_values("indice_estrategico_pct", ascending=False)
            .head(20)
            .to_dict(orient="records")
        )

    return {
        "ranking_estrategico_top20": ranking_estrategico,
        "maior_eleitorado_top10": maior_eleitorado,
        "menor_margem_top10": menor_margem,
        "maior_score_articulacao_top10": maior_score_articulacao,
        "nao_visitados_prioritarios_top20": nao_visitados_prioritarios,
    }


def gerar_dimensoes(df: pd.DataFrame) -> dict:
    municipios = sorted(df["municipio"].dropna().unique().tolist()) if "municipio" in df.columns else []
    partidos = sorted(df["partido"].dropna().unique().tolist()) if "partido" in df.columns else []

    grupos = []
    if "grupo_politico" in df.columns:
        grupos = sorted([x for x in df["grupo_politico"].dropna().unique().tolist() if x != ""])

    relacoes = []
    if "relacao_davi" in df.columns:
        relacoes = sorted([x for x in df["relacao_davi"].dropna().unique().tolist() if x != ""])

    prioridades = []
    if "prioridade_final" in df.columns:
        prioridades = sorted([x for x in df["prioridade_final"].dropna().unique().tolist() if x != ""])

    return {
        "municipios": municipios,
        "partidos": partidos,
        "grupos_politicos": grupos,
        "relacoes_davi": relacoes,
        "prioridades": prioridades,
    }


def gerar_json_dashboard(df: pd.DataFrame) -> dict:
    df_vereadores = carregar_vereadores_municipais_df()
    vereadores_municipais = df_vereadores.to_dict(orient="records") if not df_vereadores.empty else []

    return {
        "metadata": {
            "projeto": "Alagoas Political Intelligence",
            "versao": "dashboard_v2",
            "fonte_principal": str(INPUT_CSV.relative_to(BASE_DIR)).replace("\\", "/"),
            "fonte_vereadores_municipais": str(INPUT_VEREADORES_MUNICIPAIS.relative_to(BASE_DIR)).replace("\\", "/"),
            "total_registros": int(len(df)),
            "total_registros_vereadores_municipais": int(len(vereadores_municipais)),
        },
        "indicadores": gerar_indicadores(df, df_vereadores),
        "dimensoes": gerar_dimensoes(df),
        "rankings": gerar_ranking(df),
        "municipios": df.to_dict(orient="records"),
        "vereadores_municipais": vereadores_municipais,
    }


def salvar_json(payload: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> None:
    print("\nGERANDO BASE DO DASHBOARD V2")
    print("=" * 80)

    df = carregar_base()
    print(f"Base carregada: {INPUT_CSV}")
    print(f"Linhas carregadas: {len(df)}")
    print(f"Colunas carregadas: {len(df.columns)}")

    df = preparar_dados(df)
    payload = gerar_json_dashboard(df)
    salvar_json(payload)

    print("\nArquivo JSON gerado com sucesso:")
    print(OUTPUT_JSON)

    print("\nIndicadores principais:")
    for chave, valor in payload["indicadores"].items():
        print(f"- {chave}: {valor}")

    print("\nRankings gerados:")
    for chave, valor in payload["rankings"].items():
        print(f"- {chave}: {len(valor)} registros")

    print("\nCamada de vereadores municipais:")
    print(f"- vereadores_municipais: {len(payload['vereadores_municipais'])} registros")

    print("\nProcesso concluído.")


if __name__ == "__main__":
    main()