from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd


TOP_ROTEIRO = 30
MUNICIPIOS_POR_SEMANA = 8


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


def carregar_cruzamento_ou_agenda(root: Path) -> pd.DataFrame:
    caminho = encontrar_arquivo(
        root,
        [
            "data/reference/parceiros/gabi-goncalves/agenda_conjunta_davi_gabi_v1.csv",
            "data/final/parceiros/gabi-goncalves/cruzamento_davi_gabi_v1.csv",
            "data/final/parceiros/gabi-goncalves/cruzamento_davi_gabi_v1.xlsx",
        ],
    )

    if caminho is None:
        raise FileNotFoundError(
            "Não encontrei a agenda/cruzamento Davi + Gabi. "
            "Rode antes o Sprint 04: scripts/analytics/gerar_cruzamento_davi_gabi_sprint04.py"
        )

    print(f"[OK] Base de cruzamento/agenda encontrada: {caminho}")

    df = ler_tabela(caminho)

    col_municipio = encontrar_coluna(df, ["municipio", "nm_municipio", "nome_municipio"])
    col_rank = encontrar_coluna(df, ["ranking_sinergia_davi_gabi", "ordem_agenda", "rank", "ranking"])
    col_prioridade = encontrar_coluna(df, ["prioridade_sinergia_davi_gabi", "prioridade", "prioridade_agenda"])
    col_status = encontrar_coluna(df, ["status_agenda_conjunta", "status", "status_execucao"])
    col_score = encontrar_coluna(df, ["score_sinergia_davi_gabi", "score", "indice"])
    col_lideranca = encontrar_coluna(df, ["principal_lideranca", "nome_lideranca", "lideranca"])
    col_partido_lideranca = encontrar_coluna(df, ["partido_principal_lideranca", "partido_lideranca", "partido"])
    col_prefeito = encontrar_coluna(df, ["prefeito_2024", "prefeito", "nome_prefeito"])
    col_partido_prefeito = encontrar_coluna(df, ["partido_prefeito_2024", "partido_prefeito"])
    col_meta = encontrar_coluna(df, ["meta_votos_referencia_gabi", "meta_referencia_gabi", "meta"])
    col_potencial = encontrar_coluna(df, ["potencial_transferencia_10pct", "potencial"])
    col_acao = encontrar_coluna(df, ["acao_recomendada", "ação_recomendada", "acao"])
    col_formato = encontrar_coluna(df, ["formato_agenda_recomendada", "formato"])
    col_justificativa = encontrar_coluna(df, ["justificativa_sinergia", "justificativa"])
    col_eleitorado = encontrar_coluna(df, ["eleitorado"])
    col_semana = encontrar_coluna(df, ["semana_sugerida", "semana"])

    if col_municipio is None:
        raise RuntimeError("Não encontrei coluna de município no cruzamento/agenda.")

    base = pd.DataFrame()
    base["municipio"] = df[col_municipio].astype(str).str.strip()
    base["municipio_key"] = base["municipio"].apply(normalizar_texto)

    base["ranking_sinergia_davi_gabi"] = (
        converter_numero(df[col_rank]).astype(int)
        if col_rank
        else range(1, len(df) + 1)
    )

    base["prioridade_sinergia_davi_gabi"] = (
        df[col_prioridade].fillna("").astype(str)
        if col_prioridade
        else "A definir"
    )

    base["status_agenda_conjunta"] = (
        df[col_status].fillna("").astype(str)
        if col_status
        else "A planejar"
    )

    base["score_sinergia_davi_gabi"] = (
        converter_numero(df[col_score])
        if col_score
        else 0
    )

    base["principal_lideranca"] = (
        df[col_lideranca].fillna("").astype(str)
        if col_lideranca
        else ""
    )

    base["partido_principal_lideranca"] = (
        df[col_partido_lideranca].fillna("").astype(str)
        if col_partido_lideranca
        else ""
    )

    base["prefeito_2024"] = (
        df[col_prefeito].fillna("").astype(str)
        if col_prefeito
        else ""
    )

    base["partido_prefeito_2024"] = (
        df[col_partido_prefeito].fillna("").astype(str)
        if col_partido_prefeito
        else ""
    )

    base["meta_votos_referencia_gabi"] = (
        converter_numero(df[col_meta]).astype(int)
        if col_meta
        else 0
    )

    base["potencial_transferencia_10pct"] = (
        converter_numero(df[col_potencial]).astype(int)
        if col_potencial
        else 0
    )

    base["acao_recomendada"] = (
        df[col_acao].fillna("").astype(str)
        if col_acao
        else "Validar agenda política"
    )

    base["formato_agenda_recomendada"] = (
        df[col_formato].fillna("").astype(str)
        if col_formato
        else ""
    )

    base["justificativa_sinergia"] = (
        df[col_justificativa].fillna("").astype(str)
        if col_justificativa
        else ""
    )

    base["eleitorado"] = (
        converter_numero(df[col_eleitorado]).astype(int)
        if col_eleitorado
        else 0
    )

    base["semana_original"] = (
        df[col_semana].fillna("").astype(str)
        if col_semana
        else ""
    )

    base = base[
        (base["municipio_key"] != "")
        & (base["municipio"].astype(str).str.upper() != "NAN")
    ].copy()

    base = base.sort_values(
        by=["ranking_sinergia_davi_gabi", "score_sinergia_davi_gabi"],
        ascending=[True, False],
    ).head(TOP_ROTEIRO).reset_index(drop=True)

    base["ordem_prioridade"] = range(1, len(base) + 1)

    return base


def macro_regiao_municipio(municipio: str) -> str:
    key = normalizar_texto(municipio)

    regiao_metropolitana = {
        "MACEIO", "RIO LARGO", "SATUBA", "SANTA LUZIA DO NORTE", "COQUEIRO SECO",
        "MARECHAL DEODORO", "PILAR", "MESSIAS", "PARIPUEIRA", "BARRA DE SANTO ANTONIO",
        "BARRA DE SAO MIGUEL", "ROTEIRO"
    }

    agreste = {
        "ARAPIRACA", "GIRAU DO PONCIANO", "LAGOA DA CANOA", "FEIRA GRANDE",
        "CAMPO GRANDE", "SAO SEBASTIAO", "JUNQUEIRO", "TEOTONIO VILELA",
        "TRAIPU", "CRAIBAS", "COITE DO NOIA", "LIMOEIRO DE ANADIA",
        "TAQUARANA", "ANADIA", "BELO MONTE", "OLHO D AGUA GRANDE",
        "CAMPO ALEGRE", "SAO MIGUEL DOS CAMPOS"
    }

    serrana_que_bran = {
        "QUEBRANGULO", "PALMEIRA DOS INDIOS", "ESTRELA DE ALAGOAS",
        "MINADOR DO NEGRAO", "CACIMBINHAS", "MAR VERMELHO", "PAULO JACINTO",
        "VIÇOSA", "VICOSA", "CHÃ PRETA", "CHA PRETA", "PINDOBA",
        "IBATEGUARA", "MURICI", "UNIAO DOS PALMARES", "BRANQUINHA", "SANTANA DO MUNDAU"
    }

    zona_mata = {
        "SAO JOSE DA LAJE", "COLONIA LEOPOLDINA", "NOVO LINO", "JACUIPE",
        "JUNDIA", "CAMPESTRE", "PORTO CALVO", "MATRIZ DE CAMARAGIBE",
        "PASSO DE CAMARAGIBE", "SAO LUIS DO QUITUNDE", "JOAQUIM GOMES",
        "FLEXEIRAS", "MESSIAS", "ATALAIA", "CAPELA", "CAJUEIRO"
    }

    litoral_norte = {
        "MARAGOGI", "JAPARATINGA", "PORTO DE PEDRAS", "SAO MIGUEL DOS MILAGRES",
        "PASSO DE CAMARAGIBE", "BARRA DE SANTO ANTONIO", "PARIPUEIRA"
    }

    litoral_sul = {
        "CORURIPE", "FELIZ DESERTO", "PIACABUCU", "PENEDO", "JEQUIA DA PRAIA",
        "ROTEIRO", "BARRA DE SAO MIGUEL"
    }

    baixo_sao_francisco = {
        "PENEDO", "PIACABUCU", "PORTO REAL DO COLEGIO", "IGREJA NOVA",
        "SAO BRAS", "OLHO D AGUA GRANDE", "BELO MONTE", "TRAIPU"
    }

    sertao = {
        "SANTANA DO IPANEMA", "DELMIRO GOUVEIA", "PIRANHAS", "OLHO D AGUA DAS FLORES",
        "OLHO D AGUA DO CASADO", "AGUA BRANCA", "INHAPI", "MATA GRANDE",
        "CANAPI", "OURO BRANCO", "MARAVILHA", "POCO DAS TRINCHEIRAS",
        "POÇO DAS TRINCHEIRAS", "SAO JOSE DA TAPERA", "CARNEIROS", "SENADOR RUI PALMEIRA",
        "PÃO DE AÇÚCAR", "PAO DE ACUCAR", "MONTEIROPOLIS", "JACARE DOS HOMENS",
        "BATALHA", "MAJOR ISIDORO", "DOIS RIACHOS", "JARAMATAIA",
        "PALESTINA", "BELO MONTE"
    }

    if key in regiao_metropolitana:
        return "Região Metropolitana / Maceió"

    if key in serrana_que_bran:
        return "Eixo Serrano / Quebrangulo"

    if key in agreste:
        return "Agreste / Arapiraca"

    if key in zona_mata:
        return "Zona da Mata"

    if key in litoral_norte:
        return "Litoral Norte"

    if key in litoral_sul:
        return "Litoral Sul"

    if key in baixo_sao_francisco:
        return "Baixo São Francisco"

    if key in sertao:
        return "Sertão"

    return "Interior / Curadoria"


def eixo_logistico(regiao: str) -> str:
    if regiao == "Região Metropolitana / Maceió":
        return "Base Maceió"

    if regiao == "Eixo Serrano / Quebrangulo":
        return "Base Quebrangulo / Arapiraca"

    if regiao == "Agreste / Arapiraca":
        return "Base Arapiraca"

    if regiao == "Zona da Mata":
        return "Base Maceió ou União dos Palmares"

    if regiao == "Litoral Norte":
        return "Base Maceió / Litoral Norte"

    if regiao == "Litoral Sul":
        return "Base Maceió / Litoral Sul"

    if regiao == "Baixo São Francisco":
        return "Base Arapiraca / Penedo"

    if regiao == "Sertão":
        return "Base Arapiraca / Sertão com pernoite"

    return "Base a definir"


def observacao_logistica(regiao: str) -> str:
    if regiao == "Região Metropolitana / Maceió":
        return "Agenda de fácil execução a partir de Maceió; pode ser combinada com reuniões de gabinete, lideranças e imprensa local."

    if regiao == "Eixo Serrano / Quebrangulo":
        return "Agenda estratégica por conectar a região simbólica de Quebrangulo ao projeto territorial do Davi."

    if regiao == "Agreste / Arapiraca":
        return "Agenda com boa eficiência logística usando Arapiraca como ponto de apoio para múltiplos municípios no mesmo dia."

    if regiao == "Zona da Mata":
        return "Agenda recomendada com agrupamento de municípios próximos para reduzir deslocamento e ampliar contato com lideranças."

    if regiao == "Litoral Norte":
        return "Agenda recomendada em bloco, saindo de Maceió e concentrando visitas em sequência territorial."

    if regiao == "Litoral Sul":
        return "Agenda recomendada em bloco; avaliar combinação com Penedo, Coruripe e municípios do litoral."

    if regiao == "Baixo São Francisco":
        return "Agenda de interior com maior tempo de deslocamento; ideal montar programação com ao menos duas cidades próximas."

    if regiao == "Sertão":
        return "Agenda com recomendação de pernoite ou roteiro estendido; evitar bate-volta improdutivo."

    return "Município precisa de curadoria logística antes de confirmação de agenda."


def objetivo_politico(row: pd.Series) -> str:
    prioridade = str(row.get("prioridade_sinergia_davi_gabi", "")).strip()
    municipio = row.get("municipio", "")
    lideranca = str(row.get("principal_lideranca", "")).strip()

    if prioridade == "Muito alta":
        if lideranca:
            return f"Confirmar agenda conjunta Davi + Gabi em {municipio} com validação prévia da liderança {lideranca}."
        return f"Confirmar agenda conjunta Davi + Gabi em {municipio} e identificar liderança local de sustentação."

    if prioridade == "Alta":
        if lideranca:
            return f"Validar aderência política de {lideranca} e preparar agenda coordenada em {municipio}."
        return f"Validar lideranças locais e preparar agenda coordenada em {municipio}."

    if prioridade == "Média":
        return f"Realizar curadoria política antes de agenda pública em {municipio}."

    return f"Monitorar oportunidade de aproximação política em {municipio}."


def tipo_agenda(row: pd.Series) -> str:
    prioridade = str(row.get("prioridade_sinergia_davi_gabi", "")).strip()

    if prioridade == "Muito alta":
        return "Agenda conjunta pública + reunião com lideranças"

    if prioridade == "Alta":
        return "Visita política coordenada + curadoria local"

    if prioridade == "Média":
        return "Reunião fechada de validação política"

    return "Monitoramento político"


def preparar_roteiro(base: pd.DataFrame) -> pd.DataFrame:
    df = base.copy()

    df["macro_regiao"] = df["municipio"].apply(macro_regiao_municipio)
    df["eixo_logistico"] = df["macro_regiao"].apply(eixo_logistico)
    df["observacao_logistica"] = df["macro_regiao"].apply(observacao_logistica)

    df["semana_numero"] = df["ordem_prioridade"].apply(
        lambda ordem: min(4, ((int(ordem) - 1) // MUNICIPIOS_POR_SEMANA) + 1)
    )
    df["semana_roteiro"] = df["semana_numero"].apply(lambda s: f"Semana {s}")

    ordem_regiao = {
        "Região Metropolitana / Maceió": 1,
        "Eixo Serrano / Quebrangulo": 2,
        "Agreste / Arapiraca": 3,
        "Zona da Mata": 4,
        "Litoral Norte": 5,
        "Litoral Sul": 6,
        "Baixo São Francisco": 7,
        "Sertão": 8,
        "Interior / Curadoria": 9,
    }

    df["ordem_regiao"] = df["macro_regiao"].map(ordem_regiao).fillna(99).astype(int)

    df = df.sort_values(
        by=["semana_numero", "ordem_regiao", "ordem_prioridade", "score_sinergia_davi_gabi"],
        ascending=[True, True, True, False],
    ).reset_index(drop=True)

    dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira"]
    turnos = ["Manhã", "Tarde/Noite"]

    dia_sugerido = []
    turno_sugerido = []
    ordem_na_semana = []

    for _, grupo in df.groupby("semana_numero", sort=True):
        for posicao, indice in enumerate(grupo.index):
            dia_idx = min(posicao // 2, len(dias) - 1)
            turno_idx = posicao % 2

            dia_sugerido.append((indice, dias[dia_idx]))
            turno_sugerido.append((indice, turnos[turno_idx]))
            ordem_na_semana.append((indice, posicao + 1))

    df["dia_sugerido"] = ""
    df["turno_sugerido"] = ""
    df["ordem_na_semana"] = 0

    for indice, valor in dia_sugerido:
        df.loc[indice, "dia_sugerido"] = valor

    for indice, valor in turno_sugerido:
        df.loc[indice, "turno_sugerido"] = valor

    for indice, valor in ordem_na_semana:
        df.loc[indice, "ordem_na_semana"] = valor

    df["tipo_agenda"] = df.apply(tipo_agenda, axis=1)
    df["objetivo_politico"] = df.apply(objetivo_politico, axis=1)

    df["preparacao_previa"] = df.apply(
        lambda row: (
            f"Antes da visita, confirmar relação local com {row['principal_lideranca']}."
            if str(row.get("principal_lideranca", "")).strip()
            else "Antes da visita, definir liderança local responsável pela mobilização."
        ),
        axis=1,
    )

    df["produto_esperado"] = df.apply(
        lambda row: (
            "Apoio político validado, agenda registrada, responsável local definido e estimativa de mobilização atualizada."
            if row["prioridade_sinergia_davi_gabi"] in ["Muito alta", "Alta"]
            else "Aderência política validada e decisão sobre avançar ou monitorar."
        ),
        axis=1,
    )

    df["status_execucao"] = "A planejar"
    df["responsavel_preparacao"] = ""
    df["contato_local"] = ""
    df["data_sugerida"] = ""
    df["observacao_politica"] = ""

    ordem_colunas = [
        "ordem_prioridade",
        "semana_roteiro",
        "semana_numero",
        "ordem_na_semana",
        "dia_sugerido",
        "turno_sugerido",
        "municipio",
        "macro_regiao",
        "eixo_logistico",
        "prioridade_sinergia_davi_gabi",
        "status_agenda_conjunta",
        "score_sinergia_davi_gabi",
        "principal_lideranca",
        "partido_principal_lideranca",
        "prefeito_2024",
        "partido_prefeito_2024",
        "meta_votos_referencia_gabi",
        "potencial_transferencia_10pct",
        "tipo_agenda",
        "acao_recomendada",
        "objetivo_politico",
        "formato_agenda_recomendada",
        "justificativa_sinergia",
        "preparacao_previa",
        "observacao_logistica",
        "produto_esperado",
        "responsavel_preparacao",
        "contato_local",
        "data_sugerida",
        "status_execucao",
        "observacao_politica",
        "municipio_key",
    ]

    for coluna in ordem_colunas:
        if coluna not in df.columns:
            df[coluna] = ""

    return df[ordem_colunas]


def gerar_resumo_semanal(roteiro: pd.DataFrame) -> pd.DataFrame:
    resumo = (
        roteiro.groupby(["semana_numero", "semana_roteiro"], as_index=False)
        .agg(
            municipios=("municipio", lambda x: ", ".join(x.astype(str).tolist())),
            total_municipios=("municipio", "count"),
            regioes=("macro_regiao", lambda x: ", ".join(sorted(set(x.astype(str))))),
            meta_gabi_semana=("meta_votos_referencia_gabi", "sum"),
            potencial_transferencia_10pct=("potencial_transferencia_10pct", "sum"),
            liderancas=("principal_lideranca", lambda x: ", ".join([v for v in x.astype(str).tolist() if v.strip()])[:500]),
        )
    )

    resumo["objetivo_da_semana"] = resumo.apply(
        lambda row: (
            "Abrir agenda conjunta nos municípios de maior sinergia e validar lideranças prioritárias."
            if int(row["semana_numero"]) == 1
            else (
                "Expandir presença territorial e confirmar apoios municipais de segunda camada."
                if int(row["semana_numero"]) == 2
                else (
                    "Consolidar municípios de média prioridade e corrigir lacunas de articulação."
                    if int(row["semana_numero"]) == 3
                    else "Fechar ciclo inicial de visitas e organizar retorno aos municípios com maior resposta."
                )
            )
        ),
        axis=1,
    )

    return resumo


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


def gerar_dashboard_roteiro_json(roteiro: pd.DataFrame, resumo: pd.DataFrame) -> dict:
    return {
        "metadata": {
            "projeto": "Roteiro Territorial Davi Maia + Gabi Gonçalves",
            "versao": "sprint05_roteiro_territorial",
            "atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "status": "Roteiro territorial preliminar criado a partir do cruzamento Davi + Gabi."
        },
        "indicadores": {
            "municipios_no_roteiro": int(len(roteiro)),
            "semanas_planejadas": int(roteiro["semana_numero"].nunique()),
            "meta_gabi_roteiro": int(roteiro["meta_votos_referencia_gabi"].sum()),
            "potencial_transferencia_10pct": int(roteiro["potencial_transferencia_10pct"].sum()),
            "agendas_muito_alta": int(len(roteiro[roteiro["prioridade_sinergia_davi_gabi"] == "Muito alta"])),
            "agendas_alta": int(len(roteiro[roteiro["prioridade_sinergia_davi_gabi"] == "Alta"])),
        },
        "resumo_semanal": [
            {
                "semana": row["semana_roteiro"],
                "total_municipios": int(row["total_municipios"]),
                "municipios": row["municipios"],
                "regioes": row["regioes"],
                "meta_gabi_semana": int(row["meta_gabi_semana"]),
                "potencial_transferencia_10pct": int(row["potencial_transferencia_10pct"]),
                "objetivo": row["objetivo_da_semana"],
            }
            for _, row in resumo.iterrows()
        ],
        "roteiro": [
            {
                "ordem": int(row["ordem_prioridade"]),
                "semana": row["semana_roteiro"],
                "dia": row["dia_sugerido"],
                "turno": row["turno_sugerido"],
                "municipio": row["municipio"],
                "macro_regiao": row["macro_regiao"],
                "prioridade": row["prioridade_sinergia_davi_gabi"],
                "score": round(float(row["score_sinergia_davi_gabi"]), 2),
                "lideranca": row["principal_lideranca"],
                "prefeito": row["prefeito_2024"],
                "meta_gabi": int(row["meta_votos_referencia_gabi"]),
                "tipo_agenda": row["tipo_agenda"],
                "objetivo": row["objetivo_politico"],
                "logistica": row["observacao_logistica"],
            }
            for _, row in roteiro.iterrows()
        ]
    }


def atualizar_base_dashboard(root: Path, roteiro: pd.DataFrame, resumo: pd.DataFrame) -> None:
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
    dados["metadata"]["versao"] = "sprint05_roteiro_territorial"
    dados["metadata"]["atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    dados["metadata"]["status"] = "Roteiro territorial Davi + Gabi adicionado ao painel."

    dados.setdefault("indicadores_gabi", {})
    dados["indicadores_gabi"]["municipios_no_roteiro_davi_gabi"] = int(len(roteiro))
    dados["indicadores_gabi"]["semanas_roteiro_davi_gabi"] = int(roteiro["semana_numero"].nunique())
    dados["indicadores_gabi"]["meta_gabi_roteiro_davi_gabi"] = int(roteiro["meta_votos_referencia_gabi"].sum())
    dados["indicadores_gabi"]["status_roteiro"] = "Roteiro territorial preliminar criado para validação política."

    dados["roteiro_territorial_davi_gabi"] = [
        {
            "ordem": int(row["ordem_prioridade"]),
            "semana": row["semana_roteiro"],
            "dia": row["dia_sugerido"],
            "turno": row["turno_sugerido"],
            "municipio": row["municipio"],
            "prioridade": row["prioridade_sinergia_davi_gabi"],
            "lideranca": row["principal_lideranca"],
            "acao": row["acao_recomendada"],
        }
        for _, row in roteiro.head(20).iterrows()
    ]

    dados["resumo_semanal_roteiro"] = [
        {
            "semana": row["semana_roteiro"],
            "municipios": row["municipios"],
            "total_municipios": int(row["total_municipios"]),
            "meta_gabi_semana": int(row["meta_gabi_semana"]),
            "objetivo": row["objetivo_da_semana"],
        }
        for _, row in resumo.iterrows()
    ]

    salvar_json(caminho, dados)


def atualizar_cruzamento_json(root: Path, roteiro: pd.DataFrame, resumo: pd.DataFrame) -> None:
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
    dados["metadata"]["versao"] = "sprint05_roteiro_territorial"
    dados["metadata"]["atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    dados["metadata"]["status"] = "Roteiro territorial Davi + Gabi incorporado ao cruzamento."

    dados["roteiro_territorial"] = [
        {
            "ordem": int(row["ordem_prioridade"]),
            "semana": row["semana_roteiro"],
            "dia": row["dia_sugerido"],
            "turno": row["turno_sugerido"],
            "municipio": row["municipio"],
            "macro_regiao": row["macro_regiao"],
            "lideranca": row["principal_lideranca"],
            "tipo_agenda": row["tipo_agenda"],
            "objetivo": row["objetivo_politico"],
        }
        for _, row in roteiro.iterrows()
    ]

    dados["resumo_semanal_roteiro"] = [
        {
            "semana": row["semana_roteiro"],
            "municipios": row["municipios"],
            "regioes": row["regioes"],
            "objetivo": row["objetivo_da_semana"],
        }
        for _, row in resumo.iterrows()
    ]

    salvar_json(caminho, dados)


def gerar_briefing_sprint05(roteiro: pd.DataFrame, resumo: pd.DataFrame) -> str:
    top5 = roteiro.head(5)

    linhas = [
        "# Briefing — Sprint 05 — Roteiro Territorial Davi Maia + Gabi Gonçalves",
        "",
        "## Objetivo",
        "",
        "Transformar o cruzamento Davi + Gabi em um roteiro semanal de visitas e validação política.",
        "",
        "## Resultado geral",
        "",
        f"- Municípios no roteiro: {len(roteiro)}",
        f"- Semanas planejadas: {roteiro['semana_numero'].nunique()}",
        f"- Meta de referência Gabi no roteiro: {int(roteiro['meta_votos_referencia_gabi'].sum())}",
        f"- Potencial de transferência em cenário 10%: {int(roteiro['potencial_transferencia_10pct'].sum())}",
        "",
        "## Top 5 agendas iniciais",
        "",
    ]

    for _, row in top5.iterrows():
        linhas.append(
            f"- {int(row['ordem_prioridade'])}. {row['municipio']} — "
            f"{row['semana_roteiro']} — {row['dia_sugerido']} — "
            f"{row['prioridade_sinergia_davi_gabi']} — {row['principal_lideranca']}"
        )

    linhas.extend(
        [
            "",
            "## Arquivos gerados",
            "",
            "- data/final/parceiros/gabi-goncalves/roteiro_territorial_davi_gabi_v1.csv",
            "- data/final/parceiros/gabi-goncalves/roteiro_territorial_davi_gabi_v1.xlsx",
            "- data/reference/parceiros/gabi-goncalves/plano_semanal_roteiro_davi_gabi_v1.csv",
            "- data/dashboard/parceiros/gabi-goncalves/roteiro_territorial_davi_gabi_v1.json",
            "- docs/briefing_gabi_sprint05.md",
            "",
            "## Próximo sprint recomendado",
            "",
            "Sprint 06 — Curadoria Política.",
            "",
            "O próximo passo é preencher relação real com Gabi, Davi, Renan Filho, Paulo Dantas, prefeitos, vereadores e lideranças locais antes de consolidar agendas públicas.",
        ]
    )

    return "\n".join(linhas) + "\n"


def criar_roteiro_js() -> str:
    return r'''const ROTEIRO_PATH = "../../data/dashboard/parceiros/gabi-goncalves/roteiro_territorial_davi_gabi_v1.json";

function formatarNumeroRoteiro(valor) {
  if (valor === null || valor === undefined || valor === "") {
    return "-";
  }

  const numero = Number(valor);

  if (Number.isNaN(numero)) {
    return String(valor);
  }

  return numero.toLocaleString("pt-BR");
}

async function carregarRoteiro() {
  try {
    const resposta = await fetch(ROTEIRO_PATH, { cache: "no-store" });

    if (!resposta.ok) {
      throw new Error(`Erro ao carregar roteiro: ${resposta.status}`);
    }

    return await resposta.json();
  } catch (erro) {
    console.warn(erro.message);
    return null;
  }
}

function renderResumoRoteiro(dados) {
  const grid = document.getElementById("roteiroResumoGrid");

  if (!grid || !dados) {
    return;
  }

  const indicadores = dados.indicadores || {};

  const cards = [
    {
      rotulo: "Municípios no roteiro",
      valor: indicadores.municipios_no_roteiro,
      detalhe: "Agenda territorial preliminar"
    },
    {
      rotulo: "Semanas planejadas",
      valor: indicadores.semanas_planejadas,
      detalhe: "Ciclo inicial de visitas"
    },
    {
      rotulo: "Meta Gabi no roteiro",
      valor: indicadores.meta_gabi_roteiro,
      detalhe: "Votos de referência"
    },
    {
      rotulo: "Potencial 10%",
      valor: indicadores.potencial_transferencia_10pct,
      detalhe: "Conversão preliminar"
    }
  ];

  grid.innerHTML = cards.map((card) => `
    <article class="roteiro-mini-card">
      <span>${card.rotulo}</span>
      <strong>${formatarNumeroRoteiro(card.valor)}</strong>
      <small>${card.detalhe}</small>
    </article>
  `).join("");
}

function renderSemanasRoteiro(dados) {
  const grid = document.getElementById("roteiroSemanasGrid");

  if (!grid || !dados) {
    return;
  }

  const semanas = dados.resumo_semanal || [];

  if (!semanas.length) {
    grid.innerHTML = `
      <article class="roteiro-empty">
        Roteiro semanal ainda não foi calculado.
      </article>
    `;
    return;
  }

  grid.innerHTML = semanas.map((semana) => `
    <article class="semana-card">
      <strong>${semana.semana}</strong>
      <h3>${semana.total_municipios} município(s)</h3>
      <p>${semana.municipios}</p>
      <small>${semana.objetivo}</small>
    </article>
  `).join("");
}

function renderTabelaRoteiro(dados) {
  const tbody = document.getElementById("roteiroTableBody");

  if (!tbody || !dados) {
    return;
  }

  const roteiro = dados.roteiro || [];

  if (!roteiro.length) {
    tbody.innerHTML = `
      <tr class="empty-row">
        <td colspan="7">Roteiro territorial ainda não disponível.</td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = roteiro.slice(0, 20).map((item) => `
    <tr>
      <td>${item.ordem}</td>
      <td>${item.semana}<br><small>${item.dia} · ${item.turno}</small></td>
      <td>${item.municipio}</td>
      <td>${item.prioridade}</td>
      <td>${item.lideranca || "-"}</td>
      <td>${formatarNumeroRoteiro(item.meta_gabi)}</td>
      <td>${item.tipo_agenda}</td>
    </tr>
  `).join("");
}

async function inicializarRoteiro() {
  const dados = await carregarRoteiro();

  renderResumoRoteiro(dados);
  renderSemanasRoteiro(dados);
  renderTabelaRoteiro(dados);
}

document.addEventListener("DOMContentLoaded", inicializarRoteiro);
'''


def atualizar_painel(root: Path) -> None:
    painel_dir = root / "parceiros" / "gabi-goncalves"
    index_path = painel_dir / "index.html"
    css_path = painel_dir / "styles.css"
    roteiro_js_path = painel_dir / "roteiro.js"

    if not index_path.exists():
        print(f"[AVISO] index.html não encontrado: {index_path}")
        return

    html = index_path.read_text(encoding="utf-8")

    if 'href="#roteiro-territorial"' not in html:
        html = html.replace(
            '<a href="#cruzamento">Davi x Gabi</a>',
            '<a href="#cruzamento">Davi x Gabi</a>\n                  <a href="#roteiro-territorial">Roteiro</a>',
        )

    secao_roteiro = '''      <section class="section roteiro-section" id="roteiro-territorial">
        <div class="section-header">
          <p class="eyebrow">Roteiro territorial</p>
          <h2>Roteiro Davi Maia + Gabi Gonçalves</h2>
          <p>
            Agenda territorial preliminar construída a partir do cruzamento entre prioridade eleitoral,
            rede de lideranças e sinergia política da parceria Davi + Gabi.
          </p>
        </div>

        <div class="roteiro-mini-grid" id="roteiroResumoGrid"></div>

        <div class="roteiro-semanas-grid" id="roteiroSemanasGrid"></div>

        <div class="panel-card roteiro-table-card">
          <div class="panel-header">
            <div>
              <p class="eyebrow">Agenda operacional</p>
              <h2>Primeiras visitas recomendadas</h2>
            </div>
            <span class="status-pill">Sprint 05</span>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Ordem</th>
                  <th>Semana</th>
                  <th>Município</th>
                  <th>Prioridade</th>
                  <th>Liderança</th>
                  <th>Meta Gabi</th>
                  <th>Tipo de agenda</th>
                </tr>
              </thead>
              <tbody id="roteiroTableBody"></tbody>
            </table>
          </div>
        </div>
      </section>
'''

    if 'id="roteiro-territorial"' not in html:
        alvo = '      <section class="section roadmap" id="proximos-passos">'
        if alvo in html:
            html = html.replace(alvo, secao_roteiro + "\n" + alvo)
        else:
            html = html.replace("</main>", secao_roteiro + "\n    </main>")

    if 'src="roteiro.js"' not in html:
        html = html.replace(
            '<script src="app.js"></script>',
            '<script src="app.js"></script>\n  <script src="roteiro.js"></script>',
        )

    index_path.write_text(html, encoding="utf-8")
    print(f"[OK] Painel HTML atualizado com seção de roteiro: {index_path}")

    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

    marcador_inicio = "/* ===== SPRINT05_ROTEIRO_INICIO ===== */"
    marcador_fim = "/* ===== SPRINT05_ROTEIRO_FIM ===== */"

    bloco_css = f'''
{marcador_inicio}

.roteiro-section {{
  background:
    radial-gradient(circle at top left, rgba(241, 210, 20, .10), transparent 28%),
    linear-gradient(180deg, rgba(255,255,255,.96), rgba(234,240,255,.88));
}}

.roteiro-mini-grid {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}}

.roteiro-mini-card {{
  padding: 18px;
  border-radius: 20px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, .94);
  box-shadow: 0 14px 34px rgba(11, 31, 77, .08);
}}

.roteiro-mini-card span {{
  display: block;
  color: var(--muted);
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: .08em;
}}

.roteiro-mini-card strong {{
  display: block;
  margin-top: 8px;
  color: var(--blue-700);
  font-size: 28px;
  line-height: 1;
  letter-spacing: -0.05em;
}}

.roteiro-mini-card small {{
  display: block;
  margin-top: 8px;
  color: var(--muted);
}}

.roteiro-semanas-grid {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}}

.semana-card {{
  padding: 20px;
  border-radius: 22px;
  border: 1px solid var(--line);
  background: #ffffff;
  box-shadow: 0 14px 34px rgba(11, 31, 77, .08);
  border-top: 5px solid var(--yellow-500);
}}

.semana-card strong {{
  display: inline-block;
  margin-bottom: 10px;
  color: var(--pink-600);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .08em;
  text-transform: uppercase;
}}

.semana-card h3 {{
  margin: 0;
  color: var(--blue-900);
  font-size: 20px;
  letter-spacing: -0.04em;
}}

.semana-card p {{
  margin: 10px 0;
  color: var(--muted);
  line-height: 1.48;
}}

.semana-card small {{
  color: var(--blue-700);
  font-weight: 700;
  line-height: 1.45;
}}

.roteiro-table-card {{
  margin-top: 18px;
}}

.roteiro-table-card td small {{
  color: var(--muted);
  font-weight: 700;
}}

.roteiro-empty {{
  grid-column: 1 / -1;
  padding: 22px;
  border-radius: 22px;
  background: #ffffff;
  border: 1px solid var(--line);
  color: var(--muted);
}}

@media (max-width: 980px) {{
  .roteiro-mini-grid,
  .roteiro-semanas-grid {{
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }}
}}

@media (max-width: 680px) {{
  .roteiro-mini-grid,
  .roteiro-semanas-grid {{
    grid-template-columns: 1fr;
  }}
}}

{marcador_fim}
'''

    padrao = rf"{re.escape(marcador_inicio)}.*?{re.escape(marcador_fim)}"

    if re.search(padrao, css, flags=re.DOTALL):
        css = re.sub(padrao, bloco_css.strip(), css, flags=re.DOTALL)
    else:
        css = css.rstrip() + "\n\n" + bloco_css.strip() + "\n"

    css_path.write_text(css, encoding="utf-8")
    print(f"[OK] CSS atualizado com estilos do roteiro: {css_path}")

    roteiro_js_path.write_text(criar_roteiro_js(), encoding="utf-8")
    print(f"[OK] roteiro.js criado/atualizado: {roteiro_js_path}")


def salvar_resultados(root: Path, roteiro: pd.DataFrame, resumo: pd.DataFrame) -> None:
    final_dir = root / "data" / "final" / "parceiros" / "gabi-goncalves"
    reference_dir = root / "data" / "reference" / "parceiros" / "gabi-goncalves"
    dashboard_dir = root / "data" / "dashboard" / "parceiros" / "gabi-goncalves"
    docs_dir = root / "docs"

    final_dir.mkdir(parents=True, exist_ok=True)
    reference_dir.mkdir(parents=True, exist_ok=True)
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    roteiro_csv = final_dir / "roteiro_territorial_davi_gabi_v1.csv"
    roteiro_xlsx = final_dir / "roteiro_territorial_davi_gabi_v1.xlsx"
    resumo_csv = reference_dir / "plano_semanal_roteiro_davi_gabi_v1.csv"
    roteiro_json = dashboard_dir / "roteiro_territorial_davi_gabi_v1.json"
    briefing_md = docs_dir / "briefing_gabi_sprint05.md"

    roteiro.to_csv(roteiro_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Roteiro territorial salvo: {roteiro_csv}")

    resumo.to_csv(resumo_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Plano semanal salvo: {resumo_csv}")

    try:
        with pd.ExcelWriter(roteiro_xlsx) as writer:
            roteiro.to_excel(writer, sheet_name="roteiro_territorial", index=False)
            resumo.to_excel(writer, sheet_name="plano_semanal", index=False)

        print(f"[OK] XLSX consolidado salvo: {roteiro_xlsx}")
    except Exception as erro:
        print(f"[AVISO] Não foi possível salvar XLSX. CSVs foram gerados normalmente. Erro: {erro}")

    roteiro_json.write_text(
        json.dumps(gerar_dashboard_roteiro_json(roteiro, resumo), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] JSON do roteiro salvo: {roteiro_json}")

    briefing_md.write_text(gerar_briefing_sprint05(roteiro, resumo), encoding="utf-8")
    print(f"[OK] Briefing salvo: {briefing_md}")


def imprimir_resumo(roteiro: pd.DataFrame, resumo: pd.DataFrame) -> None:
    print("")
    print("============================================================")
    print("RESUMO DO SPRINT 05")
    print("============================================================")
    print(f"Municípios no roteiro: {len(roteiro)}")
    print(f"Semanas planejadas: {roteiro['semana_numero'].nunique()}")
    print(f"Meta Gabi no roteiro: {int(roteiro['meta_votos_referencia_gabi'].sum()):,}".replace(",", "."))
    print(f"Potencial transferência 10%: {int(roteiro['potencial_transferencia_10pct'].sum()):,}".replace(",", "."))
    print("")
    print("TOP 15 do roteiro:")
    print("------------------------------------------------------------")

    colunas = [
        "ordem_prioridade",
        "semana_roteiro",
        "dia_sugerido",
        "turno_sugerido",
        "municipio",
        "prioridade_sinergia_davi_gabi",
        "principal_lideranca",
        "tipo_agenda",
    ]

    print(roteiro[colunas].head(15).to_string(index=False))

    print("")
    print("Resumo semanal:")
    print("------------------------------------------------------------")

    print(
        resumo[
            [
                "semana_roteiro",
                "total_municipios",
                "municipios",
                "meta_gabi_semana",
            ]
        ].to_string(index=False)
    )
    print("============================================================")


def main() -> None:
    root = detectar_raiz_projeto()

    print("============================================================")
    print("SPRINT 05 — ROTEIRO TERRITORIAL DAVI MAIA + GABI GONÇALVES")
    print("============================================================")
    print(f"[INFO] Raiz detectada: {root}")

    base = carregar_cruzamento_ou_agenda(root)
    roteiro = preparar_roteiro(base)
    resumo = gerar_resumo_semanal(roteiro)

    salvar_resultados(root, roteiro, resumo)
    atualizar_base_dashboard(root, roteiro, resumo)
    atualizar_cruzamento_json(root, roteiro, resumo)
    atualizar_painel(root)

    imprimir_resumo(roteiro, resumo)

    print("")
    print("SPRINT 05 CONCLUÍDO.")
    print("")
    print("Agora teste o painel:")
    print("  cd C:\\Users\\user\\Documents\\Workspace\\campanha_2026\\alagoas-political-intelligence")
    print("  python -m http.server 8000")
    print("")
    print("Abra:")
    print("  http://localhost:8000/parceiros/gabi-goncalves/")
    print("")
    print("Depois use Ctrl + F5 para atualizar os arquivos no navegador.")


if __name__ == "__main__":
    main()