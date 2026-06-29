import os
import re
import json
import math
import unicodedata
from datetime import datetime

import pandas as pd


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

ARQUIVO_PARCEIROS = os.path.join(
    BASE_DIR,
    "data",
    "reference",
    "parceiros_davi_2026.csv",
)

DIR_FINAL_PARCEIROS = os.path.join(
    BASE_DIR,
    "data",
    "final",
    "parceiros",
)

DIR_DASHBOARD_PARCEIROS = os.path.join(
    BASE_DIR,
    "data",
    "dashboard",
    "parceiros",
)

ARQUIVO_CONSOLIDADO_FINAL = os.path.join(
    DIR_FINAL_PARCEIROS,
    "consolidado_parceiros_territorial.csv",
)

ARQUIVO_CONSOLIDADO_DASHBOARD = os.path.join(
    DIR_DASHBOARD_PARCEIROS,
    "consolidado_parceiros_territorial.json",
)

os.makedirs(DIR_FINAL_PARCEIROS, exist_ok=True)
os.makedirs(DIR_DASHBOARD_PARCEIROS, exist_ok=True)


# ============================================================
# FUNÇÕES GERAIS
# ============================================================

def normalizar_texto(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto)

    return texto


def slugify(valor):
    texto = normalizar_texto(valor).lower()
    texto = texto.replace(" ", "-")
    texto = re.sub(r"[^a-z0-9\-]", "", texto)
    texto = re.sub(r"-+", "-", texto).strip("-")

    return texto or "parceiro-sem-id"


def resolver_caminho(caminho):
    if pd.isna(caminho) or str(caminho).strip() == "":
        return ""

    caminho = str(caminho).strip()

    if os.path.isabs(caminho):
        return caminho

    return os.path.join(BASE_DIR, caminho)


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


def ler_csv_generico(caminho, dtype=str):
    encoding = detectar_encoding(caminho)
    sep = detectar_sep(caminho, encoding)

    return pd.read_csv(
        caminho,
        sep=sep,
        encoding=encoding,
        dtype=dtype,
        low_memory=False,
        on_bad_lines="skip",
    )


def converter_int(valor):
    try:
        if pd.isna(valor):
            return 0

        texto = str(valor).strip().replace(".", "").replace(",", ".")

        if texto == "":
            return 0

        return int(float(texto))
    except Exception:
        return 0


def converter_float(valor):
    try:
        if pd.isna(valor):
            return 0.0

        texto = str(valor).strip().replace(".", "").replace(",", ".")

        if texto == "":
            return 0.0

        return float(texto)
    except Exception:
        return 0.0


def limpar_valor_json(valor):
    if isinstance(valor, dict):
        return {k: limpar_valor_json(v) for k, v in valor.items()}

    if isinstance(valor, list):
        return [limpar_valor_json(v) for v in valor]

    if isinstance(valor, float):
        if math.isnan(valor) or math.isinf(valor):
            return None
        return valor

    if pd.isna(valor) if not isinstance(valor, (str, int, float, bool, dict, list, type(None))) else False:
        return None

    return valor


def extrair_regiao_estimada(endereco):
    texto_original = "" if pd.isna(endereco) else str(endereco).strip()
    texto = normalizar_texto(texto_original)

    if not texto:
        return "NÃO INFORMADO"

    padroes = [
        r"BAIRRO[:\s]+([A-Z0-9\s\-']+)",
        r"POVOADO[:\s]+([A-Z0-9\s\-']+)",
        r"DISTRITO[:\s]+([A-Z0-9\s\-']+)",
        r"CONJUNTO[:\s]+([A-Z0-9\s\-']+)",
        r"RESIDENCIAL[:\s]+([A-Z0-9\s\-']+)",
        r"VILA[:\s]+([A-Z0-9\s\-']+)",
        r"SITIO[:\s]+([A-Z0-9\s\-']+)",
        r"SÍTIO[:\s]+([A-Z0-9\s\-']+)",
    ]

    for padrao in padroes:
        match = re.search(padrao, texto)

        if match:
            regiao = match.group(1).strip()
            regiao = re.split(r"[,.;/]", regiao)[0].strip()
            return regiao[:80] if regiao else "NÃO INFORMADO"

    partes = [p.strip() for p in re.split(r"[,;/]", texto) if p.strip()]

    if len(partes) >= 2:
        candidato = partes[-1]
        candidato = re.sub(
            r"\bN\b|\bNO\b|\bNUMERO\b|\bS N\b|\bSN\b|\bS/N\b",
            "",
            candidato,
        ).strip()

        if len(candidato) >= 3:
            return candidato[:80]

    return "NÃO INFORMADO"


def classificar_forca_reduto(percentual_parceiro, votos_parceiro):
    if votos_parceiro >= 500 or percentual_parceiro >= 8:
        return "NÚCLEO FORTE"

    if votos_parceiro >= 250 or percentual_parceiro >= 4:
        return "ÁREA RELEVANTE"

    if votos_parceiro >= 100 or percentual_parceiro >= 1.5:
        return "ÁREA COMPLEMENTAR"

    return "BAIXA PRESENÇA"


def selecionar_coluna(df, possibilidades):
    colunas_norm = {normalizar_texto(col): col for col in df.columns}

    for possibilidade in possibilidades:
        possibilidade_norm = normalizar_texto(possibilidade)

        if possibilidade_norm in colunas_norm:
            return colunas_norm[possibilidade_norm]

    return ""


# ============================================================
# FUNÇÕES DE CANDIDATO/PARCEIRO
# ============================================================

def carregar_parceiros():
    if not os.path.exists(ARQUIVO_PARCEIROS):
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_PARCEIROS}")

    df = ler_csv_generico(ARQUIVO_PARCEIROS)

    if "id_parceiro" not in df.columns:
        raise ValueError("A coluna obrigatória 'id_parceiro' não existe em parceiros_davi_2026.csv.")

    if "nome_parceiro" not in df.columns:
        raise ValueError("A coluna obrigatória 'nome_parceiro' não existe em parceiros_davi_2026.csv.")

    if "incluir_no_dashboard" not in df.columns:
        df["incluir_no_dashboard"] = "SIM"

    df["incluir_no_dashboard_norm"] = df["incluir_no_dashboard"].apply(normalizar_texto)

    df = df[df["incluir_no_dashboard_norm"].isin(["SIM", "S", "YES", "TRUE", "1"])].copy()

    return df


def validar_colunas_tse(df_tse):
    obrigatorias = [
        "ANO_ELEICAO",
        "SG_UF",
        "NM_MUNICIPIO",
        "NR_ZONA",
        "NR_SECAO",
        "DS_CARGO",
        "NR_VOTAVEL",
        "NM_VOTAVEL",
        "QT_VOTOS",
        "NR_LOCAL_VOTACAO",
        "SQ_CANDIDATO",
        "NM_LOCAL_VOTACAO",
        "DS_LOCAL_VOTACAO_ENDERECO",
    ]

    faltantes = [col for col in obrigatorias if col not in df_tse.columns]

    if faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes no arquivo TSE: {faltantes}")


def filtrar_cargo(df_tse, cargo_disputado):
    if not cargo_disputado or str(cargo_disputado).strip() == "":
        return df_tse.copy()

    cargo_norm = normalizar_texto(cargo_disputado)

    df = df_tse.copy()
    df["DS_CARGO_NORMALIZADO"] = df["DS_CARGO"].apply(normalizar_texto)

    filtrado = df[df["DS_CARGO_NORMALIZADO"] == cargo_norm].copy()

    if filtrado.empty:
        filtrado = df[df["DS_CARGO_NORMALIZADO"].str.contains(cargo_norm, na=False)].copy()

    return filtrado


def montar_tokens_busca(parceiro):
    nome_urna = parceiro.get("nome_urna_2022", "")
    nome_parceiro = parceiro.get("nome_parceiro", "")

    base = nome_urna if str(nome_urna).strip() else nome_parceiro
    base_norm = normalizar_texto(base)

    stopwords = {
        "DE",
        "DA",
        "DAS",
        "DO",
        "DOS",
        "E",
        "A",
        "O",
        "PARA",
    }

    tokens = [
        token
        for token in re.split(r"\s+", base_norm)
        if token and token not in stopwords and len(token) >= 3
    ]

    return base_norm, tokens


def auditar_candidatos_possiveis(df_cargo, parceiro):
    nome_alvo_norm, tokens = montar_tokens_busca(parceiro)

    df = df_cargo.copy()
    df["NM_VOTAVEL_NORMALIZADO"] = df["NM_VOTAVEL"].apply(normalizar_texto)
    df["QT_VOTOS_NUM"] = df["QT_VOTOS"].apply(converter_int)

    if not tokens:
        return pd.DataFrame()

    mascara = pd.Series(False, index=df.index)

    # Regra 1: nome exato.
    if nome_alvo_norm:
        mascara = mascara | (df["NM_VOTAVEL_NORMALIZADO"] == nome_alvo_norm)

    # Regra 2: todos os tokens principais aparecem no nome.
    mascara_todos_tokens = pd.Series(True, index=df.index)

    for token in tokens:
        mascara_todos_tokens = mascara_todos_tokens & df["NM_VOTAVEL_NORMALIZADO"].str.contains(token, na=False)

    mascara = mascara | mascara_todos_tokens

    # Regra 3: pelo menos um token forte aparece.
    tokens_fortes = [token for token in tokens if len(token) >= 4]

    mascara_algum_token = pd.Series(False, index=df.index)

    for token in tokens_fortes:
        mascara_algum_token = mascara_algum_token | df["NM_VOTAVEL_NORMALIZADO"].str.contains(token, na=False)

    mascara = mascara | mascara_algum_token

    encontrados = df[mascara].copy()

    if encontrados.empty:
        return pd.DataFrame()

    resumo = (
        encontrados
        .groupby(
            [
                "SQ_CANDIDATO",
                "NR_VOTAVEL",
                "NM_VOTAVEL",
                "DS_CARGO",
                "NM_MUNICIPIO",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            votos_total=("QT_VOTOS_NUM", "sum"),
            secoes=("NR_SECAO", "nunique"),
            locais_votacao=("NR_LOCAL_VOTACAO", "nunique"),
        )
    )

    resumo["nome_alvo"] = nome_alvo_norm
    resumo["tokens_busca"] = " | ".join(tokens)
    resumo["NM_VOTAVEL_NORMALIZADO"] = resumo["NM_VOTAVEL"].apply(normalizar_texto)

    resumo = resumo.sort_values(
        by=["votos_total", "locais_votacao", "secoes"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    return resumo


def escolher_candidato(df_candidatos, parceiro):
    if df_candidatos.empty:
        return None, "nenhum_candidato_encontrado"

    df = df_candidatos.copy()

    nome_alvo_norm, tokens = montar_tokens_busca(parceiro)
    nome_urna_norm = normalizar_texto(parceiro.get("nome_urna_2022", ""))
    nome_parceiro_norm = normalizar_texto(parceiro.get("nome_parceiro", ""))

    # Campos opcionais, caso a tabela de referência seja enriquecida no futuro.
    filtro_sq = str(parceiro.get("sq_candidato_2022", "")).strip()
    filtro_numero = str(parceiro.get("numero_2022", "")).strip()

    if filtro_sq:
        filtrado = df[df["SQ_CANDIDATO"].astype(str).str.strip() == filtro_sq]

        if not filtrado.empty:
            return filtrado.sort_values(by="votos_total", ascending=False).iloc[0].to_dict(), "sq_candidato_2022"

    if filtro_numero:
        filtrado = df[df["NR_VOTAVEL"].astype(str).str.strip() == filtro_numero]

        if not filtrado.empty:
            return filtrado.sort_values(by="votos_total", ascending=False).iloc[0].to_dict(), "numero_2022"

    if nome_urna_norm:
        filtrado = df[df["NM_VOTAVEL_NORMALIZADO"] == nome_urna_norm]

        if not filtrado.empty:
            return filtrado.sort_values(by="votos_total", ascending=False).iloc[0].to_dict(), "nome_urna_exato"

    if nome_parceiro_norm:
        filtrado = df[df["NM_VOTAVEL_NORMALIZADO"] == nome_parceiro_norm]

        if not filtrado.empty:
            return filtrado.sort_values(by="votos_total", ascending=False).iloc[0].to_dict(), "nome_parceiro_exato"

    # Todos os tokens principais.
    if tokens:
        mascara = pd.Series(True, index=df.index)

        for token in tokens:
            mascara = mascara & df["NM_VOTAVEL_NORMALIZADO"].str.contains(token, na=False)

        filtrado = df[mascara].copy()

        if not filtrado.empty:
            return filtrado.sort_values(by="votos_total", ascending=False).iloc[0].to_dict(), "todos_tokens"

    # Fallback: maior votação entre possíveis.
    return df.sort_values(by="votos_total", ascending=False).iloc[0].to_dict(), "maior_votacao_possivel"


def filtrar_votacao_candidato(df_cargo, candidato):
    if candidato is None:
        return pd.DataFrame()

    sq = str(candidato.get("SQ_CANDIDATO", "")).strip()
    nr = str(candidato.get("NR_VOTAVEL", "")).strip()
    nome_norm = normalizar_texto(candidato.get("NM_VOTAVEL", ""))

    df = df_cargo.copy()
    df["NM_VOTAVEL_NORMALIZADO"] = df["NM_VOTAVEL"].apply(normalizar_texto)

    if sq:
        return df[df["SQ_CANDIDATO"].astype(str).str.strip() == sq].copy()

    if nr:
        return df[df["NR_VOTAVEL"].astype(str).str.strip() == nr].copy()

    if nome_norm:
        return df[df["NM_VOTAVEL_NORMALIZADO"] == nome_norm].copy()

    return pd.DataFrame()


# ============================================================
# AGREGAÇÕES TERRITORIAIS
# ============================================================

def gerar_agregacoes(df_votacao):
    df = df_votacao.copy()

    df["QT_VOTOS_NUM"] = df["QT_VOTOS"].apply(converter_int)
    df["municipio"] = df["NM_MUNICIPIO"].astype(str).str.upper().str.strip()
    df["local_votacao"] = df["NM_LOCAL_VOTACAO"].fillna("").astype(str).str.upper().str.strip()
    df["endereco_local_votacao"] = df["DS_LOCAL_VOTACAO_ENDERECO"].fillna("").astype(str).str.upper().str.strip()
    df["regiao_estimada"] = df["endereco_local_votacao"].apply(extrair_regiao_estimada)

    total_votos = int(df["QT_VOTOS_NUM"].sum())

    secao = df.copy()

    secao = secao.rename(
        columns={
            "NM_MUNICIPIO": "municipio_original",
            "NR_ZONA": "zona",
            "NR_SECAO": "secao",
            "NR_LOCAL_VOTACAO": "numero_local_votacao",
            "NM_LOCAL_VOTACAO": "nome_local_votacao",
            "DS_LOCAL_VOTACAO_ENDERECO": "endereco",
            "QT_VOTOS": "votos_parceiro",
        }
    )

    colunas_secao = [
        "ANO_ELEICAO",
        "SG_UF",
        "CD_MUNICIPIO",
        "municipio_original",
        "zona",
        "secao",
        "numero_local_votacao",
        "nome_local_votacao",
        "endereco",
        "regiao_estimada",
        "DS_CARGO",
        "NR_VOTAVEL",
        "NM_VOTAVEL",
        "SQ_CANDIDATO",
        "votos_parceiro",
    ]

    colunas_secao = [col for col in colunas_secao if col in secao.columns]
    secao = secao[colunas_secao].copy()
    secao["votos_parceiro"] = secao["votos_parceiro"].apply(converter_int)

    local = (
        df
        .groupby(
            [
                "municipio",
                "NR_ZONA",
                "NR_LOCAL_VOTACAO",
                "local_votacao",
                "endereco_local_votacao",
                "regiao_estimada",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            votos_parceiro=("QT_VOTOS_NUM", "sum"),
            secoes_com_voto=("NR_SECAO", "nunique"),
        )
    )

    local["percentual_votos_parceiro"] = (
        local["votos_parceiro"] / total_votos * 100
    ).round(4) if total_votos else 0

    local["forca_reduto"] = local.apply(
        lambda row: classificar_forca_reduto(
            row["percentual_votos_parceiro"],
            row["votos_parceiro"],
        ),
        axis=1,
    )

    local = local.sort_values(
        by=["votos_parceiro", "percentual_votos_parceiro"],
        ascending=[False, False],
    ).reset_index(drop=True)

    local["ranking_local_parceiro"] = local.index + 1

    regiao = (
        df
        .groupby(
            [
                "municipio",
                "regiao_estimada",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            votos_parceiro=("QT_VOTOS_NUM", "sum"),
            locais_votacao=("NR_LOCAL_VOTACAO", "nunique"),
            secoes_com_voto=("NR_SECAO", "nunique"),
        )
    )

    regiao["percentual_votos_parceiro"] = (
        regiao["votos_parceiro"] / total_votos * 100
    ).round(4) if total_votos else 0

    regiao["forca_reduto"] = regiao.apply(
        lambda row: classificar_forca_reduto(
            row["percentual_votos_parceiro"],
            row["votos_parceiro"],
        ),
        axis=1,
    )

    regiao = regiao.sort_values(
        by=["votos_parceiro", "percentual_votos_parceiro"],
        ascending=[False, False],
    ).reset_index(drop=True)

    regiao["ranking_regiao_parceiro"] = regiao.index + 1

    municipio = (
        df
        .groupby(
            ["municipio"],
            dropna=False,
            as_index=False,
        )
        .agg(
            votos_parceiro=("QT_VOTOS_NUM", "sum"),
            locais_votacao=("NR_LOCAL_VOTACAO", "nunique"),
            secoes_com_voto=("NR_SECAO", "nunique"),
            regioes_estimadas=("regiao_estimada", "nunique"),
        )
    )

    municipio["percentual_votos_parceiro"] = (
        municipio["votos_parceiro"] / total_votos * 100
    ).round(4) if total_votos else 0

    municipio = municipio.sort_values(
        by=["votos_parceiro", "percentual_votos_parceiro"],
        ascending=[False, False],
    ).reset_index(drop=True)

    municipio["ranking_municipio_parceiro"] = municipio.index + 1

    return secao, local, regiao, municipio


def gerar_json_parceiro(parceiro, candidato, metodo_selecao, secao, local, regiao, municipio):
    total_votos = int(secao["votos_parceiro"].sum()) if not secao.empty else 0

    id_parceiro = str(parceiro.get("id_parceiro", "")).strip()
    nome_parceiro = str(parceiro.get("nome_parceiro", "")).strip()

    dados = {
        "metadata": {
            "titulo": f"Atuação Territorial de Parceiros — {nome_parceiro}",
            "id_parceiro": id_parceiro,
            "versao": "v1",
            "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fonte": "TSE — votação por seção eleitoral",
            "observacao_metodologica": (
                "A base oficial informa votos por seção, local de votação e endereço. "
                "Bairro/região é estimativa operacional derivada do endereço do local de votação. "
                "Este arquivo mede força territorial do parceiro, não previsão de transferência de votos."
            ),
        },
        "parceiro": {
            "id_parceiro": id_parceiro,
            "nome_parceiro": nome_parceiro,
            "nome_urna_2022": str(parceiro.get("nome_urna_2022", "")),
            "cargo_atual": str(parceiro.get("cargo_atual", "")),
            "cargo_disputado_2022": str(parceiro.get("cargo_disputado_2022", "")),
            "ano_base_eleitoral": str(parceiro.get("ano_base_eleitoral", "")),
            "uf_base_eleitoral": str(parceiro.get("uf_base_eleitoral", "")),
            "partido_2022": str(parceiro.get("partido_2022", "")),
            "partido_atual": str(parceiro.get("partido_atual", "")),
            "grupo_politico": str(parceiro.get("grupo_politico", "")),
            "relacao_com_davi": str(parceiro.get("relacao_com_davi", "")),
            "status_parceria": str(parceiro.get("status_parceria", "")),
            "prioridade_politica": str(parceiro.get("prioridade_politica", "")),
            "tipo_de_utilidade": str(parceiro.get("tipo_de_utilidade", "")),
        },
        "candidato_identificado": {
            "metodo_selecao": metodo_selecao,
            "sq_candidato": str(candidato.get("SQ_CANDIDATO", "")),
            "numero": str(candidato.get("NR_VOTAVEL", "")),
            "nome_votavel": str(candidato.get("NM_VOTAVEL", "")),
            "cargo": str(candidato.get("DS_CARGO", "")),
            "municipio_referencia_tse": str(candidato.get("NM_MUNICIPIO", "")),
            "votos_total_auditoria": int(candidato.get("votos_total", 0)),
        },
        "resumo": {
            "total_votos_parceiro": total_votos,
            "municipios_com_votos": int(municipio["municipio"].nunique()) if not municipio.empty else 0,
            "locais_votacao_com_votos": int(local["NR_LOCAL_VOTACAO"].nunique()) if not local.empty else 0,
            "secoes_com_votos": int(secao["secao"].nunique()) if not secao.empty and "secao" in secao.columns else 0,
            "regioes_estimadas": int(regiao["regiao_estimada"].nunique()) if not regiao.empty else 0,
        },
        "top_municipios": municipio.head(30).to_dict(orient="records"),
        "top_locais_votacao": local.head(50).to_dict(orient="records"),
        "top_regioes_estimadas": regiao.head(50).to_dict(orient="records"),
        "agenda_sugerida_davi_parceiro": [],
    }

    agenda = []

    for _, row in local.head(20).iterrows():
        agenda.append(
            {
                "municipio": row.get("municipio", ""),
                "local_votacao": row.get("local_votacao", ""),
                "regiao_estimada": row.get("regiao_estimada", ""),
                "votos_parceiro": int(row.get("votos_parceiro", 0)),
                "percentual_votos_parceiro": float(row.get("percentual_votos_parceiro", 0)),
                "forca_reduto": row.get("forca_reduto", ""),
                "acao_recomendada": (
                    f"Agenda conjunta Davi + {nome_parceiro} com visita territorial, "
                    "reunião com lideranças locais e validação dos vereadores com maior força no mesmo território."
                ),
                "objetivo_politico": (
                    "Converter capital eleitoral do parceiro em abertura de portas para Davi, "
                    "priorizando vereadores e lideranças que dominam os mesmos locais de votação."
                ),
            }
        )

    dados["agenda_sugerida_davi_parceiro"] = agenda

    return limpar_valor_json(dados)


# ============================================================
# PROCESSAMENTO DE CADA PARCEIRO
# ============================================================

def processar_parceiro(parceiro):
    id_parceiro = str(parceiro.get("id_parceiro", "")).strip()

    if not id_parceiro:
        id_parceiro = slugify(parceiro.get("nome_parceiro", ""))

    nome_parceiro = str(parceiro.get("nome_parceiro", "")).strip()
    ano = str(parceiro.get("ano_base_eleitoral", "")).strip()
    uf = str(parceiro.get("uf_base_eleitoral", "")).strip().upper()
    cargo = str(parceiro.get("cargo_disputado_2022", "")).strip()
    arquivo_votacao = resolver_caminho(parceiro.get("arquivo_votacao_secao", ""))

    print()
    print("=" * 80)
    print(f"PROCESSANDO PARCEIRO: {nome_parceiro} [{id_parceiro}]")
    print("=" * 80)

    dir_final = os.path.join(DIR_FINAL_PARCEIROS, id_parceiro)
    dir_dashboard = os.path.join(DIR_DASHBOARD_PARCEIROS, id_parceiro)

    os.makedirs(dir_final, exist_ok=True)
    os.makedirs(dir_dashboard, exist_ok=True)

    prefixo = f"{id_parceiro}_territorial_{ano or 'ano'}"

    saida_auditoria = os.path.join(dir_final, f"{prefixo}_auditoria_candidatos.csv")
    saida_secao = os.path.join(dir_final, f"{prefixo}_votacao_por_secao.csv")
    saida_local = os.path.join(dir_final, f"{prefixo}_redutos_por_local_votacao.csv")
    saida_regiao = os.path.join(dir_final, f"{prefixo}_redutos_por_regiao_estimada.csv")
    saida_municipio = os.path.join(dir_final, f"{prefixo}_resumo_por_municipio.csv")
    saida_json = os.path.join(dir_dashboard, f"{prefixo}.json")

    status = {
        "id_parceiro": id_parceiro,
        "nome_parceiro": nome_parceiro,
        "ano_base_eleitoral": ano,
        "uf_base_eleitoral": uf,
        "cargo_disputado": cargo,
        "status_processamento": "",
        "mensagem": "",
        "candidato_identificado": "",
        "numero": "",
        "sq_candidato": "",
        "metodo_selecao": "",
        "total_votos_parceiro": 0,
        "municipios_com_votos": 0,
        "locais_votacao_com_votos": 0,
        "secoes_com_votos": 0,
        "json_dashboard": saida_json,
    }

    if not arquivo_votacao:
        status["status_processamento"] = "IGNORADO"
        status["mensagem"] = "Campo arquivo_votacao_secao vazio."
        print(status["mensagem"])
        return status, None

    if not os.path.exists(arquivo_votacao):
        status["status_processamento"] = "PENDENTE_ARQUIVO"
        status["mensagem"] = f"Arquivo de votação não encontrado: {arquivo_votacao}"
        print(status["mensagem"])
        return status, None

    print(f"Arquivo de votação: {arquivo_votacao}")

    try:
        df_tse = ler_csv_generico(arquivo_votacao)
        validar_colunas_tse(df_tse)

        print(f"Linhas carregadas: {len(df_tse):,}".replace(",", "."))

        if ano:
            df_tse = df_tse[df_tse["ANO_ELEICAO"].astype(str).str.strip() == ano].copy()

        if uf:
            df_tse = df_tse[df_tse["SG_UF"].astype(str).str.upper().str.strip() == uf].copy()

        df_cargo = filtrar_cargo(df_tse, cargo)

        print(f"Linhas após filtro ano/UF/cargo: {len(df_cargo):,}".replace(",", "."))

        if df_cargo.empty:
            status["status_processamento"] = "SEM_DADOS_CARGO"
            status["mensagem"] = "Nenhuma linha encontrada para ano/UF/cargo informados."
            print(status["mensagem"])
            return status, None

        candidatos = auditar_candidatos_possiveis(df_cargo, parceiro)

        candidatos.to_csv(
            saida_auditoria,
            index=False,
            encoding="utf-8-sig",
        )

        print(f"Candidatos possíveis encontrados: {len(candidatos)}")
        print(f"Auditoria de candidatos: {saida_auditoria}")

        if candidatos.empty:
            status["status_processamento"] = "CANDIDATO_NAO_ENCONTRADO"
            status["mensagem"] = "Nenhum candidato compatível com nome_urna_2022/nome_parceiro foi encontrado."
            print(status["mensagem"])
            return status, None

        candidato, metodo = escolher_candidato(candidatos, parceiro)

        print()
        print("Candidato selecionado:")
        print(f"Nome: {candidato.get('NM_VOTAVEL')}")
        print(f"Número: {candidato.get('NR_VOTAVEL')}")
        print(f"SQ_CANDIDATO: {candidato.get('SQ_CANDIDATO')}")
        print(f"Cargo: {candidato.get('DS_CARGO')}")
        print(f"Município referência TSE: {candidato.get('NM_MUNICIPIO')}")
        print(f"Votos auditoria: {candidato.get('votos_total')}")
        print(f"Método de seleção: {metodo}")

        df_votacao = filtrar_votacao_candidato(df_cargo, candidato)

        if df_votacao.empty:
            status["status_processamento"] = "SEM_VOTACAO_CANDIDATO"
            status["mensagem"] = "Candidato identificado, mas sem linhas na base final filtrada."
            print(status["mensagem"])
            return status, None

        secao, local, regiao, municipio = gerar_agregacoes(df_votacao)

        secao.to_csv(saida_secao, index=False, encoding="utf-8-sig")
        local.to_csv(saida_local, index=False, encoding="utf-8-sig")
        regiao.to_csv(saida_regiao, index=False, encoding="utf-8-sig")
        municipio.to_csv(saida_municipio, index=False, encoding="utf-8-sig")

        dados_json = gerar_json_parceiro(
            parceiro=parceiro,
            candidato=candidato,
            metodo_selecao=metodo,
            secao=secao,
            local=local,
            regiao=regiao,
            municipio=municipio,
        )

        with open(saida_json, "w", encoding="utf-8") as f:
            json.dump(dados_json, f, ensure_ascii=False, indent=2, allow_nan=False)

        total_votos = int(secao["votos_parceiro"].sum())

        status["status_processamento"] = "PROCESSADO"
        status["mensagem"] = "Parceiro processado com sucesso."
        status["candidato_identificado"] = str(candidato.get("NM_VOTAVEL", ""))
        status["numero"] = str(candidato.get("NR_VOTAVEL", ""))
        status["sq_candidato"] = str(candidato.get("SQ_CANDIDATO", ""))
        status["metodo_selecao"] = metodo
        status["total_votos_parceiro"] = total_votos
        status["municipios_com_votos"] = int(municipio["municipio"].nunique()) if not municipio.empty else 0
        status["locais_votacao_com_votos"] = int(local["NR_LOCAL_VOTACAO"].nunique()) if not local.empty else 0
        status["secoes_com_votos"] = int(secao["secao"].nunique()) if not secao.empty and "secao" in secao.columns else 0

        print()
        print("Arquivos gerados:")
        print(saida_secao)
        print(saida_local)
        print(saida_regiao)
        print(saida_municipio)
        print(saida_json)

        print()
        print("Resumo territorial:")
        print(f"Total de votos: {status['total_votos_parceiro']:,}".replace(",", "."))
        print(f"Municípios com votos: {status['municipios_com_votos']}")
        print(f"Locais de votação com votos: {status['locais_votacao_com_votos']}")
        print(f"Seções com votos: {status['secoes_com_votos']}")

        print()
        print("Top 10 locais:")
        for _, row in local.head(10).iterrows():
            print(
                f"- {row['municipio']} | {row['local_votacao']} | "
                f"{int(row['votos_parceiro'])} votos | {row['forca_reduto']}"
            )

        return status, dados_json

    except Exception as e:
        status["status_processamento"] = "ERRO"
        status["mensagem"] = str(e)
        print(f"ERRO ao processar {nome_parceiro}: {e}")
        return status, None


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 80)
    print("ETL GENÉRICO — PARCEIROS DAVI 2026")
    print("=" * 80)

    parceiros = carregar_parceiros()

    print(f"Parceiros habilitados para dashboard: {len(parceiros)}")

    status_processamento = []
    jsons_processados = []

    for _, parceiro in parceiros.iterrows():
        status, dados_json = processar_parceiro(parceiro.to_dict())
        status_processamento.append(status)

        if dados_json is not None:
            jsons_processados.append(dados_json)

    df_status = pd.DataFrame(status_processamento)

    df_status.to_csv(
        ARQUIVO_CONSOLIDADO_FINAL,
        index=False,
        encoding="utf-8-sig",
    )

    consolidado_json = {
        "metadata": {
            "titulo": "Consolidado Territorial de Parceiros — Davi Maia 2026",
            "versao": "v1",
            "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fonte": "Matriz de parceiros + votação por seção eleitoral do TSE",
            "observacao_metodologica": (
                "Este consolidado organiza a força territorial dos parceiros cadastrados. "
                "A próxima camada analítica deverá cruzar estes redutos com a votação dos vereadores de 2024."
            ),
        },
        "resumo_processamento": df_status.to_dict(orient="records"),
        "parceiros_processados": jsons_processados,
    }

    consolidado_json = limpar_valor_json(consolidado_json)

    with open(ARQUIVO_CONSOLIDADO_DASHBOARD, "w", encoding="utf-8") as f:
        json.dump(consolidado_json, f, ensure_ascii=False, indent=2, allow_nan=False)

    print()
    print("=" * 80)
    print("ETL GENÉRICO CONCLUÍDO")
    print("=" * 80)
    print(f"Resumo CSV: {ARQUIVO_CONSOLIDADO_FINAL}")
    print(f"Resumo JSON: {ARQUIVO_CONSOLIDADO_DASHBOARD}")

    print()
    print("Status dos parceiros:")
    for _, row in df_status.iterrows():
        print(
            f"- {row['nome_parceiro']} | {row['status_processamento']} | "
            f"{row['total_votos_parceiro']} votos | {row['mensagem']}"
        )

    print("=" * 80)


if __name__ == "__main__":
    main()