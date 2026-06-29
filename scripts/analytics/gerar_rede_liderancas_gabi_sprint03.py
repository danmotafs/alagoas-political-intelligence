from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd


TOP_MUNICIPIOS_CURADORIA = 40
TOP_LIDERANCAS_DASHBOARD = 20
TOP_LIDERANCAS_AGENDA = 80


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

    raise RuntimeError(f"Não foi possível ler o arquivo {caminho}. Erro: {ultimo_erro}")


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
            "Não encontrei a base eleitoral da Gabi. "
            "Rode antes o Sprint 02: scripts/analytics/gerar_base_eleitoral_gabi_sprint02.py"
        )

    print(f"[OK] Base eleitoral da Gabi encontrada: {caminho}")

    if caminho.suffix.lower() == ".xlsx":
        df = pd.read_excel(caminho)
        df.columns = [normalizar_coluna(c) for c in df.columns]
    else:
        df = ler_csv_robusto(caminho)

    col_municipio = encontrar_coluna(df, ["municipio", "nm_municipio", "nome_municipio"])

    if col_municipio is None:
        raise RuntimeError("Não encontrei coluna de município na base eleitoral da Gabi.")

    df["municipio"] = df[col_municipio].astype(str).str.strip()
    df["municipio_key"] = df["municipio"].apply(normalizar_texto)

    campos_numericos = [
        "ranking_gabi_preliminar",
        "eleitorado",
        "populacao",
        "score_gabi_preliminar",
        "meta_votos_referencia_gabi",
        "votos_vereadores_total",
        "vereadores_mapeados",
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
    ]

    for campo in campos_texto:
        if campo not in df.columns:
            df[campo] = ""
        df[campo] = df[campo].fillna("").astype(str)

    df = df.drop_duplicates(subset=["municipio_key"]).reset_index(drop=True)

    return df


def carregar_vereadores(root: Path) -> pd.DataFrame:
    caminho = encontrar_arquivo(
        root,
        [
            "data/final/inteligencia_vereadores_alagoas_2024.csv",
            "data/processed/inteligencia_vereadores_alagoas_2024.csv",
            "data/final/vereadores_eleitos_alagoas_2024.csv",
            "data/processed/vereadores_eleitos_alagoas_2024.csv",
        ],
    )

    if caminho is None:
        raise FileNotFoundError(
            "Não encontrei a base individual de vereadores. "
            "Esperado: data/final/inteligencia_vereadores_alagoas_2024.csv"
        )

    print(f"[OK] Base individual de vereadores encontrada: {caminho}")

    df = ler_csv_robusto(caminho)

    col_municipio = encontrar_coluna(
        df,
        [
            "municipio",
            "nm_municipio",
            "nome_municipio",
            "municipio_nome",
            "ds_municipio",
        ],
    )

    col_nome = encontrar_coluna(
        df,
        [
            "nome_urna",
            "nm_urna_candidato",
            "nome_candidato",
            "nm_candidato",
            "candidato",
            "vereador",
            "nome",
        ],
    )

    col_partido = encontrar_coluna(
        df,
        [
            "partido",
            "sg_partido",
            "sigla_partido",
            "partido_candidato",
            "sigla",
        ],
    )

    col_votos = encontrar_coluna(
        df,
        [
            "votos",
            "qt_votos_nominais",
            "qt_votos",
            "votos_nominais",
            "total_votos",
            "votos_candidato",
        ],
    )

    col_situacao = encontrar_coluna(
        df,
        [
            "situacao",
            "ds_sit_tot_turno",
            "situacao_totalizacao",
            "resultado",
            "status_eleicao",
        ],
    )

    if col_municipio is None:
        raise RuntimeError("Não encontrei coluna de município na base de vereadores.")

    if col_nome is None:
        raise RuntimeError("Não encontrei coluna de nome do vereador na base de vereadores.")

    vereadores = pd.DataFrame()
    vereadores["municipio"] = df[col_municipio].astype(str).str.strip()
    vereadores["municipio_key"] = vereadores["municipio"].apply(normalizar_texto)
    vereadores["nome_lideranca"] = df[col_nome].astype(str).str.strip()

    if col_partido:
        vereadores["partido"] = df[col_partido].astype(str).str.strip()
    else:
        vereadores["partido"] = ""

    if col_votos:
        vereadores["votos_2024"] = converter_numero(df[col_votos]).astype(int)
    else:
        vereadores["votos_2024"] = 0

    if col_situacao:
        vereadores["situacao_eleitoral"] = df[col_situacao].astype(str).str.strip()
    else:
        vereadores["situacao_eleitoral"] = "Vereador(a) eleito(a)"

    vereadores = vereadores[
        (vereadores["municipio_key"] != "")
        & (vereadores["nome_lideranca"].astype(str).str.strip() != "")
    ].copy()

    vereadores = vereadores.sort_values(
        by=["municipio_key", "votos_2024"],
        ascending=[True, False],
    ).reset_index(drop=True)

    return vereadores


def classificar_prioridade_lideranca(row: pd.Series) -> str:
    rank_municipio = int(row.get("ranking_gabi_preliminar", 999))
    rank_local = int(row.get("rank_local_lideranca", 999))
    votos = int(row.get("votos_2024", 0))

    if rank_municipio <= 10 and rank_local <= 5:
        return "Muito alta"

    if rank_municipio <= 20 and rank_local <= 8:
        return "Alta"

    if rank_municipio <= 40 and rank_local <= 10:
        return "Média"

    if votos >= 1000:
        return "Monitorar"

    return "Baixa"


def definir_status_curadoria(prioridade: str) -> str:
    if prioridade == "Muito alta":
        return "Contato prioritário"
    if prioridade == "Alta":
        return "Curar na primeira rodada"
    if prioridade == "Média":
        return "Curar na segunda rodada"
    if prioridade == "Monitorar":
        return "Monitorar aderência"
    return "Baixa prioridade inicial"


def definir_abordagem(row: pd.Series) -> str:
    prioridade = row.get("prioridade_lideranca_gabi", "")
    municipio = row.get("municipio", "")
    nome = row.get("nome_lideranca", "")

    if prioridade == "Muito alta":
        return (
            f"Validar relação política com {nome} em {municipio}; avaliar agenda direta "
            "com Gabi e possibilidade de composição com Davi Maia."
        )

    if prioridade == "Alta":
        return (
            f"Mapear interlocutor local de {nome}; levantar histórico de alinhamento, "
            "vínculos partidários e abertura para agenda conjunta."
        )

    if prioridade == "Média":
        return (
            "Manter na lista de curadoria territorial; avaliar após confirmação dos apoios "
            "dos municípios prioritários."
        )

    return (
        "Monitorar movimentação política e reavaliar após novas alianças ou agenda municipal."
    )


def montar_rede_liderancas(base_gabi: pd.DataFrame, vereadores: pd.DataFrame) -> pd.DataFrame:
    base_prioritaria = base_gabi[
        base_gabi["ranking_gabi_preliminar"] <= TOP_MUNICIPIOS_CURADORIA
    ].copy()

    if base_prioritaria.empty:
        raise RuntimeError(
            "A base da Gabi não possui municípios prioritários. "
            "Confira o arquivo base_eleitoral_gabi_v1.csv."
        )

    df = vereadores.merge(
        base_prioritaria[
            [
                "municipio_key",
                "ranking_gabi_preliminar",
                "prioridade_visita_gabi",
                "status_articulacao_gabi",
                "eleitorado",
                "populacao",
                "score_gabi_preliminar",
                "meta_votos_referencia_gabi",
                "prefeito_2024",
                "partido_prefeito_2024",
                "relacao_gabi",
                "aderencia_gabi",
                "grupo_politico_gabi",
            ]
        ],
        on="municipio_key",
        how="inner",
    )

    if df.empty:
        raise RuntimeError(
            "Não houve correspondência entre municípios da base da Gabi e municípios da base de vereadores."
        )

    df["votos_total_vereadores_municipio_calculado"] = (
        df.groupby("municipio_key")["votos_2024"].transform("sum")
    )

    df["rank_local_lideranca"] = (
        df.groupby("municipio_key")["votos_2024"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    df["participacao_votos_lideranca_pct"] = (
        df["votos_2024"]
        / df["votos_total_vereadores_municipio_calculado"].replace(0, pd.NA)
        * 100
    ).fillna(0).round(2)

    df["potencial_transferencia_5pct"] = (df["votos_2024"] * 0.05).round().astype(int)
    df["potencial_transferencia_10pct"] = (df["votos_2024"] * 0.10).round().astype(int)
    df["potencial_transferencia_15pct"] = (df["votos_2024"] * 0.15).round().astype(int)

    df["score_votos_lideranca"] = normalizar_0_100(df["votos_2024"])

    df["score_posicao_local"] = df["rank_local_lideranca"].apply(
        lambda rank: max(0, (11 - int(rank)) / 10) * 100 if int(rank) <= 10 else 0
    )

    df["score_municipio_gabi"] = df["ranking_gabi_preliminar"].apply(
        lambda rank: max(0, (TOP_MUNICIPIOS_CURADORIA + 1 - int(rank)) / TOP_MUNICIPIOS_CURADORIA) * 100
    )

    df["score_lideranca_gabi"] = (
        df["score_municipio_gabi"] * 0.50
        + df["score_votos_lideranca"] * 0.30
        + df["score_posicao_local"] * 0.20
    ).round(2)

    df["tipo_lideranca"] = "Vereador(a)"
    df["prioridade_lideranca_gabi"] = df.apply(classificar_prioridade_lideranca, axis=1)
    df["status_curadoria_lideranca"] = df["prioridade_lideranca_gabi"].apply(definir_status_curadoria)
    df["abordagem_recomendada"] = df.apply(definir_abordagem, axis=1)

    df["responsavel_articulacao"] = ""
    df["telefone_contato"] = ""
    df["observacao_curadoria"] = ""
    df["risco_politico"] = ""
    df["proximo_passo"] = ""

    df = df.sort_values(
        by=[
            "score_lideranca_gabi",
            "ranking_gabi_preliminar",
            "rank_local_lideranca",
            "votos_2024",
        ],
        ascending=[False, True, True, False],
    ).reset_index(drop=True)

    df["ranking_lideranca_gabi"] = range(1, len(df) + 1)

    ordem_colunas = [
        "ranking_lideranca_gabi",
        "municipio",
        "ranking_gabi_preliminar",
        "prioridade_visita_gabi",
        "status_articulacao_gabi",
        "nome_lideranca",
        "tipo_lideranca",
        "partido",
        "situacao_eleitoral",
        "votos_2024",
        "rank_local_lideranca",
        "participacao_votos_lideranca_pct",
        "score_lideranca_gabi",
        "prioridade_lideranca_gabi",
        "status_curadoria_lideranca",
        "potencial_transferencia_5pct",
        "potencial_transferencia_10pct",
        "potencial_transferencia_15pct",
        "eleitorado",
        "populacao",
        "meta_votos_referencia_gabi",
        "prefeito_2024",
        "partido_prefeito_2024",
        "relacao_gabi",
        "aderencia_gabi",
        "grupo_politico_gabi",
        "abordagem_recomendada",
        "responsavel_articulacao",
        "telefone_contato",
        "observacao_curadoria",
        "risco_politico",
        "proximo_passo",
        "municipio_key",
    ]

    for coluna in ordem_colunas:
        if coluna not in df.columns:
            df[coluna] = ""

    return df[ordem_colunas]


def gerar_resumo_municipal(rede: pd.DataFrame) -> pd.DataFrame:
    resumo = (
        rede.groupby(
            [
                "municipio",
                "municipio_key",
                "ranking_gabi_preliminar",
                "prioridade_visita_gabi",
                "status_articulacao_gabi",
            ],
            as_index=False,
        )
        .agg(
            liderancas_mapeadas=("nome_lideranca", "count"),
            votos_liderancas_total=("votos_2024", "sum"),
            potencial_transferencia_5pct=("potencial_transferencia_5pct", "sum"),
            potencial_transferencia_10pct=("potencial_transferencia_10pct", "sum"),
            potencial_transferencia_15pct=("potencial_transferencia_15pct", "sum"),
            maior_score_lideranca=("score_lideranca_gabi", "max"),
        )
    )

    principais = (
        rede.sort_values(
            by=["municipio_key", "score_lideranca_gabi", "votos_2024"],
            ascending=[True, False, False],
        )
        .groupby("municipio_key")
        .head(1)[
            [
                "municipio_key",
                "nome_lideranca",
                "partido",
                "votos_2024",
                "prioridade_lideranca_gabi",
            ]
        ]
        .rename(
            columns={
                "nome_lideranca": "principal_lideranca",
                "partido": "partido_principal_lideranca",
                "votos_2024": "votos_principal_lideranca",
                "prioridade_lideranca_gabi": "prioridade_principal_lideranca",
            }
        )
    )

    resumo = resumo.merge(principais, on="municipio_key", how="left")

    resumo = resumo.sort_values(
        by=["ranking_gabi_preliminar", "votos_liderancas_total"],
        ascending=[True, False],
    ).reset_index(drop=True)

    return resumo


def gerar_agenda_curadoria(rede: pd.DataFrame) -> pd.DataFrame:
    agenda = rede.head(TOP_LIDERANCAS_AGENDA).copy()

    agenda["ordem_curadoria"] = range(1, len(agenda) + 1)

    agenda["semana_sugerida"] = agenda["ordem_curadoria"].apply(
        lambda ordem: "Semana 1" if ordem <= 20 else (
            "Semana 2" if ordem <= 40 else (
                "Semana 3" if ordem <= 60 else "Semana 4"
            )
        )
    )

    agenda["objetivo_da_abordagem"] = agenda["prioridade_lideranca_gabi"].apply(
        lambda prioridade: (
            "Confirmar possibilidade de apoio e agenda conjunta"
            if prioridade in ["Muito alta", "Alta"]
            else "Validar aderência política e capacidade de mobilização"
        )
    )

    colunas = [
        "ordem_curadoria",
        "semana_sugerida",
        "municipio",
        "ranking_gabi_preliminar",
        "nome_lideranca",
        "tipo_lideranca",
        "partido",
        "votos_2024",
        "rank_local_lideranca",
        "prioridade_lideranca_gabi",
        "status_curadoria_lideranca",
        "objetivo_da_abordagem",
        "abordagem_recomendada",
        "responsavel_articulacao",
        "telefone_contato",
        "observacao_curadoria",
        "risco_politico",
        "proximo_passo",
    ]

    return agenda[colunas]


def carregar_json(caminho: Path) -> dict:
    if caminho.exists():
        return json.loads(caminho.read_text(encoding="utf-8"))

    return {}


def salvar_json(caminho: Path, dados: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] JSON salvo: {caminho}")


def atualizar_dashboard_json(root: Path, rede: pd.DataFrame, resumo: pd.DataFrame) -> None:
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
    dados["metadata"]["versao"] = "sprint03_rede_liderancas"
    dados["metadata"]["atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    dados["metadata"]["status"] = (
        "Rede preliminar de lideranças municipais criada a partir da base de vereadores."
    )

    dados.setdefault("indicadores_gabi", {})
    dados["indicadores_gabi"]["liderancas_mapeadas"] = int(len(rede))
    dados["indicadores_gabi"]["municipios_com_liderancas_mapeadas"] = int(
        rede["municipio_key"].nunique()
    )
    dados["indicadores_gabi"]["liderancas_prioritarias_muito_alta"] = int(
        len(rede[rede["prioridade_lideranca_gabi"] == "Muito alta"])
    )
    dados["indicadores_gabi"]["liderancas_prioritarias_alta"] = int(
        len(rede[rede["prioridade_lideranca_gabi"] == "Alta"])
    )
    dados["indicadores_gabi"]["status_liderancas"] = (
        "Rede preliminar criada; nomes precisam de curadoria política."
    )

    liderancas_dashboard = []

    for _, row in rede.head(TOP_LIDERANCAS_DASHBOARD).iterrows():
        liderancas_dashboard.append(
            {
                "rank": int(row["ranking_lideranca_gabi"]),
                "municipio": row["municipio"],
                "nome": row["nome_lideranca"],
                "tipo": row["tipo_lideranca"],
                "partido": row["partido"],
                "votos_2024": int(row["votos_2024"]),
                "potencial": f"{int(row['potencial_transferencia_10pct'])} votos em cenário 10%",
                "prioridade": row["prioridade_lideranca_gabi"],
                "status": row["status_curadoria_lideranca"],
            }
        )

    dados["liderancas"] = liderancas_dashboard

    dados["resumo_liderancas_municipio"] = [
        {
            "municipio": row["municipio"],
            "liderancas_mapeadas": int(row["liderancas_mapeadas"]),
            "principal_lideranca": row["principal_lideranca"],
            "partido_principal_lideranca": row["partido_principal_lideranca"],
            "votos_principal_lideranca": int(row["votos_principal_lideranca"]),
            "potencial_transferencia_10pct": int(row["potencial_transferencia_10pct"]),
        }
        for _, row in resumo.head(20).iterrows()
    ]

    dados["proximos_passos"] = [
        {
            "sprint": "Sprint 04",
            "titulo": "Cruzamento Davi + Gabi",
            "descricao": "Cruzar lideranças da Gabi com a rede política do Davi para identificar apoios compartilháveis e agendas conjuntas."
        },
        {
            "sprint": "Sprint 05",
            "titulo": "Roteiro Territorial",
            "descricao": "Transformar lideranças prioritárias em roteiro semanal de visitas e validação política."
        },
        {
            "sprint": "Sprint 06",
            "titulo": "Curadoria Política",
            "descricao": "Preencher relação real com Gabi, Davi, Renan Filho, Paulo Dantas e lideranças municipais."
        },
        {
            "sprint": "Sprint 07",
            "titulo": "Versão de Aprovação",
            "descricao": "Consolidar painel para envio ao Davi e validação estratégica."
        },
    ]

    salvar_json(caminho, dados)


def atualizar_cruzamento_json(root: Path, rede: pd.DataFrame, resumo: pd.DataFrame) -> None:
    caminho = (
        root
        / "data"
        / "dashboard"
        / "parceiros"
        / "gabi-goncalves"
        / "cruzamento_davi_gabi_v1.json"
    )

    dados = carregar_json(caminho)

    dados.setdefault("metadata", {})
    dados["metadata"]["projeto"] = "Cruzamento Davi Maia + Gabi Gonçalves"
    dados["metadata"]["versao"] = "sprint03_rede_liderancas"
    dados["metadata"]["atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    dados["metadata"]["status"] = (
        "Camada de lideranças municipais adicionada ao cruzamento Davi + Gabi."
    )

    dados["cards"] = [
        {
            "etiqueta": "Rede municipal",
            "titulo": "Lideranças prioritárias",
            "texto": (
                "A base preliminar identifica vereadores e lideranças municipais com maior "
                "potencial de articulação para a reeleição da Gabi."
            ),
        },
        {
            "etiqueta": "Agenda conjunta",
            "titulo": "Davi + Gabi",
            "texto": (
                "O próximo passo é cruzar essas lideranças com a força territorial do Davi "
                "para selecionar agendas conjuntas mais eficientes."
            ),
        },
        {
            "etiqueta": "Curadoria política",
            "titulo": "Validação manual",
            "texto": (
                "Os nomes mapeados precisam ser classificados quanto à relação real com Gabi, "
                "Davi e grupos políticos locais."
            ),
        },
    ]

    dados["liderancas_prioritarias_preliminares"] = [
        {
            "rank": int(row["ranking_lideranca_gabi"]),
            "municipio": row["municipio"],
            "nome_lideranca": row["nome_lideranca"],
            "partido": row["partido"],
            "votos_2024": int(row["votos_2024"]),
            "prioridade": row["prioridade_lideranca_gabi"],
            "potencial_transferencia_10pct": int(row["potencial_transferencia_10pct"]),
        }
        for _, row in rede.head(30).iterrows()
    ]

    dados["municipios_com_maior_rede_liderancas"] = [
        {
            "municipio": row["municipio"],
            "liderancas_mapeadas": int(row["liderancas_mapeadas"]),
            "principal_lideranca": row["principal_lideranca"],
            "votos_liderancas_total": int(row["votos_liderancas_total"]),
            "potencial_transferencia_10pct": int(row["potencial_transferencia_10pct"]),
        }
        for _, row in resumo.head(15).iterrows()
    ]

    salvar_json(caminho, dados)


def gerar_briefing_sprint03(rede: pd.DataFrame, resumo: pd.DataFrame) -> str:
    total_liderancas = len(rede)
    municipios = rede["municipio_key"].nunique()
    muito_alta = len(rede[rede["prioridade_lideranca_gabi"] == "Muito alta"])
    alta = len(rede[rede["prioridade_lideranca_gabi"] == "Alta"])

    linhas = [
        "# Briefing — Sprint 03 — Rede de Lideranças Gabi Gonçalves",
        "",
        "## Objetivo",
        "",
        "Criar a primeira rede preliminar de lideranças municipais para a Gabi Gonçalves, considerando sua candidatura à reeleição como Deputada Estadual.",
        "",
        "## Metodologia",
        "",
        "A rede foi construída a partir da base individual de vereadores de Alagoas e cruzada com a base eleitoral preliminar da Gabi criada no Sprint 02.",
        "",
        "Foram considerados prioritários os municípios classificados entre os 40 primeiros do ranking preliminar da Gabi.",
        "",
        "## Resultado geral",
        "",
        f"- Lideranças mapeadas: {total_liderancas}",
        f"- Municípios com lideranças mapeadas: {municipios}",
        f"- Lideranças de prioridade muito alta: {muito_alta}",
        f"- Lideranças de prioridade alta: {alta}",
        "",
        "## Campos criados",
        "",
        "- ranking_lideranca_gabi",
        "- nome_lideranca",
        "- tipo_lideranca",
        "- partido",
        "- votos_2024",
        "- rank_local_lideranca",
        "- participacao_votos_lideranca_pct",
        "- score_lideranca_gabi",
        "- prioridade_lideranca_gabi",
        "- status_curadoria_lideranca",
        "- potencial_transferencia_5pct",
        "- potencial_transferencia_10pct",
        "- potencial_transferencia_15pct",
        "- abordagem_recomendada",
        "- responsavel_articulacao",
        "- telefone_contato",
        "- observacao_curadoria",
        "- risco_politico",
        "- proximo_passo",
        "",
        "## Arquivos gerados",
        "",
        "- data/final/parceiros/gabi-goncalves/rede_liderancas_gabi_v1.csv",
        "- data/final/parceiros/gabi-goncalves/rede_liderancas_gabi_v1.xlsx",
        "- data/final/parceiros/gabi-goncalves/resumo_liderancas_municipio_gabi_v1.csv",
        "- data/reference/parceiros/gabi-goncalves/agenda_curadoria_liderancas_gabi_v1.csv",
        "- data/dashboard/parceiros/gabi-goncalves/base_dashboard_gabi_v1.json",
        "- data/dashboard/parceiros/gabi-goncalves/cruzamento_davi_gabi_v1.json",
        "",
        "## Próximo sprint recomendado",
        "",
        "Sprint 04 — Cruzamento Davi + Gabi.",
        "",
        "O próximo passo será cruzar as lideranças prioritárias da Gabi com a rede de poder e o ranking territorial do Davi Maia para identificar municípios e agendas de maior eficiência política.",
        "",
    ]

    return "\n".join(linhas)


def salvar_resultados(root: Path, rede: pd.DataFrame, resumo: pd.DataFrame, agenda: pd.DataFrame) -> None:
    final_dir = root / "data" / "final" / "parceiros" / "gabi-goncalves"
    reference_dir = root / "data" / "reference" / "parceiros" / "gabi-goncalves"
    docs_dir = root / "docs"

    final_dir.mkdir(parents=True, exist_ok=True)
    reference_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    rede_csv = final_dir / "rede_liderancas_gabi_v1.csv"
    rede_xlsx = final_dir / "rede_liderancas_gabi_v1.xlsx"
    resumo_csv = final_dir / "resumo_liderancas_municipio_gabi_v1.csv"
    agenda_csv = reference_dir / "agenda_curadoria_liderancas_gabi_v1.csv"
    briefing_md = docs_dir / "briefing_gabi_sprint03.md"

    rede.to_csv(rede_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Rede de lideranças salva: {rede_csv}")

    resumo.to_csv(resumo_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Resumo municipal salvo: {resumo_csv}")

    agenda.to_csv(agenda_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Agenda de curadoria salva: {agenda_csv}")

    try:
        with pd.ExcelWriter(rede_xlsx) as writer:
            rede.to_excel(writer, sheet_name="rede_liderancas", index=False)
            resumo.to_excel(writer, sheet_name="resumo_municipal", index=False)
            agenda.to_excel(writer, sheet_name="agenda_curadoria", index=False)

        print(f"[OK] XLSX consolidado salvo: {rede_xlsx}")
    except Exception as erro:
        print(f"[AVISO] Não foi possível salvar XLSX. CSVs foram gerados normalmente. Erro: {erro}")

    briefing_md.write_text(gerar_briefing_sprint03(rede, resumo), encoding="utf-8")
    print(f"[OK] Briefing salvo: {briefing_md}")


def imprimir_resumo(rede: pd.DataFrame, resumo: pd.DataFrame) -> None:
    print("")
    print("============================================================")
    print("RESUMO DO SPRINT 03")
    print("============================================================")
    print(f"Lideranças mapeadas: {len(rede)}")
    print(f"Municípios com lideranças: {rede['municipio_key'].nunique()}")
    print(f"Prioridade Muito alta: {len(rede[rede['prioridade_lideranca_gabi'] == 'Muito alta'])}")
    print(f"Prioridade Alta: {len(rede[rede['prioridade_lideranca_gabi'] == 'Alta'])}")
    print(f"Prioridade Média: {len(rede[rede['prioridade_lideranca_gabi'] == 'Média'])}")
    print("")
    print("TOP 15 lideranças preliminares:")
    print("------------------------------------------------------------")

    colunas = [
        "ranking_lideranca_gabi",
        "municipio",
        "nome_lideranca",
        "partido",
        "votos_2024",
        "prioridade_lideranca_gabi",
        "potencial_transferencia_10pct",
    ]

    print(rede[colunas].head(15).to_string(index=False))

    print("")
    print("TOP 10 municípios por rede de lideranças:")
    print("------------------------------------------------------------")

    colunas_resumo = [
        "municipio",
        "liderancas_mapeadas",
        "principal_lideranca",
        "votos_liderancas_total",
        "potencial_transferencia_10pct",
    ]

    print(resumo[colunas_resumo].head(10).to_string(index=False))
    print("============================================================")


def main() -> None:
    root = detectar_raiz_projeto()

    print("============================================================")
    print("SPRINT 03 — REDE DE LIDERANÇAS GABI GONÇALVES")
    print("============================================================")
    print(f"[INFO] Raiz detectada: {root}")

    base_gabi = carregar_base_gabi(root)
    vereadores = carregar_vereadores(root)

    rede = montar_rede_liderancas(base_gabi, vereadores)
    resumo = gerar_resumo_municipal(rede)
    agenda = gerar_agenda_curadoria(rede)

    salvar_resultados(root, rede, resumo, agenda)
    atualizar_dashboard_json(root, rede, resumo)
    atualizar_cruzamento_json(root, rede, resumo)

    imprimir_resumo(rede, resumo)

    print("")
    print("SPRINT 03 CONCLUÍDO.")
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