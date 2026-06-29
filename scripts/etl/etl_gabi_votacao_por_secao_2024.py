import os
import json
import re
import unicodedata
import pandas as pd
from datetime import datetime


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

ARQUIVO_TSE_SECAO = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "tse_2024",
    "votacao_secao_2024_AL.csv",
)

DIR_GABI_FINAL = os.path.join(
    BASE_DIR,
    "data",
    "final",
    "parceiros",
    "gabi-goncalves",
)

DIR_GABI_DASHBOARD = os.path.join(
    BASE_DIR,
    "data",
    "dashboard",
    "parceiros",
    "gabi-goncalves",
)

os.makedirs(DIR_GABI_FINAL, exist_ok=True)
os.makedirs(DIR_GABI_DASHBOARD, exist_ok=True)

SAIDA_CANDIDATOS_AUDITORIA = os.path.join(
    DIR_GABI_FINAL,
    "auditoria_candidatos_gabi_tse_2024.csv",
)

SAIDA_VOTACAO_SECAO = os.path.join(
    DIR_GABI_FINAL,
    "gabi_votacao_por_secao_2024.csv",
)

SAIDA_REDUTOS_LOCAL = os.path.join(
    DIR_GABI_FINAL,
    "gabi_redutos_por_local_votacao_2024.csv",
)

SAIDA_REDUTOS_BAIRRO = os.path.join(
    DIR_GABI_FINAL,
    "gabi_redutos_por_regiao_estimada_2024.csv",
)

SAIDA_RESUMO_MUNICIPIO = os.path.join(
    DIR_GABI_FINAL,
    "gabi_resumo_por_municipio_2024.csv",
)

SAIDA_JSON_DASHBOARD = os.path.join(
    DIR_GABI_DASHBOARD,
    "gabi_territorial_v1.json",
)


# ============================================================
# AJUSTE MANUAL OPCIONAL
# ============================================================
# Se o ETL identificar mais de uma candidata possível, preencha abaixo
# com os dados corretos encontrados no arquivo de auditoria.
#
# Exemplos:
# FILTRO_NR_VOTAVEL = "12345"
# FILTRO_SQ_CANDIDATO = "123456789"
# FILTRO_NM_VOTAVEL_EXATO = "GABI GONCALVES"
# ============================================================

FILTRO_NR_VOTAVEL = ""
FILTRO_SQ_CANDIDATO = ""
FILTRO_NM_VOTAVEL_EXATO = ""


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_texto(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join([c for c in texto if not unicodedata.combining(c)])
    texto = re.sub(r"\s+", " ", texto)

    return texto


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


def converter_int(valor):
    try:
        if pd.isna(valor):
            return 0
        return int(float(str(valor).replace(",", ".")))
    except Exception:
        return 0


def limpar_json(obj):
    if isinstance(obj, dict):
        return {k: limpar_json(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [limpar_json(v) for v in obj]

    if pd.isna(obj) if not isinstance(obj, (list, dict, str, int, float, bool, type(None))) else False:
        return None

    if isinstance(obj, float):
        if pd.isna(obj):
            return None

    return obj


def classificar_forca_reduto(percentual_gabi, votos_gabi):
    if votos_gabi >= 300 or percentual_gabi >= 8:
        return "NÚCLEO FORTE"

    if votos_gabi >= 150 or percentual_gabi >= 4:
        return "ÁREA RELEVANTE"

    if votos_gabi >= 50 or percentual_gabi >= 1.5:
        return "ÁREA COMPLEMENTAR"

    return "BAIXA PRESENÇA"


def extrair_regiao_estimada(endereco):
    """
    Heurística simples para criar uma região/bairro estimado a partir do endereço.

    Observação metodológica:
    o TSE informa seção, local de votação e endereço.
    Bairro/região é uma inferência operacional a partir do campo de endereço.
    """

    texto_original = "" if pd.isna(endereco) else str(endereco).strip()
    texto = normalizar_texto(texto_original)

    if not texto:
        return "NÃO INFORMADO"

    # Remove complementos muito comuns.
    texto = texto.replace("RUA ", "")
    texto = texto.replace("AVENIDA ", "")
    texto = texto.replace("AV ", "")
    texto = texto.replace("TRAVESSA ", "")
    texto = texto.replace("RODOVIA ", "")
    texto = texto.replace("PRACA ", "")
    texto = texto.replace("PRAÇA ", "")

    # Tenta capturar depois de BAIRRO, POVOADO, DISTRITO, CONJUNTO etc.
    padroes = [
        r"BAIRRO[:\s]+([A-Z0-9\s\-']+)",
        r"POVOADO[:\s]+([A-Z0-9\s\-']+)",
        r"DISTRITO[:\s]+([A-Z0-9\s\-']+)",
        r"CONJUNTO[:\s]+([A-Z0-9\s\-']+)",
        r"RESIDENCIAL[:\s]+([A-Z0-9\s\-']+)",
        r"VILA[:\s]+([A-Z0-9\s\-']+)",
    ]

    for padrao in padroes:
        match = re.search(padrao, texto)

        if match:
            regiao = match.group(1).strip()
            regiao = re.split(r"[,.;/]", regiao)[0].strip()
            return regiao[:80] if regiao else "NÃO INFORMADO"

    # Se não houver marcador de bairro, usa o final do endereço após vírgula.
    partes = [p.strip() for p in re.split(r"[,;/\-]", texto) if p.strip()]

    if len(partes) >= 2:
        candidato = partes[-1]
        candidato = re.sub(r"\bN\b|\bNO\b|\bNUMERO\b|\bS N\b|\bSN\b", "", candidato).strip()

        if len(candidato) >= 3:
            return candidato[:80]

    return "NÃO INFORMADO"


def identificar_candidatos_gabi(df):
    df = df.copy()

    df["NM_VOTAVEL_NORMALIZADO"] = df["NM_VOTAVEL"].apply(normalizar_texto)

    termos = [
        "GABI",
        "GABY",
        "GABRIELA",
        "GONCALVES",
        "GONÇALVES",
    ]

    mascara = pd.Series(False, index=df.index)

    for termo in termos:
        termo_norm = normalizar_texto(termo)
        mascara = mascara | df["NM_VOTAVEL_NORMALIZADO"].str.contains(termo_norm, na=False)

    encontrados = df[mascara].copy()

    if encontrados.empty:
        return pd.DataFrame()

    encontrados["QT_VOTOS_NUM"] = encontrados["QT_VOTOS"].apply(converter_int)

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

    resumo = resumo.sort_values(
        by=["votos_total", "locais_votacao", "secoes"],
        ascending=[False, False, False],
    )

    return resumo


def escolher_candidata_automaticamente(df_candidatos):
    if df_candidatos.empty:
        return None

    candidatos = df_candidatos.copy()
    candidatos["NM_VOTAVEL_NORMALIZADO"] = candidatos["NM_VOTAVEL"].apply(normalizar_texto)
    candidatos["DS_CARGO_NORMALIZADO"] = candidatos["DS_CARGO"].apply(normalizar_texto)

    if FILTRO_SQ_CANDIDATO:
        filtrado = candidatos[candidatos["SQ_CANDIDATO"].astype(str) == str(FILTRO_SQ_CANDIDATO)]

        if not filtrado.empty:
            return filtrado.iloc[0].to_dict()

    if FILTRO_NR_VOTAVEL:
        filtrado = candidatos[candidatos["NR_VOTAVEL"].astype(str) == str(FILTRO_NR_VOTAVEL)]

        if not filtrado.empty:
            return filtrado.iloc[0].to_dict()

    if FILTRO_NM_VOTAVEL_EXATO:
        nome_alvo = normalizar_texto(FILTRO_NM_VOTAVEL_EXATO)
        filtrado = candidatos[candidatos["NM_VOTAVEL_NORMALIZADO"] == nome_alvo]

        if not filtrado.empty:
            return filtrado.iloc[0].to_dict()

    # Regra automática:
    # 1. Cargo vereador.
    # 2. Nome contém GABI/GABRIELA e GONCALVES.
    vereadores = candidatos[candidatos["DS_CARGO_NORMALIZADO"].str.contains("VEREADOR", na=False)].copy()

    if vereadores.empty:
        vereadores = candidatos.copy()

    preferenciais = vereadores[
        (
            vereadores["NM_VOTAVEL_NORMALIZADO"].str.contains("GABI", na=False)
            | vereadores["NM_VOTAVEL_NORMALIZADO"].str.contains("GABRIELA", na=False)
            | vereadores["NM_VOTAVEL_NORMALIZADO"].str.contains("GABY", na=False)
        )
        & vereadores["NM_VOTAVEL_NORMALIZADO"].str.contains("GONCALVES", na=False)
    ].copy()

    if not preferenciais.empty:
        return preferenciais.sort_values(by="votos_total", ascending=False).iloc[0].to_dict()

    # Segunda tentativa: nome contém GABI/GABRIELA/GABY.
    preferenciais = vereadores[
        vereadores["NM_VOTAVEL_NORMALIZADO"].str.contains("GABI|GABRIELA|GABY", regex=True, na=False)
    ].copy()

    if not preferenciais.empty:
        return preferenciais.sort_values(by="votos_total", ascending=False).iloc[0].to_dict()

    # Terceira tentativa: maior votação entre os encontrados.
    return vereadores.sort_values(by="votos_total", ascending=False).iloc[0].to_dict()


def filtrar_votacao_candidata(df, candidata):
    if candidata is None:
        return pd.DataFrame()

    sq = str(candidata.get("SQ_CANDIDATO", "")).strip()
    nr = str(candidata.get("NR_VOTAVEL", "")).strip()
    nome = normalizar_texto(candidata.get("NM_VOTAVEL", ""))

    base = df.copy()
    base["NM_VOTAVEL_NORMALIZADO"] = base["NM_VOTAVEL"].apply(normalizar_texto)

    mascara = pd.Series(True, index=base.index)

    if sq:
        mascara = mascara & (base["SQ_CANDIDATO"].astype(str).str.strip() == sq)
    elif nr:
        mascara = mascara & (base["NR_VOTAVEL"].astype(str).str.strip() == nr)
    elif nome:
        mascara = mascara & (base["NM_VOTAVEL_NORMALIZADO"] == nome)
    else:
        return pd.DataFrame()

    return base[mascara].copy()


def gerar_agregacoes(df_gabi):
    df = df_gabi.copy()

    df["QT_VOTOS_NUM"] = df["QT_VOTOS"].apply(converter_int)
    df["municipio"] = df["NM_MUNICIPIO"].astype(str).str.upper().str.strip()
    df["local_votacao"] = df["NM_LOCAL_VOTACAO"].fillna("").astype(str).str.upper().str.strip()
    df["endereco_local_votacao"] = df["DS_LOCAL_VOTACAO_ENDERECO"].fillna("").astype(str).str.upper().str.strip()
    df["regiao_estimada"] = df["endereco_local_votacao"].apply(extrair_regiao_estimada)

    total_votos_gabi = int(df["QT_VOTOS_NUM"].sum())

    # Por seção.
    secao = df.copy()
    secao = secao.rename(
        columns={
            "NM_MUNICIPIO": "municipio_original",
            "NR_ZONA": "zona",
            "NR_SECAO": "secao",
            "NR_LOCAL_VOTACAO": "numero_local_votacao",
            "NM_LOCAL_VOTACAO": "nome_local_votacao",
            "DS_LOCAL_VOTACAO_ENDERECO": "endereco",
            "QT_VOTOS": "votos_gabi",
        }
    )

    colunas_secao = [
        "SG_UF",
        "CD_MUNICIPIO",
        "municipio_original",
        "zona",
        "secao",
        "numero_local_votacao",
        "nome_local_votacao",
        "endereco",
        "regiao_estimada",
        "NR_VOTAVEL",
        "NM_VOTAVEL",
        "SQ_CANDIDATO",
        "votos_gabi",
    ]

    colunas_secao = [col for col in colunas_secao if col in secao.columns]
    secao = secao[colunas_secao].copy()
    secao["votos_gabi"] = secao["votos_gabi"].apply(converter_int)

    # Por local de votação.
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
            votos_gabi=("QT_VOTOS_NUM", "sum"),
            secoes_com_voto=("NR_SECAO", "nunique"),
        )
    )

    local["percentual_votos_gabi"] = (local["votos_gabi"] / total_votos_gabi * 100).round(4)
    local["forca_reduto"] = local.apply(
        lambda row: classificar_forca_reduto(
            row["percentual_votos_gabi"],
            row["votos_gabi"],
        ),
        axis=1,
    )

    local = local.sort_values(
        by=["votos_gabi", "percentual_votos_gabi"],
        ascending=[False, False],
    ).reset_index(drop=True)

    local["ranking_local_gabi"] = local.index + 1

    # Por região estimada.
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
            votos_gabi=("QT_VOTOS_NUM", "sum"),
            locais_votacao=("NR_LOCAL_VOTACAO", "nunique"),
            secoes_com_voto=("NR_SECAO", "nunique"),
        )
    )

    regiao["percentual_votos_gabi"] = (regiao["votos_gabi"] / total_votos_gabi * 100).round(4)
    regiao["forca_reduto"] = regiao.apply(
        lambda row: classificar_forca_reduto(
            row["percentual_votos_gabi"],
            row["votos_gabi"],
        ),
        axis=1,
    )

    regiao = regiao.sort_values(
        by=["votos_gabi", "percentual_votos_gabi"],
        ascending=[False, False],
    ).reset_index(drop=True)

    regiao["ranking_regiao_gabi"] = regiao.index + 1

    # Por município.
    municipio = (
        df
        .groupby(
            ["municipio"],
            dropna=False,
            as_index=False,
        )
        .agg(
            votos_gabi=("QT_VOTOS_NUM", "sum"),
            locais_votacao=("NR_LOCAL_VOTACAO", "nunique"),
            secoes_com_voto=("NR_SECAO", "nunique"),
            regioes_estimadas=("regiao_estimada", "nunique"),
        )
    )

    municipio["percentual_votos_gabi"] = (municipio["votos_gabi"] / total_votos_gabi * 100).round(4)

    municipio = municipio.sort_values(
        by=["votos_gabi", "percentual_votos_gabi"],
        ascending=[False, False],
    ).reset_index(drop=True)

    municipio["ranking_municipio_gabi"] = municipio.index + 1

    return secao, local, regiao, municipio


def gerar_json_dashboard(candidata, secao, local, regiao, municipio):
    total_votos = int(secao["votos_gabi"].sum()) if not secao.empty else 0

    dados = {
        "metadata": {
            "titulo": "Atuação Territorial de Parceiros — Gabi Gonçalves",
            "versao": "v1",
            "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fonte": "TSE — votação por seção eleitoral 2024 / AL",
            "observacao_metodologica": (
                "A base oficial informa votos por seção, local de votação e endereço. "
                "Bairro/região é estimativa operacional derivada do endereço do local de votação."
            ),
        },
        "candidata_identificada": {
            "sq_candidato": str(candidata.get("SQ_CANDIDATO", "")),
            "numero": str(candidata.get("NR_VOTAVEL", "")),
            "nome_votavel": str(candidata.get("NM_VOTAVEL", "")),
            "cargo": str(candidata.get("DS_CARGO", "")),
            "municipio_principal": str(candidata.get("NM_MUNICIPIO", "")),
            "votos_total_auditoria": int(candidata.get("votos_total", 0)),
        },
        "resumo": {
            "total_votos_gabi": total_votos,
            "municipios_com_votos": int(municipio["municipio"].nunique()) if not municipio.empty else 0,
            "locais_votacao_com_votos": int(local["NR_LOCAL_VOTACAO"].nunique()) if not local.empty else 0,
            "secoes_com_votos": int(secao["secao"].nunique()) if not secao.empty and "secao" in secao.columns else 0,
            "regioes_estimadas": int(regiao["regiao_estimada"].nunique()) if not regiao.empty else 0,
        },
        "top_municipios": municipio.head(20).to_dict(orient="records"),
        "top_locais_votacao": local.head(30).to_dict(orient="records"),
        "top_regioes_estimadas": regiao.head(30).to_dict(orient="records"),
        "agenda_sugerida_davi_gabi": [],
    }

    agenda = []

    for _, row in local.head(15).iterrows():
        agenda.append(
            {
                "municipio": row.get("municipio", ""),
                "local_votacao": row.get("local_votacao", ""),
                "regiao_estimada": row.get("regiao_estimada", ""),
                "votos_gabi": int(row.get("votos_gabi", 0)),
                "percentual_votos_gabi": float(row.get("percentual_votos_gabi", 0)),
                "forca_reduto": row.get("forca_reduto", ""),
                "acao_recomendada": (
                    "Agenda conjunta Davi + Gabi com visita territorial, reunião com lideranças locais "
                    "e validação de interlocutores comunitários."
                ),
                "objetivo_politico": (
                    "Converter capital territorial da Gabi em abertura de portas para Davi, "
                    "priorizando presença física e relacionamento local."
                ),
            }
        )

    dados["agenda_sugerida_davi_gabi"] = agenda

    return dados


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 80)
    print("ETL GABI GONÇALVES — VOTAÇÃO POR SEÇÃO / LOCAL / REGIÃO")
    print("=" * 80)

    if not os.path.exists(ARQUIVO_TSE_SECAO):
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_TSE_SECAO}")

    encoding = detectar_encoding(ARQUIVO_TSE_SECAO)
    sep = detectar_sep(ARQUIVO_TSE_SECAO, encoding)

    print(f"Arquivo TSE: {ARQUIVO_TSE_SECAO}")
    print(f"Encoding: {encoding}")
    print(f"Separador: {repr(sep)}")

    df = pd.read_csv(
        ARQUIVO_TSE_SECAO,
        sep=sep,
        encoding=encoding,
        dtype=str,
        low_memory=False,
        on_bad_lines="skip",
    )

    print(f"Linhas carregadas: {len(df):,}".replace(",", "."))

    colunas_obrigatorias = [
        "DS_CARGO",
        "NR_VOTAVEL",
        "NM_VOTAVEL",
        "QT_VOTOS",
        "NR_LOCAL_VOTACAO",
        "SQ_CANDIDATO",
        "NM_LOCAL_VOTACAO",
        "DS_LOCAL_VOTACAO_ENDERECO",
    ]

    faltantes = [col for col in colunas_obrigatorias if col not in df.columns]

    if faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes no arquivo TSE: {faltantes}")

    print("Identificando candidaturas relacionadas a Gabi/Gabriela/Gonçalves...")

    df_candidatos = identificar_candidatos_gabi(df)

    df_candidatos.to_csv(
        SAIDA_CANDIDATOS_AUDITORIA,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Candidatos encontrados na auditoria: {len(df_candidatos)}")
    print(f"Auditoria salva em: {SAIDA_CANDIDATOS_AUDITORIA}")

    if df_candidatos.empty:
        raise ValueError(
            "Nenhuma candidatura relacionada a Gabi/Gabriela/Gonçalves foi encontrada. "
            "Abra a auditoria anterior e identifique a candidata por número ou SQ_CANDIDATO."
        )

    candidata = escolher_candidata_automaticamente(df_candidatos)

    if candidata is None:
        raise ValueError("Não foi possível identificar automaticamente a candidata.")

    print()
    print("Candidata selecionada automaticamente:")
    print(f"SQ_CANDIDATO: {candidata.get('SQ_CANDIDATO')}")
    print(f"NR_VOTAVEL: {candidata.get('NR_VOTAVEL')}")
    print(f"NM_VOTAVEL: {candidata.get('NM_VOTAVEL')}")
    print(f"DS_CARGO: {candidata.get('DS_CARGO')}")
    print(f"NM_MUNICIPIO: {candidata.get('NM_MUNICIPIO')}")
    print(f"Votos total auditoria: {candidata.get('votos_total')}")
    print()

    df_gabi = filtrar_votacao_candidata(df, candidata)

    if df_gabi.empty:
        raise ValueError(
            "A candidata foi identificada na auditoria, mas o filtro final não retornou linhas. "
            "Preencha FILTRO_NR_VOTAVEL ou FILTRO_SQ_CANDIDATO no início do script."
        )

    print(f"Linhas da Gabi filtradas: {len(df_gabi):,}".replace(",", "."))

    secao, local, regiao, municipio = gerar_agregacoes(df_gabi)

    secao.to_csv(SAIDA_VOTACAO_SECAO, index=False, encoding="utf-8-sig")
    local.to_csv(SAIDA_REDUTOS_LOCAL, index=False, encoding="utf-8-sig")
    regiao.to_csv(SAIDA_REDUTOS_BAIRRO, index=False, encoding="utf-8-sig")
    municipio.to_csv(SAIDA_RESUMO_MUNICIPIO, index=False, encoding="utf-8-sig")

    dados_json = gerar_json_dashboard(
        candidata=candidata,
        secao=secao,
        local=local,
        regiao=regiao,
        municipio=municipio,
    )

    with open(SAIDA_JSON_DASHBOARD, "w", encoding="utf-8") as f:
        json.dump(dados_json, f, ensure_ascii=False, indent=2, allow_nan=False)

    print()
    print("=" * 80)
    print("ETL CONCLUÍDO")
    print("=" * 80)
    print(f"Votação por seção: {SAIDA_VOTACAO_SECAO}")
    print(f"Redutos por local: {SAIDA_REDUTOS_LOCAL}")
    print(f"Redutos por região estimada: {SAIDA_REDUTOS_BAIRRO}")
    print(f"Resumo por município: {SAIDA_RESUMO_MUNICIPIO}")
    print(f"JSON dashboard: {SAIDA_JSON_DASHBOARD}")

    print()
    print("Resumo:")
    print(f"Total de votos Gabi: {int(secao['votos_gabi'].sum()):,}".replace(",", "."))
    print(f"Municípios com votos: {municipio['municipio'].nunique()}")
    print(f"Locais de votação com votos: {local['NR_LOCAL_VOTACAO'].nunique()}")
    print(f"Regiões estimadas: {regiao['regiao_estimada'].nunique()}")

    print()
    print("Top 10 locais de votação:")
    for _, row in local.head(10).iterrows():
        print(
            f"- {row['municipio']} | {row['local_votacao']} | "
            f"{row['votos_gabi']} votos | {row['forca_reduto']}"
        )

    print("=" * 80)


if __name__ == "__main__":
    main()