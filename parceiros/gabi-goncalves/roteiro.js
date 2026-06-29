const ROTEIRO_PATH = "../../data/dashboard/parceiros/gabi-goncalves/roteiro_territorial_davi_gabi_v1.json";

function formatarNumeroRoteiro(valor) {
  if (valor === null || valor === undefined || valor === "") {
    return "-";
  }

  const numero = Number(valor);

  if (Number.isNaN(numero)) {
    return String(valor);
  }

  return numero.toLocaleString("pt-BR");
}

async function carregarRoteiro() {
  try {
    const resposta = await fetch(ROTEIRO_PATH, { cache: "no-store" });

    if (!resposta.ok) {
      throw new Error(`Erro ao carregar roteiro: ${resposta.status}`);
    }

    return await resposta.json();
  } catch (erro) {
    console.warn(erro.message);
    return null;
  }
}

function renderResumoRoteiro(dados) {
  const grid = document.getElementById("roteiroResumoGrid");

  if (!grid || !dados) {
    return;
  }

  const indicadores = dados.indicadores || {};

  const cards = [
    {
      rotulo: "Municípios no roteiro",
      valor: indicadores.municipios_no_roteiro,
      detalhe: "Agenda territorial preliminar"
    },
    {
      rotulo: "Semanas planejadas",
      valor: indicadores.semanas_planejadas,
      detalhe: "Ciclo inicial de visitas"
    },
    {
      rotulo: "Meta Gabi no roteiro",
      valor: indicadores.meta_gabi_roteiro,
      detalhe: "Votos de referência"
    },
    {
      rotulo: "Potencial 10%",
      valor: indicadores.potencial_transferencia_10pct,
      detalhe: "Conversão preliminar"
    }
  ];

  grid.innerHTML = cards.map((card) => `
    <article class="roteiro-mini-card">
      <span>${card.rotulo}</span>
      <strong>${formatarNumeroRoteiro(card.valor)}</strong>
      <small>${card.detalhe}</small>
    </article>
  `).join("");
}

function renderSemanasRoteiro(dados) {
  const grid = document.getElementById("roteiroSemanasGrid");

  if (!grid || !dados) {
    return;
  }

  const semanas = dados.resumo_semanal || [];

  if (!semanas.length) {
    grid.innerHTML = `
      <article class="roteiro-empty">
        Roteiro semanal ainda não foi calculado.
      </article>
    `;
    return;
  }

  grid.innerHTML = semanas.map((semana) => `
    <article class="semana-card">
      <strong>${semana.semana}</strong>
      <h3>${semana.total_municipios} município(s)</h3>
      <p>${semana.municipios}</p>
      <small>${semana.objetivo}</small>
    </article>
  `).join("");
}

function renderTabelaRoteiro(dados) {
  const tbody = document.getElementById("roteiroTableBody");

  if (!tbody || !dados) {
    return;
  }

  const roteiro = dados.roteiro || [];

  if (!roteiro.length) {
    tbody.innerHTML = `
      <tr class="empty-row">
        <td colspan="7">Roteiro territorial ainda não disponível.</td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = roteiro.slice(0, 20).map((item) => `
    <tr>
      <td>${item.ordem}</td>
      <td>${item.semana}<br><small>${item.dia} · ${item.turno}</small></td>
      <td>${item.municipio}</td>
      <td>${item.prioridade}</td>
      <td>${item.lideranca || "-"}</td>
      <td>${formatarNumeroRoteiro(item.meta_gabi)}</td>
      <td>${item.tipo_agenda}</td>
    </tr>
  `).join("");
}

async function inicializarRoteiro() {
  const dados = await carregarRoteiro();

  renderResumoRoteiro(dados);
  renderSemanasRoteiro(dados);
  renderTabelaRoteiro(dados);
}

document.addEventListener("DOMContentLoaded", inicializarRoteiro);
