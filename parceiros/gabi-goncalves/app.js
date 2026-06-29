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
