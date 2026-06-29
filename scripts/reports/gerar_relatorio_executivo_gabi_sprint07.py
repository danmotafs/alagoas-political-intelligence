from __future__ import annotations

import json
import re
import textwrap
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd


def detectar_raiz_projeto() -> Path:
    caminho_script = Path(__file__).resolve()

    if (
        caminho_script.parent.name.lower() == "reports"
        and caminho_script.parent.parent.name.lower() == "scripts"
    ):
        return caminho_script.parent.parent.parent

    return Path.cwd()


def limpar_texto(texto: str) -> str:
    return textwrap.dedent(texto).strip()


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
    if not caminho.exists():
        return pd.DataFrame()

    if caminho.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(caminho)
        df.columns = [normalizar_coluna(c) for c in df.columns]
        return df

    return ler_csv_robusto(caminho)


def carregar_json(caminho: Path) -> dict:
    if not caminho.exists():
        return {}

    return json.loads(caminho.read_text(encoding="utf-8"))


def formatar_numero(valor: object) -> str:
    try:
        numero = float(valor)
        if numero.is_integer():
            return f"{int(numero):,}".replace(",", ".")
        return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "-"


def valor_seguro(dados: dict, caminho: list[str], padrao: object = "-") -> object:
    atual = dados

    for chave in caminho:
        if not isinstance(atual, dict) or chave not in atual:
            return padrao
        atual = atual[chave]

    return atual


def localizar_asset(assets_dir: Path, nomes_base: list[str]) -> Path | None:
    if not assets_dir.exists():
        return None

    extensoes = {".png", ".jpg", ".jpeg", ".webp", ".svg"}

    arquivos = [
        p for p in assets_dir.iterdir()
        if p.is_file() and p.suffix.lower() in extensoes
    ]

    for nome in nomes_base:
        for arquivo in arquivos:
            if arquivo.stem.lower() == nome.lower():
                return arquivo

    for nome in nomes_base:
        for arquivo in arquivos:
            if nome.lower() in arquivo.stem.lower():
                return arquivo

    return None


def caminho_relativo_para_html(origem_html: Path, destino: Path) -> str:
    try:
        return destino.relative_to(origem_html.parent).as_posix()
    except ValueError:
        return Path("../../..").joinpath(destino).as_posix()


def tabela_html(df: pd.DataFrame, colunas: list[str], limite: int = 10) -> str:
    if df.empty:
        return '<div class="empty">Dados ainda não disponíveis para esta seção.</div>'

    colunas_existentes = [c for c in colunas if c in df.columns]

    if not colunas_existentes:
        return '<div class="empty">Colunas esperadas não foram encontradas.</div>'

    linhas = []

    for _, row in df.head(limite).iterrows():
        tds = []
        for coluna in colunas_existentes:
            valor = row[coluna]

            if pd.isna(valor):
                texto = "-"
            elif isinstance(valor, (int, float)) and coluna not in [
                "score_sinergia_davi_gabi",
                "score_lideranca_gabi",
                "score_gabi_preliminar",
            ]:
                texto = formatar_numero(valor)
            elif "score" in coluna:
                try:
                    texto = f"{float(valor):.2f}".replace(".", ",")
                except Exception:
                    texto = str(valor)
            else:
                texto = str(valor)

            tds.append(f"<td>{texto}</td>")

        linhas.append("<tr>" + "".join(tds) + "</tr>")

    cabecalho = "".join(
        f"<th>{coluna.replace('_', ' ').title()}</th>"
        for coluna in colunas_existentes
    )

    corpo = "\n".join(linhas)

    return f"""
    <div class="table-wrap">
      <table>
        <thead>
          <tr>{cabecalho}</tr>
        </thead>
        <tbody>
          {corpo}
        </tbody>
      </table>
    </div>
    """


def cards_indicadores(dashboard: dict, roteiro_json: dict, curadoria_json: dict) -> list[dict]:
    indicadores_alagoas = dashboard.get("indicadores_alagoas", {})
    indicadores_gabi = dashboard.get("indicadores_gabi", {})
    indicadores_roteiro = roteiro_json.get("indicadores", {})
    indicadores_curadoria = curadoria_json.get("indicadores", {})

    return [
        {
            "rotulo": "Meta operacional Gabi",
            "valor": formatar_numero(indicadores_gabi.get("meta_eleitoral", "-")),
            "detalhe": "Referência preliminar para planejamento",
        },
        {
            "rotulo": "Municípios prioritários",
            "valor": formatar_numero(indicadores_gabi.get("municipios_prioritarios", "-")),
            "detalhe": "Top 20 da base preliminar",
        },
        {
            "rotulo": "Lideranças mapeadas",
            "valor": formatar_numero(indicadores_gabi.get("liderancas_mapeadas", "-")),
            "detalhe": "Base municipal de vereadores",
        },
        {
            "rotulo": "Municípios no roteiro",
            "valor": formatar_numero(indicadores_roteiro.get("municipios_no_roteiro", "-")),
            "detalhe": "Agenda Davi + Gabi",
        },
        {
            "rotulo": "Meta no roteiro",
            "valor": formatar_numero(indicadores_roteiro.get("meta_gabi_roteiro", "-")),
            "detalhe": "Soma dos municípios priorizados",
        },
        {
            "rotulo": "Curadorias pendentes",
            "valor": formatar_numero(indicadores_curadoria.get("curadorias_pendentes", "-")),
            "detalhe": "Validação política necessária",
        },
        {
            "rotulo": "Eleitorado AL",
            "valor": formatar_numero(indicadores_alagoas.get("eleitorado_total", "-")),
            "detalhe": "Base estadual de referência",
        },
        {
            "rotulo": "População AL",
            "valor": formatar_numero(indicadores_alagoas.get("populacao_total", "-")),
            "detalhe": "População estimada IBGE 2024",
        },
    ]


def gerar_html(
    root: Path,
    output_html: Path,
    dashboard: dict,
    cruzamento_json: dict,
    roteiro_json: dict,
    curadoria_json: dict,
    base_eleitoral: pd.DataFrame,
    rede_liderancas: pd.DataFrame,
    cruzamento: pd.DataFrame,
    roteiro: pd.DataFrame,
    curadoria: pd.DataFrame,
) -> str:
    assets_dir = root / "parceiros" / "gabi-goncalves" / "assets"

    logo = localizar_asset(
        assets_dir,
        ["logo-gabi-2026", "logo_gabi_2026", "logo-gabi", "gabi-logo"],
    )

    foto = localizar_asset(
        assets_dir,
        ["foto-gabi", "foto_gabi", "gabi-foto", "gabi"],
    )

    logo_src = caminho_relativo_para_html(output_html, logo) if logo else ""
    foto_src = caminho_relativo_para_html(output_html, foto) if foto else ""

    atualizacao = datetime.now().strftime("%d/%m/%Y %H:%M")

    indicadores = cards_indicadores(dashboard, roteiro_json, curadoria_json)

    cards_html = "\n".join(
        f"""
        <article class="kpi-card">
          <span>{card['rotulo']}</span>
          <strong>{card['valor']}</strong>
          <small>{card['detalhe']}</small>
        </article>
        """
        for card in indicadores
    )

    resumo_semanal = roteiro_json.get("resumo_semanal", [])
    resumo_semanal_html = "\n".join(
        f"""
        <article class="week-card">
          <span>{item.get('semana', '-')}</span>
          <strong>{item.get('total_municipios', '-')} município(s)</strong>
          <p>{item.get('municipios', '-')}</p>
          <small>{item.get('objetivo', '-')}</small>
        </article>
        """
        for item in resumo_semanal
    )

    if not resumo_semanal_html:
        resumo_semanal_html = '<div class="empty">Resumo semanal ainda não disponível.</div>'

    top_municipios = tabela_html(
        base_eleitoral,
        [
            "ranking_gabi_preliminar",
            "municipio",
            "eleitorado",
            "prioridade_visita_gabi",
            "meta_votos_referencia_gabi",
            "status_articulacao_gabi",
        ],
        limite=12,
    )

    top_liderancas = tabela_html(
        rede_liderancas,
        [
            "ranking_lideranca_gabi",
            "municipio",
            "nome_lideranca",
            "partido",
            "votos_2024",
            "prioridade_lideranca_gabi",
            "potencial_transferencia_10pct",
        ],
        limite=12,
    )

    top_cruzamento = tabela_html(
        cruzamento,
        [
            "ranking_sinergia_davi_gabi",
            "municipio",
            "prioridade_sinergia_davi_gabi",
            "score_sinergia_davi_gabi",
            "principal_lideranca",
            "meta_votos_referencia_gabi",
            "acao_recomendada",
        ],
        limite=12,
    )

    top_roteiro = tabela_html(
        roteiro,
        [
            "ordem_prioridade",
            "semana_roteiro",
            "dia_sugerido",
            "turno_sugerido",
            "municipio",
            "principal_lideranca",
            "tipo_agenda",
        ],
        limite=20,
    )

    top_curadoria = tabela_html(
        curadoria,
        [
            "ordem_curadoria",
            "prioridade_curadoria",
            "prazo_curadoria",
            "municipio",
            "principal_lideranca",
            "relacao_gabi",
            "relacao_davi",
            "decisao_agenda",
        ],
        limite=20,
    )

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Relatório Executivo — Davi Maia + Gabi Gonçalves</title>

  <style>
    :root {{
      --blue-900: #0B1F4D;
      --blue-700: #1A4392;
      --yellow: #F1D214;
      --pink: #D65091;
      --pink-soft: #E280B2;
      --bg: #F6F8FC;
      --text: #14213D;
      --muted: #61708F;
      --line: #DCE4F4;
      --white: #FFFFFF;
      --radius: 24px;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at 10% 0%, rgba(241, 210, 20, .12), transparent 30%),
        radial-gradient(circle at 90% 10%, rgba(214, 80, 145, .13), transparent 30%),
        var(--bg);
      line-height: 1.45;
    }}

    .page {{
      width: min(1180px, calc(100% - 40px));
      margin: 0 auto;
      padding: 28px 0 60px;
    }}

    .cover {{
      display: grid;
      grid-template-columns: 1.25fr .75fr;
      gap: 28px;
      align-items: stretch;
      min-height: 620px;
      margin-bottom: 28px;
      padding: 32px;
      border-radius: 34px;
      background:
        linear-gradient(135deg, rgba(11,31,77,.98), rgba(26,67,146,.94)),
        var(--blue-900);
      color: #fff;
      overflow: hidden;
      position: relative;
    }}

    .cover::before {{
      content: "";
      position: absolute;
      width: 360px;
      height: 360px;
      right: -120px;
      top: -120px;
      border-radius: 999px;
      background: rgba(241, 210, 20, .22);
    }}

    .cover::after {{
      content: "";
      position: absolute;
      width: 360px;
      height: 360px;
      left: -140px;
      bottom: -120px;
      border-radius: 999px;
      background: rgba(214, 80, 145, .20);
    }}

    .cover-main,
    .cover-side {{
      position: relative;
      z-index: 2;
    }}

    .eyebrow {{
      margin: 0 0 12px;
      color: var(--yellow);
      font-size: 12px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: .14em;
    }}

    .cover h1 {{
      max-width: 760px;
      margin: 0;
      font-size: clamp(42px, 7vw, 78px);
      line-height: .92;
      letter-spacing: -0.07em;
    }}

    .cover .subtitle {{
      max-width: 660px;
      margin: 24px 0 0;
      color: rgba(255,255,255,.82);
      font-size: 20px;
    }}

    .meta-list {{
      display: grid;
      gap: 10px;
      margin-top: 34px;
    }}

    .meta-list div {{
      display: flex;
      gap: 10px;
      align-items: center;
      color: rgba(255,255,255,.82);
      font-weight: 700;
    }}

    .meta-list strong {{
      color: #fff;
    }}

    .cover-side {{
      display: grid;
      grid-template-rows: 1fr auto;
      gap: 18px;
    }}

    .photo-box {{
      min-height: 420px;
      overflow: hidden;
      border-radius: 28px;
      background: rgba(255,255,255,.12);
      border: 1px solid rgba(255,255,255,.20);
    }}

    .photo-box img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center top;
      display: block;
    }}

    .logo-box {{
      display: grid;
      place-items: center;
      min-height: 150px;
      padding: 18px;
      border-radius: 28px;
      background: #fff;
    }}

    .logo-box img {{
      max-width: 100%;
      max-height: 120px;
      object-fit: contain;
      display: block;
    }}

    .section {{
      margin: 28px 0;
      padding: 28px;
      border-radius: 30px;
      background: rgba(255,255,255,.94);
      border: 1px solid var(--line);
      box-shadow: 0 18px 50px rgba(11,31,77,.08);
    }}

    .section-header {{
      margin-bottom: 22px;
    }}

    .section-header h2 {{
      margin: 0;
      color: var(--blue-900);
      font-size: 34px;
      line-height: 1;
      letter-spacing: -0.05em;
    }}

    .section-header p {{
      max-width: 880px;
      margin: 12px 0 0;
      color: var(--muted);
      font-size: 16px;
    }}

    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
    }}

    .kpi-card {{
      padding: 20px;
      border-radius: 22px;
      border: 1px solid var(--line);
      background:
        radial-gradient(circle at 100% 0%, rgba(241,210,20,.16), transparent 34%),
        #fff;
    }}

    .kpi-card span {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: .10em;
    }}

    .kpi-card strong {{
      display: block;
      margin-top: 10px;
      color: var(--blue-700);
      font-size: 30px;
      line-height: 1;
      letter-spacing: -0.05em;
    }}

    .kpi-card small {{
      display: block;
      margin-top: 9px;
      color: var(--muted);
      font-weight: 700;
    }}

    .highlight-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
    }}

    .highlight {{
      padding: 22px;
      border-radius: 24px;
      background: #fff;
      border: 1px solid var(--line);
      border-top: 5px solid var(--yellow);
    }}

    .highlight:nth-child(2) {{
      border-top-color: var(--pink);
    }}

    .highlight:nth-child(3) {{
      border-top-color: var(--blue-700);
    }}

    .highlight strong {{
      display: block;
      color: var(--blue-900);
      font-size: 20px;
      margin-bottom: 8px;
    }}

    .highlight p {{
      margin: 0;
      color: var(--muted);
    }}

    .week-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
    }}

    .week-card {{
      padding: 20px;
      border-radius: 24px;
      background: #fff;
      border: 1px solid var(--line);
      border-top: 5px solid var(--pink);
    }}

    .week-card span {{
      color: var(--pink);
      font-size: 12px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: .10em;
    }}

    .week-card strong {{
      display: block;
      margin: 10px 0;
      color: var(--blue-900);
      font-size: 20px;
    }}

    .week-card p {{
      margin: 0 0 10px;
      color: var(--muted);
    }}

    .week-card small {{
      color: var(--blue-700);
      font-weight: 700;
    }}

    .table-wrap {{
      overflow-x: auto;
      border-radius: 20px;
      border: 1px solid var(--line);
      background: #fff;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}

    th {{
      background: var(--blue-900);
      color: #fff;
      padding: 12px;
      text-align: left;
      white-space: nowrap;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: .06em;
    }}

    td {{
      padding: 12px;
      border-top: 1px solid var(--line);
      color: var(--text);
      vertical-align: top;
    }}

    tr:nth-child(even) td {{
      background: #F8FAFF;
    }}

    .empty {{
      padding: 22px;
      border-radius: 20px;
      background: #fff;
      border: 1px solid var(--line);
      color: var(--muted);
      font-weight: 700;
    }}

    .footer {{
      padding: 24px;
      text-align: center;
      color: var(--muted);
      font-size: 13px;
    }}

    .print-note {{
      display: inline-flex;
      gap: 8px;
      align-items: center;
      margin-top: 18px;
      padding: 12px 16px;
      border-radius: 999px;
      background: rgba(241,210,20,.18);
      color: #fff;
      font-weight: 800;
    }}

    @media print {{
      body {{
        background: #fff !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }}

      .page {{
        width: 100%;
        padding: 0;
      }}

      .cover,
      .section {{
        box-shadow: none !important;
        break-inside: avoid;
        page-break-inside: avoid;
      }}

      .cover {{
        min-height: auto;
      }}

      .photo-box {{
        min-height: 360px;
      }}

      .kpi-grid {{
        grid-template-columns: repeat(4, 1fr);
      }}

      .week-grid {{
        grid-template-columns: repeat(2, 1fr);
      }}

      table {{
        font-size: 11px;
      }}

      th, td {{
        padding: 8px;
      }}

      .print-note {{
        display: none;
      }}
    }}

    @media (max-width: 900px) {{
      .cover {{
        grid-template-columns: 1fr;
      }}

      .kpi-grid,
      .highlight-grid,
      .week-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>

<body>
  <div class="page">
    <section class="cover">
      <div class="cover-main">
        <p class="eyebrow">Relatório executivo · Aprovação estratégica</p>
        <h1>Davi Maia + Gabi Gonçalves</h1>
        <p class="subtitle">
          Consolidação da inteligência territorial, rede de lideranças, roteiro de visitas
          e matriz de curadoria política para apoio à reeleição de Gabi Gonçalves.
        </p>

        <div class="meta-list">
          <div><strong>Projeto:</strong> Painel Parceiro Gabi Gonçalves 2026</div>
          <div><strong>Eixo político:</strong> Davi Maia como articulador territorial</div>
          <div><strong>Status:</strong> Versão executiva para validação e aprovação</div>
          <div><strong>Atualização:</strong> {atualizacao}</div>
        </div>

        <div class="print-note">Para enviar ao Davi: Ctrl + P → Salvar como PDF</div>
      </div>

      <aside class="cover-side">
        <div class="photo-box">
          {"<img src='" + foto_src + "' alt='Foto de Gabi Gonçalves' />" if foto_src else ""}
        </div>

        <div class="logo-box">
          {"<img src='" + logo_src + "' alt='Logo Gabi Gonçalves 2026' />" if logo_src else "Gabi Gonçalves"}
        </div>
      </aside>
    </section>

    <section class="section">
      <div class="section-header">
        <p class="eyebrow">Resumo executivo</p>
        <h2>Leitura estratégica da parceria</h2>
        <p>
          A análise organiza a candidatura de Gabi Gonçalves à reeleição como Deputada Estadual
          dentro da rede territorial liderada por Davi Maia. O painel identifica onde a parceria
          apresenta maior eficiência política, quais lideranças devem ser validadas e quais municípios
          devem compor o roteiro inicial de visitas.
        </p>
      </div>

      <div class="highlight-grid">
        <article class="highlight">
          <strong>1. Davi como eixo de articulação</strong>
          <p>
            O projeto considera Davi Maia como hub político capaz de organizar agendas, abrir portas
            municipais e conectar a pauta federal com a estadual.
          </p>
        </article>

        <article class="highlight">
          <strong>2. Gabi como candidata à reeleição</strong>
          <p>
            A base trabalha Gabi como deputada estadual em mandato, priorizando proteção e expansão
            territorial com base em municípios de maior sinergia.
          </p>
        </article>

        <article class="highlight">
          <strong>3. Curadoria antes da agenda pública</strong>
          <p>
            As agendas recomendadas precisam passar por validação política para evitar conflitos locais,
            sobreposição de apoios e baixa conversão territorial.
          </p>
        </article>
      </div>
    </section>

    <section class="section">
      <div class="section-header">
        <p class="eyebrow">Indicadores centrais</p>
        <h2>Painel de controle executivo</h2>
        <p>
          Indicadores consolidados a partir dos sprints de base eleitoral, liderança, cruzamento,
          roteiro territorial e curadoria política.
        </p>
      </div>

      <div class="kpi-grid">
        {cards_html}
      </div>
    </section>

    <section class="section">
      <div class="section-header">
        <p class="eyebrow">Base eleitoral</p>
        <h2>Municípios prioritários da Gabi</h2>
        <p>
          Ranking preliminar de municípios para a reeleição de Gabi, considerando peso eleitoral,
          prioridade territorial e aderência com a base estratégica do projeto matriz.
        </p>
      </div>

      {top_municipios}
    </section>

    <section class="section">
      <div class="section-header">
        <p class="eyebrow">Rede política</p>
        <h2>Lideranças municipais prioritárias</h2>
        <p>
          Primeira camada de lideranças municipais extraída da base de vereadores e associada
          aos municípios de maior prioridade para a Gabi.
        </p>
      </div>

      {top_liderancas}
    </section>

    <section class="section">
      <div class="section-header">
        <p class="eyebrow">Davi Maia + Gabi Gonçalves</p>
        <h2>Municípios de maior sinergia</h2>
        <p>
          Cruzamento entre prioridade eleitoral da Gabi, força territorial do Davi,
          rede de lideranças e potencial de agenda conjunta.
        </p>
      </div>

      {top_cruzamento}
    </section>

    <section class="section">
      <div class="section-header">
        <p class="eyebrow">Roteiro territorial</p>
        <h2>Plano semanal de visitas Davi + Gabi</h2>
        <p>
          Organização operacional das visitas recomendadas por semana, com foco em eficiência logística,
          validação de lideranças e conversão política.
        </p>
      </div>

      <div class="week-grid">
        {resumo_semanal_html}
      </div>
    </section>

    <section class="section">
      <div class="section-header">
        <p class="eyebrow">Agenda operacional</p>
        <h2>Primeiras visitas recomendadas</h2>
        <p>
          Roteiro inicial de municípios, lideranças e tipos de agenda sugeridos para validação.
        </p>
      </div>

      {top_roteiro}
    </section>

    <section class="section">
      <div class="section-header">
        <p class="eyebrow">Curadoria política</p>
        <h2>Matriz de validação antes da execução</h2>
        <p>
          Campos de curadoria criados para confirmar relação com Gabi, Davi, Renan Filho,
          Renan Calheiros, Paulo Dantas, prefeitos, vereadores e grupos políticos locais.
        </p>
      </div>

      {top_curadoria}
    </section>

    <section class="section">
      <div class="section-header">
        <p class="eyebrow">Encaminhamento</p>
        <h2>Próximos passos recomendados</h2>
        <p>
          Após aprovação do Davi, a recomendação é iniciar a curadoria política dos municípios
          de prioridade imediata, validar lideranças locais e transformar o roteiro preliminar
          em agenda real de pré-campanha.
        </p>
      </div>

      <div class="highlight-grid">
        <article class="highlight">
          <strong>1. Validar com Davi</strong>
          <p>Confirmar se a leitura estratégica da parceria Davi + Gabi está aderente ao plano político.</p>
        </article>

        <article class="highlight">
          <strong>2. Curar os 10 primeiros municípios</strong>
          <p>Preencher relação política real, risco local, responsável pela articulação e decisão de agenda.</p>
        </article>

        <article class="highlight">
          <strong>3. Preparar versão pública</strong>
          <p>Após aprovação, publicar ou compartilhar o painel com acesso controlado para acompanhamento.</p>
        </article>
      </div>
    </section>

    <footer class="footer">
      Relatório gerado automaticamente pelo projeto Alagoas Political Intelligence · Davi Maia + Gabi Gonçalves · {atualizacao}
    </footer>
  </div>
</body>
</html>
"""

    return html


def atualizar_painel_com_link(root: Path, relatorio_path: Path) -> None:
    index_path = root / "parceiros" / "gabi-goncalves" / "index.html"

    if not index_path.exists():
        print(f"[AVISO] index.html não encontrado: {index_path}")
        return

    html = index_path.read_text(encoding="utf-8")

    link_relatorio = "../../../reports/parceiros/gabi-goncalves/relatorio_executivo_gabi_sprint07.html"

    if 'href="#relatorio-executivo"' not in html:
        html = html.replace(
            '<a href="#curadoria-politica">Curadoria</a>',
            '<a href="#curadoria-politica">Curadoria</a>\n                  <a href="#relatorio-executivo">Relatório</a>',
        )

    secao = f"""
      <section class="section relatorio-section" id="relatorio-executivo">
        <div class="section-header">
          <p class="eyebrow">Relatório executivo</p>
          <h2>Versão para aprovação do Davi</h2>
          <p>
            Relatório consolidado com leitura estratégica, indicadores, municípios prioritários,
            roteiro territorial e matriz de curadoria política.
          </p>
        </div>

        <div class="panel-card">
          <div class="panel-header">
            <div>
              <p class="eyebrow">Arquivo gerado</p>
              <h2>Relatório Executivo Davi + Gabi</h2>
            </div>
            <a class="status-pill" href="{link_relatorio}" target="_blank" rel="noopener">
              Abrir relatório
            </a>
          </div>

          <p class="muted-text">
            Abra o relatório no navegador e use Ctrl + P para salvar em PDF antes de enviar ao Davi.
          </p>
        </div>
      </section>
"""

    if 'id="relatorio-executivo"' not in html:
        alvo = '<section class="section roadmap" id="proximos-passos">'
        if alvo in html:
            html = html.replace(alvo, secao + "\n      " + alvo)
        else:
            html = html.replace("</main>", secao + "\n    </main>")

    index_path.write_text(html, encoding="utf-8")
    print(f"[OK] Link do relatório adicionado ao painel: {index_path}")

    css_path = root / "parceiros" / "gabi-goncalves" / "styles.css"

    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")

        bloco = """
/* ===== SPRINT07_RELATORIO_INICIO ===== */

.relatorio-section {
  background:
    radial-gradient(circle at top left, rgba(241, 210, 20, .12), transparent 30%),
    linear-gradient(180deg, rgba(255,255,255,.96), rgba(234,240,255,.90));
}

.muted-text {
  color: var(--muted);
  font-weight: 700;
  line-height: 1.5;
}

/* ===== SPRINT07_RELATORIO_FIM ===== */
"""

        if "SPRINT07_RELATORIO_INICIO" not in css:
            css = css.rstrip() + "\n\n" + bloco.strip() + "\n"
            css_path.write_text(css, encoding="utf-8")
            print(f"[OK] CSS do link de relatório atualizado: {css_path}")


def gerar_briefing(root: Path, output_html: Path) -> None:
    briefing_path = root / "docs" / "briefing_gabi_sprint07.md"

    texto = f"""
# Briefing — Sprint 07 — Relatório Executivo de Aprovação

## Objetivo

Gerar uma versão executiva consolidada do painel Davi Maia + Gabi Gonçalves para aprovação estratégica.

## Arquivo principal gerado

- reports/parceiros/gabi-goncalves/relatorio_executivo_gabi_sprint07.html

## Conteúdo do relatório

- Identidade visual da Gabi;
- Resumo executivo;
- Indicadores centrais;
- Municípios prioritários;
- Rede de lideranças;
- Cruzamento Davi Maia + Gabi Gonçalves;
- Roteiro territorial;
- Curadoria política;
- Próximos passos recomendados.

## Como gerar PDF

Abrir o arquivo HTML no navegador e usar:

Ctrl + P → Salvar como PDF

## Caminho local

{output_html}

## Próximo sprint recomendado

Sprint 08 — Publicação, versionamento no GitHub e envio do link para validação.
"""

    briefing_path.parent.mkdir(parents=True, exist_ok=True)
    briefing_path.write_text(limpar_texto(texto) + "\n", encoding="utf-8")
    print(f"[OK] Briefing salvo: {briefing_path}")


def main() -> None:
    root = detectar_raiz_projeto()

    print("============================================================")
    print("SPRINT 07 — RELATÓRIO EXECUTIVO DAVI + GABI")
    print("============================================================")
    print(f"[INFO] Raiz detectada: {root}")

    dashboard_dir = root / "data" / "dashboard" / "parceiros" / "gabi-goncalves"
    final_dir = root / "data" / "final" / "parceiros" / "gabi-goncalves"

    dashboard_json = carregar_json(dashboard_dir / "base_dashboard_gabi_v1.json")
    cruzamento_json = carregar_json(dashboard_dir / "cruzamento_davi_gabi_v1.json")
    roteiro_json = carregar_json(dashboard_dir / "roteiro_territorial_davi_gabi_v1.json")
    curadoria_json = carregar_json(dashboard_dir / "curadoria_politica_davi_gabi_v1.json")

    base_eleitoral = ler_tabela(final_dir / "base_eleitoral_gabi_v1.csv")
    rede_liderancas = ler_tabela(final_dir / "rede_liderancas_gabi_v1.csv")
    cruzamento = ler_tabela(final_dir / "cruzamento_davi_gabi_v1.csv")
    roteiro = ler_tabela(final_dir / "roteiro_territorial_davi_gabi_v1.csv")
    curadoria = ler_tabela(final_dir / "curadoria_politica_davi_gabi_v1.csv")

    output_dir = root / "reports" / "parceiros" / "gabi-goncalves"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_html = output_dir / "relatorio_executivo_gabi_sprint07.html"

    html = gerar_html(
        root=root,
        output_html=output_html,
        dashboard=dashboard_json,
        cruzamento_json=cruzamento_json,
        roteiro_json=roteiro_json,
        curadoria_json=curadoria_json,
        base_eleitoral=base_eleitoral,
        rede_liderancas=rede_liderancas,
        cruzamento=cruzamento,
        roteiro=roteiro,
        curadoria=curadoria,
    )

    output_html.write_text(html, encoding="utf-8")
    print(f"[OK] Relatório executivo gerado: {output_html}")

    atualizar_painel_com_link(root, output_html)
    gerar_briefing(root, output_html)

    print("")
    print("============================================================")
    print("SPRINT 07 CONCLUÍDO")
    print("============================================================")
    print("Relatório gerado em:")
    print(f"  {output_html}")
    print("")
    print("Teste local:")
    print("  cd C:\\Users\\user\\Documents\\Workspace\\campanha_2026\\alagoas-political-intelligence")
    print("  python -m http.server 8000")
    print("")
    print("Abra:")
    print("  http://localhost:8000/reports/parceiros/gabi-goncalves/relatorio_executivo_gabi_sprint07.html")
    print("")
    print("Para gerar PDF:")
    print("  Ctrl + P -> Salvar como PDF")
    print("============================================================")


if __name__ == "__main__":
    main()