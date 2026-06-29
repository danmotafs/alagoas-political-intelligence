import os
import shutil
from datetime import datetime


BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

INDEX_HTML = os.path.join(BASE_DIR, "dashboard_v2", "index.html")
JS_DIR = os.path.join(BASE_DIR, "dashboard_v2", "js")
JS_PARCEIROS = os.path.join(JS_DIR, "parceiros.js")

os.makedirs(JS_DIR, exist_ok=True)


CSS_PARCEIROS = """
<style id="parceiros-estrategicos-style">
  .parceiros-section {
    margin-top: 36px;
  }

  .parceiros-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 16px;
    margin: 20px 0 28px;
  }

  .parceiros-card {
    background: #ffffff;
    border: 1px solid rgba(15, 91, 45, 0.14);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
  }

  .parceiros-card small {
    display: block;
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: .04em;
  }

  .parceiros-card strong {
    display: block;
    color: #063b20;
    font-size: 26px;
    line-height: 1.1;
  }

  .parceiros-card span {
    display: block;
    margin-top: 6px;
    color: #64748b;
    font-size: 12px;
  }

  .parceiros-note {
    background: #fff9db;
    border: 1px solid #f4d66a;
    color: #5a4600;
    border-radius: 16px;
    padding: 14px 16px;
    font-size: 13px;
    margin: 12px 0 22px;
  }

  .parceiros-subgrid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 22px;
  }

  .parceiros-table-wrap {
    width: 100%;
    overflow-x: auto;
    border: 1px solid rgba(15, 91, 45, 0.14);
    border-radius: 18px;
    background: #ffffff;
  }

  .parceiros-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }

  .parceiros-table th {
    background: #063b20;
    color: #ffffff;
    text-align: left;
    padding: 12px 10px;
    white-space: nowrap;
  }

  .parceiros-table td {
    border-bottom: 1px solid #edf2ef;
    padding: 10px;
    vertical-align: top;
  }

  .parceiros-table tr:nth-child(even) td {
    background: #fbfdfc;
  }

  .parceiros-pill {
    display: inline-block;
    border-radius: 999px;
    padding: 5px 9px;
    font-size: 11px;
    font-weight: 800;
    background: #eaf4ee;
    color: #063b20;
    white-space: nowrap;
  }

  .parceiros-pill.alta {
    background: #dcfce7;
    color: #166534;
  }

  .parceiros-pill.media {
    background: #fef9c3;
    color: #854d0e;
  }

  .parceiros-pill.baixa {
    background: #e0f2fe;
    color: #075985;
  }

  .parceiros-empty {
    color: #64748b;
    padding: 16px;
  }

  @media (max-width: 1100px) {
    .parceiros-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @media (max-width: 720px) {
    .parceiros-grid {
      grid-template-columns: 1fr;
    }
  }

  @media print {
    .parceiros-section {
      break-inside: avoid;
    }

    .parceiros-table {
      font-size: 10px;
    }

    .parceiros-table th,
    .parceiros-table td {
      padding: 6px;
    }
  }
</style>
"""


SECAO_PARCEIROS = """
<section id="parceiros-estrategicos-2026" class="section parceiros-section">
  <div class="section-header">
    <div>
      <p class="eyebrow">Matriz de Parceiros Políticos</p>
      <h2>Parceiros Estratégicos 2026</h2>
      <p class="section-description">
        Cruzamento entre a votação dos parceiros de Davi em 2022 e os redutos dos vereadores alagoanos em 2024.
        A ferramenta identifica quais parceiros podem abrir portas para Davi em territórios e locais de votação específicos.
      </p>
    </div>
  </div>

  <div class="parceiros-note">
    Leitura metodológica: a convergência não representa apoio confirmado nem previsão automática de votos.
    Ela indica onde existe sobreposição territorial entre o parceiro e vereadores que podem ser abordados politicamente.
  </div>

  <div class="parceiros-grid">
    <div class="parceiros-card">
      <small>Parceiros processados</small>
      <strong id="parceiros-processados">-</strong>
      <span>Parceiros incluídos na matriz</span>
    </div>

    <div class="parceiros-card">
      <small>Municípios</small>
      <strong id="parceiros-municipios">-</strong>
      <span>Com convergência territorial</span>
    </div>

    <div class="parceiros-card">
      <small>Vereadores</small>
      <strong id="parceiros-vereadores">-</strong>
      <span>Com redutos convergentes</span>
    </div>

    <div class="parceiros-card">
      <small>Potencial 20%</small>
      <strong id="parceiros-potencial">-</strong>
      <span>Vereadores únicos</span>
    </div>

    <div class="parceiros-card">
      <small>% da meta</small>
      <strong id="parceiros-meta">-</strong>
      <span>Sobre meta de 60 mil votos</span>
    </div>
  </div>

  <div class="parceiros-subgrid">
    <div>
      <h3>Ranking de Parceiros por Utilidade Territorial</h3>
      <div class="parceiros-table-wrap">
        <table class="parceiros-table">
          <thead>
            <tr>
              <th>Parceiro</th>
              <th>Cruzamentos</th>
              <th>Municípios</th>
              <th>Vereadores</th>
              <th>Potencial 20%</th>
              <th>% Meta</th>
              <th>Principal Município</th>
              <th>Principal Local</th>
            </tr>
          </thead>
          <tbody id="parceiros-ranking-body">
            <tr><td colspan="8" class="parceiros-empty">Carregando dados...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div>
      <h3>Top Convergências Parceiro x Vereador</h3>
      <div class="parceiros-table-wrap">
        <table class="parceiros-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Parceiro</th>
              <th>Município</th>
              <th>Local de votação</th>
              <th>Vereador</th>
              <th>Partido</th>
              <th>Votos Parceiro</th>
              <th>Votos Vereador</th>
              <th>Índice</th>
              <th>Classificação</th>
              <th>Potencial 20%</th>
            </tr>
          </thead>
          <tbody id="parceiros-convergencias-body">
            <tr><td colspan="11" class="parceiros-empty">Carregando dados...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div>
      <h3>Vereadores Prioritários para Abordagem com Parceiros</h3>
      <div class="parceiros-table-wrap">
        <table class="parceiros-table">
          <thead>
            <tr>
              <th>Parceiro</th>
              <th>Município</th>
              <th>Vereador</th>
              <th>Partido</th>
              <th>Local de votação</th>
              <th>Votos Parceiro</th>
              <th>Votos Vereador</th>
              <th>Índice</th>
              <th>Potencial 20%</th>
            </tr>
          </thead>
          <tbody id="parceiros-vereadores-body">
            <tr><td colspan="9" class="parceiros-empty">Carregando dados...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</section>
"""


JS_PARCEIROS_CONTEUDO = r"""
(function () {
  const DATA_URL = "../data/dashboard/base_dashboard_v2.json";

  function formatInt(value) {
    const n = Number(value || 0);
    return n.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
  }

  function formatPct(value) {
    const n = Number(value || 0);
    return `${n.toLocaleString("pt-BR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}%`;
  }

  function safeText(value) {
    if (value === null || value === undefined || value === "") return "-";
    return String(value);
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function classificarPill(classificacao) {
    const texto = safeText(classificacao);
    const normalizado = texto.toUpperCase();

    let classe = "";

    if (normalizado.includes("ALTA")) classe = "alta";
    else if (normalizado.includes("MÉDIA") || normalizado.includes("MEDIA")) classe = "media";
    else if (normalizado.includes("BAIXA")) classe = "baixa";

    return `<span class="parceiros-pill ${classe}">${texto}</span>`;
  }

  function renderRankingParceiros(lista) {
    const tbody = document.getElementById("parceiros-ranking-body");
    if (!tbody) return;

    if (!Array.isArray(lista) || lista.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="parceiros-empty">Nenhum parceiro processado.</td></tr>`;
      return;
    }

    tbody.innerHTML = lista
      .map((item) => {
        return `
          <tr>
            <td><strong>${safeText(item.nome_parceiro)}</strong></td>
            <td>${formatInt(item.total_cruzamentos)}</td>
            <td>${formatInt(item.municipios_com_convergencia)}</td>
            <td>${formatInt(item.vereadores_convergentes)}</td>
            <td>${formatInt(item.potencial_vereadores_unicos_20pct)}</td>
            <td>${formatPct(item.percentual_meta_davi_20pct)}</td>
            <td>${safeText(item.principal_municipio)}</td>
            <td>${safeText(item.principal_local_votacao)}</td>
          </tr>
        `;
      })
      .join("");
  }

  function renderTopConvergencias(lista) {
    const tbody = document.getElementById("parceiros-convergencias-body");
    if (!tbody) return;

    if (!Array.isArray(lista) || lista.length === 0) {
      tbody.innerHTML = `<tr><td colspan="11" class="parceiros-empty">Nenhuma convergência encontrada.</td></tr>`;
      return;
    }

    tbody.innerHTML = lista
      .slice(0, 25)
      .map((item, index) => {
        return `
          <tr>
            <td>${formatInt(item.ranking_convergencia || index + 1)}</td>
            <td><strong>${safeText(item.nome_parceiro)}</strong></td>
            <td>${safeText(item.municipio)}</td>
            <td>${safeText(item.local_votacao_parceiro)}</td>
            <td>${safeText(item.vereador)}</td>
            <td>${safeText(item.partido_vereador)}</td>
            <td>${formatInt(item.votos_parceiro_local)}</td>
            <td>${formatInt(item.votos_vereador_local)}</td>
            <td>${Number(item.indice_convergencia || 0).toLocaleString("pt-BR", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}</td>
            <td>${classificarPill(item.classificacao_convergencia)}</td>
            <td>${formatInt(item.potencial_davi_20pct_local)}</td>
          </tr>
        `;
      })
      .join("");
  }

  function renderVereadoresPrioritarios(lista) {
    const tbody = document.getElementById("parceiros-vereadores-body");
    if (!tbody) return;

    if (!Array.isArray(lista) || lista.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" class="parceiros-empty">Nenhum vereador prioritário encontrado.</td></tr>`;
      return;
    }

    tbody.innerHTML = lista
      .slice(0, 30)
      .map((item) => {
        return `
          <tr>
            <td><strong>${safeText(item.nome_parceiro)}</strong></td>
            <td>${safeText(item.municipio)}</td>
            <td>${safeText(item.vereador)}</td>
            <td>${safeText(item.partido_vereador)}</td>
            <td>${safeText(item.local_votacao_parceiro)}</td>
            <td>${formatInt(item.votos_parceiro_local)}</td>
            <td>${formatInt(item.votos_vereador_local)}</td>
            <td>${Number(item.indice_convergencia || 0).toLocaleString("pt-BR", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}</td>
            <td>${formatInt(item.potencial_davi_20pct_local)}</td>
          </tr>
        `;
      })
      .join("");
  }

  async function carregarParceirosEstrategicos() {
    const section = document.getElementById("parceiros-estrategicos-2026");

    if (!section) return;

    try {
      const response = await fetch(`${DATA_URL}?v=parceiros-estrategicos-${Date.now()}`);

      if (!response.ok) {
        throw new Error(`Erro HTTP ${response.status} ao carregar base_dashboard_v2.json`);
      }

      const data = await response.json();
      const modulo = data.parceiros_estrategicos_2026;

      if (!modulo || !modulo.resumo_geral) {
        section.style.display = "none";
        return;
      }

      const resumo = modulo.resumo_geral;

      setText("parceiros-processados", formatInt(resumo.parceiros_processados));
      setText("parceiros-municipios", formatInt(resumo.municipios_com_convergencia));
      setText("parceiros-vereadores", formatInt(resumo.vereadores_convergentes));
      setText("parceiros-potencial", formatInt(resumo.potencial_vereadores_unicos_20pct));
      setText("parceiros-meta", formatPct(resumo.percentual_meta_davi_potencial_unico_20pct));

      renderRankingParceiros(modulo.resumo_por_parceiro || []);
      renderTopConvergencias(modulo.top_convergencias || []);
      renderVereadoresPrioritarios(modulo.vereadores_prioritarios || []);
    } catch (error) {
      console.error("Erro ao carregar módulo de parceiros estratégicos:", error);

      const section = document.getElementById("parceiros-estrategicos-2026");

      if (section) {
        const erro = document.createElement("div");
        erro.className = "parceiros-note";
        erro.textContent = `Não foi possível carregar o módulo de parceiros estratégicos: ${error.message}`;
        section.prepend(erro);
      }
    }
  }

  document.addEventListener("DOMContentLoaded", carregarParceirosEstrategicos);
})();
"""


def criar_backup(caminho):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = caminho.replace(".html", f"_backup_antes_secao_parceiros_{timestamp}.html")

    shutil.copy2(caminho, backup)

    return backup


def inserir_antes(conteudo, marcador, bloco):
    if marcador not in conteudo:
        return conteudo, False

    return conteudo.replace(marcador, bloco + "\n" + marcador, 1), True


def main():
    print("=" * 80)
    print("INTEGRAÇÃO VISUAL — SEÇÃO PARCEIROS ESTRATÉGICOS DASHBOARD V2")
    print("=" * 80)

    if not os.path.exists(INDEX_HTML):
        raise FileNotFoundError(f"Arquivo não encontrado: {INDEX_HTML}")

    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    backup = criar_backup(INDEX_HTML)
    print(f"Backup criado: {backup}")

    if 'id="parceiros-estrategicos-style"' not in html:
        html, ok_css = inserir_antes(html, "</head>", CSS_PARCEIROS)

        if ok_css:
            print("CSS de parceiros inserido no <head>.")
        else:
            print("Aviso: não encontrei </head>. CSS não foi inserido.")

    if 'id="parceiros-estrategicos-2026"' not in html:
        if "</main>" in html:
            html, ok_secao = inserir_antes(html, "</main>", SECAO_PARCEIROS)
        elif "</body>" in html:
            html, ok_secao = inserir_antes(html, "</body>", SECAO_PARCEIROS)
        else:
            ok_secao = False

        if ok_secao:
            print("Seção Parceiros Estratégicos inserida.")
        else:
            print("Aviso: não encontrei </main> nem </body>. Seção não foi inserida.")

    script_tag = '<script src="js/parceiros.js?v=parceiros-estrategicos-v1"></script>'

    if "js/parceiros.js" not in html:
        html, ok_script = inserir_antes(html, "</body>", script_tag)

        if ok_script:
            print("Script parceiros.js inserido antes de </body>.")
        else:
            print("Aviso: não encontrei </body>. Script não foi inserido.")

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    with open(JS_PARCEIROS, "w", encoding="utf-8") as f:
        f.write(JS_PARCEIROS_CONTEUDO)

    print(f"JS criado/atualizado: {JS_PARCEIROS}")

    print()
    print("Integração visual concluída.")
    print("Teste local recomendado:")
    print("python -m http.server 8000")
    print("http://localhost:8000/dashboard_v2/?v=parceiros-estrategicos-v1")
    print("=" * 80)


if __name__ == "__main__":
    main()