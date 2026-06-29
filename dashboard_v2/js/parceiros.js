
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
