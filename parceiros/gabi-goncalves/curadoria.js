const CURADORIA_PATH = "../../data/dashboard/parceiros/gabi-goncalves/curadoria_politica_davi_gabi_v1.json";

function formatarNumeroCuradoria(valor) {
  if (valor === null || valor === undefined || valor === "") {
    return "-";
  }

  const numero = Number(valor);

  if (Number.isNaN(numero)) {
    return String(valor);
  }

  return numero.toLocaleString("pt-BR");
}

async function carregarCuradoria() {
  try {
    const resposta = await fetch(CURADORIA_PATH, { cache: "no-store" });

    if (!resposta.ok) {
      throw new Error(`Erro ao carregar curadoria: ${resposta.status}`);
    }

    return await resposta.json();
  } catch (erro) {
    console.warn(erro.message);
    return null;
  }
}

function renderCuradoriaResumo(dados) {
  const grid = document.getElementById("curadoriaResumoGrid");

  if (!grid || !dados) {
    return;
  }

  const indicadores = dados.indicadores || {};

  const cards = [
    {
      rotulo: "Municípios para curadoria",
      valor: indicadores.municipios_para_curadoria,
      detalhe: "Base Davi + Gabi"
    },
    {
      rotulo: "Pendentes",
      valor: indicadores.curadorias_pendentes,
      detalhe: "Aguardando validação"
    },
    {
      rotulo: "Prioridade imediata",
      valor: indicadores.prioridade_imediata,
      detalhe: "Validar primeiro"
    },
    {
      rotulo: "Meta em curadoria",
      valor: indicadores.meta_gabi_em_curadoria,
      detalhe: "Votos de referência"
    }
  ];

  grid.innerHTML = cards.map((card) => `
    <article class="curadoria-mini-card">
      <span>${card.rotulo}</span>
      <strong>${formatarNumeroCuradoria(card.valor)}</strong>
      <small>${card.detalhe}</small>
    </article>
  `).join("");
}

function renderCuradoriaTabela(dados) {
  const tbody = document.getElementById("curadoriaTableBody");

  if (!tbody || !dados) {
    return;
  }

  const linhas = dados.curadoria || [];

  if (!linhas.length) {
    tbody.innerHTML = `
      <tr class="empty-row">
        <td colspan="7">Curadoria política ainda não disponível.</td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = linhas.slice(0, 20).map((item) => `
    <tr>
      <td>${item.ordem}</td>
      <td>${item.municipio}</td>
      <td>${item.prioridade}<br><small>${item.prazo}</small></td>
      <td>${item.lideranca || "-"}</td>
      <td>${item.relacao_gabi}</td>
      <td>${item.relacao_davi}</td>
      <td>${item.decisao}</td>
    </tr>
  `).join("");
}

async function inicializarCuradoria() {
  const dados = await carregarCuradoria();

  renderCuradoriaResumo(dados);
  renderCuradoriaTabela(dados);
}

document.addEventListener("DOMContentLoaded", inicializarCuradoria);
