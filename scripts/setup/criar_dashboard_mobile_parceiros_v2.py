import os
import json
import math
import re
import unicodedata
from datetime import datetime

import pandas as pd


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

BASE_DASHBOARD_JSON = os.path.join(
    BASE_DIR,
    "data",
    "dashboard",
    "base_dashboard_v2.json",
)

PARCEIROS_CSV = os.path.join(
    BASE_DIR,
    "data",
    "reference",
    "parceiros_davi_2026.csv",
)

VEREADORES_SECAO_CSV = os.path.join(
    BASE_DIR,
    "data",
    "final",
    "votacao_secao_vereadores_top10.csv",
)

INSTAGRAM_VEREADORES_CSV = os.path.join(
    BASE_DIR,
    "data",
    "reference",
    "instagram_vereadores_2024.csv",
)

MOBILE_DATA_JSON = os.path.join(
    BASE_DIR,
    "data",
    "dashboard",
    "parceiros",
    "mobile_parceiros_v2.json",
)

MOBILE_DIR = os.path.join(BASE_DIR, "dashboard_mobile_parceiros")
CSS_DIR = os.path.join(MOBILE_DIR, "css")
JS_DIR = os.path.join(MOBILE_DIR, "js")

INDEX_HTML = os.path.join(MOBILE_DIR, "index.html")
CSS_FILE = os.path.join(CSS_DIR, "mobile-parceiros.css")
JS_FILE = os.path.join(JS_DIR, "mobile-parceiros.js")

META_DAVI = 60000

os.makedirs(os.path.dirname(MOBILE_DATA_JSON), exist_ok=True)
os.makedirs(MOBILE_DIR, exist_ok=True)
os.makedirs(CSS_DIR, exist_ok=True)
os.makedirs(JS_DIR, exist_ok=True)


# ============================================================
# FUNÇÕES DE DADOS
# ============================================================

def normalizar_texto(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
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

        texto = str(valor).strip().replace(",", ".")

        if texto == "":
            return 0.0

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

    return obj


def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def carregar_parceiros_reference():
    if not os.path.exists(PARCEIROS_CSV):
        return pd.DataFrame()

    return ler_csv(PARCEIROS_CSV)


def carregar_instagram_vereadores():
    if os.path.exists(INSTAGRAM_VEREADORES_CSV):
        df = ler_csv(INSTAGRAM_VEREADORES_CSV)

        if "vereador" not in df.columns:
            return {}

        if "instagram_url" not in df.columns:
            return {}

        mapa = {}

        for _, row in df.iterrows():
            vereador_norm = normalizar_texto(row.get("vereador", ""))
            municipio_norm = normalizar_texto(row.get("municipio", ""))
            chave = f"{municipio_norm}|{vereador_norm}"
            mapa[chave] = str(row.get("instagram_url", "")).strip()

        return mapa

    return {}


def criar_template_instagram_vereadores(vereadores_prioritarios):
    if os.path.exists(INSTAGRAM_VEREADORES_CSV):
        return

    linhas = []

    for item in vereadores_prioritarios:
        linhas.append(
            {
                "municipio": item.get("municipio", ""),
                "vereador": item.get("vereador", ""),
                "partido": item.get("partido_vereador", ""),
                "instagram_url": "",
                "observacao": "Preencher manualmente com o link oficial do Instagram do vereador.",
            }
        )

    df = pd.DataFrame(linhas).drop_duplicates(
        subset=["municipio", "vereador", "partido"]
    )

    os.makedirs(os.path.dirname(INSTAGRAM_VEREADORES_CSV), exist_ok=True)
    df.to_csv(INSTAGRAM_VEREADORES_CSV, index=False, encoding="utf-8-sig")


def carregar_estatisticas_municipios_vereadores():
    """
    Calcula:
    - votos totais na base de vereadores 2024 por município;
    - votos do PSD na base de vereadores 2024 por município.

    Observação:
    esse cálculo usa a base territorial disponível no projeto.
    """
    if not os.path.exists(VEREADORES_SECAO_CSV):
        return {}

    df = ler_csv(VEREADORES_SECAO_CSV)

    if "municipio" not in df.columns or "votos" not in df.columns:
        return {}

    df["municipio_norm"] = df["municipio"].apply(normalizar_texto)
    df["votos_num"] = df["votos"].apply(converter_int)

    if "partido" in df.columns:
        df["partido_norm"] = df["partido"].apply(normalizar_texto)
    else:
        df["partido_norm"] = ""

    total = (
        df.groupby("municipio_norm", as_index=False)
        .agg(votos_totais_cidade=("votos_num", "sum"))
    )

    psd = (
        df[df["partido_norm"] == "PSD"]
        .groupby("municipio_norm", as_index=False)
        .agg(votos_psd_cidade=("votos_num", "sum"))
    )

    base = total.merge(psd, on="municipio_norm", how="left")
    base["votos_psd_cidade"] = base["votos_psd_cidade"].fillna(0).astype(int)

    mapa = {}

    for _, row in base.iterrows():
        mapa[row["municipio_norm"]] = {
            "votos_totais_cidade": int(row["votos_totais_cidade"]),
            "votos_psd_cidade": int(row["votos_psd_cidade"]),
        }

    return mapa


def encontrar_foto_parceiro(id_parceiro, nome_parceiro, row_reference):
    """
    Prioridade:
    1. coluna foto_parceiro no CSV de referência;
    2. busca automática por arquivo com nome do parceiro;
    3. vazio, para usar iniciais no front.
    """

    possiveis_colunas = [
        "foto_parceiro",
        "imagem_parceiro",
        "foto",
        "imagem",
        "avatar",
    ]

    for col in possiveis_colunas:
        if col in row_reference and str(row_reference.get(col, "")).strip():
            caminho = str(row_reference.get(col, "")).strip()
            return caminho.replace("\\", "/")

    termos = [
        id_parceiro,
        nome_parceiro,
        nome_parceiro.lower().replace(" ", "-"),
        nome_parceiro.lower().replace(" ", "_"),
    ]

    extensoes = [".png", ".jpg", ".jpeg", ".webp"]

    pastas_busca = [
        os.path.join(BASE_DIR, "dashboard_mobile_parceiros", "assets"),
        os.path.join(BASE_DIR, "parceiros", id_parceiro),
        os.path.join(BASE_DIR, "parceiros", id_parceiro, "assets"),
        os.path.join(BASE_DIR, "dashboard_v2", "assets"),
        os.path.join(BASE_DIR, "assets"),
        os.path.join(BASE_DIR, "public"),
    ]

    for pasta in pastas_busca:
        if not os.path.exists(pasta):
            continue

        for raiz, _, arquivos in os.walk(pasta):
            for arquivo in arquivos:
                nome_arquivo_norm = normalizar_texto(arquivo)

                if not any(arquivo.lower().endswith(ext) for ext in extensoes):
                    continue

                for termo in termos:
                    termo_norm = normalizar_texto(termo)

                    if termo_norm and termo_norm in nome_arquivo_norm:
                        caminho_abs = os.path.join(raiz, arquivo)
                        caminho_rel = os.path.relpath(caminho_abs, MOBILE_DIR)
                        return caminho_rel.replace("\\", "/")

    return ""


def preparar_mobile_data():
    base = carregar_json(BASE_DASHBOARD_JSON)
    modulo = base.get("parceiros_estrategicos_2026", {})

    resumo_por_parceiro = modulo.get("resumo_por_parceiro", [])
    top_convergencias = modulo.get("top_convergencias", [])
    vereadores_prioritarios = modulo.get("vereadores_prioritarios", [])
    resumo_municipios = modulo.get("resumo_municipios", [])
    territorial_parceiros = modulo.get("territorial_parceiros", [])

    criar_template_instagram_vereadores(vereadores_prioritarios)

    instagram_map = carregar_instagram_vereadores()
    stats_municipios = carregar_estatisticas_municipios_vereadores()
    parceiros_ref = carregar_parceiros_reference()

    parceiros_ref_map = {}

    if not parceiros_ref.empty and "id_parceiro" in parceiros_ref.columns:
        for _, row in parceiros_ref.iterrows():
            parceiros_ref_map[str(row.get("id_parceiro", "")).strip()] = row.to_dict()

    parceiros = []

    for resumo in resumo_por_parceiro:
        nome_parceiro = resumo.get("nome_parceiro", "")
        id_parceiro = ""

        territorial = None

        for item in territorial_parceiros:
            nome_item = item.get("parceiro", {}).get("nome_parceiro", "")
            id_item = item.get("metadata", {}).get("id_parceiro", "")

            if normalizar_texto(nome_item) == normalizar_texto(nome_parceiro):
                territorial = item
                id_parceiro = id_item
                break

        if not id_parceiro:
            id_parceiro = normalizar_texto(nome_parceiro).lower().replace(" ", "-")

        ref = parceiros_ref_map.get(id_parceiro, {})

        foto = encontrar_foto_parceiro(id_parceiro, nome_parceiro, ref)

        info_parceiro = territorial.get("parceiro", {}) if territorial else {}
        candidato = territorial.get("candidato_identificado", {}) if territorial else {}
        resumo_territorial = territorial.get("resumo", {}) if territorial else {}

        votos_2022 = resumo_territorial.get("total_votos_parceiro") or candidato.get("votos_total_auditoria") or 0

        cidades = []

        for item in resumo_municipios:
            if normalizar_texto(item.get("nome_parceiro", "")) != normalizar_texto(nome_parceiro):
                continue

            municipio = item.get("municipio", "")
            municipio_norm = normalizar_texto(municipio)
            stats = stats_municipios.get(municipio_norm, {})

            votos_parceiro_cidade = converter_int(item.get("votos_parceiro_nos_locais", 0))
            potencial = converter_int(item.get("potencial_davi_20pct_local", 0))

            cidades.append(
                {
                    "municipio": municipio,
                    "votos_totais_cidade": stats.get("votos_totais_cidade", 0),
                    "votos_parceiro_cidade": votos_parceiro_cidade,
                    "votos_psd_cidade": stats.get("votos_psd_cidade", 0),
                    "vereadores_convergentes": converter_int(item.get("vereadores_convergentes", 0)),
                    "locais_convergentes": converter_int(item.get("locais_convergentes", 0)),
                    "potencial_votos": potencial,
                    "maior_indice_convergencia": converter_float(item.get("maior_indice_convergencia", 0)),
                }
            )

        cidades = sorted(
            cidades,
            key=lambda x: (
                x["potencial_votos"],
                x["votos_parceiro_cidade"],
                x["vereadores_convergentes"],
            ),
            reverse=True,
        )

        abordagem = []

        for item in vereadores_prioritarios:
            if normalizar_texto(item.get("nome_parceiro", "")) != normalizar_texto(nome_parceiro):
                continue

            municipio = item.get("municipio", "")
            vereador = item.get("vereador", "")
            chave_instagram = f"{normalizar_texto(municipio)}|{normalizar_texto(vereador)}"

            abordagem.append(
                {
                    "municipio": municipio,
                    "local_votacao": item.get("local_votacao_parceiro", ""),
                    "vereador": vereador,
                    "partido_vereador": item.get("partido_vereador", ""),
                    "instagram_url": instagram_map.get(chave_instagram, ""),
                    "votos_parceiro_local": converter_int(item.get("votos_parceiro_local", 0)),
                    "votos_vereador_local": converter_int(item.get("votos_vereador_local", 0)),
                    "potencial_votos": converter_int(item.get("potencial_davi_20pct_local", 0)),
                    "indice_convergencia": converter_float(item.get("indice_convergencia", 0)),
                }
            )

        abordagem = sorted(
            abordagem,
            key=lambda x: (
                x["potencial_votos"],
                x["votos_parceiro_local"],
                x["votos_vereador_local"],
            ),
            reverse=True,
        )

        relevancia = [
            {
                "tipo": "parceiro",
                "nome": nome_parceiro,
                "valor": converter_int(resumo.get("potencial_vereadores_unicos_20pct", 0)),
                "percentual_meta": round(
                    converter_int(resumo.get("potencial_vereadores_unicos_20pct", 0)) / META_DAVI * 100,
                    2,
                ),
            }
        ]

        for item in abordagem[:10]:
            relevancia.append(
                {
                    "tipo": "vereador",
                    "nome": item["vereador"],
                    "municipio": item["municipio"],
                    "valor": item["potencial_votos"],
                    "percentual_meta": round(item["potencial_votos"] / META_DAVI * 100, 2),
                }
            )

        parceiros.append(
            {
                "id_parceiro": id_parceiro,
                "nome_parceiro": nome_parceiro,
                "foto_parceiro": foto,
                "cargo_atual": info_parceiro.get("cargo_atual") or candidato.get("cargo") or "Parceiro político",
                "votos_2022": converter_int(votos_2022),
                "municipios_convergencia": converter_int(resumo.get("municipios_com_convergencia", 0)),
                "vereadores_convergentes": converter_int(resumo.get("vereadores_convergentes", 0)),
                "potencial_votos": converter_int(resumo.get("potencial_vereadores_unicos_20pct", 0)),
                "percentual_meta": converter_float(resumo.get("percentual_meta_davi_20pct", 0)),
                "principal_municipio": resumo.get("principal_municipio", ""),
                "principal_local_votacao": resumo.get("principal_local_votacao", ""),
                "cidades": cidades,
                "abordagem": abordagem,
                "relevancia": relevancia,
            }
        )

    dados = {
        "metadata": {
            "titulo": "Dashboard Mobile Parceiros — Davi Maia 2026",
            "versao": "v2",
            "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fonte": "base_dashboard_v2.json + módulo de parceiros estratégicos",
            "observacao": (
                "Versão simplificada para decisão rápida em celular. "
                "O painel completo continua sendo a base analítica."
            ),
        },
        "meta_davi_2026": META_DAVI,
        "legendas": {
            "municipios_convergencia": (
                "Municípios onde o parceiro teve presença eleitoral em 2022 "
                "e existem vereadores com votação relevante em 2024 nos mesmos territórios."
            ),
            "potencial_votos": (
                "Estimativa operacional considerando 20% dos votos dos vereadores convergentes únicos."
            ),
            "votos_psd": (
                "Votos do PSD na base territorial de vereadores 2024 disponível no projeto."
            ),
        },
        "parceiros": parceiros,
    }

    dados = limpar_json(dados)

    with open(MOBILE_DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2, allow_nan=False)

    return dados


# ============================================================
# ARQUIVOS DO FRONTEND MOBILE
# ============================================================

HTML = r'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <title>Painel Mobile — Parceiros Davi Maia 2026</title>

  <link rel="stylesheet" href="css/mobile-parceiros.css?v=2" />
</head>

<body>
  <main class="app-shell">
    <header class="hero">
      <div class="topbar">
        <a href="../dashboard_v2/" class="back-link">← Painel completo</a>
        <span class="tag">Mobile</span>
      </div>

      <p class="eyebrow yellow">Rede Davi Maia 2026</p>
      <h1>Parceiros Estratégicos</h1>
      <p class="subtitle">
        Decisão rápida: quem ajuda, onde ajuda, com quais vereadores e com qual potencial de votos.
      </p>
    </header>

    <section class="section compact">
      <p class="eyebrow">Selecionar parceiro</p>
      <h2>Quem vai abrir território?</h2>
      <div id="partner-selector" class="partner-selector">
        <div class="loading-card">Carregando parceiros...</div>
      </div>
    </section>

    <section id="partner-detail" class="partner-detail hidden">
      <div class="partner-profile-card">
        <div id="partner-avatar" class="partner-avatar">
          <span>--</span>
        </div>

        <div class="partner-profile-info">
          <p class="eyebrow">Parceiro selecionado</p>
          <h2 id="partner-name">-</h2>
          <p id="partner-role">-</p>
        </div>
      </div>

      <section class="metric-grid">
        <article class="metric-card featured">
          <small>Votos em 2022</small>
          <strong id="metric-votos-2022">-</strong>
          <span>Capital eleitoral do parceiro</span>
        </article>

        <article class="metric-card info">
          <small>Municípios em convergência</small>
          <strong id="metric-municipios">-</strong>
          <span id="legend-municipios">Municípios com sobreposição territorial.</span>
        </article>

        <article class="metric-card">
          <small>Vereadores</small>
          <strong id="metric-vereadores">-</strong>
          <span>Prioritários para abordagem</span>
        </article>

        <article class="metric-card featured">
          <small>Potencial de votos</small>
          <strong id="metric-potencial">-</strong>
          <span class="footnote">considerando 20% dos votos dos vereadores convergentes únicos</span>
        </article>

        <article class="metric-card">
          <small>% da meta</small>
          <strong id="metric-percentual-meta">-</strong>
          <span>Meta Davi: 60 mil votos</span>
        </article>
      </section>

      <section class="decision-card">
        <p class="eyebrow">Decisão rápida</p>
        <h2 id="quick-decision-title">-</h2>
        <p id="quick-decision-text">-</p>
      </section>

      <section class="section">
        <p class="eyebrow">Principais cidades</p>
        <h2>Cidades onde o parceiro mais ajuda</h2>
        <div id="top-cities" class="list-stack"></div>
      </section>

      <section class="section">
        <p class="eyebrow">Locais + vereadores</p>
        <h2>Onde visitar e quem abordar</h2>
        <div id="school-vereador-list" class="list-stack"></div>
      </section>

      <section class="section">
        <p class="eyebrow">Relevância para a meta</p>
        <h2>Impacto estimado na meta de 60 mil votos</h2>

        <div id="impact-tabs" class="impact-tabs"></div>

        <div class="impact-card">
          <div class="impact-header">
            <div>
              <strong id="impact-title">-</strong>
              <span id="impact-subtitle">-</span>
            </div>
            <strong id="impact-value">-</strong>
          </div>

          <div class="progress-wrap">
            <div id="impact-bar" class="progress-bar"></div>
          </div>

          <p id="impact-note" class="impact-note">-</p>
        </div>
      </section>
    </section>

    <section id="empty-state" class="empty-state hidden">
      <h2>Nenhum parceiro processado ainda</h2>
      <p>O painel mobile será preenchido automaticamente pelo painel completo.</p>
    </section>
  </main>

  <script src="js/mobile-parceiros.js?v=2"></script>
</body>
</html>
'''


CSS = r'''* {
  box-sizing: border-box;
}

:root {
  --blue-dark: #071b4d;
  --blue: #1f4591;
  --yellow: #ffe100;
  --pink: #dd4f99;
  --text: #071b4d;
  --muted: #64748b;
  --line: #dce4f2;
  --bg: #f3f6fb;
  --white: #ffffff;
  --green: #16a34a;
}

body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
  color: var(--text);
  background:
    radial-gradient(circle at top right, rgba(255, 225, 0, .18), transparent 28%),
    radial-gradient(circle at top left, rgba(221, 79, 153, .13), transparent 28%),
    var(--bg);
}

.app-shell {
  width: 100%;
  max-width: 520px;
  margin: 0 auto;
  padding: 14px;
  padding-bottom: 36px;
}

.hero {
  background: linear-gradient(145deg, var(--blue-dark), var(--blue));
  color: white;
  border-radius: 28px;
  padding: 22px;
  min-height: 250px;
  box-shadow: 0 18px 45px rgba(7, 27, 77, .22);
  position: relative;
  overflow: hidden;
}

.hero::after {
  content: "";
  position: absolute;
  width: 180px;
  height: 180px;
  right: -60px;
  bottom: -60px;
  border-radius: 50%;
  background: rgba(255, 225, 0, .22);
}

.topbar {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 34px;
}

.back-link {
  text-decoration: none;
  color: var(--blue-dark);
  background: white;
  border-radius: 999px;
  padding: 9px 13px;
  font-size: 13px;
  font-weight: 800;
}

.tag {
  border: 1px solid rgba(255, 255, 255, .35);
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 800;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--pink);
  text-transform: uppercase;
  letter-spacing: .11em;
  font-size: 11px;
  font-weight: 900;
}

.eyebrow.yellow {
  color: var(--yellow);
}

.hero h1 {
  position: relative;
  z-index: 1;
  margin: 0;
  font-size: 40px;
  line-height: .98;
}

.subtitle {
  position: relative;
  z-index: 1;
  max-width: 360px;
  margin: 16px 0 0;
  color: rgba(255, 255, 255, .9);
  font-size: 15px;
  line-height: 1.5;
}

.section {
  background: rgba(255, 255, 255, .94);
  border: 1px solid rgba(220, 228, 242, .9);
  border-radius: 24px;
  padding: 18px;
  margin-top: 16px;
  box-shadow: 0 12px 30px rgba(7, 27, 77, .08);
}

.section h2 {
  margin: 0 0 12px;
  font-size: 22px;
  line-height: 1.12;
}

.partner-selector {
  display: flex;
  overflow-x: auto;
  gap: 12px;
  padding: 4px 0 8px;
  scroll-snap-type: x mandatory;
}

.partner-button {
  min-width: 150px;
  max-width: 150px;
  scroll-snap-align: start;
  border: 1px solid var(--line);
  background: white;
  border-radius: 22px;
  padding: 12px;
  text-align: left;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(7, 27, 77, .06);
}

.partner-button.active {
  border: 2px solid var(--yellow);
  background: #fffbe6;
}

.partner-thumb {
  width: 70px;
  height: 70px;
  border-radius: 22px;
  background: linear-gradient(145deg, var(--blue-dark), var(--blue));
  color: var(--yellow);
  display: grid;
  place-items: center;
  font-weight: 900;
  font-size: 20px;
  margin-bottom: 10px;
  overflow: hidden;
}

.partner-thumb img,
.partner-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.partner-button strong {
  display: block;
  font-size: 14px;
  line-height: 1.2;
}

.partner-button span {
  display: block;
  color: var(--muted);
  font-size: 12px;
  margin-top: 5px;
}

.loading-card {
  color: var(--muted);
  padding: 18px;
}

.hidden {
  display: none !important;
}

.partner-profile-card {
  display: grid;
  grid-template-columns: 92px 1fr;
  gap: 14px;
  align-items: center;
  margin-top: 16px;
  background: white;
  border: 1px solid var(--line);
  border-radius: 26px;
  padding: 14px;
  box-shadow: 0 12px 30px rgba(7, 27, 77, .08);
}

.partner-avatar {
  width: 92px;
  height: 92px;
  border-radius: 26px;
  background: linear-gradient(145deg, var(--blue-dark), var(--blue));
  display: grid;
  place-items: center;
  color: var(--yellow);
  font-weight: 900;
  font-size: 26px;
  overflow: hidden;
}

.partner-profile-info h2 {
  margin: 0 0 6px;
  font-size: 25px;
  line-height: 1.08;
}

.partner-profile-info p {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
}

.metric-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 16px;
}

.metric-card {
  background: white;
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 15px;
  min-height: 118px;
  box-shadow: 0 8px 20px rgba(7, 27, 77, .06);
}

.metric-card.featured {
  border-top: 5px solid var(--yellow);
}

.metric-card small,
.mini-stat small {
  display: block;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .08em;
  font-size: 10px;
  font-weight: 900;
  margin-bottom: 10px;
}

.metric-card strong {
  display: block;
  color: var(--blue-dark);
  font-size: 28px;
  line-height: 1;
}

.metric-card span {
  display: block;
  margin-top: 9px;
  color: var(--muted);
  font-size: 12px;
}

.footnote {
  font-size: 10px !important;
  line-height: 1.35;
}

.decision-card {
  margin-top: 16px;
  border-radius: 26px;
  padding: 20px;
  background: linear-gradient(145deg, #fff9db, #ffffff);
  border: 1px solid #f4d66a;
}

.decision-card h2 {
  margin: 0 0 10px;
  font-size: 23px;
}

.decision-card p {
  margin: 0;
  color: #514100;
  font-size: 14px;
  line-height: 1.55;
}

.list-stack {
  display: grid;
  gap: 10px;
}

.item-card {
  background: white;
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 14px;
}

.item-card-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.item-card h3 {
  margin: 0;
  font-size: 16px;
  line-height: 1.24;
}

.item-card p {
  margin: 7px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.45;
}

.badge,
.link-button {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 6px 9px;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
  background: #eef3ff;
  color: var(--blue-dark);
  text-decoration: none;
}

.link-button {
  background: #dcfce7;
  color: #166534;
}

.link-button.disabled {
  background: #f1f5f9;
  color: #64748b;
  pointer-events: none;
}

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 10px;
}

.mini-stat {
  border-radius: 14px;
  background: #f8fafc;
  padding: 9px;
}

.mini-stat strong {
  display: block;
  color: var(--blue-dark);
  font-size: 17px;
  margin-top: 3px;
}

.impact-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 10px;
}

.impact-tab {
  border: 1px solid var(--line);
  background: white;
  border-radius: 999px;
  padding: 9px 12px;
  white-space: nowrap;
  color: var(--blue-dark);
  font-weight: 900;
  font-size: 12px;
}

.impact-tab.active {
  background: var(--blue-dark);
  color: white;
}

.impact-card {
  background: white;
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 16px;
}

.impact-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.impact-header strong {
  display: block;
  font-size: 18px;
}

.impact-header span {
  display: block;
  margin-top: 4px;
  color: var(--muted);
  font-size: 12px;
}

.progress-wrap {
  margin-top: 16px;
  width: 100%;
  height: 18px;
  background: #edf2f7;
  border-radius: 999px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  width: 0%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--yellow), var(--green));
  transition: width .25s ease;
}

.impact-note {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.4;
}

.empty-state {
  margin-top: 16px;
  background: white;
  border: 1px solid var(--line);
  border-radius: 24px;
  padding: 22px;
}

@media (max-width: 380px) {
  .hero h1 {
    font-size: 34px;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }
}
'''


JS = r'''const DATA_URL = "../data/dashboard/parceiros/mobile_parceiros_v2.json";

let data = null;
let parceiros = [];
let selecionado = null;
let impactoAtualIndex = 0;

function fmtInt(value) {
  return Number(value || 0).toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}

function fmtPct(value) {
  return `${Number(value || 0).toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`;
}

function safe(value, fallback = "-") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function initials(name) {
  const parts = safe(name, "").trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "--";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function imageOrInitials(src, name) {
  if (!src) return `<span>${initials(name)}</span>`;

  return `<img src="${src}" alt="${safe(name)}" onerror="this.parentElement.innerHTML='<span>${initials(name)}</span>'" />`;
}

function renderSelector() {
  const el = document.getElementById("partner-selector");
  if (!el) return;

  if (!parceiros.length) {
    el.innerHTML = `<div class="loading-card">Nenhum parceiro processado.</div>`;
    return;
  }

  el.innerHTML = parceiros.map((p, index) => {
    const active = selecionado?.id_parceiro === p.id_parceiro ? "active" : "";

    return `
      <button class="partner-button ${active}" data-index="${index}" type="button">
        <div class="partner-thumb">${imageOrInitials(p.foto_parceiro, p.nome_parceiro)}</div>
        <strong>${safe(p.nome_parceiro)}</strong>
        <span>${safe(p.cargo_atual)}</span>
        <span>Potencial de votos: ${fmtInt(p.potencial_votos)}</span>
      </button>
    `;
  }).join("");

  el.querySelectorAll(".partner-button").forEach((btn) => {
    btn.addEventListener("click", () => selecionarParceiro(Number(btn.dataset.index)));
  });
}

function itemCard({ title, badge, description, stats }) {
  const statsHtml = Array.isArray(stats)
    ? `
      <div class="two-col">
        ${stats.map((s) => `
          <div class="mini-stat">
            <small>${s.label}</small>
            <strong>${s.value}</strong>
          </div>
        `).join("")}
      </div>
    `
    : "";

  return `
    <article class="item-card">
      <div class="item-card-header">
        <h3>${safe(title)}</h3>
        ${badge || ""}
      </div>
      ${description ? `<p>${description}</p>` : ""}
      ${statsHtml}
    </article>
  `;
}

function renderCidades(p) {
  const el = document.getElementById("top-cities");
  if (!el) return;

  const cidades = Array.isArray(p.cidades) ? p.cidades.slice(0, 6) : [];

  if (!cidades.length) {
    el.innerHTML = itemCard({
      title: "Sem cidades processadas",
      description: "As cidades aparecerão após o processamento do painel completo.",
    });
    return;
  }

  el.innerHTML = cidades.map((c, index) => {
    return itemCard({
      title: `${index + 1}. ${safe(c.municipio)}`,
      badge: `<span class="badge">Total: ${fmtInt(c.votos_totais_cidade)}</span>`,
      description: data.legendas?.municipios_convergencia || "Município com convergência territorial.",
      stats: [
        { label: "Votos parceiro", value: fmtInt(c.votos_parceiro_cidade) },
        { label: "Votos PSD", value: fmtInt(c.votos_psd_cidade) },
        { label: "Vereadores", value: fmtInt(c.vereadores_convergentes) },
        { label: "Potencial de votos", value: fmtInt(c.potencial_votos) },
      ],
    });
  }).join("");
}

function vereadorButton(item) {
  if (item.instagram_url) {
    return `<a class="link-button" href="${item.instagram_url}" target="_blank" rel="noopener noreferrer">${safe(item.vereador)}</a>`;
  }

  return `<span class="link-button disabled">${safe(item.vereador)}</span>`;
}

function renderLocaisEVereadores(p) {
  const el = document.getElementById("school-vereador-list");
  if (!el) return;

  const lista = Array.isArray(p.abordagem) ? p.abordagem.slice(0, 12) : [];

  if (!lista.length) {
    el.innerHTML = itemCard({
      title: "Sem locais e vereadores processados",
      description: "Os dados aparecerão após o cruzamento territorial.",
    });
    return;
  }

  el.innerHTML = lista.map((item, index) => {
    return itemCard({
      title: `${index + 1}. ${safe(item.local_votacao)}`,
      badge: `<span class="badge">${safe(item.partido_vereador, "Partido não informado")}</span>`,
      description: `${safe(item.municipio)} · Vereador: ${vereadorButton(item)}`,
      stats: [
        { label: "Votos parceiro", value: fmtInt(item.votos_parceiro_local) },
        { label: "Votos vereador", value: fmtInt(item.votos_vereador_local) },
        { label: "Potencial de votos", value: fmtInt(item.potencial_votos) },
        { label: "Instagram", value: item.instagram_url ? "abrir" : "a preencher" },
      ],
    });
  }).join("");
}

function renderImpactTabs(p) {
  const el = document.getElementById("impact-tabs");
  if (!el) return;

  const lista = Array.isArray(p.relevancia) ? p.relevancia : [];

  if (!lista.length) {
    el.innerHTML = "";
    return;
  }

  el.innerHTML = lista.map((item, index) => {
    const active = index === impactoAtualIndex ? "active" : "";

    return `
      <button class="impact-tab ${active}" data-index="${index}" type="button">
        ${safe(item.nome)}
      </button>
    `;
  }).join("");

  el.querySelectorAll(".impact-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      impactoAtualIndex = Number(btn.dataset.index);
      renderImpacto(p);
      renderImpactTabs(p);
    });
  });
}

function renderImpacto(p) {
  const lista = Array.isArray(p.relevancia) ? p.relevancia : [];
  const item = lista[impactoAtualIndex] || lista[0];

  if (!item) {
    setText("impact-title", "Sem dados de impacto");
    setText("impact-subtitle", "-");
    setText("impact-value", "-");
    setText("impact-note", "O impacto aparecerá após o processamento dos parceiros.");
    return;
  }

  const pct = Number(item.percentual_meta || 0);
  const width = Math.min(100, Math.max(0, pct));

  setText("impact-title", item.nome);
  setText("impact-subtitle", item.tipo === "parceiro" ? "Impacto do parceiro na meta" : `Vereador · ${safe(item.municipio)}`);
  setText("impact-value", `${fmtInt(item.valor)} votos`);
  setText("impact-note", `${fmtPct(pct)} da meta de 60 mil votos do Davi.`);

  const bar = document.getElementById("impact-bar");
  if (bar) bar.style.width = `${width}%`;
}

function renderDetalhe(p) {
  document.getElementById("partner-detail")?.classList.remove("hidden");
  document.getElementById("empty-state")?.classList.add("hidden");

  setText("partner-name", p.nome_parceiro);
  setText("partner-role", p.cargo_atual);

  const avatar = document.getElementById("partner-avatar");
  if (avatar) {
    avatar.innerHTML = imageOrInitials(p.foto_parceiro, p.nome_parceiro);
  }

  setText("metric-votos-2022", fmtInt(p.votos_2022));
  setText("metric-municipios", fmtInt(p.municipios_convergencia));
  setText("metric-vereadores", fmtInt(p.vereadores_convergentes));
  setText("metric-potencial", fmtInt(p.potencial_votos));
  setText("metric-percentual-meta", fmtPct(p.percentual_meta));

  const legend = document.getElementById("legend-municipios");
  if (legend) legend.textContent = data.legendas?.municipios_convergencia || legend.textContent;

  setText("quick-decision-title", `${p.nome_parceiro} ajuda principalmente em ${safe(p.principal_municipio)}`);
  setText(
    "quick-decision-text",
    `Priorizar agendas nos locais onde há sobreposição entre votos do parceiro e votos de vereadores. Local de maior atenção: ${safe(p.principal_local_votacao)}.`
  );

  renderCidades(p);
  renderLocaisEVereadores(p);

  impactoAtualIndex = 0;
  renderImpactTabs(p);
  renderImpacto(p);
}

function selecionarParceiro(index) {
  selecionado = parceiros[index];
  renderSelector();
  renderDetalhe(selecionado);
}

async function init() {
  try {
    const response = await fetch(`${DATA_URL}?v=mobile-parceiros-v2-${Date.now()}`);

    if (!response.ok) {
      throw new Error(`Erro HTTP ${response.status}`);
    }

    data = await response.json();
    parceiros = Array.isArray(data.parceiros) ? data.parceiros : [];

    if (!parceiros.length) {
      document.getElementById("empty-state")?.classList.remove("hidden");
      renderSelector();
      return;
    }

    selecionarParceiro(0);
  } catch (error) {
    console.error("Erro ao carregar dashboard mobile:", error);

    const empty = document.getElementById("empty-state");

    if (empty) {
      empty.classList.remove("hidden");
      empty.innerHTML = `
        <h2>Erro ao carregar dados</h2>
        <p>${error.message}</p>
      `;
    }
  }
}

document.addEventListener("DOMContentLoaded", init);
'''


def escrever_frontend():
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(HTML)

    with open(CSS_FILE, "w", encoding="utf-8") as f:
        f.write(CSS)

    with open(JS_FILE, "w", encoding="utf-8") as f:
        f.write(JS)


def main():
    print("=" * 80)
    print("DASHBOARD MOBILE PARCEIROS V2 — GERAÇÃO COMPLETA")
    print("=" * 80)

    dados = preparar_mobile_data()
    escrever_frontend()

    print("Arquivos atualizados:")
    print(MOBILE_DATA_JSON)
    print(INDEX_HTML)
    print(CSS_FILE)
    print(JS_FILE)

    print()
    print("Parceiros no mobile:")
    for p in dados.get("parceiros", []):
        print(
            f"- {p['nome_parceiro']} | "
            f"votos 2022: {p['votos_2022']} | "
            f"potencial: {p['potencial_votos']} | "
            f"vereadores: {p['vereadores_convergentes']}"
        )

    print()
    print("Template de Instagram dos vereadores:")
    print(INSTAGRAM_VEREADORES_CSV)

    print()
    print("Teste local:")
    print("http://localhost:8000/dashboard_mobile_parceiros/?v=mobile-parceiros-v2")
    print("=" * 80)


if __name__ == "__main__":
    main()