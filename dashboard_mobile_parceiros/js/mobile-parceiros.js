const DATA_URL = "../data/dashboard/parceiros/mobile_parceiros_v2.json";

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

function cargoArtigo(p) {
  return p?.cargo_generico_artigo || "a liderança";
}

function cargoArtigoMaiusculo(p) {
  return p?.cargo_generico_artigo_maiusculo || "A liderança";
}

function cargoGenerico(p) {
  return p?.cargo_generico || "liderança";
}

function labelSelecionada(p) {
  const cargo = cargoGenerico(p);

  if (["deputado", "vereador", "senador", "prefeito"].includes(cargo)) {
    return `${cargo} selecionado`;
  }

  if (["deputada", "vereadora", "senadora", "prefeita"].includes(cargo)) {
    return `${cargo} selecionada`;
  }

  return "liderança selecionada";
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function imageOrInitials(src, name) {
  if (!src) return `<span>${initials(name)}</span>`;
  return `<img src="${src}" alt="${safe(name)}" onerror="this.parentElement.innerHTML='<span>${initials(name)}</span>'" />`;
}

function renderAddCard() {
  return `
    <article class="add-partner-card" aria-label="Futuro novo apoio político">
      <div class="add-plus">+</div>
      <strong>Novo apoio</strong>
      <span>Futuros deputados e lideranças</span>
    </article>
  `;
}

function renderSelector() {
  const el = document.getElementById("partner-selector");
  if (!el) return;

  if (!parceiros.length) {
    el.innerHTML = `
      <div class="loading-card">Nenhuma liderança processada.</div>
      ${renderAddCard()}
    `;
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
  }).join("") + renderAddCard();

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
      description: `Município onde ${cargoArtigo(p)} teve presença eleitoral em 2022 e existem vereadores com votação relevante em 2024 nos mesmos territórios.`,
      stats: [
        { label: `Votos ${cargoGenerico(p)}`, value: fmtInt(c.votos_parceiro_cidade) },
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
        { label: `Votos ${cargoGenerico(p)}`, value: fmtInt(item.votos_parceiro_local) },
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
    setText("impact-note", "O impacto aparecerá após o processamento das lideranças.");
    return;
  }

  const pct = Number(item.percentual_meta || 0);
  const width = Math.min(100, Math.max(0, pct));

  setText("impact-title", item.nome);
  setText(
    "impact-subtitle",
    item.tipo === "parceiro"
      ? `Impacto de ${cargoArtigo(p)} na meta`
      : `Vereador · ${safe(item.municipio)}`
  );
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
  setText("selected-cargo-label", labelSelecionada(p));

  const avatar = document.getElementById("partner-avatar");
  if (avatar) {
    avatar.innerHTML = imageOrInitials(p.foto_parceiro, p.nome_parceiro);
  }

  setText("metric-votos-2022", fmtInt(p.votos_2022));
  setText("metric-municipios", fmtInt(p.municipios_convergencia));
  setText("metric-vereadores", fmtInt(p.vereadores_convergentes));
  setText("metric-potencial", fmtInt(p.potencial_votos));
  setText("metric-percentual-meta", fmtPct(p.percentual_meta));

  setText("legend-votos-2022", `Capital eleitoral de ${cargoArtigo(p)}`);
  setText(
    "legend-municipios",
    `Municípios onde ${cargoArtigo(p)} teve presença eleitoral em 2022 e existem vereadores com votação relevante em 2024 nos mesmos territórios.`
  );
  setText("cities-title", `Cidades onde ${cargoArtigo(p)} mais ajuda`);

  setText("quick-decision-title", `${p.nome_parceiro} ajuda principalmente em ${safe(p.principal_municipio)}`);
  setText(
    "quick-decision-text",
    `Priorizar agendas nos locais onde há sobreposição entre votos de ${cargoArtigo(p)} e votos de vereadores. Local de maior atenção: ${safe(p.principal_local_votacao)}.`
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
    const response = await fetch(`${DATA_URL}?v=mobile-parceiros-v3-${Date.now()}`);

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
