import os
import re
import json


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

MOBILE_DIR = os.path.join(BASE_DIR, "dashboard_mobile_parceiros")
ASSETS_PARCEIROS_DIR = os.path.join(MOBILE_DIR, "assets", "parceiros")

INDEX_HTML = os.path.join(MOBILE_DIR, "index.html")
CSS_FILE = os.path.join(MOBILE_DIR, "css", "mobile-parceiros.css")
JS_FILE = os.path.join(MOBILE_DIR, "js", "mobile-parceiros.js")

MOBILE_DATA_JSON = os.path.join(
    BASE_DIR,
    "data",
    "dashboard",
    "parceiros",
    "mobile_parceiros_v2.json",
)


# ============================================================
# FUNÇÕES
# ============================================================

def encontrar_logo_davi():
    """
    Localiza a logo do Davi Maia na pasta:
    dashboard_mobile_parceiros/assets/parceiros

    Prioridade máxima:
    - logo_davi_maia.*
    - logo-davi-maia.*

    Isso evita que o script use uma foto do Davi no lugar da logo.
    """

    if not os.path.exists(ASSETS_PARCEIROS_DIR):
        return ""

    arquivos = os.listdir(ASSETS_PARCEIROS_DIR)

    candidatos_prioritarios = []
    candidatos_secundarios = []

    for arquivo in arquivos:
        nome = arquivo.lower()

        if not nome.endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):
            continue

        # Prioridade máxima: logo_davi_maia
        if nome.startswith("logo_davi_maia") or nome.startswith("logo-davi-maia"):
            candidatos_prioritarios.append(arquivo)
            continue

        # Fallback apenas se não existir logo_davi_maia
        if (
            "logo" in nome
            and (
                "davi_maia" in nome
                or "davi-maia" in nome
                or "davi" in nome
            )
        ):
            candidatos_secundarios.append(arquivo)

    if candidatos_prioritarios:
        candidatos_prioritarios.sort()
        return f"assets/parceiros/{candidatos_prioritarios[0]}"

    if candidatos_secundarios:
        candidatos_secundarios.sort()
        return f"assets/parceiros/{candidatos_secundarios[0]}"

    return ""


def enriquecer_mobile_data():
    """
    Acrescenta campos auxiliares de cargo/gênero ao JSON mobile.

    Exemplo:
    cargo_atual = Deputada Estadual
    gera:
    - cargo_generico = deputada
    - cargo_generico_artigo = a deputada
    - cargo_generico_artigo_maiusculo = A deputada
    """

    if not os.path.exists(MOBILE_DATA_JSON):
        print(f"[AVISO] JSON mobile não encontrado: {MOBILE_DATA_JSON}")
        return

    with open(MOBILE_DATA_JSON, "r", encoding="utf-8") as f:
        dados = json.load(f)

    for parceiro in dados.get("parceiros", []):
        cargo = str(parceiro.get("cargo_atual", "")).strip().lower()

        if "deputada" in cargo:
            parceiro["cargo_generico"] = "deputada"
            parceiro["cargo_generico_artigo"] = "a deputada"
            parceiro["cargo_generico_artigo_maiusculo"] = "A deputada"

        elif "deputado" in cargo:
            parceiro["cargo_generico"] = "deputado"
            parceiro["cargo_generico_artigo"] = "o deputado"
            parceiro["cargo_generico_artigo_maiusculo"] = "O deputado"

        elif "vereadora" in cargo:
            parceiro["cargo_generico"] = "vereadora"
            parceiro["cargo_generico_artigo"] = "a vereadora"
            parceiro["cargo_generico_artigo_maiusculo"] = "A vereadora"

        elif "vereador" in cargo:
            parceiro["cargo_generico"] = "vereador"
            parceiro["cargo_generico_artigo"] = "o vereador"
            parceiro["cargo_generico_artigo_maiusculo"] = "O vereador"

        elif "senadora" in cargo:
            parceiro["cargo_generico"] = "senadora"
            parceiro["cargo_generico_artigo"] = "a senadora"
            parceiro["cargo_generico_artigo_maiusculo"] = "A senadora"

        elif "senador" in cargo:
            parceiro["cargo_generico"] = "senador"
            parceiro["cargo_generico_artigo"] = "o senador"
            parceiro["cargo_generico_artigo_maiusculo"] = "O senador"

        elif "prefeita" in cargo:
            parceiro["cargo_generico"] = "prefeita"
            parceiro["cargo_generico_artigo"] = "a prefeita"
            parceiro["cargo_generico_artigo_maiusculo"] = "A prefeita"

        elif "prefeito" in cargo:
            parceiro["cargo_generico"] = "prefeito"
            parceiro["cargo_generico_artigo"] = "o prefeito"
            parceiro["cargo_generico_artigo_maiusculo"] = "O prefeito"

        else:
            parceiro["cargo_generico"] = "liderança"
            parceiro["cargo_generico_artigo"] = "a liderança"
            parceiro["cargo_generico_artigo_maiusculo"] = "A liderança"

    with open(MOBILE_DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2, allow_nan=False)

    print("[OK] mobile_parceiros_v2.json enriquecido com cargo/gênero.")


def gerar_html(logo_davi):
    """
    Regenera o index.html do dashboard mobile.
    Remove o botão 'Mobile' e coloca a logo do Davi no topo direito.
    """

    if logo_davi:
        logo_html = f"""
        <div class="davi-logo-wrap">
          <img src="{logo_davi}" alt="Davi Maia" />
        </div>
        """
    else:
        logo_html = """
        <div class="davi-logo-wrap fallback">
          <span>DAVI<br>MAIA</span>
        </div>
        """

    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <title>Painel Mobile — Parceiros Davi Maia 2026</title>

  <link rel="stylesheet" href="css/mobile-parceiros.css?v=3" />
</head>

<body>
  <main class="app-shell">
    <header class="hero">
      <div class="topbar">
        <a href="../dashboard_v2/" class="back-link">← Painel completo</a>
        {logo_html}
      </div>

      <p class="eyebrow yellow">Rede Davi Maia 2026</p>
      <h1>Parceiros Estratégicos</h1>
      <p class="subtitle">
        Decisão rápida: quem ajuda, onde ajuda, com quais vereadores e com qual potencial de votos.
      </p>
    </header>

    <section class="section compact">
      <p class="eyebrow">Selecionar liderança</p>
      <h2>Quem vai abrir território?</h2>
      <div id="partner-selector" class="partner-selector">
        <div class="loading-card">Carregando lideranças...</div>
      </div>
    </section>

    <section id="partner-detail" class="partner-detail hidden">
      <div class="partner-profile-card">
        <div id="partner-avatar" class="partner-avatar">
          <span>--</span>
        </div>

        <div class="partner-profile-info">
          <p id="selected-cargo-label" class="eyebrow">Liderança selecionada</p>
          <h2 id="partner-name">-</h2>
          <p id="partner-role">-</p>
        </div>
      </div>

      <section class="metric-grid">
        <article class="metric-card featured">
          <small>Votos em 2022</small>
          <strong id="metric-votos-2022">-</strong>
          <span id="legend-votos-2022">Capital eleitoral da liderança</span>
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
          <span class="footnote">
            fórmula: 50% dos votos da liderança no território + 50% dos votos do vereador convergente
          </span>
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
        <h2 id="cities-title">Cidades onde a liderança mais ajuda</h2>
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
      <h2>Nenhuma liderança processada ainda</h2>
      <p>O painel mobile será preenchido automaticamente pelo painel completo.</p>
    </section>
  </main>

  <script src="js/mobile-parceiros.js?v=3"></script>
</body>
</html>
'''

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print("[OK] index.html atualizado.")


def gerar_css():
    """
    Regenera o CSS do painel mobile.
    """

    css = r'''* {
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
  z-index: 2;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 34px;
  gap: 12px;
}

.back-link {
  text-decoration: none;
  color: var(--blue-dark);
  background: white;
  border-radius: 999px;
  padding: 9px 13px;
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
}

.davi-logo-wrap {
  width: 92px;
  height: 48px;
  border-radius: 16px;
  background: rgba(255, 255, 255, .95);
  border: 1px solid rgba(255, 255, 255, .35);
  display: grid;
  place-items: center;
  padding: 7px;
  overflow: hidden;
}

.davi-logo-wrap img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.davi-logo-wrap.fallback span {
  color: var(--blue-dark);
  font-size: 12px;
  line-height: .95;
  font-weight: 900;
  text-align: center;
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

.partner-button,
.add-partner-card {
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

.add-partner-card {
  border: 2px dashed #cbd5e1;
  background: #f8fafc;
  cursor: default;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.add-plus {
  width: 70px;
  height: 70px;
  border-radius: 22px;
  background: white;
  border: 1px solid var(--line);
  color: var(--blue-dark);
  display: grid;
  place-items: center;
  font-size: 38px;
  font-weight: 900;
  margin-bottom: 10px;
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

.partner-button strong,
.add-partner-card strong {
  display: block;
  font-size: 14px;
  line-height: 1.2;
}

.partner-button span,
.add-partner-card span {
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

  .davi-logo-wrap {
    width: 78px;
    height: 42px;
  }
}
'''

    with open(CSS_FILE, "w", encoding="utf-8") as f:
        f.write(css)

    print("[OK] CSS atualizado.")


def gerar_js():
    """
    Regenera o JS do painel mobile.
    """

    js = r'''const DATA_URL = "../data/dashboard/parceiros/mobile_parceiros_v2.json";

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
'''

    with open(JS_FILE, "w", encoding="utf-8") as f:
        f.write(js)

    print("[OK] JS atualizado.")


def main():
    print("=" * 80)
    print("MELHORIAS DASHBOARD MOBILE PARCEIROS V3")
    print("=" * 80)

    logo_davi = encontrar_logo_davi()

    print(f"Logo Davi detectada: {logo_davi or 'NÃO ENCONTRADA — será usado fallback'}")

    enriquecer_mobile_data()
    gerar_html(logo_davi)
    gerar_css()
    gerar_js()

    print()
    print("Arquivos atualizados:")
    print(INDEX_HTML)
    print(CSS_FILE)
    print(JS_FILE)
    print(MOBILE_DATA_JSON)

    print()
    print("Teste local:")
    print("http://localhost:8000/dashboard_mobile_parceiros/?v=mobile-parceiros-v3-logo-davi")
    print("=" * 80)


if __name__ == "__main__":
    main()