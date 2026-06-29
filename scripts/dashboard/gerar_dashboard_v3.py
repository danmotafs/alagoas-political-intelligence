import json
import shutil
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

FINAL_DIR = BASE_DIR / "data" / "final"
DASH_V2_DIR = BASE_DIR / "dashboard_v2"
DASH_V3_DIR = BASE_DIR / "dashboard_v3"

ARQ_POLOS = FINAL_DIR / "polos_eleitorais_top10.csv"
ARQ_REDUTOS = FINAL_DIR / "redutos_qualificados_top10.csv"
ARQ_AGENDA = FINAL_DIR / "agenda_territorial_davi_maia.csv"

SAIDA_DATA = DASH_V3_DIR / "territorial_v3_data.js"
SAIDA_HTML = DASH_V3_DIR / "index.html"


def ler_csv(caminho):
    for encoding in ["utf-8-sig", "latin1"]:
        for sep in [";", ","]:
            try:
                df = pd.read_csv(caminho, sep=sep, encoding=encoding, dtype=str, low_memory=False)
                if len(df.columns) > 1:
                    return df.fillna("")
            except Exception:
                pass
    raise ValueError(f"Não foi possível ler {caminho}")


def copiar_dashboard_v2():
    if not DASH_V2_DIR.exists():
        raise FileNotFoundError(f"Pasta dashboard_v2 não encontrada: {DASH_V2_DIR}")

    if DASH_V3_DIR.exists():
        shutil.rmtree(DASH_V3_DIR)

    shutil.copytree(DASH_V2_DIR, DASH_V3_DIR)


def main():
    copiar_dashboard_v2()

    polos = ler_csv(ARQ_POLOS)
    redutos = ler_csv(ARQ_REDUTOS)
    agenda = ler_csv(ARQ_AGENDA)

    data = {
        "polos": polos.to_dict(orient="records"),
        "redutos": redutos.to_dict(orient="records"),
        "agenda": agenda.to_dict(orient="records"),
        "resumo": {
            "polos": len(polos),
            "redutos": len(redutos),
            "agenda": len(agenda),
            "municipios": agenda["municipio"].nunique(),
        },
    }

    SAIDA_DATA.write_text(
        "window.TERRITORIAL_V3_DATA = " + json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    html = SAIDA_HTML.read_text(encoding="utf-8")

    bloco = """
<script src="territorial_v3_data.js"></script>

<section class="section" id="mapa-influencia-territorial">
  <div class="section-header">
    <div class="eyebrow">DASHBOARD V3</div>
    <h2>Mapa de Influência Territorial</h2>
    <p>Nova camada operacional baseada em votação por seção, polos eleitorais, redutos qualificados e agenda territorial.</p>
  </div>

  <div class="cards-grid">
    <div class="metric-card"><span>Polos eleitorais</span><strong id="v3Polos">0</strong></div>
    <div class="metric-card"><span>Redutos qualificados</span><strong id="v3Redutos">0</strong></div>
    <div class="metric-card"><span>Agendas territoriais</span><strong id="v3Agenda">0</strong></div>
    <div class="metric-card"><span>Municípios estratégicos</span><strong id="v3Municipios">0</strong></div>
  </div>

  <div class="filters-card">
    <div class="section-header">
      <div class="eyebrow">OPERAÇÃO TERRITORIAL</div>
      <h2>Agenda, Polos e Redutos</h2>
      <p>Identifique onde Davi Maia deve priorizar presença física, reuniões e mobilização.</p>
    </div>

    <div class="tab-buttons">
      <button onclick="v3Tab='agenda';v3Render()">Agenda Territorial</button>
      <button onclick="v3Tab='polos';v3Render()">Polos Eleitorais</button>
      <button onclick="v3Tab='redutos';v3Render()">Redutos Qualificados</button>
    </div>

    <div class="filter-grid">
      <select id="v3Municipio" onchange="v3Render()">
        <option value="">Todos os municípios</option>
      </select>
      <input id="v3Busca" oninput="v3Render()" placeholder="Buscar vereador, local ou bairro">
    </div>

    <div id="v3Tabela"></div>
  </div>
</section>

<script>
const v3 = window.TERRITORIAL_V3_DATA;
let v3Tab = "agenda";

function fmt(v){ return v || ""; }

function pct(v){
  let n = Number(String(v || "").replace(",", "."));
  if (Number.isNaN(n)) return v || "";
  if (n > 100) n = n / 100;
  return n.toLocaleString("pt-BR", {minimumFractionDigits:2, maximumFractionDigits:2}) + "%";
}

function badge(v){
  return `<span class="status-badge">${v || ""}</span>`;
}

function initV3(){
  document.getElementById("v3Polos").innerText = v3.resumo.polos;
  document.getElementById("v3Redutos").innerText = v3.resumo.redutos;
  document.getElementById("v3Agenda").innerText = v3.resumo.agenda;
  document.getElementById("v3Municipios").innerText = v3.resumo.municipios;

  const municipios = [...new Set(v3.agenda.map(x => x.municipio).filter(Boolean))].sort();
  const select = document.getElementById("v3Municipio");
  municipios.forEach(m => {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    select.appendChild(opt);
  });

  v3Render();
}

function filtrar(rows){
  const municipio = document.getElementById("v3Municipio").value.toLowerCase();
  const busca = document.getElementById("v3Busca").value.toLowerCase();

  return rows.filter(r => {
    const okMun = !municipio || String(r.municipio || "").toLowerCase() === municipio;
    const okBusca = !busca || Object.values(r).join(" ").toLowerCase().includes(busca);
    return okMun && okBusca;
  }).slice(0, 200);
}

function tabelaAgenda(){
  const rows = filtrar(v3.agenda);
  return `<table><thead><tr>
    <th>#</th><th>Município</th><th>Vereador</th><th>Partido</th><th>Local prioritário</th><th>Bairro</th><th>Votos</th><th>%</th><th>Nível</th><th>Agenda</th>
  </tr></thead><tbody>
  ${rows.map(r => `<tr>
    <td>${fmt(r.ranking_reduto_qualificado)}</td>
    <td>${fmt(r.municipio)}</td>
    <td>${fmt(r.vereador)}</td>
    <td>${fmt(r.partido)}</td>
    <td>${fmt(r.local_prioritario)}</td>
    <td>${fmt(r.bairro)}</td>
    <td>${fmt(r.votos_local_principal)}</td>
    <td>${pct(r.percentual_local_principal)}</td>
    <td>${badge(r.nivel_reduto)}</td>
    <td>${badge(r.prioridade_agenda)}</td>
  </tr>`).join("")}</tbody></table>`;
}

function tabelaPolos(){
  const rows = filtrar(v3.polos);
  return `<table><thead><tr>
    <th>Ranking</th><th>Município</th><th>Local</th><th>Bairro</th><th>Votos</th><th>Vereadores</th><th>Seções</th><th>Classificação</th>
  </tr></thead><tbody>
  ${rows.map(r => `<tr>
    <td>${fmt(r.ranking_polo_geral)}</td>
    <td>${fmt(r.municipio)}</td>
    <td>${fmt(r.local_votacao)}</td>
    <td>${fmt(r.bairro)}</td>
    <td>${fmt(r.votos_totais)}</td>
    <td>${fmt(r.qtd_vereadores)}</td>
    <td>${fmt(r.qtd_secoes)}</td>
    <td>${badge(r.classificacao_local)}</td>
  </tr>`).join("")}</tbody></table>`;
}

function tabelaRedutos(){
  const rows = filtrar(v3.redutos);
  return `<table><thead><tr>
    <th>#</th><th>Município</th><th>Vereador</th><th>Partido</th><th>Local</th><th>Votos local</th><th>Votos total</th><th>%</th><th>Nível</th>
  </tr></thead><tbody>
  ${rows.map(r => `<tr>
    <td>${fmt(r.ranking_reduto_qualificado)}</td>
    <td>${fmt(r.municipio)}</td>
    <td>${fmt(r.vereador)}</td>
    <td>${fmt(r.partido)}</td>
    <td>${fmt(r.local_principal)}</td>
    <td>${fmt(r.votos_local_principal)}</td>
    <td>${fmt(r.votos_totais_vereador)}</td>
    <td>${pct(r.percentual_local_principal)}</td>
    <td>${badge(r.nivel_reduto)}</td>
  </tr>`).join("")}</tbody></table>`;
}

function v3Render(){
  if(v3Tab === "agenda") document.getElementById("v3Tabela").innerHTML = tabelaAgenda();
  if(v3Tab === "polos") document.getElementById("v3Tabela").innerHTML = tabelaPolos();
  if(v3Tab === "redutos") document.getElementById("v3Tabela").innerHTML = tabelaRedutos();
}

initV3();
</script>
"""

    html = html.replace("</body>", bloco + "\n</body>")
    SAIDA_HTML.write_text(html, encoding="utf-8")

    print("Dashboard V3 gerado preservando a estrutura completa do V2.")
    print(f"Abra: {SAIDA_HTML}")


if __name__ == "__main__":
    main()