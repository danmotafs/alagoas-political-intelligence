from __future__ import annotations

import argparse
import json
import shutil
import textwrap
from datetime import datetime
from pathlib import Path


def limpar_texto(texto: str) -> str:
    return textwrap.dedent(texto).lstrip()


def detectar_raiz_projeto() -> Path:
    """
    Detecta a raiz do projeto mesmo quando o script é executado de dentro de scripts/setup.
    Estrutura esperada:
    alagoas-political-intelligence/
      scripts/
        setup/
          criar_painel_gabi_sprint01.py
    """
    caminho_script = Path(__file__).resolve()

    if (
        caminho_script.parent.name.lower() == "setup"
        and caminho_script.parent.parent.name.lower() == "scripts"
    ):
        return caminho_script.parent.parent.parent

    return Path.cwd()


def escrever_arquivo(caminho: Path, conteudo: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8")
    print(f"[OK] Arquivo criado/atualizado: {caminho}")


def escrever_json(caminho: Path, dados: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] JSON criado/atualizado: {caminho}")


def copiar_logo(origem: str | None, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)

    if not origem:
        print("[AVISO] Nenhuma logo foi informada no parâmetro --logo.")
        print(f"[AÇÃO MANUAL] Depois copie a logo da Gabi para: {destino}")
        return

    origem_path = Path(origem)

    if not origem_path.exists():
        print(f"[AVISO] Logo não encontrada em: {origem_path}")
        print(f"[AÇÃO MANUAL] Depois copie a logo da Gabi para: {destino}")
        return

    shutil.copy2(origem_path, destino)
    print(f"[OK] Logo copiada para: {destino}")


def gerar_html() -> str:
    return limpar_texto(
        '''
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <title>Gabi Gonçalves 2026 | Inteligência Territorial</title>
          <meta name="description" content="Painel de inteligência territorial, eleitoral e política para Gabi Gonçalves 2026." />
          <link rel="stylesheet" href="styles.css" />
        </head>

        <body>
          <div class="page-shell">
            <header class="hero">
              <nav class="topbar">
                <a class="back-link" href="../../dashboard_v2/">← Painel Davi Maia</a>

                <div class="topbar-actions">
                  <a href="#visao-geral">Visão geral</a>
                  <a href="#dados">Dados</a>
                  <a href="#cruzamento">Davi x Gabi</a>
                  <a href="#proximos-passos">Próximos passos</a>
                </div>
              </nav>

              <section class="hero-grid">
                <div class="hero-content">
                  <p class="eyebrow">Módulo parceiro · Rede Davi Maia 2026</p>
                  <h1>Inteligência Territorial e Eleitoral</h1>
                  <h2>Gabi Gonçalves</h2>

                  <p class="hero-subtitle">
                    Painel individualizado para análise de expansão territorial, articulação municipal,
                    rede de lideranças e sinergia política com o eixo Davi Maia.
                  </p>

                  <div class="hero-tags">
                    <span>Deputada Estadual 2026</span>
                    <span>Alagoas</span>
                    <span>Pré-campanha</span>
                  </div>
                </div>

                <aside class="candidate-card">
                  <div class="logo-frame">
                    <img
                      id="campaignLogo"
                      src="assets/logo-gabi-2026.png"
                      alt="Logomarca Gabi Gonçalves 2026"
                      onerror="this.style.display='none'; document.querySelector('.brand-fallback').style.display='flex';"
                    />

                    <div class="brand-fallback">
                      <strong>Gabi</strong>
                      <small>Gonçalves</small>
                    </div>
                  </div>

                  <div class="candidate-meta">
                    <span>Parceira política</span>
                    <strong>Gabi Gonçalves</strong>
                    <p>Pré-candidata a Deputada Estadual</p>
                  </div>
                </aside>
              </section>
            </header>

            <main>
              <section class="section" id="visao-geral">
                <div class="section-header">
                  <p class="eyebrow">Visão geral</p>
                  <h2>Indicadores Estratégicos</h2>
                  <p>
                    Estrutura inicial do painel parceiro. Os indicadores gerais de Alagoas foram herdados
                    da base matriz; os indicadores próprios da Gabi serão preenchidos nos próximos ETLs.
                  </p>
                </div>

                <div class="kpi-grid">
                  <article class="kpi-card">
                    <span>Municípios</span>
                    <strong id="kpiMunicipios">-</strong>
                    <small>Base territorial de Alagoas</small>
                  </article>

                  <article class="kpi-card">
                    <span>Eleitorado</span>
                    <strong id="kpiEleitorado">-</strong>
                    <small>Eleitorado total mapeado</small>
                  </article>

                  <article class="kpi-card">
                    <span>População</span>
                    <strong id="kpiPopulacao">-</strong>
                    <small>População estimada na base</small>
                  </article>

                  <article class="kpi-card">
                    <span>Vereadores</span>
                    <strong id="kpiVereadores">-</strong>
                    <small>Rede legislativa municipal</small>
                  </article>

                  <article class="kpi-card highlight">
                    <span>Meta Gabi</span>
                    <strong id="kpiMeta">A definir</strong>
                    <small>Meta estadual será calibrada</small>
                  </article>

                  <article class="kpi-card">
                    <span>Sinergia Davi x Gabi</span>
                    <strong id="kpiSinergia">Sprint 01</strong>
                    <small>Camada de cruzamento criada</small>
                  </article>
                </div>
              </section>

              <section class="section strategy-section">
                <div class="section-header">
                  <p class="eyebrow">Modelo político</p>
                  <h2>Davi Maia como eixo de articulação</h2>
                  <p>
                    A leitura estratégica deste módulo considera Davi Maia como hub político da rede,
                    com capacidade de apoio territorial e interlocução com lideranças estaduais.
                  </p>
                </div>

                <div class="strategy-grid">
                  <article class="strategy-card">
                    <span>01</span>
                    <h3>Painel matriz</h3>
                    <p>
                      O painel do Davi permanece como base principal da inteligência territorial,
                      reunindo municípios, lideranças, rede de poder e priorização estratégica.
                    </p>
                  </article>

                  <article class="strategy-card">
                    <span>02</span>
                    <h3>Painel parceiro</h3>
                    <p>
                      A Gabi passa a ter uma página própria, com identidade visual, cargo, meta eleitoral
                      e campos de análise individualizados.
                    </p>
                  </article>

                  <article class="strategy-card">
                    <span>03</span>
                    <h3>Cruzamento político</h3>
                    <p>
                      A próxima camada vai comparar territórios, lideranças e oportunidades para medir
                      onde a parceria Davi x Gabi tem maior eficiência eleitoral.
                    </p>
                  </article>
                </div>
              </section>

              <section class="section two-columns" id="dados">
                <div class="panel-card">
                  <div class="panel-header">
                    <div>
                      <p class="eyebrow">Ranking territorial</p>
                      <h2>Municípios Prioritários da Gabi</h2>
                    </div>

                    <span class="status-pill">Aguardando curadoria</span>
                  </div>

                  <div class="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Rank</th>
                          <th>Município</th>
                          <th>Eleitorado</th>
                          <th>Prioridade</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody id="rankingTable"></tbody>
                    </table>
                  </div>
                </div>

                <div class="panel-card">
                  <div class="panel-header">
                    <div>
                      <p class="eyebrow">Lideranças</p>
                      <h2>Rede Política Inicial</h2>
                    </div>

                    <span class="status-pill">Sprint 02</span>
                  </div>

                  <div class="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Município</th>
                          <th>Liderança</th>
                          <th>Tipo</th>
                          <th>Potencial</th>
                        </tr>
                      </thead>
                      <tbody id="liderancasTable"></tbody>
                    </table>
                  </div>
                </div>
              </section>

              <section class="section" id="cruzamento">
                <div class="section-header">
                  <p class="eyebrow">Sinergia política</p>
                  <h2>Cruzamento Davi Maia x Gabi Gonçalves</h2>
                  <p>
                    Esta seção será usada para identificar territórios onde a presença de Davi pode
                    impulsionar a Gabi, territórios onde a Gabi já possui aderência própria e agendas
                    conjuntas com maior retorno político.
                  </p>
                </div>

                <div class="cross-grid" id="crossGrid"></div>
              </section>

              <section class="section roadmap" id="proximos-passos">
                <div class="section-header">
                  <p class="eyebrow">Pipeline</p>
                  <h2>Próximos passos recomendados</h2>
                  <p>
                    Após a estrutura visual, os próximos sprints devem preencher a base própria da Gabi
                    e iniciar os cruzamentos territoriais com a base do Davi.
                  </p>
                </div>

                <div class="roadmap-list" id="roadmapList"></div>
              </section>
            </main>

            <footer class="footer">
              <p>Plataforma de Inteligência Política · Rede Davi Maia 2026 · Módulo Gabi Gonçalves</p>
              <small id="lastUpdate">Atualização: -</small>
            </footer>
          </div>

          <script src="app.js"></script>
        </body>
        </html>
        '''
    )


def gerar_css() -> str:
    return limpar_texto(
        '''
        :root {
          --blue-900: #0B1F4D;
          --blue-800: #123478;
          --blue-700: #1A4392;
          --blue-100: #EAF0FF;
          --yellow-500: #F1D214;
          --yellow-600: #D7B900;
          --pink-500: #E280B2;
          --pink-600: #D65091;
          --ink: #172033;
          --muted: #6B7280;
          --line: rgba(26, 67, 146, 0.13);
          --card: rgba(255, 255, 255, 0.92);
          --bg: #F6F8FC;
          --shadow: 0 24px 60px rgba(11, 31, 77, 0.14);
          --radius-xl: 28px;
          --radius-lg: 22px;
        }

        * {
          box-sizing: border-box;
        }

        html {
          scroll-behavior: smooth;
        }

        body {
          margin: 0;
          font-family: Arial, Helvetica, sans-serif;
          color: var(--ink);
          background:
            radial-gradient(circle at top left, rgba(241, 210, 20, .14), transparent 32%),
            radial-gradient(circle at top right, rgba(226, 128, 178, .18), transparent 30%),
            linear-gradient(180deg, #F8FAFF 0%, #EEF3FF 42%, #F6F8FC 100%);
        }

        a {
          color: inherit;
        }

        .page-shell {
          width: min(1180px, calc(100% - 32px));
          margin: 0 auto;
        }

        .hero {
          padding: 24px 0 28px;
        }

        .topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 26px;
        }

        .back-link,
        .topbar-actions a {
          text-decoration: none;
          font-size: 13px;
          font-weight: 800;
          color: var(--blue-700);
        }

        .back-link {
          display: inline-flex;
          align-items: center;
          padding: 10px 14px;
          border: 1px solid var(--line);
          border-radius: 999px;
          background: rgba(255, 255, 255, .78);
          box-shadow: 0 10px 22px rgba(11, 31, 77, .06);
        }

        .topbar-actions {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .topbar-actions a {
          padding: 10px 12px;
          border-radius: 999px;
        }

        .topbar-actions a:hover,
        .back-link:hover {
          background: var(--blue-100);
        }

        .hero-grid {
          display: grid;
          grid-template-columns: minmax(0, 1.4fr) 380px;
          gap: 24px;
          align-items: stretch;
        }

        .hero-content,
        .candidate-card,
        .section,
        .panel-card,
        .strategy-card,
        .cross-card,
        .roadmap-item,
        .kpi-card {
          border: 1px solid var(--line);
          background: var(--card);
          box-shadow: var(--shadow);
          backdrop-filter: blur(16px);
        }

        .hero-content {
          min-height: 460px;
          padding: 46px;
          border-radius: var(--radius-xl);
          background:
            linear-gradient(135deg, rgba(26, 67, 146, .96), rgba(11, 31, 77, .96)),
            radial-gradient(circle at 20% 20%, rgba(241, 210, 20, .32), transparent 30%);
          color: #ffffff;
          position: relative;
          overflow: hidden;
        }

        .hero-content::after {
          content: "";
          position: absolute;
          right: -80px;
          bottom: -100px;
          width: 320px;
          height: 320px;
          border-radius: 50%;
          background: rgba(241, 210, 20, .18);
        }

        .eyebrow {
          margin: 0 0 10px;
          font-size: 12px;
          line-height: 1.2;
          font-weight: 900;
          letter-spacing: .12em;
          text-transform: uppercase;
          color: var(--pink-600);
        }

        .hero-content .eyebrow {
          color: var(--yellow-500);
        }

        .hero h1 {
          margin: 0;
          max-width: 760px;
          font-size: clamp(38px, 6vw, 72px);
          line-height: .92;
          letter-spacing: -0.06em;
        }

        .hero h2 {
          margin: 10px 0 18px;
          font-size: clamp(32px, 5vw, 64px);
          line-height: .95;
          color: var(--yellow-500);
          letter-spacing: -0.05em;
        }

        .hero-subtitle {
          position: relative;
          z-index: 1;
          max-width: 720px;
          margin: 0;
          font-size: 18px;
          line-height: 1.65;
          color: rgba(255, 255, 255, .86);
        }

        .hero-tags {
          position: relative;
          z-index: 1;
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          margin-top: 28px;
        }

        .hero-tags span {
          padding: 10px 14px;
          border-radius: 999px;
          font-size: 12px;
          font-weight: 900;
          color: #ffffff;
          background: rgba(255, 255, 255, .12);
          border: 1px solid rgba(255, 255, 255, .18);
        }

        .candidate-card {
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          gap: 22px;
          padding: 24px;
          border-radius: var(--radius-xl);
        }

        .logo-frame {
          min-height: 280px;
          display: grid;
          place-items: center;
          border-radius: 24px;
          background:
            radial-gradient(circle at 20% 10%, rgba(241, 210, 20, .22), transparent 32%),
            radial-gradient(circle at 70% 30%, rgba(226, 128, 178, .22), transparent 34%),
            linear-gradient(180deg, #ffffff, #EEF3FF);
          border: 1px solid var(--line);
          overflow: hidden;
        }

        .logo-frame img {
          width: min(100%, 310px);
          height: auto;
          display: block;
        }

        .brand-fallback {
          display: none;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: var(--blue-700);
          text-align: center;
        }

        .brand-fallback strong {
          font-size: 72px;
          line-height: .9;
          letter-spacing: -0.08em;
        }

        .brand-fallback small {
          font-size: 22px;
          font-weight: 900;
          color: var(--pink-600);
          text-transform: uppercase;
        }

        .candidate-meta {
          padding: 20px;
          border-radius: 22px;
          background: var(--blue-900);
          color: #ffffff;
        }

        .candidate-meta span {
          display: block;
          margin-bottom: 8px;
          font-size: 12px;
          font-weight: 900;
          color: var(--yellow-500);
          text-transform: uppercase;
          letter-spacing: .1em;
        }

        .candidate-meta strong {
          display: block;
          font-size: 28px;
          line-height: 1;
          letter-spacing: -0.04em;
        }

        .candidate-meta p {
          margin: 8px 0 0;
          color: rgba(255, 255, 255, .78);
        }

        .section {
          margin: 24px 0;
          padding: 28px;
          border-radius: var(--radius-xl);
        }

        .section-header {
          max-width: 840px;
          margin-bottom: 22px;
        }

        .section-header h2 {
          margin: 0;
          font-size: clamp(26px, 3vw, 40px);
          line-height: 1;
          letter-spacing: -0.05em;
          color: var(--blue-900);
        }

        .section-header p:not(.eyebrow) {
          margin: 12px 0 0;
          color: var(--muted);
          line-height: 1.65;
        }

        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(6, minmax(0, 1fr));
          gap: 14px;
        }

        .kpi-card {
          padding: 18px;
          border-radius: 20px;
          box-shadow: none;
        }

        .kpi-card span {
          display: block;
          min-height: 30px;
          color: var(--muted);
          font-size: 12px;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: .08em;
        }

        .kpi-card strong {
          display: block;
          margin-top: 8px;
          font-size: 28px;
          line-height: 1;
          color: var(--blue-700);
          letter-spacing: -0.05em;
        }

        .kpi-card small {
          display: block;
          margin-top: 8px;
          color: var(--muted);
          line-height: 1.35;
        }

        .kpi-card.highlight {
          background: linear-gradient(135deg, var(--yellow-500), #fff3a5);
          border-color: rgba(215, 185, 0, .45);
        }

        .kpi-card.highlight strong {
          color: var(--blue-900);
        }

        .strategy-section {
          background:
            linear-gradient(135deg, rgba(255,255,255,.95), rgba(234,240,255,.92));
        }

        .strategy-grid,
        .cross-grid,
        .roadmap-list {
          display: grid;
          gap: 14px;
        }

        .strategy-grid {
          grid-template-columns: repeat(3, minmax(0, 1fr));
        }

        .strategy-card,
        .cross-card,
        .roadmap-item {
          padding: 22px;
          border-radius: var(--radius-lg);
          box-shadow: none;
        }

        .strategy-card span {
          display: inline-grid;
          place-items: center;
          width: 42px;
          height: 42px;
          margin-bottom: 16px;
          border-radius: 16px;
          background: var(--blue-700);
          color: var(--yellow-500);
          font-weight: 900;
        }

        .strategy-card h3,
        .cross-card h3,
        .roadmap-item h3 {
          margin: 0;
          color: var(--blue-900);
          letter-spacing: -0.03em;
        }

        .strategy-card p,
        .cross-card p,
        .roadmap-item p {
          margin: 10px 0 0;
          color: var(--muted);
          line-height: 1.58;
        }

        .two-columns {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 18px;
          background: transparent;
          border: 0;
          box-shadow: none;
          padding: 0;
        }

        .panel-card {
          padding: 24px;
          border-radius: var(--radius-xl);
        }

        .panel-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 18px;
        }

        .panel-header h2 {
          margin: 0;
          color: var(--blue-900);
          letter-spacing: -0.04em;
        }

        .status-pill {
          flex: 0 0 auto;
          padding: 8px 10px;
          border-radius: 999px;
          background: rgba(241, 210, 20, .22);
          color: var(--blue-900);
          font-size: 11px;
          font-weight: 900;
          text-transform: uppercase;
        }

        .table-wrap {
          width: 100%;
          overflow-x: auto;
        }

        table {
          width: 100%;
          border-collapse: collapse;
          min-width: 520px;
        }

        th,
        td {
          padding: 14px 12px;
          border-bottom: 1px solid var(--line);
          text-align: left;
          font-size: 13px;
        }

        th {
          color: var(--blue-900);
          font-size: 11px;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: .08em;
        }

        td {
          color: #24304A;
        }

        .empty-row td {
          padding: 28px 12px;
          color: var(--muted);
          line-height: 1.5;
        }

        .cross-grid {
          grid-template-columns: repeat(3, minmax(0, 1fr));
        }

        .cross-card {
          border-top: 5px solid var(--yellow-500);
        }

        .cross-card strong {
          display: block;
          margin-bottom: 8px;
          color: var(--pink-600);
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: .08em;
        }

        .roadmap-list {
          grid-template-columns: repeat(4, minmax(0, 1fr));
        }

        .roadmap-item {
          position: relative;
          overflow: hidden;
        }

        .roadmap-item::before {
          content: "";
          position: absolute;
          inset: 0 auto 0 0;
          width: 5px;
          background: linear-gradient(180deg, var(--blue-700), var(--pink-600), var(--yellow-500));
        }

        .roadmap-item small {
          display: inline-block;
          margin-bottom: 10px;
          color: var(--pink-600);
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: .08em;
        }

        .footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          padding: 28px 0 42px;
          color: var(--muted);
          font-size: 13px;
        }

        .footer p {
          margin: 0;
        }

        .footer small {
          color: var(--blue-700);
          font-weight: 800;
        }

        @media (max-width: 980px) {
          .hero-grid,
          .two-columns {
            grid-template-columns: 1fr;
          }

          .kpi-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }

          .strategy-grid,
          .cross-grid,
          .roadmap-list {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .hero-content {
            min-height: auto;
          }
        }

        @media (max-width: 680px) {
          .page-shell {
            width: min(100% - 22px, 1180px);
          }

          .topbar {
            align-items: stretch;
            flex-direction: column;
          }

          .topbar-actions {
            overflow-x: auto;
            padding-bottom: 4px;
          }

          .hero-content,
          .candidate-card,
          .section,
          .panel-card {
            padding: 20px;
            border-radius: 22px;
          }

          .hero h1 {
            font-size: 42px;
          }

          .hero h2 {
            font-size: 38px;
          }

          .hero-subtitle {
            font-size: 15px;
          }

          .kpi-grid,
          .strategy-grid,
          .cross-grid,
          .roadmap-list {
            grid-template-columns: 1fr;
          }

          .logo-frame {
            min-height: 220px;
          }

          .footer {
            align-items: flex-start;
            flex-direction: column;
          }
        }
        '''
    )


def gerar_js() -> str:
    return limpar_texto(
        '''
        const DATA_PATHS = {
          base: "../../data/dashboard/parceiros/gabi-goncalves/base_dashboard_gabi_v1.json",
          meta: "../../data/dashboard/parceiros/gabi-goncalves/meta_eleitoral_gabi_estadual_2026.json",
          cruzamento: "../../data/dashboard/parceiros/gabi-goncalves/cruzamento_davi_gabi_v1.json"
        };

        const fallbackBase = {
          metadata: {
            atualizacao: "Aguardando carga de dados"
          },
          indicadores_alagoas: {
            municipios: 102,
            eleitorado_total: 2442894,
            populacao_total: 3220104,
            vereadores_mapeados: 2462
          },
          indicadores_gabi: {
            meta_eleitoral: null
          },
          ranking_municipios: [],
          liderancas: [],
          proximos_passos: []
        };

        const fallbackCruzamento = {
          cards: []
        };

        function formatNumber(value) {
          if (value === null || value === undefined || value === "") {
            return "A definir";
          }

          const numero = Number(value);

          if (Number.isNaN(numero)) {
            return String(value);
          }

          return numero.toLocaleString("pt-BR");
        }

        async function carregarJSON(path, fallback) {
          try {
            const resposta = await fetch(path, { cache: "no-store" });

            if (!resposta.ok) {
              throw new Error(`Erro ao carregar ${path}: ${resposta.status}`);
            }

            return await resposta.json();
          } catch (erro) {
            console.warn(erro.message);
            return fallback;
          }
        }

        function setText(id, value) {
          const el = document.getElementById(id);

          if (el) {
            el.textContent = value;
          }
        }

        function renderKPIs(base, meta) {
          const alagoas = base.indicadores_alagoas || {};
          const gabi = base.indicadores_gabi || {};

          const metaEleitoral =
            meta?.meta_eleitoral_gabi_2026?.meta_votos ??
            gabi.meta_eleitoral ??
            null;

          setText("kpiMunicipios", formatNumber(alagoas.municipios));
          setText("kpiEleitorado", formatNumber(alagoas.eleitorado_total));
          setText("kpiPopulacao", formatNumber(alagoas.populacao_total));
          setText("kpiVereadores", formatNumber(alagoas.vereadores_mapeados));
          setText("kpiMeta", formatNumber(metaEleitoral));
        }

        function renderRanking(base) {
          const tbody = document.getElementById("rankingTable");
          const ranking = base.ranking_municipios || [];

          if (!tbody) {
            return;
          }

          if (!ranking.length) {
            tbody.innerHTML = `
              <tr class="empty-row">
                <td colspan="5">
                  Ranking próprio da Gabi ainda não foi calculado. No Sprint 02, vamos criar
                  a base inicial de municípios prioritários para Deputada Estadual.
                </td>
              </tr>
            `;
            return;
          }

          tbody.innerHTML = ranking.map((item, index) => `
            <tr>
              <td>${item.rank || index + 1}</td>
              <td>${item.municipio || "-"}</td>
              <td>${formatNumber(item.eleitorado)}</td>
              <td>${item.prioridade || "A definir"}</td>
              <td>${item.status || "Aguardando análise"}</td>
            </tr>
          `).join("");
        }

        function renderLiderancas(base) {
          const tbody = document.getElementById("liderancasTable");
          const liderancas = base.liderancas || [];

          if (!tbody) {
            return;
          }

          if (!liderancas.length) {
            tbody.innerHTML = `
              <tr class="empty-row">
                <td colspan="4">
                  Rede inicial de lideranças ainda não foi curada. No Sprint 03, vamos cruzar
                  vereadores, prefeitos, partidos, votação e aderência política à Gabi.
                </td>
              </tr>
            `;
            return;
          }

          tbody.innerHTML = liderancas.map((item) => `
            <tr>
              <td>${item.municipio || "-"}</td>
              <td>${item.nome || "-"}</td>
              <td>${item.tipo || "-"}</td>
              <td>${item.potencial || "A definir"}</td>
            </tr>
          `).join("");
        }

        function renderCruzamento(cruzamento) {
          const grid = document.getElementById("crossGrid");
          const cards = cruzamento.cards || [];

          if (!grid) {
            return;
          }

          const defaultCards = [
            {
              etiqueta: "Eixo principal",
              titulo: "Davi como hub político",
              texto: "O painel considera Davi Maia como eixo de articulação territorial, com a Gabi estruturada como parceira estadual dentro da rede."
            },
            {
              etiqueta: "Eficiência territorial",
              titulo: "Agendas conjuntas",
              texto: "A próxima etapa vai identificar municípios onde uma visita conjunta pode gerar maior retorno político para os dois projetos."
            },
            {
              etiqueta: "Base de apoio",
              titulo: "Vereadores e lideranças",
              texto: "O cruzamento vai mapear quais lideranças podem operar simultaneamente na construção de votos para Federal e Estadual."
            }
          ];

          const fonte = cards.length ? cards : defaultCards;

          grid.innerHTML = fonte.map((card) => `
            <article class="cross-card">
              <strong>${card.etiqueta || "Cruzamento"}</strong>
              <h3>${card.titulo || "-"}</h3>
              <p>${card.texto || ""}</p>
            </article>
          `).join("");
        }

        function renderRoadmap(base) {
          const lista = document.getElementById("roadmapList");
          const passos = base.proximos_passos || [];

          if (!lista) {
            return;
          }

          const defaultSteps = [
            {
              sprint: "Sprint 02",
              titulo: "Base Eleitoral da Gabi",
              descricao: "Definir meta estadual, municípios prioritários e campos próprios da candidata."
            },
            {
              sprint: "Sprint 03",
              titulo: "Rede de Lideranças",
              descricao: "Cruzar vereadores, prefeitos, partidos e lideranças com potencial de apoio."
            },
            {
              sprint: "Sprint 04",
              titulo: "Davi x Gabi",
              descricao: "Criar indicadores de sinergia, sobreposição territorial e agenda conjunta."
            },
            {
              sprint: "Sprint 05",
              titulo: "Publicação",
              descricao: "Validar localmente, subir ao GitHub Pages e gerar link de compartilhamento."
            }
          ];

          const fonte = passos.length ? passos : defaultSteps;

          lista.innerHTML = fonte.map((passo) => `
            <article class="roadmap-item">
              <small>${passo.sprint || "Sprint"}</small>
              <h3>${passo.titulo || "-"}</h3>
              <p>${passo.descricao || ""}</p>
            </article>
          `).join("");
        }

        function renderAtualizacao(base) {
          const metadata = base.metadata || {};
          const atualizacao = metadata.atualizacao || "Aguardando atualização";

          setText("lastUpdate", `Atualização: ${atualizacao}`);
        }

        async function inicializarPainel() {
          const [base, meta, cruzamento] = await Promise.all([
            carregarJSON(DATA_PATHS.base, fallbackBase),
            carregarJSON(DATA_PATHS.meta, {}),
            carregarJSON(DATA_PATHS.cruzamento, fallbackCruzamento)
          ]);

          renderKPIs(base, meta);
          renderRanking(base);
          renderLiderancas(base);
          renderCruzamento(cruzamento);
          renderRoadmap(base);
          renderAtualizacao(base);
        }

        document.addEventListener("DOMContentLoaded", inicializarPainel);
        '''
    )


def gerar_base_json() -> dict:
    hoje = datetime.now().strftime("%d/%m/%Y %H:%M")

    return {
        "metadata": {
            "projeto": "Painel Parceiro Gabi Gonçalves 2026",
            "versao": "sprint01_estrutura",
            "atualizacao": hoje,
            "candidata": "Gabi Gonçalves",
            "cargo": "Deputada Estadual",
            "painel_matriz": "Davi Maia - Deputado Federal",
            "status": "Estrutura criada; dados próprios da Gabi pendentes de curadoria"
        },
        "identidade_visual": {
            "azul_principal": "#1A4392",
            "azul_escuro": "#0B1F4D",
            "amarelo_destaque": "#F1D214",
            "rosa_campanha": "#E280B2",
            "fundo_claro": "#F6F8FC"
        },
        "indicadores_alagoas": {
            "municipios": 102,
            "eleitorado_total": 2442894,
            "populacao_total": 3220104,
            "prefeitos_mapeados": 102,
            "vereadores_mapeados": 2462,
            "votos_vereadores_total": 1114135
        },
        "indicadores_gabi": {
            "meta_eleitoral": None,
            "municipios_prioritarios": 0,
            "liderancas_mapeadas": 0,
            "municipios_com_sinergia_davi": 0,
            "status_meta": "A definir no Sprint 02"
        },
        "ranking_municipios": [],
        "liderancas": [],
        "oportunidades": [],
        "proximos_passos": [
            {
                "sprint": "Sprint 02",
                "titulo": "Base Eleitoral da Gabi",
                "descricao": "Definir meta estadual, municípios prioritários, status de visita e campos próprios da candidata."
            },
            {
                "sprint": "Sprint 03",
                "titulo": "Rede de Lideranças",
                "descricao": "Cruzar vereadores, prefeitos, partidos, votos municipais e aderência política à Gabi."
            },
            {
                "sprint": "Sprint 04",
                "titulo": "Cruzamento Davi x Gabi",
                "descricao": "Criar camada de sinergia territorial, agendas conjuntas e potencial de transferência política."
            },
            {
                "sprint": "Sprint 05",
                "titulo": "Publicação",
                "descricao": "Validar visualmente, subir ao GitHub Pages e gerar link de compartilhamento."
            }
        ]
    }


def gerar_meta_json() -> dict:
    return {
        "metadata": {
            "projeto": "Meta Eleitoral Gabi Gonçalves 2026",
            "versao": "sprint01_placeholder",
            "status": "Aguardando definição estratégica"
        },
        "meta_eleitoral_gabi_2026": {
            "cargo": "Deputada Estadual",
            "meta_votos": None,
            "observacao": "Meta será definida após análise do quociente eleitoral estadual, histórico de votação, base territorial e alianças firmadas."
        },
        "cenarios_transferencia": [
            {
                "cenario": "Conservador",
                "percentual_transferencia_vereadores": None,
                "descricao": "A definir após curadoria da rede de vereadores."
            },
            {
                "cenario": "Moderado",
                "percentual_transferencia_vereadores": None,
                "descricao": "A definir após curadoria da rede de vereadores."
            },
            {
                "cenario": "Agressivo",
                "percentual_transferencia_vereadores": None,
                "descricao": "A definir após curadoria da rede de vereadores."
            }
        ]
    }


def gerar_cruzamento_json() -> dict:
    return {
        "metadata": {
            "projeto": "Cruzamento Davi Maia x Gabi Gonçalves",
            "versao": "sprint01_estrutura",
            "status": "Camada conceitual criada; dados serão preenchidos nos próximos sprints"
        },
        "eixo_politico": {
            "descricao": "Davi Maia é tratado como eixo político principal; Gabi Gonçalves é estruturada como parceira estadual com painel individualizado.",
            "hipotese_estrategica": "A força territorial e institucional do Davi pode impulsionar a expansão da Gabi em municípios e lideranças já mapeadas no painel matriz."
        },
        "cards": [
            {
                "etiqueta": "Eixo principal",
                "titulo": "Davi como hub político",
                "texto": "O painel considera Davi Maia como eixo de articulação territorial, com a Gabi estruturada como parceira estadual dentro da rede."
            },
            {
                "etiqueta": "Eficiência territorial",
                "titulo": "Agendas conjuntas",
                "texto": "A próxima etapa vai identificar municípios onde uma visita conjunta pode gerar maior retorno político para os dois projetos."
            },
            {
                "etiqueta": "Base de apoio",
                "titulo": "Vereadores e lideranças",
                "texto": "O cruzamento vai mapear quais lideranças podem operar simultaneamente na construção de votos para Federal e Estadual."
            }
        ],
        "campos_futuros": [
            "municipio",
            "forca_davi",
            "forca_gabi",
            "sinergia_davi_gabi",
            "liderancas_compartilhadas",
            "agenda_conjunta_recomendada",
            "potencial_transferencia_federal",
            "potencial_transferencia_estadual",
            "prioridade_operacional"
        ]
    }


def gerar_briefing_md() -> str:
    return limpar_texto(
        '''
        # Briefing — Sprint 01 — Painel Parceiro Gabi Gonçalves

        ## Objetivo

        Criar a estrutura inicial do painel individualizado da Gabi Gonçalves dentro do projeto alagoas-political-intelligence, mantendo Davi Maia como eixo político principal e a Gabi como parceira de pré-campanha para Deputada Estadual.

        ## Decisão estratégica

        O painel da Gabi não será um projeto isolado neste momento. Ele será criado como módulo parceiro dentro do projeto principal do Davi Maia.

        Estrutura de acesso prevista:

        - Painel principal Davi Maia: /dashboard_v2/
        - Painel parceiro Gabi Gonçalves: /parceiros/gabi-goncalves/

        ## Identidade visual

        A identidade do painel da Gabi foi baseada na logomarca enviada:

        - Azul principal: #1A4392
        - Azul escuro: #0B1F4D
        - Amarelo destaque: #F1D214
        - Rosa campanha: #E280B2
        - Fundo claro: #F6F8FC

        ## Arquivos criados

        - parceiros/gabi-goncalves/index.html
        - parceiros/gabi-goncalves/styles.css
        - parceiros/gabi-goncalves/app.js
        - parceiros/gabi-goncalves/assets/logo-gabi-2026.png
        - data/dashboard/parceiros/gabi-goncalves/base_dashboard_gabi_v1.json
        - data/dashboard/parceiros/gabi-goncalves/meta_eleitoral_gabi_estadual_2026.json
        - data/dashboard/parceiros/gabi-goncalves/cruzamento_davi_gabi_v1.json
        - docs/briefing_painel_gabi_sprint01.md
        - scripts/setup/criar_painel_gabi_sprint01.py

        ## Modelo político adotado

        O Davi Maia é tratado como eixo principal da rede de inteligência política.

        A Gabi Gonçalves passa a ser analisada como parceira estadual, com painel próprio, identidade visual própria e futura camada de cruzamento territorial com a base do Davi.

        ## Próximos sprints sugeridos

        ### Sprint 02 — Base Eleitoral da Gabi

        - Definir meta eleitoral estadual.
        - Criar campos próprios:
          - relacao_gabi
          - aderencia_gabi
          - grupo_politico_gabi
          - status_articulacao_gabi
          - prioridade_visita_gabi
        - Gerar primeira base de municípios prioritários.

        ### Sprint 03 — Rede de Lideranças

        - Cruzar vereadores, prefeitos, partidos, votação e potencial de apoio.
        - Criar ranking de lideranças estratégicas para a Gabi.

        ### Sprint 04 — Cruzamento Davi x Gabi

        - Identificar municípios de alta sinergia.
        - Mapear agendas conjuntas recomendadas.
        - Criar score de eficiência territorial da parceria.

        ### Sprint 05 — Publicação

        - Validar localmente.
        - Subir ao GitHub.
        - Publicar no GitHub Pages.

        ## Link previsto após publicação

        https://danmotafs.github.io/alagoas-political-intelligence/parceiros/gabi-goncalves/
        '''
    )


def injetar_link_no_dashboard_davi(root: Path) -> None:
    index_davi = root / "dashboard_v2" / "index.html"

    if not index_davi.exists():
        print("[AVISO] dashboard_v2/index.html não encontrado.")
        print("[AVISO] Link para o painel da Gabi não foi injetado no painel do Davi.")
        return

    html = index_davi.read_text(encoding="utf-8")
    marcador = "<!-- SPRINT01_GABI_PARTNER_LINK -->"

    if marcador in html:
        print("[OK] Link da Gabi já existe no dashboard do Davi. Nenhuma alteração feita.")
        return

    backup = index_davi.with_suffix(".html.bak_sprint01_gabi")
    backup.write_text(html, encoding="utf-8")
    print(f"[OK] Backup criado: {backup}")

    bloco = limpar_texto(
        f'''
        {marcador}
        <style>
          .gabi-partner-floating-link {{
            position: fixed;
            right: 18px;
            bottom: 18px;
            z-index: 9999;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            border-radius: 999px;
            background: linear-gradient(135deg, #1A4392 0%, #0B1F4D 100%);
            color: #ffffff;
            font-family: Arial, Helvetica, sans-serif;
            font-size: 13px;
            font-weight: 800;
            letter-spacing: .02em;
            text-decoration: none;
            box-shadow: 0 14px 30px rgba(11, 31, 77, .28);
            border: 1px solid rgba(255, 255, 255, .22);
          }}

          .gabi-partner-floating-link span {{
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: #F1D214;
            box-shadow: 0 0 0 4px rgba(241, 210, 20, .20);
          }}

          .gabi-partner-floating-link:hover {{
            transform: translateY(-2px);
            filter: brightness(1.06);
          }}

          @media (max-width: 720px) {{
            .gabi-partner-floating-link {{
              left: 14px;
              right: 14px;
              bottom: 14px;
              justify-content: center;
              border-radius: 18px;
            }}
          }}
        </style>

        <a class="gabi-partner-floating-link" href="../parceiros/gabi-goncalves/" title="Abrir painel parceiro da Gabi Gonçalves">
          <span></span>
          Painel Parceiro · Gabi Gonçalves
        </a>
        '''
    )

    if "</body>" in html:
        html = html.replace("</body>", bloco + "\n</body>")
    else:
        html += "\n" + bloco

    index_davi.write_text(html, encoding="utf-8")
    print("[OK] Link flutuante para o painel da Gabi injetado no dashboard_v2/index.html")


def validar_raiz_projeto(root: Path) -> None:
    print(f"[INFO] Raiz detectada: {root}")

    if not (root / "dashboard_v2").exists():
        print("[AVISO] A pasta dashboard_v2 não foi encontrada.")
        print("[DICA] Confirme se o script está dentro de:")
        print("       alagoas-political-intelligence\\scripts\\setup\\")

    if not (root / ".git").exists():
        print("[AVISO] A pasta .git não foi encontrada na raiz detectada.")
        print("[AVISO] Isso não impede a criação dos arquivos, mas confira se a raiz está correta.")


def criar_estrutura(root: Path, caminho_logo: str | None) -> None:
    parceiro_dir = root / "parceiros" / "gabi-goncalves"
    assets_dir = parceiro_dir / "assets"
    data_dir = root / "data" / "dashboard" / "parceiros" / "gabi-goncalves"
    docs_dir = root / "docs"

    escrever_arquivo(parceiro_dir / "index.html", gerar_html())
    escrever_arquivo(parceiro_dir / "styles.css", gerar_css())
    escrever_arquivo(parceiro_dir / "app.js", gerar_js())

    copiar_logo(caminho_logo, assets_dir / "logo-gabi-2026.png")

    escrever_json(data_dir / "base_dashboard_gabi_v1.json", gerar_base_json())
    escrever_json(data_dir / "meta_eleitoral_gabi_estadual_2026.json", gerar_meta_json())
    escrever_json(data_dir / "cruzamento_davi_gabi_v1.json", gerar_cruzamento_json())

    escrever_arquivo(docs_dir / "briefing_painel_gabi_sprint01.md", gerar_briefing_md())

    injetar_link_no_dashboard_davi(root)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cria a estrutura inicial do painel parceiro Gabi Gonçalves 2026."
    )

    parser.add_argument(
        "--logo",
        required=False,
        help="Caminho local da logomarca da Gabi. Exemplo: C:\\Users\\user\\Downloads\\logo-gabi-2026.png",
    )

    args = parser.parse_args()

    root = detectar_raiz_projeto()

    print("============================================================")
    print("SPRINT 01 — PAINEL PARCEIRO GABI GONÇALVES")
    print("============================================================")

    validar_raiz_projeto(root)
    criar_estrutura(root, args.logo)

    print("")
    print("============================================================")
    print("SPRINT 01 CONCLUÍDO")
    print("============================================================")
    print("Arquivos principais criados:")
    print("  parceiros/gabi-goncalves/index.html")
    print("  parceiros/gabi-goncalves/styles.css")
    print("  parceiros/gabi-goncalves/app.js")
    print("  parceiros/gabi-goncalves/assets/logo-gabi-2026.png")
    print("  data/dashboard/parceiros/gabi-goncalves/base_dashboard_gabi_v1.json")
    print("  data/dashboard/parceiros/gabi-goncalves/meta_eleitoral_gabi_estadual_2026.json")
    print("  data/dashboard/parceiros/gabi-goncalves/cruzamento_davi_gabi_v1.json")
    print("")
    print("Para testar localmente, vá para a raiz do projeto:")
    print("  cd C:\\Users\\user\\Documents\\Workspace\\campanha_2026\\alagoas-political-intelligence")
    print("")
    print("Depois rode:")
    print("  python -m http.server 8000")
    print("")
    print("E acesse:")
    print("  http://localhost:8000/parceiros/gabi-goncalves/")
    print("")
    print("Link previsto no GitHub Pages:")
    print("  https://danmotafs.github.io/alagoas-political-intelligence/parceiros/gabi-goncalves/")
    print("============================================================")


if __name__ == "__main__":
    main()