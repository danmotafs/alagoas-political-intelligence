from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd


TOP_AGENDA_CONJUNTA = 30
TOP_DASHBOARD = 20


def detectar_raiz_projeto() -> Path:
    caminho_script = Path(__file__).resolve()

    if (
        caminho_script.parent.name.lower() == "analytics"
        and caminho_script.parent.parent.name.lower() == "scripts"
    ):
        return caminho_script.parent.parent.parent

    return Path.cwd()


def normalizar_texto(valor: object) -> str:
    if valor is None or pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = " ".join(texto.split())
    return texto


def normalizar_coluna(coluna: str) -> str:
    texto = normalizar_texto(coluna).lower()
    texto = texto.replace(" ", "_")
    texto = texto.replace("-", "_")
    texto = texto.replace("/", "_")
    texto = texto.replace(".", "")
    texto = texto.replace("ç", "c")
    return texto


def encontrar_arquivo(root: Path, candidatos: list[str]) -> Path | None:
    for relativo in candidatos:
        caminho = root / relativo
        if caminho.exists():
            return caminho

    return None


def ler_csv_robusto(caminho: Path) -> pd.DataFrame:
    tentativas = [
        {"encoding": "utf-8-sig", "sep": None, "engine": "python"},
        {"encoding": "utf-8", "sep": None, "engine": "python"},
        {"encoding": "latin1", "sep": None, "engine": "python"},
        {"encoding": "cp1252", "sep": None, "engine": "python"},
    ]

    ultimo_erro: Exception | None = None

    for kwargs in tentativas:
        try:
            df = pd.read_csv(caminho, **kwargs)
            df.columns = [normalizar_coluna(c) for c in df.columns]
            return df
        except Exception as erro:
            ultimo_erro = erro

    raise RuntimeError(f"Não foi possível ler {caminho}. Erro: {ultimo_erro}")


def ler_tabela(caminho: Path) -> pd.DataFrame:
    if caminho.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(caminho)
        df.columns = [normalizar_coluna(c) for c in df.columns]
        return df

    return ler_csv_robusto(caminho)


def encontrar_coluna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    colunas = list(df.columns)
    candidatos_norm = [normalizar_coluna(c) for c in candidatos]

    for candidato in candidatos_norm:
        if candidato in colunas:
            return candidato

    for candidato in candidatos_norm:
        for coluna in colunas:
            if candidato in coluna:
                return coluna

    return None


def converter_numero(serie: pd.Series) -> pd.Series:
    if serie is None:
        return pd.Series(dtype="float64")

    if pd.api.types.is_numeric_dtype(serie):
        return pd.to_numeric(serie, errors="coerce").fillna(0)

    def parse_valor(valor: object) -> float:
        if valor is None or pd.isna(valor):
            return 0.0

        texto = str(valor).strip()

        if texto == "":
            return 0.0

        texto = texto.replace("\u00a0", " ")

        if re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
            return float(texto.replace(".", ""))

        if re.fullmatch(r"\d{1,3}(\.\d{3})+,\d+", texto):
            return float(texto.replace(".", "").replace(",", "."))

        if re.fullmatch(r"\d+\.0+", texto):
            return float(texto)

        if re.fullmatch(r"\d+", texto):
            return float(texto)

        if re.fullmatch(r"\d+,\d+", texto):
            return float(texto.replace(",", "."))

        texto_limpo = re.sub(r"[^0-9,.\-]", "", texto)

        if texto_limpo.count(",") == 1 and texto_limpo.count(".") >= 1:
            texto_limpo = texto_limpo.replace(".", "").replace(",", ".")
        elif texto_limpo.count(",") == 1 and texto_limpo.count(".") == 0:
            texto_limpo = texto_limpo.replace(",", ".")

        try:
            return float(texto_limpo)
        except ValueError:
            return 0.0

    return serie.apply(parse_valor).astype(float)


def normalizar_0_100(serie: pd.Series) -> pd.Series:
    valores = converter_numero(serie)

    minimo = valores.min()
    maximo = valores.max()

    if pd.isna(minimo) or pd.isna(maximo) or maximo == minimo:
        return pd.Series([0.0] * len(valores), index=valores.index)

    return ((valores - minimo) / (maximo - minimo)) * 100


def carregar_base_gabi(root: Path) -> pd.DataFrame:
    caminho = encontrar_arquivo(
        root,
        [
            "data/final/parceiros/gabi-goncalves/base_eleitoral_gabi_v1.csv",
            "data/final/parceiros/gabi-goncalves/base_eleitoral_gabi_v1.xlsx",
        ],
    )

    if caminho is None:
        raise FileNotFoundError(
            "Base eleitoral da Gabi não encontrada. Rode antes o Sprint 02."
        )

    print(f"[OK] Base eleitoral da Gabi encontrada: {caminho}")
    df = ler_tabela(caminho)

    col_municipio = encontrar_coluna(df, ["municipio", "nm_municipio", "nome_municipio"])

    if col_municipio is None:
        raise RuntimeError("Não encontrei coluna de município na base da Gabi.")

    df["municipio"] = df[col_municipio].astype(str).str.strip()
    df["municipio_key"] = df["municipio"].apply(normalizar_texto)

    campos_numericos = [
        "ranking_gabi_preliminar",
        "eleitorado",
        "populacao",
        "score_gabi_preliminar",
        "meta_votos_referencia_gabi",
        "ranking_base_davi",
        "indice_estrategico_base_davi",
        "votos_vereadores_total",
        "vereadores_mapeados",
        "potencial_transferencia_vereadores_5pct",
        "potencial_transferencia_vereadores_10pct",
        "potencial_transferencia_vereadores_15pct",
    ]

    for campo in campos_numericos:
        if campo not in df.columns:
            df[campo] = 0
        df[campo] = converter_numero(df[campo])

    campos_texto = [
        "prioridade_visita_gabi",
        "status_articulacao_gabi",
        "prefeito_2024",
        "partido_prefeito_2024",
        "relacao_gabi",
        "aderencia_gabi",
        "grupo_politico_gabi",
        "observacao_curadoria_gabi",
        "justificativa_prioridade_gabi",
    ]

    for campo in campos_texto:
        if campo not in df.columns:
            df[campo] = ""
        df[campo] = df[campo].fillna("").astype(str)

    return df.drop_duplicates(subset=["municipio_key"]).reset_index(drop=True)


def carregar_ranking_davi(root: Path) -> pd.DataFrame:
    caminho = encontrar_arquivo(
        root,
        [
            "data/final/ranking_estrategico_alagoas_2024.csv",
            "data/processed/ranking_estrategico_alagoas_2024.csv",
        ],
    )

    if caminho is None:
        print("[AVISO] Ranking estratégico do Davi não encontrado. Usarei campos já presentes na base da Gabi.")
        return pd.DataFrame(columns=["municipio_key"])

    print(f"[OK] Ranking estratégico do Davi encontrado: {caminho}")
    df = ler_tabela(caminho)

    col_municipio = encontrar_coluna(df, ["municipio", "nm_municipio", "nome_municipio"])
    col_rank = encontrar_coluna(df, ["ranking", "rank", "posicao", "ranking_estrategico"])
    col_score = encontrar_coluna(
        df,
        [
            "indice_estrategico",
            "score_estrategico",
            "pontuacao_estrategica",
            "indice",
            "score",
        ],
    )

    if col_municipio is None:
        print("[AVISO] Ranking do Davi sem coluna de município reconhecida.")
        return pd.DataFrame(columns=["municipio_key"])

    ranking = pd.DataFrame()
    ranking["municipio_key"] = df[col_municipio].apply(normalizar_texto)

    if col_rank:
        ranking["ranking_davi_ref"] = converter_numero(df[col_rank])
    else:
        ranking["ranking_davi_ref"] = 0

    if col_score:
        ranking["score_davi_ref"] = converter_numero(df[col_score])
    else:
        ranking["score_davi_ref"] = 0

    return ranking.drop_duplicates(subset=["municipio_key"]).reset_index(drop=True)


def carregar_resumo_liderancas(root: Path) -> pd.DataFrame:
    caminho = encontrar_arquivo(
        root,
        [
            "data/final/parceiros/gabi-goncalves/resumo_liderancas_municipio_gabi_v1.csv",
            "data/final/parceiros/gabi-goncalves/rede_liderancas_gabi_v1.csv",
        ],
    )

    if caminho is None:
        print("[AVISO] Rede de lideranças da Gabi não encontrada. Rode antes o Sprint 03.")
        return pd.DataFrame(columns=["municipio_key"])

    print(f"[OK] Base de lideranças da Gabi encontrada: {caminho}")
    df = ler_tabela(caminho)

    col_municipio = encontrar_coluna(df, ["municipio", "nm_municipio", "nome_municipio"])

    if col_municipio is None:
        print("[AVISO] Base de lideranças sem coluna de município reconhecida.")
        return pd.DataFrame(columns=["municipio_key"])

    df["municipio"] = df[col_municipio].astype(str).str.strip()
    df["municipio_key"] = df["municipio"].apply(normalizar_texto)

    if "liderancas_mapeadas" in df.columns:
        resumo = df.copy()
    else:
        col_nome = encontrar_coluna(df, ["nome_lideranca", "nome", "vereador"])
        col_votos = encontrar_coluna(df, ["votos_2024", "votos", "qt_votos"])
        col_potencial = encontrar_coluna(
            df,
            [
                "potencial_transferencia_10pct",
                "potencial_10pct",
                "potencial_transferencia",
            ],
        )
        col_score = encontrar_coluna(
            df,
            ["score_lideranca_gabi", "score_lideranca", "score"]
        )

        if col_nome is None:
            df["nome_lideranca"] = ""
            col_nome = "nome_lideranca"

        if col_votos is None:
            df["votos_2024"] = 0
            col_votos = "votos_2024"

        if col_potencial is None:
            df["potencial_transferencia_10pct"] = converter_numero(df[col_votos]) * 0.10
            col_potencial = "potencial_transferencia_10pct"

        if col_score is None:
            df["score_lideranca_gabi"] = normalizar_0_100(df[col_votos])
            col_score = "score_lideranca_gabi"

        df[col_votos] = converter_numero(df[col_votos])
        df[col_potencial] = converter_numero(df[col_potencial])
        df[col_score] = converter_numero(df[col_score])

        idx_principal = (
            df.sort_values(
                by=["municipio_key", col_score, col_votos],
                ascending=[True, False, False],
            )
            .groupby("municipio_key")
            .head(1)
            .copy()
        )

        resumo = (
            df.groupby(["municipio", "municipio_key"], as_index=False)
            .agg(
                liderancas_mapeadas=(col_nome, "count"),
                votos_liderancas_total=(col_votos, "sum"),
                potencial_transferencia_10pct=(col_potencial, "sum"),
                maior_score_lideranca=(col_score, "max"),
            )
        )

        principais = idx_principal[["municipio_key", col_nome, col_votos]].copy()
        principais = principais.rename(
            columns={
                col_nome: "principal_lideranca",
                col_votos: "votos_principal_lideranca",
            }
        )

        resumo = resumo.merge(principais, on="municipio_key", how="left")

    campos_numericos = [
        "liderancas_mapeadas",
        "votos_liderancas_total",
        "potencial_transferencia_5pct",
        "potencial_transferencia_10pct",
        "potencial_transferencia_15pct",
        "maior_score_lideranca",
        "votos_principal_lideranca",
    ]

    for campo in campos_numericos:
        if campo not in resumo.columns:
            resumo[campo] = 0
        resumo[campo] = converter_numero(resumo[campo])

    if "principal_lideranca" not in resumo.columns:
        resumo["principal_lideranca"] = ""

    if "partido_principal_lideranca" not in resumo.columns:
        resumo["partido_principal_lideranca"] = ""

    if "prioridade_principal_lideranca" not in resumo.columns:
        resumo["prioridade_principal_lideranca"] = ""

    resumo["principal_lideranca"] = resumo["principal_lideranca"].fillna("").astype(str)

    return resumo.drop_duplicates(subset=["municipio_key"]).reset_index(drop=True)


def classificar_sinergia(score: float) -> str:
    if score >= 80:
        return "Muito alta"
    if score >= 65:
        return "Alta"
    if score >= 50:
        return "Média"
    if score >= 35:
        return "Baixa"
    return "Monitoramento"


def definir_status_agenda(prioridade: str) -> str:
    if prioridade == "Muito alta":
        return "Agenda conjunta prioritária"
    if prioridade == "Alta":
        return "Agenda conjunta recomendada"
    if prioridade == "Média":
        return "Avaliar agenda após curadoria"
    if prioridade == "Baixa":
        return "Monitorar oportunidade"
    return "Sem prioridade imediata"


def definir_formato_agenda(row: pd.Series) -> str:
    prioridade = row.get("prioridade_sinergia_davi_gabi", "")
    municipio = row.get("municipio", "")
    principal = str(row.get("principal_lideranca", "")).strip()
    prefeito = str(row.get("prefeito_2024", "")).strip()

    partes = []

    if prioridade == "Muito alta":
        partes.append("agenda conjunta Davi + Gabi")
    elif prioridade == "Alta":
        partes.append("visita política coordenada")
    elif prioridade == "Média":
        partes.append("reunião de validação territorial")
    else:
        partes.append("monitoramento político")

    if principal:
        partes.append(f"com validação da liderança {principal}")

    if prefeito and prefeito.lower() not in ["nan", "none"]:
        partes.append(f"e leitura do grupo do prefeito {prefeito}")

    return f"{municipio}: " + "; ".join(partes) + "."


def definir_justificativa(row: pd.Series) -> str:
    prioridade = row.get("prioridade_sinergia_davi_gabi", "")
    municipio = row.get("municipio", "")
    score = float(row.get("score_sinergia_davi_gabi", 0))
    liderancas = int(row.get("liderancas_mapeadas", 0))
    meta = int(row.get("meta_votos_referencia_gabi", 0))

    if prioridade == "Muito alta":
        return (
            f"{municipio} combina alta prioridade territorial, presença na base estratégica "
            f"do Davi, rede local com {liderancas} liderança(s) mapeada(s) e meta de referência "
            f"de {meta} votos para Gabi. Score de sinergia: {score:.2f}."
        )

    if prioridade == "Alta":
        return (
            f"{municipio} apresenta boa aderência para agenda conjunta, com rede política local "
            f"já identificada e potencial de conversão territorial. Score de sinergia: {score:.2f}."
        )

    if prioridade == "Média":
        return (
            f"{municipio} deve permanecer na segunda camada de articulação, dependendo de validação "
            f"política das lideranças e disponibilidade de agenda. Score de sinergia: {score:.2f}."
        )

    return (
        f"{municipio} deve ser mantido em monitoramento até novas informações de apoio local, "
        f"agenda ou aderência política. Score de sinergia: {score:.2f}."
    )


def calcular_cruzamento(
    base_gabi: pd.DataFrame,
    ranking_davi: pd.DataFrame,
    resumo_liderancas: pd.DataFrame,
) -> pd.DataFrame:
    df = base_gabi.copy()

    if not ranking_davi.empty:
        df = df.merge(ranking_davi, on="municipio_key", how="left")
    else:
        df["ranking_davi_ref"] = df["ranking_base_davi"]
        df["score_davi_ref"] = df["indice_estrategico_base_davi"]

    if not resumo_liderancas.empty:
        df = df.merge(
            resumo_liderancas[
                [
                    "municipio_key",
                    "liderancas_mapeadas",
                    "votos_liderancas_total",
                    "potencial_transferencia_10pct",
                    "maior_score_lideranca",
                    "principal_lideranca",
                    "partido_principal_lideranca",
                    "votos_principal_lideranca",
                    "prioridade_principal_lideranca",
                ]
            ],
            on="municipio_key",
            how="left",
        )
    else:
        df["liderancas_mapeadas"] = 0
        df["votos_liderancas_total"] = 0
        df["potencial_transferencia_10pct"] = 0
        df["maior_score_lideranca"] = 0
        df["principal_lideranca"] = ""
        df["partido_principal_lideranca"] = ""
        df["votos_principal_lideranca"] = 0
        df["prioridade_principal_lideranca"] = ""

    campos_num = [
        "ranking_davi_ref",
        "score_davi_ref",
        "ranking_base_davi",
        "indice_estrategico_base_davi",
        "ranking_gabi_preliminar",
        "score_gabi_preliminar",
        "eleitorado",
        "meta_votos_referencia_gabi",
        "liderancas_mapeadas",
        "votos_liderancas_total",
        "potencial_transferencia_10pct",
        "maior_score_lideranca",
        "votos_principal_lideranca",
    ]

    for campo in campos_num:
        if campo not in df.columns:
            df[campo] = 0
        df[campo] = converter_numero(df[campo])

    df["score_davi_base"] = df["score_davi_ref"]

    if df["score_davi_base"].sum() <= 0:
        df["score_davi_base"] = df["indice_estrategico_base_davi"]

    if df["score_davi_base"].sum() <= 0:
        df["score_davi_base"] = df["ranking_base_davi"].apply(
            lambda rank: max(0, (103 - int(rank))) if int(rank) > 0 else 0
        )

    df["score_davi_normalizado"] = normalizar_0_100(df["score_davi_base"])
    df["score_gabi_normalizado"] = normalizar_0_100(df["score_gabi_preliminar"])
    df["score_liderancas_normalizado"] = normalizar_0_100(df["potencial_transferencia_10pct"])
    df["score_eleitorado_normalizado"] = normalizar_0_100(df["eleitorado"])

    df["bonus_top_municipio"] = df["ranking_gabi_preliminar"].apply(
        lambda rank: 100 if int(rank) <= 10 else (
            75 if int(rank) <= 20 else (
                50 if int(rank) <= 40 else 20
            )
        )
    )

    df["score_sinergia_davi_gabi"] = (
        df["score_davi_normalizado"] * 0.30
        + df["score_gabi_normalizado"] * 0.30
        + df["score_liderancas_normalizado"] * 0.20
        + df["score_eleitorado_normalizado"] * 0.10
        + df["bonus_top_municipio"] * 0.10
    ).round(2)

    df = df.sort_values(
        by=[
            "score_sinergia_davi_gabi",
            "ranking_gabi_preliminar",
            "eleitorado",
        ],
        ascending=[False, True, False],
    ).reset_index(drop=True)

    df["ranking_sinergia_davi_gabi"] = range(1, len(df) + 1)
    df["prioridade_sinergia_davi_gabi"] = df["score_sinergia_davi_gabi"].apply(classificar_sinergia)
    df["status_agenda_conjunta"] = df["prioridade_sinergia_davi_gabi"].apply(definir_status_agenda)
    df["formato_agenda_recomendada"] = df.apply(definir_formato_agenda, axis=1)
    df["justificativa_sinergia"] = df.apply(definir_justificativa, axis=1)

    df["semana_sugerida"] = df["ranking_sinergia_davi_gabi"].apply(
        lambda rank: "Semana 1" if rank <= 8 else (
            "Semana 2" if rank <= 16 else (
                "Semana 3" if rank <= 24 else (
                    "Semana 4" if rank <= TOP_AGENDA_CONJUNTA else "Monitoramento"
                )
            )
        )
    )

    df["acao_recomendada"] = df["prioridade_sinergia_davi_gabi"].apply(
        lambda prioridade: (
            "Agendar visita conjunta Davi + Gabi"
            if prioridade == "Muito alta"
            else (
                "Validar liderança e preparar agenda coordenada"
                if prioridade == "Alta"
                else (
                    "Curar politicamente antes de agenda pública"
                    if prioridade == "Média"
                    else "Monitorar"
                )
            )
        )
    )

    ordem_colunas = [
        "ranking_sinergia_davi_gabi",
        "municipio",
        "prioridade_sinergia_davi_gabi",
        "status_agenda_conjunta",
        "score_sinergia_davi_gabi",
        "ranking_gabi_preliminar",
        "prioridade_visita_gabi",
        "score_gabi_preliminar",
        "ranking_davi_ref",
        "score_davi_ref",
        "ranking_base_davi",
        "indice_estrategico_base_davi",
        "eleitorado",
        "populacao",
        "meta_votos_referencia_gabi",
        "liderancas_mapeadas",
        "principal_lideranca",
        "partido_principal_lideranca",
        "votos_principal_lideranca",
        "prioridade_principal_lideranca",
        "votos_liderancas_total",
        "potencial_transferencia_10pct",
        "prefeito_2024",
        "partido_prefeito_2024",
        "relacao_gabi",
        "aderencia_gabi",
        "grupo_politico_gabi",
        "semana_sugerida",
        "acao_recomendada",
        "formato_agenda_recomendada",
        "justificativa_sinergia",
        "municipio_key",
    ]

    for coluna in ordem_colunas:
        if coluna not in df.columns:
            df[coluna] = ""

    return df[ordem_colunas]


def gerar_agenda_conjunta(cruzamento: pd.DataFrame) -> pd.DataFrame:
    agenda = cruzamento.head(TOP_AGENDA_CONJUNTA).copy()

    agenda["ordem_agenda"] = range(1, len(agenda) + 1)
    agenda["responsavel_preparacao"] = ""
    agenda["contato_local"] = ""
    agenda["data_sugerida"] = ""
    agenda["status_execucao"] = "A planejar"
    agenda["observacao_politica"] = ""

    colunas = [
        "ordem_agenda",
        "semana_sugerida",
        "municipio",
        "prioridade_sinergia_davi_gabi",
        "status_agenda_conjunta",
        "score_sinergia_davi_gabi",
        "principal_lideranca",
        "partido_principal_lideranca",
        "prefeito_2024",
        "partido_prefeito_2024",
        "meta_votos_referencia_gabi",
        "potencial_transferencia_10pct",
        "acao_recomendada",
        "formato_agenda_recomendada",
        "justificativa_sinergia",
        "responsavel_preparacao",
        "contato_local",
        "data_sugerida",
        "status_execucao",
        "observacao_politica",
    ]

    return agenda[colunas]


def carregar_json(caminho: Path) -> dict:
    if not caminho.exists():
        return {}

    return json.loads(caminho.read_text(encoding="utf-8"))


def salvar_json(caminho: Path, dados: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] JSON salvo: {caminho}")


def atualizar_base_dashboard(root: Path, cruzamento: pd.DataFrame) -> None:
    caminho = (
        root
        / "data"
        / "dashboard"
        / "parceiros"
        / "gabi-goncalves"
        / "base_dashboard_gabi_v1.json"
    )

    dados = carregar_json(caminho)

    dados.setdefault("metadata", {})
    dados["metadata"]["versao"] = "sprint04_cruzamento_davi_gabi"
    dados["metadata"]["atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    dados["metadata"]["status"] = "Cruzamento Davi + Gabi criado com priorização de agenda conjunta."

    muito_alta = int(len(cruzamento[cruzamento["prioridade_sinergia_davi_gabi"] == "Muito alta"]))
    alta = int(len(cruzamento[cruzamento["prioridade_sinergia_davi_gabi"] == "Alta"]))
    media = int(len(cruzamento[cruzamento["prioridade_sinergia_davi_gabi"] == "Média"]))

    dados.setdefault("indicadores_gabi", {})
    dados["indicadores_gabi"]["municipios_alta_sinergia_davi_gabi"] = muito_alta
    dados["indicadores_gabi"]["municipios_sinergia_alta"] = alta
    dados["indicadores_gabi"]["municipios_sinergia_media"] = media
    dados["indicadores_gabi"]["agenda_conjunta_prioritaria"] = int(
        len(cruzamento.head(TOP_AGENDA_CONJUNTA))
    )
    dados["indicadores_gabi"]["status_cruzamento"] = (
        "Cruzamento Davi + Gabi calculado; agenda conjunta preliminar criada."
    )

    dados["oportunidades_sinergia"] = [
        {
            "rank": int(row["ranking_sinergia_davi_gabi"]),
            "municipio": row["municipio"],
            "prioridade": row["prioridade_sinergia_davi_gabi"],
            "score": round(float(row["score_sinergia_davi_gabi"]), 2),
            "principal_lideranca": row["principal_lideranca"],
            "meta_referencia_gabi": int(row["meta_votos_referencia_gabi"]),
            "acao_recomendada": row["acao_recomendada"],
        }
        for _, row in cruzamento.head(TOP_DASHBOARD).iterrows()
    ]

    dados["proximos_passos"] = [
        {
            "sprint": "Sprint 05",
            "titulo": "Roteiro Territorial",
            "descricao": "Converter os municípios de maior sinergia em roteiro semanal de visitas Davi + Gabi."
        },
        {
            "sprint": "Sprint 06",
            "titulo": "Curadoria Política",
            "descricao": "Preencher relação real com Gabi, Davi, Renan Filho, Paulo Dantas, prefeitos e vereadores."
        },
        {
            "sprint": "Sprint 07",
            "titulo": "Versão executiva",
            "descricao": "Gerar relatório em PDF com mapa de prioridades, agenda conjunta e justificativa estratégica."
        },
        {
            "sprint": "Sprint 08",
            "titulo": "Publicação",
            "descricao": "Subir versão aprovada para GitHub Pages e compartilhar com Davi."
        },
    ]

    salvar_json(caminho, dados)


def atualizar_cruzamento_json(root: Path, cruzamento: pd.DataFrame, agenda: pd.DataFrame) -> None:
    caminho = (
        root
        / "data"
        / "dashboard"
        / "parceiros"
        / "gabi-goncalves"
        / "cruzamento_davi_gabi_v1.json"
    )

    dados = carregar_json(caminho)

    dados["metadata"] = {
        "projeto": "Cruzamento Davi Maia + Gabi Gonçalves",
        "versao": "sprint04_cruzamento_davi_gabi",
        "atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "status": "Cruzamento territorial e político calculado para priorização de agenda conjunta."
    }

    dados["eixo_politico"] = {
        "descricao": (
            "Davi Maia é tratado como eixo político principal da rede. "
            "Gabi Gonçalves é analisada como deputada estadual em mandato e candidata à reeleição."
        ),
        "hipotese_estrategica": (
            "A combinação entre força territorial do Davi, prioridade eleitoral da Gabi e rede municipal "
            "de lideranças permite identificar onde uma agenda conjunta tem maior eficiência política."
        ),
    }

    dados["indicadores"] = {
        "municipios_analisados": int(len(cruzamento)),
        "municipios_muito_alta_sinergia": int(len(cruzamento[cruzamento["prioridade_sinergia_davi_gabi"] == "Muito alta"])),
        "municipios_alta_sinergia": int(len(cruzamento[cruzamento["prioridade_sinergia_davi_gabi"] == "Alta"])),
        "agenda_conjunta_top30": int(len(agenda)),
    }

    dados["cards"] = [
        {
            "etiqueta": "Sinergia territorial",
            "titulo": "Municípios prioritários",
            "texto": (
                "O cruzamento identifica os municípios onde a prioridade da Gabi, a força territorial do Davi "
                "e a rede local de lideranças aparecem de forma combinada."
            ),
        },
        {
            "etiqueta": "Agenda conjunta",
            "titulo": "Davi + Gabi",
            "texto": (
                "A agenda conjunta deve começar pelos municípios de maior score, validando lideranças locais "
                "e potencial de transferência para Federal e Estadual."
            ),
        },
        {
            "etiqueta": "Decisão operacional",
            "titulo": "Curadoria antes da visita",
            "texto": (
                "Antes de confirmar agendas públicas, os nomes mapeados precisam ser validados politicamente "
                "para evitar conflitos locais e sobreposição de apoios."
            ),
        },
    ]

    dados["municipios_alta_sinergia"] = [
        {
            "rank": int(row["ranking_sinergia_davi_gabi"]),
            "municipio": row["municipio"],
            "prioridade": row["prioridade_sinergia_davi_gabi"],
            "score": round(float(row["score_sinergia_davi_gabi"]), 2),
            "principal_lideranca": row["principal_lideranca"],
            "prefeito_2024": row["prefeito_2024"],
            "meta_referencia_gabi": int(row["meta_votos_referencia_gabi"]),
            "acao_recomendada": row["acao_recomendada"],
            "justificativa": row["justificativa_sinergia"],
        }
        for _, row in cruzamento.head(TOP_DASHBOARD).iterrows()
    ]

    dados["agenda_conjunta_recomendada"] = [
        {
            "ordem": int(row["ordem_agenda"]),
            "semana": row["semana_sugerida"],
            "municipio": row["municipio"],
            "prioridade": row["prioridade_sinergia_davi_gabi"],
            "principal_lideranca": row["principal_lideranca"],
            "acao_recomendada": row["acao_recomendada"],
            "formato": row["formato_agenda_recomendada"],
        }
        for _, row in agenda.iterrows()
    ]

    salvar_json(caminho, dados)


def gerar_briefing_sprint04(cruzamento: pd.DataFrame, agenda: pd.DataFrame) -> str:
    muito_alta = int(len(cruzamento[cruzamento["prioridade_sinergia_davi_gabi"] == "Muito alta"]))
    alta = int(len(cruzamento[cruzamento["prioridade_sinergia_davi_gabi"] == "Alta"]))
    media = int(len(cruzamento[cruzamento["prioridade_sinergia_davi_gabi"] == "Média"]))

    top5 = cruzamento.head(5)

    linhas = [
        "# Briefing — Sprint 04 — Cruzamento Davi Maia + Gabi Gonçalves",
        "",
        "## Objetivo",
        "",
        "Criar a primeira camada de cruzamento entre a força territorial do Davi Maia e a base eleitoral preliminar da Gabi Gonçalves.",
        "",
        "## Metodologia",
        "",
        "O score de sinergia foi calculado combinando:",
        "",
        "- score territorial do Davi Maia;",
        "- score preliminar da Gabi;",
        "- presença de lideranças municipais;",
        "- peso eleitoral do município;",
        "- bônus para municípios de maior prioridade operacional.",
        "",
        "## Resultado geral",
        "",
        f"- Municípios analisados: {len(cruzamento)}",
        f"- Municípios de sinergia muito alta: {muito_alta}",
        f"- Municípios de sinergia alta: {alta}",
        f"- Municípios de sinergia média: {media}",
        f"- Municípios na agenda conjunta preliminar: {len(agenda)}",
        "",
        "## Top 5 municípios preliminares",
        "",
    ]

    for _, row in top5.iterrows():
        linhas.append(
            f"- {int(row['ranking_sinergia_davi_gabi'])}. {row['municipio']} — "
            f"{row['prioridade_sinergia_davi_gabi']} — score {float(row['score_sinergia_davi_gabi']):.2f}"
        )

    linhas.extend(
        [
            "",
            "## Arquivos gerados",
            "",
            "- data/final/parceiros/gabi-goncalves/cruzamento_davi_gabi_v1.csv",
            "- data/final/parceiros/gabi-goncalves/cruzamento_davi_gabi_v1.xlsx",
            "- data/reference/parceiros/gabi-goncalves/agenda_conjunta_davi_gabi_v1.csv",
            "- data/dashboard/parceiros/gabi-goncalves/cruzamento_davi_gabi_v1.json",
            "- docs/briefing_gabi_sprint04.md",
            "",
            "## Próximo sprint recomendado",
            "",
            "Sprint 05 — Roteiro Territorial Davi + Gabi.",
            "",
            "O próximo passo será transformar a agenda conjunta preliminar em um roteiro semanal de visitas, organizando municípios, lideranças, justificativa e prioridade operacional.",
        ]
    )

    return "\n".join(linhas) + "\n"


def salvar_resultados(root: Path, cruzamento: pd.DataFrame, agenda: pd.DataFrame) -> None:
    final_dir = root / "data" / "final" / "parceiros" / "gabi-goncalves"
    reference_dir = root / "data" / "reference" / "parceiros" / "gabi-goncalves"
    docs_dir = root / "docs"

    final_dir.mkdir(parents=True, exist_ok=True)
    reference_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    cruzamento_csv = final_dir / "cruzamento_davi_gabi_v1.csv"
    cruzamento_xlsx = final_dir / "cruzamento_davi_gabi_v1.xlsx"
    agenda_csv = reference_dir / "agenda_conjunta_davi_gabi_v1.csv"
    briefing_md = docs_dir / "briefing_gabi_sprint04.md"

    cruzamento.to_csv(cruzamento_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Cruzamento salvo: {cruzamento_csv}")

    agenda.to_csv(agenda_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Agenda conjunta salva: {agenda_csv}")

    try:
        with pd.ExcelWriter(cruzamento_xlsx) as writer:
            cruzamento.to_excel(writer, sheet_name="cruzamento", index=False)
            agenda.to_excel(writer, sheet_name="agenda_conjunta", index=False)

        print(f"[OK] XLSX consolidado salvo: {cruzamento_xlsx}")
    except Exception as erro:
        print(f"[AVISO] Não foi possível salvar XLSX. CSVs foram gerados normalmente. Erro: {erro}")

    briefing_md.write_text(
        gerar_briefing_sprint04(cruzamento, agenda),
        encoding="utf-8",
    )
    print(f"[OK] Briefing salvo: {briefing_md}")


def imprimir_resumo(cruzamento: pd.DataFrame, agenda: pd.DataFrame) -> None:
    print("")
    print("============================================================")
    print("RESUMO DO SPRINT 04")
    print("============================================================")
    print(f"Municípios analisados: {len(cruzamento)}")
    print(
        "Sinergia Muito alta: "
        f"{len(cruzamento[cruzamento['prioridade_sinergia_davi_gabi'] == 'Muito alta'])}"
    )
    print(
        "Sinergia Alta: "
        f"{len(cruzamento[cruzamento['prioridade_sinergia_davi_gabi'] == 'Alta'])}"
    )
    print(
        "Sinergia Média: "
        f"{len(cruzamento[cruzamento['prioridade_sinergia_davi_gabi'] == 'Média'])}"
    )
    print(f"Agenda conjunta preliminar: {len(agenda)} municípios")
    print("")
    print("TOP 15 Davi + Gabi:")
    print("------------------------------------------------------------")

    colunas = [
        "ranking_sinergia_davi_gabi",
        "municipio",
        "prioridade_sinergia_davi_gabi",
        "score_sinergia_davi_gabi",
        "principal_lideranca",
        "meta_votos_referencia_gabi",
        "acao_recomendada",
    ]

    print(cruzamento[colunas].head(15).to_string(index=False))
    print("============================================================")


def main() -> None:
    root = detectar_raiz_projeto()

    print("============================================================")
    print("SPRINT 04 — CRUZAMENTO DAVI MAIA + GABI GONÇALVES")
    print("============================================================")
    print(f"[INFO] Raiz detectada: {root}")

    base_gabi = carregar_base_gabi(root)
    ranking_davi = carregar_ranking_davi(root)
    resumo_liderancas = carregar_resumo_liderancas(root)

    cruzamento = calcular_cruzamento(base_gabi, ranking_davi, resumo_liderancas)
    agenda = gerar_agenda_conjunta(cruzamento)

    salvar_resultados(root, cruzamento, agenda)
    atualizar_base_dashboard(root, cruzamento)
    atualizar_cruzamento_json(root, cruzamento, agenda)

    imprimir_resumo(cruzamento, agenda)

    print("")
    print("SPRINT 04 CONCLUÍDO.")
    print("")
    print("Agora teste o painel:")
    print("  cd C:\\Users\\user\\Documents\\Workspace\\campanha_2026\\alagoas-political-intelligence")
    print("  python -m http.server 8000")
    print("")
    print("Abra:")
    print("  http://localhost:8000/parceiros/gabi-goncalves/")
    print("")
    print("Depois use Ctrl + F5 para atualizar os JSONs no navegador.")


if __name__ == "__main__":
    main()