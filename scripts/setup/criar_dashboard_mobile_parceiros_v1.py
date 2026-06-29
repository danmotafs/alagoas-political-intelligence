import os


BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

MOBILE_DIR = os.path.join(BASE_DIR, "dashboard_mobile_parceiros")
CSS_DIR = os.path.join(MOBILE_DIR, "css")
JS_DIR = os.path.join(MOBILE_DIR, "js")

os.makedirs(MOBILE_DIR, exist_ok=True)
os.makedirs(CSS_DIR, exist_ok=True)
os.makedirs(JS_DIR, exist_ok=True)

INDEX_HTML = os.path.join(MOBILE_DIR, "index.html")
CSS_FILE = os.path.join(CSS_DIR, "mobile-parceiros.css")
JS_FILE = os.path.join(JS_DIR, "mobile-parceiros.js")


HTML = r'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <title>Painel Mobile — Parceiros Davi Maia 2026</title>

  <link rel="stylesheet" href="css/mobile-parceiros.css?v=1" />
</head>

<body>
  <main class="app-shell">
    <header class="hero">
      <div class="topbar">
        <a href="../dashboard_v2/" class="back-link">← Painel completo</a>
        <span class="tag">Mobile</span>
      </div>

      <p class="eyebrow">Rede Davi Maia 2026</p>
      <h1>Parceiros Estratégicos</h1>
      <p class="subtitle">
        Leitura rápida de contribuição territorial dos parceiros políticos para a meta de 60 mil votos.
      </p>
    </header>

    <section class="section compact">
      <div class="section-title-row">
        <div>
          <p class="eyebrow mini">Selecionar parceiro</p>
          <h2>Quem vai abrir território?</h2>
        </div>
      </div>

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
          <p class="eyebrow mini">Parceiro selecionado</p>
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

        <article class="metric-card">
          <small>Municípios</small>
          <strong id="metric-municipios">-</strong>
          <span>Com convergência</span>
        </article>

        <article class="metric-card">
          <small>Vereadores</small>
          <strong id="metric-vereadores">-</strong>
          <span>Prioritários</span>
        </article>

        <article class="metric-card featured">
          <small>Potencial 20%</small>
          <strong id="metric-potencial">-</strong>
          <span>Para meta Davi</span>
        </article>

        <article class="metric-card">
          <small>% da meta</small>
          <strong id="metric-percentual-meta">-</strong>
          <span>Meta: 60 mil votos</span>
        </article>
      </section>

      <section class="decision-card">
        <p class="eyebrow mini">Decisão rápida</p>
        <h2 id="quick-decision-title">-</h2>
        <p id="quick-decision-text">-</p>
      </section>

      <section class="section">
        <p class="eyebrow mini">Principais cidades</p>
        <h2>Cidades onde o parceiro mais ajuda</h2>
        <div id="top-cities" class="list-stack"></div>
      </section>

      <section class="section">
        <p class="eyebrow mini">Locais prioritários</p>
        <h2>Onde visitar primeiro</h2>
        <div id="top-locations" class="list-stack"></div>
      </section>

      <section class="section">
        <p class="eyebrow mini">Vereadores convergentes</p>
        <h2>Quem abordar com o parceiro</h2>
        <div id="top-vereadores" class="list-stack"></div>
      </section>

      <section class="section">
        <p class="eyebrow mini">Agenda sugerida</p>
        <h2>Próximas ações</h2>
        <div id="agenda-list" class="list-stack"></div>
      </section>
    </section>

    <section id="empty-state" class="empty-state hidden">
      <h2>Nenhum parceiro processado ainda</h2>
      <p>
        O painel mobile será preenchido automaticamente quando o painel completo gerar o módulo de parceiros estratégicos.
      </p>
    </section>
  </main>

  <script src="js/mobile-parceiros.js?v=1"></script>
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
  --text: #0b1b45;
  --muted: #6b7280;
  --line: #dce4f2;
  --bg: #f3f6fb;
  --white: #ffffff;
  --success: #16a34a;
  --warning: #ca8a04;
}

body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
  color: var(--text);
  background:
    radial-gradient(circle at top right, rgba(255, 225, 0, .18), transparent 28%),
    radial-gradient(circle at top left, rgba(221, 79, 153, .15), transparent 28%),
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
  display: inline-flex;
  align-items: center;
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
  color: white;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--yellow);
  text-transform: uppercase;
  letter-spacing: .11em;
  font-size: 12px;
  font-weight: 900;
}

.eyebrow.mini {
  color: var(--pink);
  font-size: 11px;
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
  color: rgba(255, 255, 255, .88);
  font-size: 15px;
  line-height: 1.5;
}

.section {
  background: rgba(255, 255, 255, .92);
  border: 1px solid rgba(220, 228, 242, .9);
  border-radius: 24px;
  padding: 18px;
  margin-top: 16px;
  box-shadow: 0 12px 30px rgba(7, 27, 77, .08);
}

.section.compact {
  padding-bottom: 12px;
}

.section h2 {
  margin: 0 0 12px;
  font-size: 22px;
  line-height: 1.12;
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.partner-selector {
  display: flex;
  overflow-x: auto;
  gap: 12px;
  padding: 4px 0 8px;
  scroll-snap-type: x mandatory;
}

.partner-button {
  min-width: 138px;
  max-width: 138px;
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
  width: 62px;
  height: 62px;
  border-radius: 20px;
  background: linear-gradient(145deg, var(--blue-dark), var(--blue));
  color: var(--yellow);
  display: grid;
  place-items: center;
  font-weight: 900;
  font-size: 19px;
  margin-bottom: 10px;
  overflow: hidden;
}

.partner-thumb img {
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

.partner-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
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
  min-height: 116px;
  box-shadow: 0 8px 20px rgba(7, 27, 77, .06);
}

.metric-card.featured {
  border-top: 5px solid var(--yellow);
}

.metric-card small {
  display: block;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .08em;
  font-size: 11px;
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

.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 6px 9px;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
  background: #eef3ff;
  color: var(--blue-dark);
}

.badge.high {
  background: #dcfce7;
  color: #166534;
}

.badge.mid {
  background: #fef9c3;
  color: #854d0e;
}

.badge.low {
  background: #e0f2fe;
  color: #075985;
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

.mini-stat small {
  display: block;
  color: var(--muted);
  font-size: 10px;
  text-transform: uppercase;
  font-weight: 900;
}

.mini-stat strong {
  display: block;
  color: var(--blue-dark);
  font-size: 17px;
  margin-top: 3px;
}

.empty-state {
  margin-top: 16px;
  background: white;
  border: 1px solid var(--line);
  border-radius: 24px;
  padding: 22px;
}

.empty-state h2 {
  margin: 0 0 8px;
}

.empty-state p {
  margin: 0;
  color: var(--muted);
}

@media (max-width: 380px) {
  .hero h1 {
    font-size: 34px;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }

  .partner-profile-card {
    grid-template-columns: 76px 1fr;
  }

  .partner-avatar {
    width: 76px;
    height: 76px;
    border-radius: 22px;
  }
}
'''


JS = r'''const DATA_URL = "../data/dashboard/base_dashboard_v2.json";

let appData = null;
let parceiros = [];
let parceiroSelecionado = null;

function fmtInt(value) {
  const n = Number(value || 0);
  return n.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}

function fmtPct(value) {
  const n = Number(value || 0);
  return `${n.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`;
}

function safe(value, fallback = "-") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function initials(name) {
  const parts = safe(name, "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (parts.length === 0) return "--";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();

  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function getModulo() {
  return appData?.parceiros_estrategicos_2026 || null;
}

function getTerritorialParceiros() {
  const modulo = getModulo();
  return Array.isArray(modulo?.territorial_parceiros)
    ? modulo.territorial_parceiros
    : [];
}

function getResumoPorParceiro() {
  const modulo = getModulo();
  return Array.isArray(modulo?.resumo_por_parceiro)
    ? modulo.resumo_por_parceiro
    : [];
}

function getTopConvergencias() {
  const modulo = getModulo();
  return Array.isArray(modulo?.top_convergencias)
    ? modulo.top_convergencias
    : [];
}

function getVereadoresPrioritarios() {
  const modulo = getModulo();
  return Array.isArray(modulo?.vereadores_prioritarios)
    ? modulo.vereadores_prioritarios
    : [];
}

function normalizarNome(value) {
  return safe(value, "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toUpperCase();
}

function encontrarTerritorial(nomeParceiro) {
  const alvo = normalizarNome(nomeParceiro);

  return getTerritorialParceiros().find((item) => {
    const nome =
      item?.parceiro?.nome_parceiro ||
      item?.metadata?.titulo ||
      item?.candidato_identificado?.nome_votavel ||
      "";
    return normalizarNome(nome).includes(alvo) || alvo.includes(normalizarNome(nome));
  });
}

function montarParceiros() {
  const resumos = getResumoPorParceiro();

  parceiros = resumos.map((resumo) => {
    const territorial = encontrarTerritorial(resumo.nome_parceiro);

    return {
      nome: resumo.nome_parceiro,
      resumo,
      territorial,
    };
  });
}

function renderPartnerSelector() {
  const container = document.getElementById("partner-selector");
  if (!container) return;

  if (!parceiros.length) {
    container.innerHTML = `<div class="loading-card">Nenhum parceiro encontrado.</div>`;
    return;
  }

  container.innerHTML = parceiros
    .map((p, index) => {
      const active = parceiroSelecionado?.nome === p.nome ? "active" : "";
      const cargo = p.territorial?.parceiro?.cargo_atual || "Parceiro político";
      const total = p.resumo?.potencial_vereadores_unicos_20pct || 0;

      return `
        <button class="partner-button ${active}" data-index="${index}" type="button">
          <div class="partner-thumb"><span>${initials(p.nome)}</span></div>
          <strong>${safe(p.nome)}</strong>
          <span>${safe(cargo)}</span>
          <span>Potencial 20%: ${fmtInt(total)}</span>
        </button>
      `;
    })
    .join("");

  container.querySelectorAll(".partner-button").forEach((btn) => {
    btn.addEventListener("click", () => {
      const index = Number(btn.dataset.index);
      selecionarParceiro(index);
    });
  });
}

function classificacaoBadge(texto) {
  const t = safe(texto);
  const n = normalizarNome(t);

  let cls = "low";
  if (n.includes("ALTA")) cls = "high";
  else if (n.includes("MEDIA")) cls = "mid";

  return `<span class="badge ${cls}">${t}</span>`;
}

function itemCard({ title, badge, description, stats }) {
  const statsHtml = Array.isArray(stats)
    ? `
      <div class="two-col">
        ${stats
          .map(
            (s) => `
              <div class="mini-stat">
                <small>${s.label}</small>
                <strong>${s.value}</strong>
              </div>
            `
          )
          .join("")}
      </div>
    `
    : "";

  return `
    <article class="item-card">
      <div class="item-card-header">
        <h3>${safe(title)}</h3>
        ${badge ? badge : ""}
      </div>
      ${description ? `<p>${description}</p>` : ""}
      ${statsHtml}
    </article>
  `;
}

function renderTopCities(parceiro) {
  const el = document.getElementById("top-cities");
  if (!el) return;

  const municipios = Array.isArray(parceiro.territorial?.top_municipios)
    ? parceiro.territorial.top_municipios
    : [];

  const resumoMunicipios = Array.isArray(getModulo()?.resumo_municipios)
    ? getModulo().resumo_municipios.filter((m) => m.nome_parceiro === parceiro.nome)
    : [];

  const base = resumoMunicipios.length ? resumoMunicipios : municipios;

  if (!base.length) {
    el.innerHTML = itemCard({
      title: "Sem cidades processadas",
      description: "Os dados serão preenchidos após o processamento territorial do parceiro.",
    });
    return;
  }

  el.innerHTML = base.slice(0, 5).map((item, index) => {
    const municipio = item.municipio || item.municipio_original || "-";
    const votosParceiro = item.votos_parceiro_nos_locais || item.votos_parceiro || 0;
    const vereadores = item.vereadores_convergentes || item.locais_votacao || 0;
    const potencial = item.potencial_davi_20pct_local || 0;

    return itemCard({
      title: `${index + 1}. ${municipio}`,
      badge: `<span class="badge">${fmtInt(votosParceiro)} votos</span>`,
      description: "Cidade com presença territorial relevante do parceiro e/ou convergência com vereadores.",
      stats: [
        { label: "Vereadores/locais", value: fmtInt(vereadores) },
        { label: "Potencial 20%", value: fmtInt(potencial) },
      ],
    });
  }).join("");
}

function renderTopLocations(parceiro) {
  const el = document.getElementById("top-locations");
  if (!el) return;

  const top = getTopConvergencias()
    .filter((item) => item.nome_parceiro === parceiro.nome)
    .slice(0, 6);

  const territorialLocais = Array.isArray(parceiro.territorial?.top_locais_votacao)
    ? parceiro.territorial.top_locais_votacao
    : [];

  const base = top.length ? top : territorialLocais.slice(0, 6);

  if (!base.length) {
    el.innerHTML = itemCard({
      title: "Sem locais priorizados",
      description: "Os locais aparecerão após o cruzamento com vereadores.",
    });
    return;
  }

  el.innerHTML = base.map((item, index) => {
    const local = item.local_votacao_parceiro || item.local_votacao || "-";
    const municipio = item.municipio || "-";
    const votosParceiro = item.votos_parceiro_local || item.votos_parceiro || 0;
    const vereador = item.vereador ? `Vereador convergente: ${item.vereador}` : "Reduto eleitoral do parceiro.";

    return itemCard({
      title: `${index + 1}. ${local}`,
      badge: classificacaoBadge(item.classificacao_convergencia || item.forca_reduto || "Prioritário"),
      description: `${municipio}. ${vereador}`,
      stats: [
        { label: "Votos parceiro", value: fmtInt(votosParceiro) },
        { label: "Índice", value: item.indice_convergencia ? Number(item.indice_convergencia).toFixed(2) : "-" },
      ],
    });
  }).join("");
}

function renderVereadores(parceiro) {
  const el = document.getElementById("top-vereadores");
  if (!el) return;

  const lista = getVereadoresPrioritarios()
    .filter((item) => item.nome_parceiro === parceiro.nome)
    .slice(0, 8);

  if (!lista.length) {
    el.innerHTML = itemCard({
      title: "Sem vereadores convergentes",
      description: "A lista será preenchida após o cruzamento com os redutos dos vereadores de 2024.",
    });
    return;
  }

  el.innerHTML = lista.map((item, index) => {
    return itemCard({
      title: `${index + 1}. ${safe(item.vereador)}`,
      badge: classificacaoBadge(item.classificacao_convergencia),
      description: `${safe(item.municipio)} · ${safe(item.local_votacao_parceiro)} · Partido: ${safe(item.partido_vereador)}`,
      stats: [
        { label: "Votos vereador", value: fmtInt(item.votos_vereador_local) },
        { label: "Potencial 20%", value: fmtInt(item.potencial_davi_20pct_local) },
      ],
    });
  }).join("");
}

function renderAgenda(parceiro) {
  const el = document.getElementById("agenda-list");
  if (!el) return;

  const lista = getTopConvergencias()
    .filter((item) => item.nome_parceiro === parceiro.nome)
    .slice(0, 5);

  if (!lista.length) {
    el.innerHTML = itemCard({
      title: "Sem agenda sugerida",
      description: "A agenda será gerada quando houver convergência territorial qualificada.",
    });
    return;
  }

  el.innerHTML = lista.map((item, index) => {
    return itemCard({
      title: `${index + 1}. ${safe(item.municipio)} — ${safe(item.local_votacao_parceiro)}`,
      badge: `<span class="badge high">Visitar</span>`,
      description: `Agenda Davi + ${parceiro.nome} com foco no vereador ${safe(item.vereador)}. Validar apoio, lideranças locais e entrada territorial.`,
      stats: [
        { label: "Votos parceiro", value: fmtInt(item.votos_parceiro_local) },
        { label: "Votos vereador", value: fmtInt(item.votos_vereador_local) },
      ],
    });
  }).join("");
}

function atualizarDetalhe(parceiro) {
  const detail = document.getElementById("partner-detail");
  const empty = document.getElementById("empty-state");

  if (!detail) return;

  detail.classList.remove("hidden");
  if (empty) empty.classList.add("hidden");

  const territorial = parceiro.territorial || {};
  const resumo = parceiro.resumo || {};
  const parceiroInfo = territorial.parceiro || {};
  const candidato = territorial.candidato_identificado || {};
  const territorialResumo = territorial.resumo || {};

  const nome = parceiro.nome;
  const cargo = parceiroInfo.cargo_atual || candidato.cargo || "Parceiro político";

  setText("partner-name", nome);
  setText("partner-role", cargo);

  const avatar = document.getElementById("partner-avatar");
  if (avatar) {
    avatar.innerHTML = `<span>${initials(nome)}</span>`;
  }

  setText("metric-votos-2022", fmtInt(territorialResumo.total_votos_parceiro || candidato.votos_total_auditoria || 0));
  setText("metric-municipios", fmtInt(resumo.municipios_com_convergencia || territorialResumo.municipios_com_votos || 0));
  setText("metric-vereadores", fmtInt(resumo.vereadores_convergentes || 0));
  setText("metric-potencial", fmtInt(resumo.potencial_vereadores_unicos_20pct || 0));
  setText("metric-percentual-meta", fmtPct(resumo.percentual_meta_davi_20pct || 0));

  const principalMunicipio = resumo.principal_municipio || "territórios convergentes";
  const principalLocal = resumo.principal_local_votacao || "locais prioritários";

  setText("quick-decision-title", `${nome} ajuda principalmente em ${principalMunicipio}`);
  setText(
    "quick-decision-text",
    `O uso político mais objetivo deste parceiro é abrir diálogo com vereadores nos locais onde houve sobreposição entre a votação do parceiro em 2022 e os redutos dos vereadores em 2024. Local de maior atenção: ${principalLocal}.`
  );

  renderTopCities(parceiro);
  renderTopLocations(parceiro);
  renderVereadores(parceiro);
  renderAgenda(parceiro);
}

function selecionarParceiro(index) {
  parceiroSelecionado = parceiros[index];
  renderPartnerSelector();
  atualizarDetalhe(parceiroSelecionado);
}

async function init() {
  try {
    const response = await fetch(`${DATA_URL}?v=mobile-parceiros-${Date.now()}`);

    if (!response.ok) {
      throw new Error(`Erro HTTP ${response.status}`);
    }

    appData = await response.json();

    montarParceiros();

    if (!parceiros.length) {
      document.getElementById("empty-state")?.classList.remove("hidden");
      return;
    }

    selecionarParceiro(0);
  } catch (error) {
    console.error("Erro ao carregar painel mobile de parceiros:", error);

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


def main():
    print("=" * 80)
    print("CRIANDO DASHBOARD MOBILE — PARCEIROS DAVI 2026")
    print("=" * 80)

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(HTML)

    with open(CSS_FILE, "w", encoding="utf-8") as f:
        f.write(CSS)

    with open(JS_FILE, "w", encoding="utf-8") as f:
        f.write(JS)

    print("Arquivos criados:")
    print(INDEX_HTML)
    print(CSS_FILE)
    print(JS_FILE)

    print()
    print("Teste local:")
    print("python -m http.server 8000")
    print("http://localhost:8000/dashboard_mobile_parceiros/?v=mobile-parceiros-v1")
    print("=" * 80)


if __name__ == "__main__":
    main()