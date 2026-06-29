const DATA_URL = "../data/dashboard/base_dashboard_v2.json";

let dashboardData = null;
let municipios = [];

const formatNumber = (value) => {
  return Number(value || 0).toLocaleString("pt-BR");
};

const formatPercent = (value) => {
  return `${Number(value || 0).toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 2,
  })}%`;
};

const getById = (id) => document.getElementById(id);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function carregarDados() {
  try {
    const response = await fetch(DATA_URL);

    if (!response.ok) {
      throw new Error(`Erro ao carregar JSON: ${response.status}`);
    }

    dashboardData = await response.json();
    municipios = dashboardData.municipios || [];

    preencherCards();
    preencherFiltros();
    renderizarDashboard(municipios);
    configurarEventos();
  } catch (error) {
    console.error(error);
    alert(
      "Não foi possível carregar os dados do dashboard. " +
      "Se você abriu o HTML diretamente pelo navegador, execute um servidor local com: python -m http.server 8000"
    );
  }
}

function preencherCards() {
  const indicadores = dashboardData.indicadores || {};

  getById("cardMunicipios").textContent = formatNumber(indicadores.total_municipios);
  getById("cardEleitorado").textContent = formatNumber(indicadores.eleitorado_total);
  getById("cardPopulacao").textContent = formatNumber(indicadores.populacao_total);
  getById("cardVisitados").textContent = formatNumber(indicadores.municipios_visitados);
  getById("cardCobertura").textContent = formatPercent(indicadores.cobertura_territorial_pct);
  getById("cardPrefeitos").textContent = formatNumber(indicadores.prefeitos_mapeados);

  getById("cardVereadores").textContent = formatNumber(indicadores.vereadores_mapeados);
  getById("cardPotencialConservador").textContent = formatNumber(
    indicadores.potencial_transferencia_conservador_total
  );
}

function preencherFiltros() {
  preencherSelect("filtroMunicipio", dashboardData.dimensoes?.municipios || []);
  preencherSelect("filtroPartido", dashboardData.dimensoes?.partidos || []);
  preencherSelect("filtroPrioridade", dashboardData.dimensoes?.prioridades || []);
}

function preencherSelect(id, valores) {
  const select = getById(id);

  valores
    .filter((valor) => valor !== null && valor !== undefined && String(valor).trim() !== "")
    .sort((a, b) => String(a).localeCompare(String(b), "pt-BR"))
    .forEach((valor) => {
      const option = document.createElement("option");
      option.value = valor;
      option.textContent = valor;
      select.appendChild(option);
    });
}

function configurarEventos() {
  [
    "filtroMunicipio",
    "filtroPartido",
    "filtroVisitado",
    "filtroPrioridade",
    "filtroEleitorado",
  ].forEach((id) => {
    getById(id).addEventListener("change", aplicarFiltros);
  });

  getById("btnLimparFiltros").addEventListener("click", limparFiltros);
}

function aplicarFiltros() {
  const municipioSelecionado = getById("filtroMunicipio").value;
  const partidoSelecionado = getById("filtroPartido").value;
  const visitadoSelecionado = getById("filtroVisitado").value;
  const prioridadeSelecionada = getById("filtroPrioridade").value;
  const faixaEleitorado = getById("filtroEleitorado").value;

  let dadosFiltrados = [...municipios];

  if (municipioSelecionado) {
    dadosFiltrados = dadosFiltrados.filter((item) => item.municipio === municipioSelecionado);
  }

  if (partidoSelecionado) {
    dadosFiltrados = dadosFiltrados.filter((item) => item.partido === partidoSelecionado);
  }

  if (visitadoSelecionado !== "") {
    const valorBooleano = visitadoSelecionado === "true";
    dadosFiltrados = dadosFiltrados.filter((item) => item.visitado_pre_campanha === valorBooleano);
  }

  if (prioridadeSelecionada) {
    dadosFiltrados = dadosFiltrados.filter((item) => item.prioridade_final === prioridadeSelecionada);
  }

  if (faixaEleitorado) {
    dadosFiltrados = dadosFiltrados.filter((item) =>
      filtrarFaixaEleitorado(item.eleitorado_2024, faixaEleitorado)
    );
  }

  renderizarDashboard(dadosFiltrados);
}

function filtrarFaixaEleitorado(eleitorado, faixa) {
  const valor = Number(eleitorado || 0);

  if (faixa === "ate_10000") return valor <= 10000;
  if (faixa === "10000_30000") return valor > 10000 && valor <= 30000;
  if (faixa === "30000_100000") return valor > 30000 && valor <= 100000;
  if (faixa === "acima_100000") return valor > 100000;

  return true;
}

function limparFiltros() {
  getById("filtroMunicipio").value = "";
  getById("filtroPartido").value = "";
  getById("filtroVisitado").value = "";
  getById("filtroPrioridade").value = "";
  getById("filtroEleitorado").value = "";

  renderizarDashboard(municipios);
}

function renderizarDashboard(dados) {
  renderizarRanking(dados);
  renderizarNaoVisitados(dados);
  renderizarLiderancasMunicipais();
  renderizarRedePoder(dados);
  renderizarMargens(dados);
  renderizarScore(dados);

  getById("contadorRegistros").textContent = `${formatNumber(dados.length)} registros`;
}

function renderizarRanking(dados) {
  const ranking = [...dados]
    .sort((a, b) => Number(b.indice_estrategico_pct || 0) - Number(a.indice_estrategico_pct || 0))
    .slice(0, 20);

  const tbody = getById("tabelaRanking");
  tbody.innerHTML = "";

  ranking.forEach((item) => {
    const titulo = `Município de ${item.municipio}. Eleitorado: ${formatNumber(item.eleitorado_2024)}. Índice estratégico: ${formatPercent(item.indice_estrategico_pct)}.`;

    tbody.innerHTML += `
      <tr>
        <td>${item.rank || "-"}</td>
        <td title="${escapeHtml(titulo)}"><strong>${escapeHtml(item.municipio || "-")}</strong></td>
        <td>${formatNumber(item.eleitorado_2024)}</td>
        <td>${formatPercent(item.indice_estrategico_pct)}</td>
      </tr>
    `;
  });
}

function renderizarNaoVisitados(dados) {
  const lista = [...dados]
    .filter((item) => item.visitado_pre_campanha === false)
    .sort((a, b) => Number(b.indice_estrategico_pct || 0) - Number(a.indice_estrategico_pct || 0))
    .slice(0, 20);

  const tbody = getById("tabelaNaoVisitados");
  tbody.innerHTML = "";

  lista.forEach((item) => {
    const titulo = `${item.municipio} ainda não aparece como visitado na base. Possui eleitorado de ${formatNumber(item.eleitorado_2024)} e índice estratégico de ${formatPercent(item.indice_estrategico_pct)}.`;

    tbody.innerHTML += `
      <tr>
        <td title="${escapeHtml(titulo)}"><strong>${escapeHtml(item.municipio || "-")}</strong></td>
        <td>${escapeHtml(item.partido || "-")}</td>
        <td>${formatNumber(item.eleitorado_2024)}</td>
        <td>${formatPercent(item.indice_estrategico_pct)}</td>
      </tr>
    `;
  });
}

function renderizarLiderancasMunicipais() {
  const lista = dashboardData.vereadores_municipais || [];
  const tbody = getById("tabelaLiderancasMunicipais");

  if (!tbody) return;

  tbody.innerHTML = "";

  lista
    .sort((a, b) => Number(a.rank_municipal || 9999) - Number(b.rank_municipal || 9999))
    .slice(0, 50)
    .forEach((item) => {
      const conservador = Number(item.potencial_transferencia_conservador || 0);
      const alto = Number(item.potencial_transferencia_alto || 0);
      const votosLider = Number(item.principal_lideranca_votos || 0);
      const totalVotos = Number(item.total_votos_vereadores || 0);

      const tooltipLideranca =
        `${item.principal_lideranca || "Esta liderança"} foi a principal liderança municipal em votos em ${item.municipio || "seu município"}, ` +
        `com ${formatNumber(votosLider)} votos. Considerando a força agregada dos vereadores do município, ` +
        `o potencial estimado de contribuição para Davi Maia varia de ${formatNumber(conservador)} votos em cenário conservador ` +
        `a ${formatNumber(alto)} votos em cenário alto.`;

      const tooltipMunicipio =
        `${item.municipio || "Município"} possui ${formatNumber(item.vereadores_eleitos)} vereadores eleitos, ` +
        `com ${formatNumber(totalVotos)} votos nominais somados. Potencial político municipal: ${item.potencial_politico_municipio || "-"}.`;

      tbody.innerHTML += `
        <tr>
          <td>${item.rank_municipal || "-"}</td>
          <td title="${escapeHtml(tooltipMunicipio)}"><strong>${escapeHtml(item.municipio || "-")}</strong></td>
          <td>${formatNumber(item.vereadores_eleitos)}</td>
          <td>${formatNumber(item.total_votos_vereadores)}</td>
          <td title="${escapeHtml(tooltipLideranca)}"><strong>${escapeHtml(item.principal_lideranca || "-")}</strong></td>
          <td>${escapeHtml(item.principal_lideranca_partido || "-")}</td>
          <td>${formatNumber(item.principal_lideranca_votos)}</td>
          <td><span class="badge prioridade" title="${escapeHtml(tooltipMunicipio)}">${escapeHtml(item.potencial_politico_municipio || "-")}</span></td>
        </tr>
      `;
    });
}

function renderizarRedePoder(dados) {
  const lista = [...dados].sort((a, b) => Number(a.rank || 999) - Number(b.rank || 999));

  const tbody = getById("tabelaRedePoder");
  tbody.innerHTML = "";

  lista.forEach((item) => {
    const statusClass = item.visitado_pre_campanha ? "visitado" : "nao-visitado";
    const statusTexto = item.visitado_pre_campanha ? "Visitado" : "Não visitado";

    const tooltipPrefeito =
      `${item.prefeito || "Prefeito"} é o prefeito de ${item.municipio || "município"}, pelo partido ${item.partido || "-"}. ` +
      `Teve ${formatNumber(item.votos_prefeito)} votos, com ${formatPercent(item.percentual_prefeito)} dos votos. ` +
      `A margem de vitória foi de ${formatPercent(item.margem_vitoria_pct)}.`;

    const tooltipMunicipio =
      `${item.municipio || "Município"} possui eleitorado de ${formatNumber(item.eleitorado_2024)}. ` +
      `Status de visitação: ${statusTexto}. Prioridade: ${item.prioridade_final || item.prioridade_politica || "-"}.`;

    const tooltipSegundo =
      `${item.segundo_colocado || "Segundo colocado"} foi o principal concorrente municipal, pelo partido ${item.partido_segundo_colocado || "-"}, ` +
      `com ${formatNumber(item.votos_segundo_colocado)} votos.`;

    tbody.innerHTML += `
      <tr>
        <td title="${escapeHtml(tooltipMunicipio)}"><strong>${escapeHtml(item.municipio || "-")}</strong></td>
        <td title="${escapeHtml(tooltipPrefeito)}"><strong>${escapeHtml(item.prefeito || "-")}</strong></td>
        <td>${escapeHtml(item.partido || "-")}</td>
        <td>${formatNumber(item.eleitorado_2024)}</td>
        <td>${formatPercent(item.margem_vitoria_pct)}</td>
        <td title="${escapeHtml(tooltipSegundo)}">${escapeHtml(item.segundo_colocado || "-")}</td>
        <td><span class="badge ${statusClass}" title="${escapeHtml(tooltipMunicipio)}">${statusTexto}</span></td>
        <td><span class="badge prioridade">${escapeHtml(item.prioridade_final || item.prioridade_politica || "-")}</span></td>
      </tr>
    `;
  });
}

function renderizarMargens(dados) {
  const lista = [...dados]
    .filter((item) => Number(item.margem_vitoria_pct || 0) > 0)
    .sort((a, b) => Number(a.margem_vitoria_pct || 0) - Number(b.margem_vitoria_pct || 0))
    .slice(0, 10);

  const tbody = getById("tabelaMargem");
  tbody.innerHTML = "";

  lista.forEach((item) => {
    const titulo = `${item.municipio} teve uma das menores margens de vitória municipal: ${formatPercent(item.margem_vitoria_pct)}. Isso pode indicar ambiente político competitivo.`;

    tbody.innerHTML += `
      <tr>
        <td title="${escapeHtml(titulo)}"><strong>${escapeHtml(item.municipio || "-")}</strong></td>
        <td>${escapeHtml(item.prefeito || "-")}</td>
        <td>${formatPercent(item.margem_vitoria_pct)}</td>
      </tr>
    `;
  });
}

function renderizarScore(dados) {
  const lista = [...dados]
    .sort((a, b) => Number(b.score_articulacao || 0) - Number(a.score_articulacao || 0))
    .slice(0, 10);

  const tbody = getById("tabelaScore");
  tbody.innerHTML = "";

  lista.forEach((item) => {
    const titulo = `${item.municipio} possui score de articulação ${formatNumber(item.score_articulacao)}. Grupo político: ${item.grupo_politico || item.grupo_politico_classificacao || "-"}.`;

    tbody.innerHTML += `
      <tr>
        <td title="${escapeHtml(titulo)}"><strong>${escapeHtml(item.municipio || "-")}</strong></td>
        <td>${escapeHtml(item.grupo_politico || item.grupo_politico_classificacao || "-")}</td>
        <td>${formatNumber(item.score_articulacao)}</td>
      </tr>
    `;
  });
}

document.addEventListener("DOMContentLoaded", carregarDados);