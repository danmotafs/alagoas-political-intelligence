import os
import json
import math
import pandas as pd
from datetime import datetime


# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================

BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

DATA_DASHBOARD = os.path.join(BASE_DIR, "data", "dashboard", "base_dashboard_v2.json")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard_v2")

os.makedirs(REPORTS_DIR, exist_ok=True)

META_DAVI = 60000

ARQUIVO_HTML = os.path.join(REPORTS_DIR, "relatorio_analitico_dashboard_davi_maia.html")
ARQUIVO_ROTEIRO_CSV = os.path.join(REPORTS_DIR, "roteiro_semanal_visitas_davi_maia.csv")
ARQUIVO_ROTEIRO_JSON = os.path.join(REPORTS_DIR, "roteiro_semanal_visitas_davi_maia.json")
ARQUIVO_HIGHLIGHTS_CSV = os.path.join(REPORTS_DIR, "highlights_dashboard_davi_maia.csv")


# ============================================================
# COORDENADAS APROXIMADAS
# ============================================================
# Usadas para estimar distâncias logísticas.
# A distância calculada é aproximada e serve para planejamento inicial.
# Para uso operacional final, validar no Google Maps/Waze no dia da agenda.
# ============================================================

COORDENADAS = {
    "MACEIÓ": (-9.6498, -35.7089),
    "QUEBRANGULO": (-9.3189, -36.4728),
    "ARAPIRACA": (-9.7525, -36.6615),
    "RIO LARGO": (-9.4783, -35.8533),
    "MARECHAL DEODORO": (-9.7103, -35.8950),
    "PENEDO": (-10.2874, -36.5868),
    "SÃO MIGUEL DOS CAMPOS": (-9.7836, -36.0936),
    "CORURIPE": (-10.1256, -36.1756),
    "DELMIRO GOUVEIA": (-9.3853, -37.9990),
    "PALMEIRA DOS ÍNDIOS": (-9.4057, -36.6328),
    "UNIÃO DOS PALMARES": (-9.1592, -36.0223),
    "SANTANA DO IPANEMA": (-9.3783, -37.2453),
    "ATALAIA": (-9.5019, -36.0228),
    "TEOTÔNIO VILELA": (-9.9166, -36.3492),
    "PILAR": (-9.5972, -35.9561),
    "GIRAU DO PONCIANO": (-9.8842, -36.8289),
    "SÃO SEBASTIÃO": (-9.9339, -36.5542),
    "CAMPO ALEGRE": (-9.7845, -36.3505),
    "MARAGOGI": (-9.0122, -35.2228),
    "SÃO LUÍS DO QUITUNDE": (-9.3182, -35.5606),
    "SÃO JOSÉ DA TAPERA": (-9.5576, -37.3810),
    "QUEBRANGULO": (-9.3189, -36.4728),
    "VIÇOSA": (-9.3751, -36.2400),
    "ANADIA": (-9.6847, -36.3042),
    "IGREJA NOVA": (-10.1250, -36.6612),
    "MATA GRANDE": (-9.1183, -37.7322),
    "TAQUARANA": (-9.6450, -36.4978),
    "ROTEIRO": (-9.8356, -35.9781),
    "PORTO DE PEDRAS": (-9.1606, -35.2958),
    "COQUEIRO SECO": (-9.6372, -35.7997),
    "TANQUE D'ARCA": (-9.5336, -36.4369),
}


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_nome(valor):
    if valor is None:
        return ""

    texto = str(valor).strip().upper()

    substituicoes = {
        "Á": "A",
        "À": "A",
        "Â": "A",
        "Ã": "A",
        "É": "E",
        "Ê": "E",
        "Í": "I",
        "Ó": "O",
        "Ô": "O",
        "Õ": "O",
        "Ú": "U",
        "Ç": "C",
    }

    for origem, destino in substituicoes.items():
        texto = texto.replace(origem, destino)

    return texto


def format_int(valor):
    try:
        return f"{int(round(float(valor))):,}".replace(",", ".")
    except Exception:
        return "0"


def format_pct(valor):
    try:
        return f"{float(valor):.2f}%".replace(".", ",")
    except Exception:
        return "0,00%"


def haversine_km(origem, destino):
    if origem not in COORDENADAS or destino not in COORDENADAS:
        return None

    lat1, lon1 = COORDENADAS[origem]
    lat2, lon2 = COORDENADAS[destino]

    raio_terra = 6371

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distancia_reta = raio_terra * c

    # Fator aproximado para converter distância em linha reta para distância rodoviária.
    distancia_rodoviaria_estimativa = distancia_reta * 1.25

    return round(distancia_rodoviaria_estimativa, 1)


def obter_distancia_logistica(municipio):
    municipio_norm = normalizar_nome(municipio)

    dist_maceio = haversine_km("MACEIÓ", municipio_norm)
    dist_quebrangulo = haversine_km("QUEBRANGULO", municipio_norm)

    if dist_maceio is None:
        dist_maceio = ""
    if dist_quebrangulo is None:
        dist_quebrangulo = ""

    return dist_maceio, dist_quebrangulo


def carregar_json_dashboard():
    if not os.path.exists(DATA_DASHBOARD):
        raise FileNotFoundError(f"Arquivo não encontrado: {DATA_DASHBOARD}")

    with open(DATA_DASHBOARD, "r", encoding="utf-8") as f:
        return json.load(f)


def obter_lista_municipios(dados):
    candidatos = [
        dados.get("municipios"),
        dados.get("dados"),
        dados.get("base"),
        dados.get("rankings", {}).get("ranking_estrategico_top20"),
    ]

    for item in candidatos:
        if isinstance(item, list) and len(item) > 0:
            return item

    return []


def obter_lista_vereadores(dados):
    candidatos = [
        dados.get("ranking_contribuicao_davi_corrigido"),
        dados.get("contribuicao_vereadores_corrigida", {}).get("vereadores_top_500"),
        dados.get("meta_eleitoral_davi_2026", {}).get("ranking_vereadores"),
    ]

    for item in candidatos:
        if isinstance(item, list) and len(item) > 0:
            return item

    return []


def obter_lista_municipios_contribuicao(dados):
    candidatos = [
        dados.get("forca_politica_vereadores_corrigida"),
        dados.get("contribuicao_vereadores_corrigida", {}).get("municipios"),
        dados.get("meta_eleitoral_davi_2026", {}).get("ranking_municipios"),
    ]

    for item in candidatos:
        if isinstance(item, list) and len(item) > 0:
            return item

    return []


def obter_resumo_meta(dados):
    return (
        dados.get("meta_eleitoral_davi_2026", {}).get("resumo_geral")
        or dados.get("contribuicao_vereadores_corrigida", {}).get("resumo_geral")
        or {}
    )


def eh_base_renan_paulo(item):
    """
    Critério operacional inicial para encontrar vereadores/cidades próximos
    da base Renan Filho / Paulo Dantas.

    Como a base ainda pode estar incompleta, usamos múltiplas pistas:
    - grupo_politico_classificacao = Calheiros
    - grupo_politico_padronizado = Grupo Calheiros
    - relação com Davi como aliado/aliado_forte/potencial_aliado
    - partido municipal MDB
    - partido do vereador MDB
    """

    campos = [
        item.get("grupo_politico_classificacao", ""),
        item.get("grupo_politico_padronizado", ""),
        item.get("grupo_politico", ""),
        item.get("relacao_davi_classificacao", ""),
        item.get("relacao_davi", ""),
        item.get("partido_municipio", ""),
        item.get("partido", ""),
    ]

    texto = " ".join([normalizar_nome(campo) for campo in campos])

    if "CALHEIROS" in texto:
        return True

    if "ALIADO_FORTE" in texto or "ALIADO FORTE" in texto:
        return True

    if "ALIADO" in texto:
        return True

    if "POTENCIAL_ALIADO" in texto or "POTENCIAL ALIADO" in texto:
        return True

    if "MDB" in texto:
        return True

    return False


def classificar_corredor_logistico(municipio):
    municipio_norm = normalizar_nome(municipio)

    agreste_quebrangulo = {
        "QUEBRANGULO",
        "PALMEIRA DOS INDIOS",
        "ARAPIRACA",
        "TAQUARANA",
        "IGREJA NOVA",
        "GIRAU DO PONCIANO",
        "SAO SEBASTIAO",
        "VIÇOSA",
        "VICOSA",
        "ANADIA",
        "TANQUE D'ARCA",
    }

    metropolitana = {
        "MACEIO",
        "RIO LARGO",
        "MARECHAL DEODORO",
        "PILAR",
        "ATALAIA",
        "COQUEIRO SECO",
        "SANTA LUZIA DO NORTE",
    }

    litoral_sul_baixo_sao_francisco = {
        "SAO MIGUEL DOS CAMPOS",
        "CORURIPE",
        "PENEDO",
        "TEOTONIO VILELA",
        "CAMPO ALEGRE",
        "ROTEIRO",
    }

    sertao = {
        "DELMIRO GOUVEIA",
        "SANTANA DO IPANEMA",
        "SAO JOSE DA TAPERA",
        "MATA GRANDE",
    }

    litoral_norte = {
        "MARAGOGI",
        "SAO LUIS DO QUITUNDE",
        "PORTO DE PEDRAS",
    }

    if municipio_norm in agreste_quebrangulo:
        return "Eixo Agreste / Quebrangulo"
    if municipio_norm in metropolitana:
        return "Eixo Maceió / Região Metropolitana"
    if municipio_norm in litoral_sul_baixo_sao_francisco:
        return "Eixo Sul / Baixo São Francisco"
    if municipio_norm in sertao:
        return "Eixo Sertão"
    if municipio_norm in litoral_norte:
        return "Eixo Litoral Norte"

    return "Eixo complementar"


def gerar_highlights(dados, df_municipios, df_vereadores, df_municipios_contrib, resumo_meta):
    highlights = []

    indicadores = dados.get("indicadores", {})

    highlights.append({
        "secao": "Visão Geral",
        "highlight": "Base territorial analisada",
        "descricao": (
            f"O painel consolida {format_int(indicadores.get('total_municipios'))} municípios, "
            f"{format_int(indicadores.get('eleitorado_total'))} eleitores e "
            f"{format_int(indicadores.get('vereadores_mapeados'))} vereadores mapeados."
        ),
    })

    highlights.append({
        "secao": "Meta Eleitoral",
        "highlight": "Meta Davi Maia 2026",
        "descricao": (
            f"A meta operacional foi fixada em {format_int(resumo_meta.get('meta_votos_davi_2026', META_DAVI))} votos. "
            f"No cenário conservador de 10%, o potencial bruto mapeado é de "
            f"{format_int(resumo_meta.get('potencial_bruto_10pct'))} votos."
        ),
    })

    if not df_municipios.empty:
        top_municipio = df_municipios.sort_values(
            by="indice_estrategico_pct", ascending=False
        ).iloc[0]

        highlights.append({
            "secao": "Ranking Estratégico",
            "highlight": "Município com maior índice estratégico",
            "descricao": (
                f"{top_municipio.get('municipio')} lidera o ranking estratégico, com eleitorado de "
                f"{format_int(top_municipio.get('eleitorado_2024'))} e índice de "
                f"{format_pct(top_municipio.get('indice_estrategico_pct'))}."
            ),
        })

        nao_visitados = df_municipios[df_municipios.get("visitado_pre_campanha") == False].copy()

        if not nao_visitados.empty:
            top_nao_visitado = nao_visitados.sort_values(
                by="indice_estrategico_pct", ascending=False
            ).iloc[0]

            highlights.append({
                "secao": "Não Visitados",
                "highlight": "Principal cidade prioritária ainda não visitada",
                "descricao": (
                    f"{top_nao_visitado.get('municipio')} aparece como prioridade não visitada, "
                    f"com eleitorado de {format_int(top_nao_visitado.get('eleitorado_2024'))}."
                ),
            })

        margens = df_municipios[
            pd.to_numeric(df_municipios.get("margem_vitoria_pct"), errors="coerce").fillna(0) > 0
        ].copy()

        if not margens.empty:
            menor_margem = margens.sort_values(by="margem_vitoria_pct", ascending=True).iloc[0]

            highlights.append({
                "secao": "Competitividade Municipal",
                "highlight": "Menor margem de vitória",
                "descricao": (
                    f"{menor_margem.get('municipio')} teve margem de vitória de apenas "
                    f"{format_pct(menor_margem.get('margem_vitoria_pct'))}, indicando ambiente político competitivo."
                ),
            })

        score = df_municipios.copy()
        score["score_articulacao_num"] = pd.to_numeric(score.get("score_articulacao"), errors="coerce").fillna(0)

        if not score.empty:
            top_score = score.sort_values(by="score_articulacao_num", ascending=False).iloc[0]

            highlights.append({
                "secao": "Score Político",
                "highlight": "Maior score de articulação",
                "descricao": (
                    f"{top_score.get('municipio')} possui score de articulação de "
                    f"{format_int(top_score.get('score_articulacao'))}. "
                    f"Esse score deve ser lido como priorização operacional, não como previsão eleitoral."
                ),
            })

    if not df_vereadores.empty:
        top_vereador = df_vereadores.sort_values(
            by="contribuicao_davi_20pct", ascending=False
        ).iloc[0]

        highlights.append({
            "secao": "Vereadores",
            "highlight": "Principal contribuição individual potencial",
            "descricao": (
                f"{top_vereador.get('nome_urna') or top_vereador.get('vereador')} em "
                f"{top_vereador.get('municipio')} recebeu {format_int(top_vereador.get('votos'))} votos em 2024. "
                f"No teto operacional de 20%, pode representar {format_int(top_vereador.get('contribuicao_davi_20pct'))} votos potenciais."
            ),
        })

    if not df_municipios_contrib.empty:
        top_cidade_contrib = df_municipios_contrib.sort_values(
            by="contribuicao_davi_20pct", ascending=False
        ).iloc[0]

        highlights.append({
            "secao": "Contribuição por Município",
            "highlight": "Cidade com maior potencial bruto de vereadores",
            "descricao": (
                f"{top_cidade_contrib.get('municipio')} lidera o potencial bruto municipal, "
                f"com {format_int(top_cidade_contrib.get('contribuicao_davi_20pct'))} votos no teto de 20%."
            ),
        })

    return pd.DataFrame(highlights)


def preparar_roteiro(df_vereadores, df_municipios):
    if df_vereadores.empty:
        return pd.DataFrame()

    base = df_vereadores.copy()

    base["municipio_norm"] = base["municipio"].apply(normalizar_nome)
    base["contribuicao_20"] = pd.to_numeric(base.get("contribuicao_davi_20pct"), errors="coerce").fillna(0)
    base["contribuicao_15"] = pd.to_numeric(base.get("contribuicao_davi_15pct"), errors="coerce").fillna(0)
    base["contribuicao_10"] = pd.to_numeric(base.get("contribuicao_davi_10pct"), errors="coerce").fillna(0)
    base["votos_num"] = pd.to_numeric(base.get("votos"), errors="coerce").fillna(0)

    base["base_renan_paulo"] = base.apply(eh_base_renan_paulo, axis=1)

    # Prioridade inicial: base Renan/Paulo Dantas.
    prioritaria = base[base["base_renan_paulo"] == True].copy()

    # Se o filtro ficar pequeno por falta de curadoria, complementa com ranking geral.
    if prioritaria["contribuicao_20"].sum() < META_DAVI:
        complemento = base[base["base_renan_paulo"] == False].copy()
        prioritaria = pd.concat([prioritaria, complemento], ignore_index=True)

    prioritaria = prioritaria.sort_values(
        by=["base_renan_paulo", "contribuicao_20", "votos_num"],
        ascending=[False, False, False]
    ).copy()

    prioritaria["acumulado_20"] = prioritaria["contribuicao_20"].cumsum()
    prioritaria["entra_para_meta"] = prioritaria["acumulado_20"] <= META_DAVI

    # Inclui o vereador que cruza a meta.
    if len(prioritaria[prioritaria["acumulado_20"] >= META_DAVI]) > 0:
        corte = prioritaria[prioritaria["acumulado_20"] >= META_DAVI].index[0]
        prioritaria = prioritaria.loc[:corte].copy()

    # Agrupa por município para montar roteiro de visitas.
    agrupado = (
        prioritaria.groupby("municipio", as_index=False)
        .agg(
            vereadores_prioritarios=("vereador", "count"),
            votos_vereadores_2024=("votos_num", "sum"),
            potencial_10pct=("contribuicao_10", "sum"),
            potencial_15pct=("contribuicao_15", "sum"),
            potencial_20pct=("contribuicao_20", "sum"),
            principal_vereador=("nome_urna", "first"),
            principal_vereador_nome_completo=("vereador", "first"),
            principal_partido=("partido", "first"),
            base_renan_paulo=("base_renan_paulo", "max"),
        )
    )

    # Enriquecimento com indicadores municipais, se disponível.
    if not df_municipios.empty:
        cols = [
            "municipio",
            "eleitorado_2024",
            "indice_estrategico_pct",
            "prefeito",
            "partido",
            "grupo_politico_classificacao",
            "relacao_davi_classificacao",
            "prioridade_final",
            "visitado_pre_campanha",
            "score_articulacao",
        ]

        cols_existentes = [col for col in cols if col in df_municipios.columns]

        agrupado = agrupado.merge(
            df_municipios[cols_existentes].drop_duplicates(subset=["municipio"]),
            on="municipio",
            how="left"
        )

    agrupado["corredor_logistico"] = agrupado["municipio"].apply(classificar_corredor_logistico)

    distancias = agrupado["municipio"].apply(obter_distancia_logistica)
    agrupado["distancia_estimada_maceio_km"] = [item[0] for item in distancias]
    agrupado["distancia_estimada_quebrangulo_km"] = [item[1] for item in distancias]

    agrupado["prioridade_visita_score"] = (
        pd.to_numeric(agrupado["potencial_20pct"], errors="coerce").fillna(0) * 1.0
        + pd.to_numeric(agrupado.get("eleitorado_2024"), errors="coerce").fillna(0) * 0.01
        + pd.to_numeric(agrupado.get("score_articulacao"), errors="coerce").fillna(0) * 10
    )

    agrupado = agrupado.sort_values(
        by=["base_renan_paulo", "prioridade_visita_score", "potencial_20pct"],
        ascending=[False, False, False]
    ).reset_index(drop=True)

    # Distribui em semanas.
    roteiro = []
    semana = 1
    dia_da_semana = ["Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira"]
    idx_dia = 0

    for _, row in agrupado.iterrows():
        municipio = row["municipio"]
        corredor = row["corredor_logistico"]

        distancia_maceio = row.get("distancia_estimada_maceio_km", "")
        distancia_quebrangulo = row.get("distancia_estimada_quebrangulo_km", "")

        if corredor == "Eixo Agreste / Quebrangulo":
            base_saida = "Quebrangulo ou Maceió"
            logica = "Aproveitar vínculo afetivo e territorial com Quebrangulo; concentrar agendas no Agreste."
        elif corredor == "Eixo Maceió / Região Metropolitana":
            base_saida = "Maceió"
            logica = "Agenda curta, com ida e volta no mesmo dia a partir da residência do Davi."
        elif corredor == "Eixo Sul / Baixo São Francisco":
            base_saida = "Maceió"
            logica = "Agrupar visitas no eixo Sul para reduzir deslocamentos e maximizar reuniões em sequência."
        elif corredor == "Eixo Sertão":
            base_saida = "Quebrangulo ou pernoite regional"
            logica = "Rota de maior distância; recomendável agrupar 2 a 3 cidades e avaliar pernoite."
        elif corredor == "Eixo Litoral Norte":
            base_saida = "Maceió"
            logica = "Rota de litoral norte; ideal agrupar agendas próximas no mesmo dia ou em dois dias consecutivos."
        else:
            base_saida = "Maceió"
            logica = "Agenda complementar a ser encaixada conforme disponibilidade política."

        roteiro.append({
            "semana": semana,
            "dia_sugerido": dia_da_semana[idx_dia],
            "municipio": municipio,
            "corredor_logistico": corredor,
            "base_saida_recomendada": base_saida,
            "distancia_estimada_maceio_km": distancia_maceio,
            "distancia_estimada_quebrangulo_km": distancia_quebrangulo,
            "vereadores_prioritarios": int(row.get("vereadores_prioritarios", 0)),
            "principal_vereador": row.get("principal_vereador", ""),
            "principal_vereador_nome_completo": row.get("principal_vereador_nome_completo", ""),
            "principal_partido": row.get("principal_partido", ""),
            "potencial_10pct": int(row.get("potencial_10pct", 0)),
            "potencial_15pct": int(row.get("potencial_15pct", 0)),
            "potencial_20pct": int(row.get("potencial_20pct", 0)),
            "eleitorado_2024": row.get("eleitorado_2024", ""),
            "prefeito": row.get("prefeito", ""),
            "partido_prefeito": row.get("partido", ""),
            "grupo_politico": row.get("grupo_politico_classificacao", ""),
            "relacao_davi": row.get("relacao_davi_classificacao", ""),
            "prioridade_final": row.get("prioridade_final", ""),
            "visitado_pre_campanha": row.get("visitado_pre_campanha", ""),
            "score_articulacao": row.get("score_articulacao", ""),
            "base_renan_paulo_dantas": bool(row.get("base_renan_paulo", False)),
            "objetivo_da_visita": (
                f"Validar apoio político com {row.get('principal_vereador', '')}, "
                f"mapear capacidade real de transferência e pactuar agenda territorial local."
            ),
            "logica_logistica": logica,
            "observacao_metodologica": (
                "Potencial calculado como fração dos votos nominais dos vereadores em 2024. "
                "Não representa previsão de voto nem apoio confirmado."
            ),
        })

        idx_dia += 1

        if idx_dia >= len(dia_da_semana):
            idx_dia = 0
            semana += 1

    df_roteiro = pd.DataFrame(roteiro)

    if not df_roteiro.empty:
        df_roteiro["potencial_20pct_acumulado"] = df_roteiro["potencial_20pct"].cumsum()
        df_roteiro["percentual_meta_acumulado"] = (
            df_roteiro["potencial_20pct_acumulado"] / META_DAVI * 100
        ).round(2)

    return df_roteiro


def tabela_html(df, colunas, limite=20):
    if df is None or df.empty:
        return "<p class='muted'>Sem dados disponíveis para esta seção.</p>"

    df_view = df.copy().head(limite)

    html = "<div class='table-wrap'><table><thead><tr>"

    for titulo, _ in colunas:
        html += f"<th>{titulo}</th>"

    html += "</tr></thead><tbody>"

    for _, row in df_view.iterrows():
        html += "<tr>"

        for _, campo in colunas:
            valor = row.get(campo, "")

            if isinstance(valor, float):
                if math.isnan(valor):
                    valor = ""
                elif "pct" in campo or "percentual" in campo:
                    valor = format_pct(valor)
                else:
                    valor = format_int(valor) if valor.is_integer() else f"{valor:.2f}"

            if isinstance(valor, int):
                valor = format_int(valor)

            html += f"<td>{valor}</td>"

        html += "</tr>"

    html += "</tbody></table></div>"

    return html


def gerar_html(dados, df_municipios, df_vereadores, df_municipios_contrib, df_highlights, df_roteiro, resumo_meta):
    indicadores = dados.get("indicadores", {})

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    top_estrategico = df_municipios.sort_values(
        by="indice_estrategico_pct", ascending=False
    ) if not df_municipios.empty else pd.DataFrame()

    nao_visitados = df_municipios[
        df_municipios.get("visitado_pre_campanha") == False
    ].copy() if not df_municipios.empty and "visitado_pre_campanha" in df_municipios.columns else pd.DataFrame()

    if not nao_visitados.empty:
        nao_visitados = nao_visitados.sort_values(by="indice_estrategico_pct", ascending=False)

    margens = df_municipios.copy()

    if not margens.empty and "margem_vitoria_pct" in margens.columns:
        margens["margem_vitoria_pct_num"] = pd.to_numeric(margens["margem_vitoria_pct"], errors="coerce").fillna(0)
        margens = margens[margens["margem_vitoria_pct_num"] > 0]
        margens = margens.sort_values(by="margem_vitoria_pct_num", ascending=True)

    score = df_municipios.copy()

    if not score.empty and "score_articulacao" in score.columns:
        score["score_articulacao_num"] = pd.to_numeric(score["score_articulacao"], errors="coerce").fillna(0)
        score = score.sort_values(by="score_articulacao_num", ascending=False)

    vereadores_top = df_vereadores.copy()

    if not vereadores_top.empty and "contribuicao_davi_20pct" in vereadores_top.columns:
        vereadores_top["contribuicao_davi_20pct_num"] = pd.to_numeric(
            vereadores_top["contribuicao_davi_20pct"], errors="coerce"
        ).fillna(0)

        vereadores_top = vereadores_top.sort_values(by="contribuicao_davi_20pct_num", ascending=False)

    municipios_contrib = df_municipios_contrib.copy()

    if not municipios_contrib.empty and "contribuicao_davi_20pct" in municipios_contrib.columns:
        municipios_contrib["contribuicao_davi_20pct_num"] = pd.to_numeric(
            municipios_contrib["contribuicao_davi_20pct"], errors="coerce"
        ).fillna(0)

        municipios_contrib = municipios_contrib.sort_values(by="contribuicao_davi_20pct_num", ascending=False)

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Relatório Analítico — Inteligência Territorial e Eleitoral</title>
  <style>
    :root {{
      --green-dark: #063b20;
      --green: #0f5b2d;
      --green-soft: #eaf4ee;
      --gold: #f2c300;
      --text: #0b1726;
      --muted: #64748b;
      --bg: #f5f7f4;
      --white: #ffffff;
      --border: #dbe5df;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      padding: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.45;
    }}

    .page {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 32px;
    }}

    .hero {{
      background: linear-gradient(135deg, var(--green-dark), var(--green));
      color: white;
      border-radius: 28px;
      padding: 44px;
      margin-bottom: 28px;
      box-shadow: 0 18px 50px rgba(0,0,0,.16);
      display: grid;
      grid-template-columns: 1.4fr .8fr;
      gap: 28px;
      align-items: center;
    }}

    .eyebrow {{
      color: var(--gold);
      text-transform: uppercase;
      letter-spacing: 4px;
      font-weight: 800;
      font-size: 13px;
      margin-bottom: 12px;
    }}

    h1 {{
      font-size: 48px;
      line-height: 1.05;
      margin: 0 0 18px;
    }}

    .subtitle {{
      font-size: 18px;
      opacity: .94;
      max-width: 780px;
    }}

    .hero-card {{
      background: rgba(255,255,255,.10);
      border: 1px solid rgba(255,255,255,.20);
      border-radius: 24px;
      padding: 24px;
    }}

    .hero-card h2 {{
      margin: 0 0 8px;
      font-size: 26px;
    }}

    .tag {{
      display: inline-block;
      border: 1px solid rgba(242,195,0,.7);
      color: white;
      padding: 8px 14px;
      border-radius: 999px;
      margin-right: 8px;
      font-size: 13px;
      font-weight: 700;
    }}

    .section {{
      background: var(--white);
      border-radius: 24px;
      padding: 28px;
      margin-bottom: 24px;
      border: 1px solid var(--border);
      box-shadow: 0 8px 24px rgba(15, 23, 42, .05);
    }}

    .section-title {{
      margin: 0 0 6px;
      font-size: 28px;
      color: var(--green-dark);
    }}

    .section-subtitle {{
      margin: 0 0 22px;
      color: var(--muted);
      font-size: 15px;
    }}

    .cards {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }}

    .card {{
      border-top: 5px solid var(--gold);
      background: #fbfdfc;
      border-radius: 18px;
      padding: 18px;
      border-left: 1px solid var(--border);
      border-right: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
    }}

    .card .label {{
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 10px;
    }}

    .card .value {{
      color: var(--green-dark);
      font-size: 28px;
      font-weight: 900;
    }}

    .highlight-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
    }}

    .highlight {{
      background: var(--green-soft);
      border-left: 6px solid var(--green);
      padding: 18px;
      border-radius: 16px;
    }}

    .highlight strong {{
      color: var(--green-dark);
      display: block;
      margin-bottom: 6px;
    }}

    .highlight span {{
      color: var(--muted);
      font-size: 14px;
    }}

    .table-wrap {{
      overflow-x: auto;
      border-radius: 18px;
      border: 1px solid var(--border);
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      background: white;
    }}

    th {{
      background: var(--green-dark);
      color: white;
      text-align: left;
      padding: 12px 10px;
      white-space: nowrap;
    }}

    td {{
      border-bottom: 1px solid #edf2ef;
      padding: 10px;
      vertical-align: top;
    }}

    tr:nth-child(even) td {{
      background: #fbfdfc;
    }}

    .note {{
      border: 1px solid #f4d66a;
      background: #fff9db;
      padding: 16px;
      border-radius: 16px;
      color: #5a4600;
      font-size: 14px;
    }}

    .muted {{
      color: var(--muted);
    }}

    .footer {{
      text-align: center;
      color: var(--muted);
      font-size: 12px;
      padding: 22px;
    }}

    @media print {{
      body {{
        background: white;
      }}
      .page {{
        padding: 0;
      }}
      .section, .hero {{
        box-shadow: none;
        break-inside: avoid;
      }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div>
        <div class="eyebrow">Plataforma de Inteligência Política</div>
        <h1>Relatório Analítico<br>Territorial e Eleitoral</h1>
        <p class="subtitle">
          Síntese executiva do dashboard de pré-campanha de Davi Maia, com highlights estratégicos,
          leitura das principais tabelas e roteiro semanal inicial de visitas orientado pela meta de 60 mil votos.
        </p>
        <div style="margin-top: 22px;">
          <span class="tag">Pré-Campanha 2026</span>
          <span class="tag">Deputado Federal</span>
          <span class="tag">Alagoas</span>
        </div>
      </div>
      <div class="hero-card">
        <h2>Davi Maia</h2>
        <p>Pré-candidato a Deputado Federal</p>
        <p><strong>Gerado em:</strong> {agora}</p>
        <p><strong>Base:</strong> Dashboard V2 — Inteligência Territorial e Eleitoral</p>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">1. Visão Geral dos Indicadores</h2>
      <p class="section-subtitle">Resumo dos principais números consolidados no dashboard.</p>
      <div class="cards">
        <div class="card"><div class="label">Municípios</div><div class="value">{format_int(indicadores.get("total_municipios"))}</div></div>
        <div class="card"><div class="label">Eleitorado</div><div class="value">{format_int(indicadores.get("eleitorado_total"))}</div></div>
        <div class="card"><div class="label">População</div><div class="value">{format_int(indicadores.get("populacao_total"))}</div></div>
        <div class="card"><div class="label">Vereadores mapeados</div><div class="value">{format_int(indicadores.get("vereadores_mapeados"))}</div></div>
        <div class="card"><div class="label">Meta Davi 2026</div><div class="value">{format_int(resumo_meta.get("meta_votos_davi_2026", META_DAVI))}</div></div>
        <div class="card"><div class="label">Potencial 10%</div><div class="value">{format_int(resumo_meta.get("potencial_bruto_10pct"))}</div></div>
        <div class="card"><div class="label">Potencial 15%</div><div class="value">{format_int(resumo_meta.get("potencial_bruto_15pct"))}</div></div>
        <div class="card"><div class="label">Potencial 20%</div><div class="value">{format_int(resumo_meta.get("potencial_bruto_20pct"))}</div></div>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">2. Highlights Executivos</h2>
      <p class="section-subtitle">Principais leituras extraídas automaticamente das tabelas do painel.</p>
      <div class="highlight-grid">
        {''.join([f"<div class='highlight'><strong>{row['secao']} — {row['highlight']}</strong><span>{row['descricao']}</span></div>" for _, row in df_highlights.iterrows()])}
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">3. Ranking Estratégico Territorial</h2>
      <p class="section-subtitle">Municípios com maior índice estratégico, combinando peso eleitoral e relevância territorial.</p>
      {tabela_html(top_estrategico, [
        ("Município", "municipio"),
        ("Eleitorado", "eleitorado_2024"),
        ("Índice Estratégico", "indice_estrategico_pct"),
        ("Prefeito", "prefeito"),
        ("Partido", "partido"),
        ("Prioridade", "prioridade_final"),
      ], limite=15)}
    </section>

    <section class="section">
      <h2 class="section-title">4. Municípios Prioritários Ainda Não Visitados</h2>
      <p class="section-subtitle">Cidades relevantes para priorização de agenda física.</p>
      {tabela_html(nao_visitados, [
        ("Município", "municipio"),
        ("Eleitorado", "eleitorado_2024"),
        ("Índice Estratégico", "indice_estrategico_pct"),
        ("Prefeito", "prefeito"),
        ("Partido", "partido"),
        ("Prioridade", "prioridade_final"),
      ], limite=15)}
    </section>

    <section class="section">
      <h2 class="section-title">5. Força Política dos Vereadores</h2>
      <p class="section-subtitle">Vereadores com maior contribuição potencial corrigida, usando o teto operacional de 20%.</p>
      {tabela_html(vereadores_top, [
        ("Município", "municipio"),
        ("Vereador", "nome_urna"),
        ("Partido", "partido"),
        ("Votos 2024", "votos"),
        ("Potencial 10%", "contribuicao_davi_10pct"),
        ("Potencial 15%", "contribuicao_davi_15pct"),
        ("Potencial 20%", "contribuicao_davi_20pct"),
        ("% Meta 20%", "percentual_meta_davi_20pct"),
      ], limite=25)}
    </section>

    <section class="section">
      <h2 class="section-title">6. Contribuição Potencial por Município</h2>
      <p class="section-subtitle">Cidades com maior concentração de votos potenciais entre vereadores mapeados.</p>
      {tabela_html(municipios_contrib, [
        ("Município", "municipio"),
        ("Vereadores", "vereadores"),
        ("Total de Votos", "total_de_votos"),
        ("Potencial 10%", "contribuicao_davi_10pct"),
        ("Potencial 15%", "contribuicao_davi_15pct"),
        ("Potencial 20%", "contribuicao_davi_20pct"),
        ("% Meta 20%", "percentual_meta_davi_20pct"),
        ("Principal liderança", "principal_lideranca"),
      ], limite=20)}
    </section>

    <section class="section">
      <h2 class="section-title">7. Competitividade Municipal — Menores Margens</h2>
      <p class="section-subtitle">Municípios onde o ambiente político local foi mais competitivo.</p>
      {tabela_html(margens, [
        ("Município", "municipio"),
        ("Prefeito", "prefeito"),
        ("Partido", "partido"),
        ("Segundo colocado", "segundo_colocado"),
        ("Margem %", "margem_vitoria_pct"),
        ("Margem votos", "margem_vitoria_votos"),
      ], limite=12)}
    </section>

    <section class="section">
      <h2 class="section-title">8. Maior Score Político</h2>
      <p class="section-subtitle">Municípios com maior score de articulação no painel.</p>
      {tabela_html(score, [
        ("Município", "municipio"),
        ("Prefeito", "prefeito"),
        ("Partido", "partido"),
        ("Grupo", "grupo_politico_classificacao"),
        ("Relação Davi", "relacao_davi_classificacao"),
        ("Score", "score_articulacao"),
        ("Prioridade", "prioridade_final"),
      ], limite=12)}
    </section>

    <section class="section">
      <h2 class="section-title">9. Roteiro Semanal Inicial de Visitas</h2>
      <p class="section-subtitle">
        Agenda inicial priorizando vereadores/cidades próximos à base Renan Filho / Paulo Dantas,
        com Maceió como residência/base logística e Quebrangulo como referência territorial e afetiva.
      </p>
      <div class="note">
        As distâncias são estimativas logísticas iniciais. Para execução de agenda, validar deslocamento real no Google Maps ou Waze.
        O potencial de votos é cálculo de conversão, não previsão eleitoral nem apoio confirmado.
      </div>
      <br>
      {tabela_html(df_roteiro, [
        ("Semana", "semana"),
        ("Dia", "dia_sugerido"),
        ("Município", "municipio"),
        ("Corredor", "corredor_logistico"),
        ("Base saída", "base_saida_recomendada"),
        ("Dist. Maceió km", "distancia_estimada_maceio_km"),
        ("Dist. Quebrangulo km", "distancia_estimada_quebrangulo_km"),
        ("Vereadores", "vereadores_prioritarios"),
        ("Principal vereador", "principal_vereador"),
        ("Partido", "principal_partido"),
        ("Potencial 20%", "potencial_20pct"),
        ("Acumulado", "potencial_20pct_acumulado"),
        ("% Meta acumulado", "percentual_meta_acumulado"),
      ], limite=40)}
    </section>

    <section class="section">
      <h2 class="section-title">10. Leitura Estratégica Final</h2>
      <p>
        O painel mostra que a meta de 60 mil votos deve ser tratada como uma construção territorial progressiva,
        combinando apoios de vereadores, validação política municipal e presença física nos corredores mais relevantes.
        A estratégia inicial recomendada é começar pela base politicamente mais próxima de Renan Filho e Paulo Dantas,
        priorizando municípios com alto potencial de contribuição e boa viabilidade logística a partir de Maceió e Quebrangulo.
      </p>
      <p>
        O roteiro deve ser lido como uma primeira versão operacional. Após cada visita, recomenda-se atualizar a base com:
        apoio confirmado, apoio em negociação, resistência local, interlocutor responsável, bairros/redutos prioritários e próxima ação.
      </p>
    </section>

    <div class="footer">
      Relatório gerado automaticamente a partir do Dashboard V2 — Alagoas Political Intelligence.
    </div>
  </main>
</body>
</html>
"""

    return html


def main():
    print("=" * 80)
    print("GERAÇÃO DO RELATÓRIO ANALÍTICO E ROTEIRO SEMANAL — DAVI MAIA")
    print("=" * 80)

    dados = carregar_json_dashboard()

    municipios_lista = obter_lista_municipios(dados)
    vereadores_lista = obter_lista_vereadores(dados)
    municipios_contrib_lista = obter_lista_municipios_contribuicao(dados)
    resumo_meta = obter_resumo_meta(dados)

    df_municipios = pd.DataFrame(municipios_lista)
    df_vereadores = pd.DataFrame(vereadores_lista)
    df_municipios_contrib = pd.DataFrame(municipios_contrib_lista)

    print(f"Municípios carregados: {len(df_municipios)}")
    print(f"Vereadores carregados: {len(df_vereadores)}")
    print(f"Municípios com contribuição carregados: {len(df_municipios_contrib)}")

    df_highlights = gerar_highlights(
        dados=dados,
        df_municipios=df_municipios,
        df_vereadores=df_vereadores,
        df_municipios_contrib=df_municipios_contrib,
        resumo_meta=resumo_meta,
    )

    df_roteiro = preparar_roteiro(
        df_vereadores=df_vereadores,
        df_municipios=df_municipios,
    )

    html = gerar_html(
        dados=dados,
        df_municipios=df_municipios,
        df_vereadores=df_vereadores,
        df_municipios_contrib=df_municipios_contrib,
        df_highlights=df_highlights,
        df_roteiro=df_roteiro,
        resumo_meta=resumo_meta,
    )

    with open(ARQUIVO_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    df_highlights.to_csv(ARQUIVO_HIGHLIGHTS_CSV, index=False, encoding="utf-8-sig")
    df_roteiro.to_csv(ARQUIVO_ROTEIRO_CSV, index=False, encoding="utf-8-sig")

    with open(ARQUIVO_ROTEIRO_JSON, "w", encoding="utf-8") as f:
        json.dump(df_roteiro.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

    print()
    print("Arquivos gerados:")
    print(ARQUIVO_HTML)
    print(ARQUIVO_ROTEIRO_CSV)
    print(ARQUIVO_ROTEIRO_JSON)
    print(ARQUIVO_HIGHLIGHTS_CSV)

    if not df_roteiro.empty:
        total_20 = int(df_roteiro["potencial_20pct"].sum())
        ultimo_pct = float(df_roteiro["percentual_meta_acumulado"].max())

        print()
        print("Resumo do roteiro:")
        print(f"Cidades no roteiro: {len(df_roteiro)}")
        print(f"Potencial 20% acumulado: {format_int(total_20)} votos")
        print(f"Percentual da meta: {ultimo_pct:.2f}%")

    print("=" * 80)


if __name__ == "__main__":
    main()