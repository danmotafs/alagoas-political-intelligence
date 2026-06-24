const DATA_URL = "../data/dashboard/base_dashboard_v2.json";

let dashboardData = null;
let municipios = [];

const formatNumber = (value) => {
  const numero = Number(value || 0);

  if (!Number.isFinite(numero)) {
    return "0";
  }

  return numero.toLocaleString("pt-BR");
};

const formatPercent = (value) => {
  const numero = Number(value || 0);

  if (!Number.isFinite(numero)) {
    return "0%";
  }

  return `${numero.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 2,
  })}%`;
};

const getById = (id) => document.getElementById(id);

function setText(id, value) {
  const el = getById(id);
  if (!el) return;
  el.textContent = value;
}

function safeAddEvent(id, event, handler) {
  const el = getById(id);
  if (!el) return;
  el.addEventListener(event, handler);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getArrayByPriority(possibilidades) {
  for (const item of possibilidades) {
    if (Array.isArray(item) && item.length > 0) {
      return item;
    }
  }

  return [];
}

function obterMunicipiosBase() {
  return getArrayByPriority([
    dashboardData?.municipios,
    dashboardData?.dados,
    dashboardData?.base,
    dashboardData?.rankings?.ranking_estrategico_top20,
    dashboardData?.rankings?.maior_eleitorado_top10,
  ]);
}

function obterBaseLiderancasMunicipais() {
  return getArrayByPriority([
    dashboardData?.forca_politica_vereadores_corrigida,
    dashboardData?.contribuicao_vereadores_corrigida?.municipios,
    dashboardData?.meta_eleitoral_davi_2026?.ranking_municipios,
    dashboardData?.meta_eleitoral_davi_2026?.ranking_municipios_corrigidos,
    dashboardData?.vereadores_municipais,
    dashboardData?.rankings?.forca_politica_vereadores,
  ]);
}

function obterRankingVereadoresCorrigido() {
  return getArrayByPriority([
    dashboardData?.ranking_contribuicao_davi_corrigido,
    dashboardData?.contribuicao_vereadores_corrigida?.vereadores_top_500,
    dashboardData?.meta_eleitoral_davi_2026?.ranking_vereadores,
    dashboardData?.meta_eleitoral_davi_2026?.top_vereadores,
  ]);
}

function obterResumoMeta() {
  return (
    dashboardData?.meta_eleitoral_davi_2026?.resumo_geral ||
    dashboardData?.contribuicao_vereadores_corrigida?.resumo_geral ||
    dashboardData?.indicadores ||
    {}
  );
}

async function carregarDados() {
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });

    if (!response.ok) {
      throw new Error(`Erro ao carregar JSON: ${response.status}`);
    }

    dashboardData = await response.json();

    municipios = obterMunicipiosBase();

    if (!Array.isArray(municipios)) {
      municipios = [];
    }

    preencherCards();
    preencherFiltros();
    renderizarDashboard(municipios);
    configurarEventos();

    console.log("Dashboard carregado com sucesso.", {
      municipios: municipios.length,
      indicadores: dashboardData?.indicadores,
      meta: obterResumoMeta(),
    });
  } catch (error) {
    console.error("Erro ao carregar/processar dashboard:", error);

    const mensagemErro =
      error && error.stack
        ? error.stack
        : error && error.message
          ? error.message
          : String(error);

    alert(`ERRO REAL NO DASHBOARD:

${mensagemErro}

Copie esta mensagem e envie aqui.`);
  }
}

function preencherCards() {
  const indicadores = dashboardData?.indicadores || {};
  const resumoMeta = obterResumoMeta();

  setText(
    "cardMunicipios",
    formatNumber(indicadores.total_municipios || resumoMeta.municipios_mapeados)
  );

  setText("cardEleitorado", formatNumber(indicadores.eleitorado_total));
  setText("cardPopulacao", formatNumber(indicadores.populacao_total));
  setText("cardVisitados", formatNumber(indicadores.municipios_visitados));
  setText("cardCobertura", formatPercent(indicadores.cobertura_territorial_pct));
  setText("cardPrefeitos", formatNumber(indicadores.prefeitos_mapeados));

  setText(
    "cardVereadores",
    formatNumber(indicadores.vereadores_mapeados || resumoMeta.vereadores_mapeados)
  );

  const potencialConservador =
    indicadores.potencial_bruto_10pct_total ||
    resumoMeta.potencial_bruto_10pct ||
    indicadores.potencial_transferencia_conservador_total;

  setText("cardPotencialConservador", formatNumber(potencialConservador));

  setText("cardMetaDavi", formatNumber(resumoMeta.meta_votos_davi_2026));
  setText("cardPotencial10", formatNumber(resumoMeta.potencial_bruto_10pct));
  setText("cardPotencial15", formatNumber(resumoMeta.potencial_bruto_15pct));
  setText("cardPotencial20", formatNumber(resumoMeta.potencial_bruto_20pct));
  setText("cardQtdVereadores10", formatNumber(resumoMeta.qtd_vereadores_para_meta_10pct));
  setText("cardQtdVereadores15", formatNumber(resumoMeta.qtd_vereadores_para_meta_15pct));
  setText("cardQtdVereadores20", formatNumber(resumoMeta.qtd_vereadores_para_meta_20pct));
}

function preencherFiltros() {
  preencherSelect("filtroMunicipio", dashboardData?.dimensoes?.municipios || []);
  preencherSelect("filtroPartido", dashboardData?.dimensoes?.partidos || []);
  preencherSelect("filtroPrioridade", dashboardData?.dimensoes?.prioridades || []);
}

function preencherSelect(id, valores) {
  const select = getById(id);

  if (!select) return;

  const valorAtual = select.value;

  [...select.querySelectorAll("option")]
    .filter((option) => option.value !== "")
    .forEach((option) => option.remove());

  valores
    .filter((valor) => valor !== null && valor !== undefined && String(valor).trim() !== "")
    .sort((a, b) => String(a).localeCompare(String(b), "pt-BR"))
    .forEach((valor) => {
      const option = document.createElement("option");
      option.value = valor;
      option.textContent = valor;
      select.appendChild(option);
    });

  select.value = valorAtual;
}

function configurarEventos() {
  [
    "filtroMunicipio",
    "filtroPartido",
    "filtroVisitado",
    "filtroPrioridade",
    "filtroEleitorado",
  ].forEach((id) => {
    safeAddEvent(id, "change", aplicarFiltros);
  });

  safeAddEvent("btnLimparFiltros", "click", limparFiltros);
}

function aplicarFiltros() {
  const municipioSelecionado = getById("filtroMunicipio")?.value || "";
  const partidoSelecionado = getById("filtroPartido")?.value || "";
  const visitadoSelecionado = getById("filtroVisitado")?.value || "";
  const prioridadeSelecionada = getById("filtroPrioridade")?.value || "";
  const faixaEleitorado = getById("filtroEleitorado")?.value || "";

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
    dadosFiltrados = dadosFiltrados.filter((item) => {
      const prioridade = item.prioridade_final || item.prioridade_politica || "";
      return prioridade === prioridadeSelecionada;
    });
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
  const campos = [
    "filtroMunicipio",
    "filtroPartido",
    "filtroVisitado",
    "filtroPrioridade",
    "filtroEleitorado",
  ];

  campos.forEach((id) => {
    const el = getById(id);
    if (el) el.value = "";
  });

  renderizarDashboard(municipios);
}

function renderizarDashboard(dados) {
  const dadosSeguros = Array.isArray(dados) ? dados : [];

  renderizarRanking(dadosSeguros);
  renderizarNaoVisitados(dadosSeguros);
  renderizarLiderancasMunicipais();
  renderizarRankingVereadoresCorrigido();
  renderizarRedePoder(dadosSeguros);
  renderizarMargens(dadosSeguros);
  renderizarScore(dadosSeguros);
  renderizarMetaEleitoral();

  setText("contadorRegistros", `${formatNumber(dadosSeguros.length)} registros`);
}

function renderizarRanking(dados) {
  const tbody = getById("tabelaRanking");
  if (!tbody) return;

  const ranking = [...dados]
    .sort((a, b) => Number(b.indice_estrategico_pct || 0) - Number(a.indice_estrategico_pct || 0))
    .slice(0, 20);

  tbody.innerHTML = "";

  ranking.forEach((item, index) => {
    const titulo = `Município de ${item.municipio}. Eleitorado: ${formatNumber(
      item.eleitorado_2024
    )}. Índice estratégico: ${formatPercent(item.indice_estrategico_pct)}.`;

    tbody.innerHTML += `
      <tr>
        <td>${item.rank || index + 1}</td>
        <td title="${escapeHtml(titulo)}"><strong>${escapeHtml(item.municipio || "-")}</strong></td>
        <td>${formatNumber(item.eleitorado_2024)}</td>
        <td>${formatPercent(item.indice_estrategico_pct)}</td>
      </tr>
    `;
  });
}

function renderizarNaoVisitados(dados) {
  const tbody = getById("tabelaNaoVisitados");
  if (!tbody) return;

  const lista = [...dados]
    .filter((item) => item.visitado_pre_campanha === false)
    .sort((a, b) => Number(b.indice_estrategico_pct || 0) - Number(a.indice_estrategico_pct || 0))
    .slice(0, 20);

  tbody.innerHTML = "";

  lista.forEach((item) => {
    const titulo = `${item.municipio} ainda não aparece como visitado na base. Possui eleitorado de ${formatNumber(
      item.eleitorado_2024
    )} e índice estratégico de ${formatPercent(item.indice_estrategico_pct)}.`;

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
  const lista = obterBaseLiderancasMunicipais();
  const tbody = getById("tabelaLiderancasMunicipais");

  if (!tbody) return;

  tbody.innerHTML = "";

  lista
    .sort((a, b) => {
      const rankA = Number(
        a.rank_municipal ||
          a.ranking_municipal_contribuicao ||
          a.ranking_municipal_potencial ||
          9999
      );

      const rankB = Number(
        b.rank_municipal ||
          b.ranking_municipal_contribuicao ||
          b.ranking_municipal_potencial ||
          9999
      );

      return rankA - rankB;
    })
    .slice(0, 50)
    .forEach((item, index) => {
      const rank =
        item.rank_municipal ||
        item.ranking_municipal_contribuicao ||
        item.ranking_municipal_potencial ||
        index + 1;

      const municipio = item.municipio || "-";

      const vereadores =
        item.vereadores_eleitos ||
        item.vereadores ||
        item.vereadores_mapeados ||
        0;

      const totalVotos =
        item.total_votos_vereadores ||
        item.total_de_votos ||
        item.votos_vereadores_2024 ||
        0;

      const principalLideranca =
        item.principal_lideranca ||
        item.principal_lideranca_nome_urna ||
        "-";

      const partido =
        item.principal_lideranca_partido ||
        item.partido ||
        "-";

      const votosLider = item.principal_lideranca_votos || 0;

      const potencialCorrigido =
        item.principal_lideranca_contribuicao_20pct ||
        item.maior_potencial_individual_20pct ||
        item.potencial_corrigido ||
        item.contribuicao_davi_20pct ||
        item.potencial_transferencia_conservador ||
        0;

      const potencialMunicipal20 =
        item.contribuicao_davi_20pct ||
        item.votos_potenciais_davi_20pct ||
        item.potencial_corrigido ||
        item.potencial_transferencia_alto ||
        0;

      const percentualMeta20 =
        item.percentual_meta_davi_20pct ||
        item.principal_lideranca_percentual_meta_20pct ||
        0;

      const potencialPolitico =
        item.potencial_politico_municipio ||
        item.potencial_label ||
        "Teto 20%";

      const tooltipLideranca =
        item.principal_lideranca_tooltip ||
        `${principalLideranca} foi a principal liderança municipal em votos em ${municipio}, ` +
          `com ${formatNumber(votosLider)} votos. Pela metodologia corrigida, o teto operacional de contribuição individual é de ` +
          `${formatNumber(potencialCorrigido)} votos, equivalente a ${formatPercent(percentualMeta20)} da meta de 60.000 votos.`;

      const tooltipMunicipio =
        item.tooltip_potencial_corrigido ||
        `${municipio} possui ${formatNumber(vereadores)} vereadores mapeados, com ${formatNumber(
          totalVotos
        )} votos nominais somados. Potencial municipal corrigido no teto de 20%: ${formatNumber(
          potencialMunicipal20
        )} votos.`;

      tbody.innerHTML += `
        <tr>
          <td>${rank}</td>
          <td title="${escapeHtml(tooltipMunicipio)}"><strong>${escapeHtml(municipio)}</strong></td>
          <td>${formatNumber(vereadores)}</td>
          <td>${formatNumber(totalVotos)}</td>
          <td title="${escapeHtml(tooltipLideranca)}"><strong>${escapeHtml(principalLideranca)}</strong></td>
          <td>${escapeHtml(partido)}</td>
          <td>${formatNumber(votosLider)}</td>
          <td><span class="badge prioridade" title="${escapeHtml(tooltipMunicipio)}">${escapeHtml(potencialPolitico)}</span></td>
        </tr>
      `;
    });
}

function renderizarRankingVereadoresCorrigido() {
  const tbody = getById("tabelaRankingContribuicaoDavi");
  if (!tbody) return;

  const lista = obterRankingVereadoresCorrigido();

  tbody.innerHTML = "";

  lista
    .sort((a, b) => Number(a.ranking_contribuicao_davi || 9999) - Number(b.ranking_contribuicao_davi || 9999))
    .slice(0, 100)
    .forEach((item, index) => {
      const tooltip =
        item.tooltip_contribuicao_corrigida ||
        `${item.vereador || item.nome_urna || "Vereador"} recebeu ${formatNumber(
          item.votos
        )} votos em 2024. Contribuição corrigida: ${formatNumber(
          item.contribuicao_davi_10pct
        )} votos em 10%, ${formatNumber(item.contribuicao_davi_15pct)} em 15% e ${formatNumber(
          item.contribuicao_davi_20pct
        )} em 20%.`;

      tbody.innerHTML += `
        <tr>
          <td>${item.ranking_contribuicao_davi || index + 1}</td>
          <td>${escapeHtml(item.municipio || "-")}</td>
          <td title="${escapeHtml(tooltip)}"><strong>${escapeHtml(item.nome_urna || item.vereador || "-")}</strong></td>
          <td>${escapeHtml(item.partido || "-")}</td>
          <td>${formatNumber(item.votos)}</td>
          <td>${formatNumber(item.contribuicao_davi_10pct)}</td>
          <td>${formatNumber(item.contribuicao_davi_15pct)}</td>
          <td>${formatNumber(item.contribuicao_davi_20pct)}</td>
          <td>${formatPercent(item.percentual_meta_davi_20pct)}</td>
        </tr>
      `;
    });
}

function renderizarRedePoder(dados) {
  const tbody = getById("tabelaRedePoder");
  if (!tbody) return;

  const lista = [...dados].sort((a, b) => Number(a.rank || 999) - Number(b.rank || 999));

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
  const tbody = getById("tabelaMargem");
  if (!tbody) return;

  const lista = [...dados]
    .filter((item) => Number(item.margem_vitoria_pct || 0) > 0)
    .sort((a, b) => Number(a.margem_vitoria_pct || 0) - Number(b.margem_vitoria_pct || 0))
    .slice(0, 10);

  tbody.innerHTML = "";

  lista.forEach((item) => {
    const titulo = `${item.municipio} teve uma das menores margens de vitória municipal: ${formatPercent(
      item.margem_vitoria_pct
    )}. Isso pode indicar ambiente político competitivo.`;

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
  const tbody = getById("tabelaScore");
  if (!tbody) return;

  const lista = [...dados]
    .sort((a, b) => Number(b.score_articulacao || 0) - Number(a.score_articulacao || 0))
    .slice(0, 10);

  tbody.innerHTML = "";

  lista.forEach((item) => {
    const grupo =
      item.grupo_politico_padronizado ||
      item.grupo_politico_classificacao ||
      item.grupo_politico ||
      "SEM GRUPO";

    const titulo =
      `${item.municipio} possui score de articulação ${formatNumber(item.score_articulacao)}. ` +
      `Grupo político: ${grupo}. ` +
      `O score deve ser interpretado como métrica operacional de priorização, não como previsão eleitoral.`;

    tbody.innerHTML += `
      <tr>
        <td title="${escapeHtml(titulo)}"><strong>${escapeHtml(item.municipio || "-")}</strong></td>
        <td>${escapeHtml(grupo)}</td>
        <td>${formatNumber(item.score_articulacao)}</td>
      </tr>
    `;
  });
}

function renderizarMetaEleitoral() {
  const resumo = obterResumoMeta();

  const tbody = getById("tabelaMetaEleitoral");
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td>Meta operacional Davi Maia 2026</td>
      <td>${formatNumber(resumo.meta_votos_davi_2026)}</td>
      <td>Quantidade de votos definida como objetivo estratégico da pré-campanha.</td>
    </tr>
    <tr>
      <td>Potencial bruto 10%</td>
      <td>${formatNumber(resumo.potencial_bruto_10pct)}</td>
      <td>Cenário conservador: conversão de 10% dos votos dos vereadores mapeados.</td>
    </tr>
    <tr>
      <td>Potencial bruto 15%</td>
      <td>${formatNumber(resumo.potencial_bruto_15pct)}</td>
      <td>Cenário intermediário: conversão de 15% dos votos dos vereadores mapeados.</td>
    </tr>
    <tr>
      <td>Potencial bruto 20%</td>
      <td>${formatNumber(resumo.potencial_bruto_20pct)}</td>
      <td>Teto operacional: conversão máxima de 20% dos votos dos vereadores mapeados.</td>
    </tr>
    <tr>
      <td>Vereadores necessários no cenário 10%</td>
      <td>${formatNumber(resumo.qtd_vereadores_para_meta_10pct)}</td>
      <td>Quantidade teórica de vereadores, ordenados por maior contribuição potencial, para atingir 60 mil votos.</td>
    </tr>
    <tr>
      <td>Vereadores necessários no cenário 15%</td>
      <td>${formatNumber(resumo.qtd_vereadores_para_meta_15pct)}</td>
      <td>Quantidade teórica de vereadores no cenário intermediário.</td>
    </tr>
    <tr>
      <td>Vereadores necessários no cenário 20%</td>
      <td>${formatNumber(resumo.qtd_vereadores_para_meta_20pct)}</td>
      <td>Quantidade teórica de vereadores no teto operacional.</td>
    </tr>
  `;
}

document.addEventListener("DOMContentLoaded", carregarDados);