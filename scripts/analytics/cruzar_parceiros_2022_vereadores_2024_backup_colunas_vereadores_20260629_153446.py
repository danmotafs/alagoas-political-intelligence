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

ARQUIVOS_VEREADORES_POSSIVEIS = [
    os.path.join(BASE_DIR, "data", "final", "votacao_secao_vereadores_top10.csv"),
    os.path.join(BASE_DIR, "data", "final", "mapa_influencia_vereadores_top10.csv"),
    os.path.join(BASE_DIR, "data", "final", "mapa_influencia_geografico.csv"),
]

DIR_FINAL_PARCEIROS = os.path.join(BASE_DIR, "data", "final", "parceiros")
DIR_DASHBOARD_PARCEIROS = os.path.join(BASE_DIR, "data", "dashboard", "parceiros")

SAIDA_CONSOLIDADO_CSV = os.path.join(
    DIR_FINAL_PARCEIROS,
    "consolidado_cruzamento_parceiros_vereadores_2024.csv",
)

SAIDA_CONSOLIDADO_JSON = os.path.join(
    DIR_DASHBOARD_PARCEIROS,
    "consolidado_cruzamento_parceiros_vereadores_2024.json",
)

META_DAVI = 60000
TOP_N_VEREADORES_POR_LOCAL = 15

os.makedirs(DIR_FINAL_PARCEIROS, exist_ok=True)
os.makedirs(DIR_DASHBOARD_PARCEIROS, exist_ok=True)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_texto(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto)
    return texto


def normalizar_nome_chave(valor):
    texto = normalizar_texto(valor)
    texto = re.sub(r"[^A-Z0-9 ]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def normalizar_numero(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if texto == "":
        return ""

    try:
        return str(int(float(texto.replace(",", "."))))
    except Exception:
        return texto


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


def escolher_coluna(df, possibilidades, obrigatoria=False, nome_logico=""):
    mapa = {normalizar_texto(col): col for col in df.columns}

    for col in possibilidades:
        col_norm = normalizar_texto(col)

        if col_norm in mapa:
            return mapa[col_norm]

    if obrigatoria:
        raise ValueError(
            f"Não foi possível localizar a coluna obrigatória: {nome_logico or possibilidades[0]}. "
            f"Colunas disponíveis: {list(df.columns)}"
        )

    return ""


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


def localizar_arquivo_vereadores():
    for caminho in ARQUIVOS_VEREADORES_POSSIVEIS:
        if os.path.exists(caminho):
            return caminho

    raise FileNotFoundError(
        "Nenhuma base de votação territorial dos vereadores foi encontrada. "
        "Arquivos procurados: "
        + " | ".join(ARQUIVOS_VEREADORES_POSSIVEIS)
    )


def carregar_parceiros():
    if not os.path.exists(ARQUIVO_PARCEIROS):
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_PARCEIROS}")

    df = ler_csv(ARQUIVO_PARCEIROS)

    if "incluir_no_dashboard" not in df.columns:
        df["incluir_no_dashboard"] = "SIM"

    df["incluir_no_dashboard_norm"] = df["incluir_no_dashboard"].apply(normalizar_texto)

    df = df[df["incluir_no_dashboard_norm"].isin(["SIM", "S", "YES", "TRUE", "1"])].copy()

    return df


def preparar_base_vereadores():
    arquivo_vereadores = localizar_arquivo_vereadores()

    print(f"Base de vereadores usada: {arquivo_vereadores}")

    df = ler_csv(arquivo_vereadores)

    col_municipio = escolher_coluna(
        df,
        ["municipio", "NM_MUNICIPIO", "municipio_original"],
        obrigatoria=True,
        nome_logico="município",
    )

    col_zona = escolher_coluna(
        df,
        ["NR_ZONA", "zona"],
        obrigatoria=True,
        nome_logico="zona",
    )

    col_local = escolher_coluna(
        df,
        ["NR_LOCAL_VOTACAO", "numero_local_votacao", "local_votacao_numero"],
        obrigatoria=True,
        nome_logico="número do local de votação",
    )

    col_nome_local = escolher_coluna(
        df,
        ["NM_LOCAL_VOTACAO", "nome_local_votacao", "local_votacao"],
        obrigatoria=False,
        nome_logico="nome do local de votação",
    )

    col_endereco = escolher_coluna(
        df,
        ["DS_LOCAL_VOTACAO_ENDERECO", "endereco", "endereco_local_votacao"],
        obrigatoria=False,
        nome_logico="endereço do local",
    )

    col_vereador = escolher_coluna(
        df,
        ["vereador", "NM_VOTAVEL", "nome_urna", "nome_candidato", "NM_CANDIDATO"],
        obrigatoria=True,
        nome_logico="vereador",
    )

    col_partido = escolher_coluna(
        df,
        ["SG_PARTIDO", "partido", "partido_vereador"],
        obrigatoria=False,
        nome_logico="partido",
    )

    col_votos = escolher_coluna(
        df,
        ["QT_VOTOS", "votos", "votos_vereador", "votos_nominais"],
        obrigatoria=True,
        nome_logico="votos",
    )

    col_cargo = escolher_coluna(
        df,
        ["DS_CARGO", "cargo"],
        obrigatoria=False,
        nome_logico="cargo",
    )

    base = df.copy()

    if col_cargo:
        base["cargo_norm"] = base[col_cargo].apply(normalizar_texto)
        base = base[base["cargo_norm"].str.contains("VEREADOR", na=False)].copy()

    base["municipio_norm"] = base[col_municipio].apply(normalizar_nome_chave)
    base["zona_norm"] = base[col_zona].apply(normalizar_numero)
    base["local_num_norm"] = base[col_local].apply(normalizar_numero)

    if col_nome_local:
        base["local_nome"] = base[col_nome_local].fillna("").astype(str).str.upper().str.strip()
    else:
        base["local_nome"] = ""

    if col_endereco:
        base["endereco_local"] = base[col_endereco].fillna("").astype(str).str.upper().str.strip()
    else:
        base["endereco_local"] = ""

    base["local_nome_norm"] = base["local_nome"].apply(normalizar_nome_chave)
    base["vereador"] = base[col_vereador].fillna("").astype(str).str.upper().str.strip()
    base["partido_vereador"] = base[col_partido].fillna("").astype(str).str.upper().str.strip() if col_partido else ""
    base["votos_vereador_local"] = base[col_votos].apply(converter_int)

    base = base[base["votos_vereador_local"] > 0].copy()

    agrupado = (
        base
        .groupby(
            [
                "municipio_norm",
                "zona_norm",
                "local_num_norm",
                "local_nome",
                "local_nome_norm",
                "endereco_local",
                "vereador",
                "partido_vereador",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            votos_vereador_local=("votos_vereador_local", "sum"),
        )
    )

    agrupado["ranking_vereador_no_local"] = (
        agrupado
        .groupby(["municipio_norm", "zona_norm", "local_num_norm"])["votos_vereador_local"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    agrupado = agrupado[
        agrupado["ranking_vereador_no_local"] <= TOP_N_VEREADORES_POR_LOCAL
    ].copy()

    print(f"Linhas de vereadores preparadas: {len(agrupado):,}".replace(",", "."))

    return agrupado


def localizar_arquivo_redutos_parceiro(id_parceiro, ano):
    dir_parceiro = os.path.join(DIR_FINAL_PARCEIROS, id_parceiro)

    if not os.path.exists(dir_parceiro):
        return ""

    candidatos = []

    for nome in os.listdir(dir_parceiro):
        nome_lower = nome.lower()

        if (
            nome_lower.endswith(".csv")
            and "redutos_por_local_votacao" in nome_lower
            and str(ano) in nome_lower
        ):
            candidatos.append(os.path.join(dir_parceiro, nome))

    if candidatos:
        candidatos.sort()
        return candidatos[-1]

    return ""


def preparar_redutos_parceiro(caminho_redutos, nome_parceiro):
    df = ler_csv(caminho_redutos)

    col_municipio = escolher_coluna(
        df,
        ["municipio", "NM_MUNICIPIO", "municipio_original"],
        obrigatoria=True,
        nome_logico="município parceiro",
    )

    col_zona = escolher_coluna(
        df,
        ["NR_ZONA", "zona"],
        obrigatoria=True,
        nome_logico="zona parceiro",
    )

    col_local = escolher_coluna(
        df,
        ["NR_LOCAL_VOTACAO", "numero_local_votacao", "local_votacao_numero"],
        obrigatoria=True,
        nome_logico="local parceiro",
    )

    col_nome_local = escolher_coluna(
        df,
        ["local_votacao", "NM_LOCAL_VOTACAO", "nome_local_votacao"],
        obrigatoria=False,
        nome_logico="nome local parceiro",
    )

    col_endereco = escolher_coluna(
        df,
        ["endereco_local_votacao", "DS_LOCAL_VOTACAO_ENDERECO", "endereco"],
        obrigatoria=False,
        nome_logico="endereço parceiro",
    )

    col_regiao = escolher_coluna(
        df,
        ["regiao_estimada"],
        obrigatoria=False,
        nome_logico="região estimada",
    )

    col_votos = escolher_coluna(
        df,
        ["votos_parceiro", "votos_gabi", "QT_VOTOS", "votos"],
        obrigatoria=True,
        nome_logico="votos parceiro",
    )

    col_percentual = escolher_coluna(
        df,
        ["percentual_votos_parceiro", "percentual_votos_gabi"],
        obrigatoria=False,
        nome_logico="percentual parceiro",
    )

    col_forca = escolher_coluna(
        df,
        ["forca_reduto"],
        obrigatoria=False,
        nome_logico="força reduto",
    )

    base = df.copy()

    base["municipio_norm"] = base[col_municipio].apply(normalizar_nome_chave)
    base["municipio"] = base[col_municipio].astype(str).str.upper().str.strip()
    base["zona_norm"] = base[col_zona].apply(normalizar_numero)
    base["local_num_norm"] = base[col_local].apply(normalizar_numero)
    base["local_votacao_parceiro"] = base[col_nome_local].fillna("").astype(str).str.upper().str.strip() if col_nome_local else ""
    base["local_nome_norm"] = base["local_votacao_parceiro"].apply(normalizar_nome_chave)
    base["endereco_parceiro"] = base[col_endereco].fillna("").astype(str).str.upper().str.strip() if col_endereco else ""
    base["regiao_estimada"] = base[col_regiao].fillna("").astype(str).str.upper().str.strip() if col_regiao else ""
    base["votos_parceiro_local"] = base[col_votos].apply(converter_int)

    if col_percentual:
        base["percentual_votos_parceiro"] = pd.to_numeric(
            base[col_percentual].astype(str).str.replace(",", ".", regex=False),
            errors="coerce",
        ).fillna(0)
    else:
        total = base["votos_parceiro_local"].sum()
        base["percentual_votos_parceiro"] = (
            base["votos_parceiro_local"] / total * 100
        ).round(4) if total else 0

    base["forca_reduto_parceiro"] = base[col_forca].fillna("").astype(str).str.upper().str.strip() if col_forca else ""

    base = base[base["votos_parceiro_local"] > 0].copy()

    base["nome_parceiro"] = nome_parceiro

    return base


def cruzar_redutos(redutos_parceiro, vereadores):
    # Cruzamento principal: município + zona + número do local de votação.
    chaves_exatas = ["municipio_norm", "zona_norm", "local_num_norm"]

    cruzamento_exato = redutos_parceiro.merge(
        vereadores,
        on=chaves_exatas,
        how="inner",
        suffixes=("_parceiro", "_vereador"),
    )

    cruzamento_exato["tipo_cruzamento"] = "MUNICIPIO_ZONA_LOCAL"

    # Fallback: município + nome do local de votação.
    # Útil caso o número do local mude entre 2022 e 2024, mas a escola/local permaneça igual.
    chaves_nome = ["municipio_norm", "local_nome_norm"]

    cruzamento_nome = redutos_parceiro.merge(
        vereadores,
        on=chaves_nome,
        how="inner",
        suffixes=("_parceiro", "_vereador"),
    )

    cruzamento_nome["tipo_cruzamento"] = "MUNICIPIO_NOME_LOCAL"

    cruzamento = pd.concat([cruzamento_exato, cruzamento_nome], ignore_index=True)

    if cruzamento.empty:
        return cruzamento

    # Remove duplicações geradas pelos dois tipos de cruzamento.
    colunas_dedup = [
        "municipio_norm",
        "zona_norm_parceiro" if "zona_norm_parceiro" in cruzamento.columns else "zona_norm",
        "local_num_norm_parceiro" if "local_num_norm_parceiro" in cruzamento.columns else "local_num_norm",
        "vereador",
        "partido_vereador",
    ]

    colunas_dedup = [col for col in colunas_dedup if col in cruzamento.columns]

    cruzamento = cruzamento.drop_duplicates(subset=colunas_dedup).copy()

    return cruzamento


def calcular_indices(cruzamento, nome_parceiro):
    if cruzamento.empty:
        return cruzamento

    df = cruzamento.copy()

    max_votos_parceiro = df["votos_parceiro_local"].max()
    max_votos_vereador = df["votos_vereador_local"].max()

    df["score_parceiro_local"] = (
        df["votos_parceiro_local"] / max_votos_parceiro * 100
    ).round(2) if max_votos_parceiro else 0

    df["score_vereador_local"] = (
        df["votos_vereador_local"] / max_votos_vereador * 100
    ).round(2) if max_votos_vereador else 0

    df["potencial_davi_10pct_local"] = (df["votos_vereador_local"] * 0.10).round(0).astype(int)
    df["potencial_davi_15pct_local"] = (df["votos_vereador_local"] * 0.15).round(0).astype(int)
    df["potencial_davi_20pct_local"] = (df["votos_vereador_local"] * 0.20).round(0).astype(int)

    max_potencial = df["potencial_davi_20pct_local"].max()

    df["score_potencial_davi"] = (
        df["potencial_davi_20pct_local"] / max_potencial * 100
    ).round(2) if max_potencial else 0

    df["indice_convergencia"] = (
        df["score_parceiro_local"] * 0.40
        + df["score_vereador_local"] * 0.40
        + df["score_potencial_davi"] * 0.20
    ).round(2)

    def classificar(valor):
        if valor >= 70:
            return "CONVERGÊNCIA ALTA"

        if valor >= 45:
            return "CONVERGÊNCIA MÉDIA"

        if valor >= 25:
            return "CONVERGÊNCIA BAIXA"

        return "CONVERGÊNCIA RESIDUAL"

    df["classificacao_convergencia"] = df["indice_convergencia"].apply(classificar)

    df["acao_recomendada"] = df.apply(
        lambda row: (
            f"Agendar articulação Davi + {nome_parceiro} com o vereador {row.get('vereador', '')} "
            f"no território do local de votação {row.get('local_votacao_parceiro', row.get('local_nome', ''))}. "
            "Objetivo: validar apoio, mapear lideranças locais e pactuar entrada territorial."
        ),
        axis=1,
    )

    df["observacao_metodologica"] = (
        "Cruzamento feito entre votação do parceiro em 2022 e votação de vereadores em 2024. "
        "A chave principal é município + zona + local de votação; quando necessário, usa-se município + nome do local."
    )

    df = df.sort_values(
        by=[
            "indice_convergencia",
            "votos_parceiro_local",
            "votos_vereador_local",
        ],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    df["ranking_convergencia"] = df.index + 1

    return df


def gerar_json_cruzamento(id_parceiro, nome_parceiro, df):
    if df.empty:
        dados = {
            "metadata": {
                "titulo": f"Cruzamento Territorial — {nome_parceiro} x Vereadores 2024",
                "id_parceiro": id_parceiro,
                "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "resumo": {
                "total_cruzamentos": 0,
                "municipios_com_convergencia": 0,
                "vereadores_convergentes": 0,
                "potencial_davi_20pct_local": 0,
            },
            "top_convergencias": [],
            "agenda_recomendada": [],
        }

        return dados

    resumo_municipios = df["municipio"].nunique() if "municipio" in df.columns else df["municipio_norm"].nunique()

    dados = {
        "metadata": {
            "titulo": f"Cruzamento Territorial — {nome_parceiro} x Vereadores 2024",
            "id_parceiro": id_parceiro,
            "versao": "v1",
            "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fonte": "TSE 2022 parceiro + TSE 2024 vereadores",
            "observacao_metodologica": (
                "O cruzamento identifica locais onde o parceiro teve voto em 2022 "
                "e vereadores tiveram força em 2024. O objetivo é orientar articulação política, "
                "não prever voto automaticamente."
            ),
        },
        "resumo": {
            "total_cruzamentos": int(len(df)),
            "municipios_com_convergencia": int(resumo_municipios),
            "vereadores_convergentes": int(df["vereador"].nunique()),
            "locais_convergentes": int(df["local_num_norm"].nunique()) if "local_num_norm" in df.columns else 0,
            "potencial_davi_10pct_local": int(df["potencial_davi_10pct_local"].sum()),
            "potencial_davi_15pct_local": int(df["potencial_davi_15pct_local"].sum()),
            "potencial_davi_20pct_local": int(df["potencial_davi_20pct_local"].sum()),
        },
        "top_convergencias": df.head(100).to_dict(orient="records"),
        "agenda_recomendada": df.head(30)[
            [
                "ranking_convergencia",
                "municipio",
                "local_votacao_parceiro",
                "regiao_estimada",
                "nome_parceiro",
                "vereador",
                "partido_vereador",
                "votos_parceiro_local",
                "votos_vereador_local",
                "indice_convergencia",
                "classificacao_convergencia",
                "potencial_davi_20pct_local",
                "acao_recomendada",
            ]
        ].to_dict(orient="records"),
    }

    return limpar_json(dados)


def processar_parceiro(parceiro, vereadores):
    id_parceiro = str(parceiro.get("id_parceiro", "")).strip()
    nome_parceiro = str(parceiro.get("nome_parceiro", "")).strip()
    ano = str(parceiro.get("ano_base_eleitoral", "")).strip()

    print()
    print("=" * 80)
    print(f"CRUZANDO PARCEIRO: {nome_parceiro} [{id_parceiro}]")
    print("=" * 80)

    caminho_redutos = localizar_arquivo_redutos_parceiro(id_parceiro, ano)

    if not caminho_redutos:
        print("Arquivo de redutos por local de votação do parceiro não encontrado.")
        return pd.DataFrame(), {
            "id_parceiro": id_parceiro,
            "nome_parceiro": nome_parceiro,
            "status": "PENDENTE_REDUTOS",
            "mensagem": "Arquivo de redutos por local de votação não encontrado.",
        }

    print(f"Redutos do parceiro: {caminho_redutos}")

    redutos = preparar_redutos_parceiro(caminho_redutos, nome_parceiro)

    print(f"Redutos carregados: {len(redutos):,}".replace(",", "."))

    cruzamento = cruzar_redutos(redutos, vereadores)

    print(f"Cruzamentos encontrados: {len(cruzamento):,}".replace(",", "."))

    cruzamento = calcular_indices(cruzamento, nome_parceiro)

    dir_final = os.path.join(DIR_FINAL_PARCEIROS, id_parceiro)
    dir_dashboard = os.path.join(DIR_DASHBOARD_PARCEIROS, id_parceiro)

    os.makedirs(dir_final, exist_ok=True)
    os.makedirs(dir_dashboard, exist_ok=True)

    saida_csv = os.path.join(
        dir_final,
        f"{id_parceiro}_cruzamento_parceiro_2022_vereadores_2024.csv",
    )

    saida_json = os.path.join(
        dir_dashboard,
        f"{id_parceiro}_cruzamento_parceiro_2022_vereadores_2024.json",
    )

    cruzamento.to_csv(saida_csv, index=False, encoding="utf-8-sig")

    dados_json = gerar_json_cruzamento(
        id_parceiro=id_parceiro,
        nome_parceiro=nome_parceiro,
        df=cruzamento,
    )

    with open(saida_json, "w", encoding="utf-8") as f:
        json.dump(dados_json, f, ensure_ascii=False, indent=2, allow_nan=False)

    if cruzamento.empty:
        status = {
            "id_parceiro": id_parceiro,
            "nome_parceiro": nome_parceiro,
            "status": "SEM_CONVERGENCIA",
            "mensagem": "Nenhum cruzamento encontrado com a base territorial de vereadores.",
            "total_cruzamentos": 0,
            "municipios_com_convergencia": 0,
            "vereadores_convergentes": 0,
            "potencial_davi_20pct_local": 0,
            "arquivo_csv": saida_csv,
            "arquivo_json": saida_json,
        }
    else:
        status = {
            "id_parceiro": id_parceiro,
            "nome_parceiro": nome_parceiro,
            "status": "PROCESSADO",
            "mensagem": "Cruzamento processado com sucesso.",
            "total_cruzamentos": int(len(cruzamento)),
            "municipios_com_convergencia": int(cruzamento["municipio"].nunique()) if "municipio" in cruzamento.columns else int(cruzamento["municipio_norm"].nunique()),
            "vereadores_convergentes": int(cruzamento["vereador"].nunique()),
            "potencial_davi_20pct_local": int(cruzamento["potencial_davi_20pct_local"].sum()),
            "arquivo_csv": saida_csv,
            "arquivo_json": saida_json,
        }

    print()
    print("Arquivos gerados:")
    print(saida_csv)
    print(saida_json)

    if not cruzamento.empty:
        print()
        print("Top 10 convergências:")
        for _, row in cruzamento.head(10).iterrows():
            print(
                f"- {row.get('municipio', row.get('municipio_norm', ''))} | "
                f"{row.get('local_votacao_parceiro', '')} | "
                f"{row.get('vereador', '')} | "
                f"Parceiro: {int(row.get('votos_parceiro_local', 0))} votos | "
                f"Vereador: {int(row.get('votos_vereador_local', 0))} votos | "
                f"Índice: {row.get('indice_convergencia', 0)} | "
                f"{row.get('classificacao_convergencia', '')}"
            )

    return cruzamento, status


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 80)
    print("CRUZAMENTO GENÉRICO — PARCEIROS 2022 x VEREADORES 2024")
    print("=" * 80)

    parceiros = carregar_parceiros()

    print(f"Parceiros habilitados: {len(parceiros)}")

    vereadores = preparar_base_vereadores()

    todos_cruzamentos = []
    status_lista = []

    for _, parceiro in parceiros.iterrows():
        cruzamento, status = processar_parceiro(parceiro.to_dict(), vereadores)

        status_lista.append(status)

        if not cruzamento.empty:
            cruzamento["id_parceiro"] = parceiro.get("id_parceiro", "")
            cruzamento["nome_parceiro"] = parceiro.get("nome_parceiro", "")
            todos_cruzamentos.append(cruzamento)

    if todos_cruzamentos:
        consolidado = pd.concat(todos_cruzamentos, ignore_index=True)
        consolidado = consolidado.sort_values(
            by=["indice_convergencia", "votos_parceiro_local", "votos_vereador_local"],
            ascending=[False, False, False],
        ).reset_index(drop=True)
        consolidado["ranking_consolidado"] = consolidado.index + 1
    else:
        consolidado = pd.DataFrame()

    consolidado.to_csv(SAIDA_CONSOLIDADO_CSV, index=False, encoding="utf-8-sig")

    status_df = pd.DataFrame(status_lista)

    dados_json = {
        "metadata": {
            "titulo": "Consolidado — Parceiros 2022 x Vereadores 2024",
            "versao": "v1",
            "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fonte": "Votação por seção 2022 dos parceiros + votação por seção 2024 dos vereadores",
            "observacao_metodologica": (
                "O objetivo é identificar convergência territorial entre parceiros do Davi "
                "e vereadores que dominam os mesmos locais de votação. "
                "A métrica orienta articulação política e agenda territorial."
            ),
        },
        "resumo_processamento": status_df.to_dict(orient="records"),
        "top_convergencias_consolidadas": consolidado.head(200).to_dict(orient="records") if not consolidado.empty else [],
    }

    dados_json = limpar_json(dados_json)

    with open(SAIDA_CONSOLIDADO_JSON, "w", encoding="utf-8") as f:
        json.dump(dados_json, f, ensure_ascii=False, indent=2, allow_nan=False)

    print()
    print("=" * 80)
    print("CRUZAMENTO CONCLUÍDO")
    print("=" * 80)
    print(f"Consolidado CSV: {SAIDA_CONSOLIDADO_CSV}")
    print(f"Consolidado JSON: {SAIDA_CONSOLIDADO_JSON}")

    print()
    print("Status:")
    for item in status_lista:
        print(
            f"- {item['nome_parceiro']} | {item['status']} | "
            f"{item.get('total_cruzamentos', 0)} cruzamentos | "
            f"{item.get('vereadores_convergentes', 0)} vereadores | "
            f"Potencial local 20%: {item.get('potencial_davi_20pct_local', 0)}"
        )

    print("=" * 80)


if __name__ == "__main__":
    main()