"use strict";

function atualizarFiltros() {
  const ativos = new Set(filtrosAplicaveis());
  const chips = Object.entries(state.filtros)
    .filter(([campo]) => ativos.has(campo))
    .flatMap(([campo, valores]) =>
      valores.map((valor) => ({
        campo,
        valor,
        label: `${ROTULOS[campo]}: ${labelFiltro(campo, valor)}`
      }))
    );
  $id("filterChips").classList.toggle("has-filters", chips.length > 0);
  $id("filterChips").innerHTML = chips
    .map(
      (x) =>
        `<button class="chip" data-remove-dim="${esc(x.campo)}" data-remove-value="${esc(x.valor)}" title="Remover filtro">${esc(x.label)} ×</button><span class="print-chip hidden">${esc(x.label)}</span>`
    )
    .join("");
  $id("filterDrawer").classList.toggle("hidden", !state.filtrosAbertos);
  $id("toggleFilters").setAttribute("aria-expanded", String(state.filtrosAbertos));
}
function opcoesPorCampo(campo) {
  if (campo === "ies") return [...IES.values()].map((x) => [String(x.id), x.nome]);
  if (campo === "curso")
    return [...CURSOS.values()].map((x) => [String(x.id), `${x.nome} · ${x.grau}`]);
  if (campo === "cidade")
    return [...LOCAIS.values()]
      .filter((x) => x.lat != null)
      .map((x) => [String(x.id), `${x.cidade} / ${x.uf}`]);
  if (campo === "uf") return [...new Set([...LOCAIS.values()].map((x) => x.uf))].map((x) => [x, x]);
  if (campo === "tipo")
    return [...new Set([...IES.values()].map((x) => x.tipo))].map((x) => [x, x]);
  if (campo === "grau")
    return [...new Set([...CURSOS.values()].map((x) => x.grau))].map((x) => [x, x]);
  if (campo === "turno")
    return [
      ["DIURNO", "Diurno"],
      ["NOTURNO", "Noturno"]
    ];
  if (campo === "oferta")
    return [
      ["Sim", "Portfólio Escolhido"],
      ["Não", "Outras ofertas"]
    ];
  if (campo === "conceito") return [1, 2, 3, 4, 5].map((n) => [String(n), `Nota ${n}`]);
  if (campo === "rede")
    return [...new Set(DADOS.dados.basica.map((row) => row[2]))].map((x) => [x, x]);
  return [];
}

const CACHE_OPCOES_FILTROS = new Map();
const LIMITE_OPCOES_FILTRO = 60;

function normalizarBuscaFiltro(valor) {
  return String(valor ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .trim();
}

function opcoesOrdenadasFiltro(campo) {
  if (!CACHE_OPCOES_FILTROS.has(campo)) {
    const opcoes = opcoesPorCampo(campo)
      .map(([valor, nome]) => ({
        valor: String(valor),
        nome: String(nome),
        busca: normalizarBuscaFiltro(`${nome} ${valor}`)
      }))
      .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));

    CACHE_OPCOES_FILTROS.set(campo, opcoes);
  }

  return CACHE_OPCOES_FILTROS.get(campo);
}

function atualizarOpcoesFiltro(campo) {
  const destino = $id("advancedFilters").querySelector(`[data-filter-options="${campo}"]`);

  if (!destino) return;

  const busca = normalizarBuscaFiltro(state.buscaFiltros[campo]);
  const ativos = new Set((state.filtros[campo] || []).map(String));

  const selecionados = [];
  const restantes = [];
  let encontrados = 0;

  for (const item of opcoesOrdenadasFiltro(campo)) {
    if (!item.busca.includes(busca)) continue;

    encontrados += 1;

    (ativos.has(item.valor) ? selecionados : restantes).push(item);
  }

  const exibidos = selecionados.concat(restantes).slice(0, LIMITE_OPCOES_FILTRO);

  destino.innerHTML =
    exibidos
      .map(
        (item) => `
          <label class="filter-option" title="${esc(item.nome)}">
            <input
              type="checkbox"
              data-option-filter="${esc(campo)}"
              value="${esc(item.valor)}"
              ${ativos.has(item.valor) ? "checked" : ""}
            />
            <span class="filter-option-label">${esc(item.nome)}</span>
          </label>
        `
      )
      .join("") +
    (encontrados > LIMITE_OPCOES_FILTRO
      ? `<div class="filter-option-hint">
          Exibindo ${LIMITE_OPCOES_FILTRO} de ${encontrados}.
          Refine a pesquisa.
        </div>`
      : encontrados === 0
        ? '<div class="filter-option-hint">Nenhum resultado encontrado.</div>'
        : "");
}

function construirFiltrosAvancados() {
  const campos = filtrosAplicaveis();

  if (!campos.includes(state.filtroAberto)) {
    state.filtroAberto = null;
  }

  $id("advancedFilters").innerHTML = campos
    .map((campo) => {
      const quantidade = state.filtros[campo]?.length || 0;

      const texto =
        quantidade === 0 ? "Todos" : `${quantidade} selecionado${quantidade > 1 ? "s" : ""}`;

      return `
        <div class="filter-field">
          <span>${esc(ROTULOS[campo])}</span>

          <details
            class="filter-select"
            data-filter-menu="${esc(campo)}"
            ${state.filtroAberto === campo ? "open" : ""}
          >
            <summary>
              <span class="filter-value">${esc(texto)}</span>
              <span class="filter-arrow">⌄</span>
            </summary>

            <div class="filter-popover">
              <input
                class="filter-search"
                type="search"
                data-search-filter="${esc(campo)}"
                aria-label="Pesquisar ${esc(ROTULOS[campo])}"
                placeholder="Pesquisar..."
                value="${esc(state.buscaFiltros[campo] || "")}"
                autocomplete="off"
              />

              <div
                class="filter-options"
                data-filter-options="${esc(campo)}"
              ></div>
            </div>
          </details>
        </div>
      `;
    })
    .join("");

  if (state.filtroAberto) {
    atualizarOpcoesFiltro(state.filtroAberto);
  }
}

function atualizarSeletorAno() {
  const f = familiaAtual();
  const anos = DADOS.anos[f] || [];
  $id("yearSelect").innerHTML = anos
    .map((a) => `<option value="${a}" ${a === state.anos[f] ? "selected" : ""}>${a}</option>`)
    .join("");
}

function atualizarHeader() {
  const f = familiaAtual();
  let kpis = [];
  if (f === "mercado") {
    const rows = filtrarMercado();
    kpis = [
      ["Ingressantes", numero(somar(rows, 5)), "Censo presencial · selecionado"],
      ["Concorrentes", numero(unicos(rows, 1)), "IES distintas"],
      ["Cursos", numero(unicos(rows, 2)), "Cursos analíticos"],
      ["Vagas", numero(somar(rows, 6)), "Vagas presenciais"],
      ["Matriculados", numero(somar(rows, 8)), "Indicador do Censo"]
    ];
    $id("mainContext").textContent =
      `${numero(rows.length)} linhas agregadas · Censo ${state.anos.mercado}`;
  } else if (f === "enade") {
    const r = dadosEnadeComVolume();
    const evals = filtrarEnade();
    kpis = [
      [
        "Ingressantes (Censo)",
        numero(r.reduce((s, x) => s + x.ingressantes, 0)),
        "Fallback por IES"
      ],
      ["IES avaliadas", numero(r.length), "Com nota e ingressantes"],
      ["Avaliações", numero(evals.length), "Notas válidas 1–5"],
      ["Participantes", numero(evals.reduce((s, x) => s + (x[6] || 0), 0)), "Enade no ano"],
      ["Ano Enade", String(state.anos.enade), "Censo pode ser anterior"]
    ];
    $id("mainContext").textContent = `Enade ${state.anos.enade} · Censo retroativo por IES`;
  } else {
    const r = filtrarBasica();
    kpis = [
      ["Ensino Médio", numero(somar(r, 8)), "Matrículas"],
      ["Educação Profissional", numero(somar(r, 9)), "Total EPT"],
      ["Profissional Técnica", numero(somar(r, 10)), "Subconjunto EPT"],
      ["Escolas", numero(somar(r, 3)), "Contagem por rede"],
      ["Municípios", numero(unicos(r, 1)), "Censo Escolar"]
    ];
    $id("mainContext").textContent = `Censo Escolar ${state.anos.basica}`;
  }
  $id("kpis").innerHTML = kpis.map((x) => DashboardIndicadores.kpi(...x)).join("");
  for (const btn of document.querySelectorAll("[data-metric]")) {
    btn.classList.toggle("active", btn.dataset.metric === state.metrica);
    btn.setAttribute("aria-pressed", String(btn.dataset.metric === state.metrica));
  }
  for (const btn of document.querySelectorAll("[data-tab]")) {
    const ativo = btn.dataset.tab === state.aba;
    btn.classList.toggle("active", ativo);
    btn.setAttribute("aria-selected", String(ativo));
  }
  for (const pg of document.querySelectorAll(".page"))
    pg.classList.toggle("active", pg.dataset.page === state.aba);
  atualizarSeletorAno();
  atualizarFiltros();
}
const RENDER_ABAS = {
  geral: renderGeral,
  mapa: renderMapa,
  evolucao_ies: renderEvolucaoIES,
  evolucao_curso: renderEvolucaoCurso,
  ranking_ies: renderRankingIES,
  ranking_curso: renderRankingCurso,
  enade_mapa: renderEnadeMapa,
  enade_ranking: renderEnadeRanking,
  basica: renderBasica
};
function renderAll() {
  atualizarHeader();
  const render = RENDER_ABAS[state.aba];
  if (!render) throw Error("Aba sem renderizador: " + state.aba);
  render();
  if (state.filtrosAbertos) construirFiltrosAvancados();
}
function gerarTodasAbas() {
  const anterior = state.aba;
  for (const aba of ABAS) {
    state.aba = aba;
    RENDER_ABAS[aba]();
  }
  state.aba = anterior;
  atualizarHeader();
}
function exportarGrafico(id) {
  const svg = $id("svg-" + id);
  if (!svg) {
    DashboardExportacao.notificar($id("toast"), "Gráfico não encontrado para exportação.");
    return;
  }
  DashboardExportacao.svgParaPNG(svg, {
    nome: `educacional_${state.anos[familiaAtual()]}_${DashboardFormatacao.idSeguro(id)}.png`,
    fundo: id.startsWith("map-") ? "#f0f5f7" : "#ffffff"
  }).catch(() => DashboardExportacao.notificar($id("toast"), "Não foi possível exportar o PNG."));
}
function inicializarListeners() {
  $id("tabs").addEventListener("click", (e) => {
    const botao = e.target.closest("[data-tab]");
    if (!botao) return;
    if (!ABAS.includes(botao.dataset.tab)) return;
    state.aba = botao.dataset.tab;
    renderAll();
    window.scrollTo({ top: 0, behavior: "instant" });
  });
  $id("yearSelect").addEventListener("change", (e) => {
    const ano = Number(e.target.value),
      familia = familiaAtual();
    if (!DADOS.anos[familia].includes(ano)) return;
    state.anos[familia] = ano;
    renderAll();
  });
  $id("metricButtons").addEventListener("click", (e) => {
    const botao = e.target.closest("[data-metric]");
    if (!botao) return;
    state.metrica = botao.dataset.metric;
    renderAll();
  });
  $id("toggleFilters").addEventListener("click", () => {
    state.filtrosAbertos = !state.filtrosAbertos;
    renderAll();
  });
  $id("resetFilters").addEventListener("click", limparFiltros);

  const filtrosAvancados = $id("advancedFilters");

  // Abrir ou fechar a lista de opções.
  filtrosAvancados.addEventListener("click", (e) => {
    const resumo = e.target.closest(".filter-select > summary");
    if (!resumo) return;

    e.preventDefault();

    const menu = resumo.parentElement;
    const estavaAberto = menu.open;

    filtrosAvancados.querySelectorAll(".filter-select[open]").forEach((elemento) => {
      elemento.open = false;
    });

    menu.open = !estavaAberto;
    state.filtroAberto = menu.open ? menu.dataset.filterMenu : null;

    if (menu.open) {
      atualizarOpcoesFiltro(state.filtroAberto);
      menu.querySelector(".filter-search")?.focus();
    }
  });

  // Pesquisar sem reconstruir o dashboard.
  filtrosAvancados.addEventListener("input", (e) => {
    const pesquisa = e.target.closest("[data-search-filter]");
    if (!pesquisa) return;

    const campo = pesquisa.dataset.searchFilter;

    state.buscaFiltros[campo] = pesquisa.value;
    atualizarOpcoesFiltro(campo);
  });

  // Selecionar ou remover opções.
  filtrosAvancados.addEventListener("change", (e) => {
    const checkbox = e.target.closest("[data-option-filter]");
    if (!checkbox) return;

    const campo = checkbox.dataset.optionFilter;

    alternarFiltro(campo, checkbox.value);

    $id("advancedFilters").querySelector(`[data-search-filter="${campo}"]`)?.focus();
  });

  $id("filterChips").addEventListener("click", (e) => {
    const botao = e.target.closest("[data-remove-dim]");
    if (botao) alternarFiltro(botao.dataset.removeDim, botao.dataset.removeValue);
  });
  $id("pages").addEventListener("click", (e) => {
    if (suprimirClickMapa) return;
    const filter = e.target.closest("[data-filter-dim]");
    if (filter) {
      alternarFiltro(filter.dataset.filterDim, filter.dataset.filterValue);
      return;
    }
    const png = e.target.closest("[data-export-svg]");
    if (png) {
      exportarGrafico(png.dataset.exportSvg);
      return;
    }
    const expand = e.target.closest("[data-expand]");
    if (expand) {
      const id = expand.dataset.expand;
      state.expandido[id] = !state.expandido[id];
      renderAll();
      return;
    }
    const modo = e.target.closest("[data-map-mode]");
    if (modo) {
      trocarAreaMapa(modo.dataset.mapMode);
      return;
    }
    const zoom = e.target.closest("[data-map-zoom]");
    if (zoom) {
      if (zoom.dataset.mapZoom === "reset") {
        state.mapaCaixa = areaBaseMapa();
        atualizarAreasMapa();
      } else aproximarMapa(zoom.dataset.mapZoom === "in" ? 0.8 : 1.25);
    }
  });
  $id("pages").addEventListener("keydown", (e) => {
    const search = e.target.closest("[data-search-id]");
    if (search && e.key === "Enter") {
      state.busca[search.dataset.searchId] = search.value.trim();
      renderAll();
      return;
    }
    const filtro = e.target.closest("[data-filter-dim]");
    if (filtro && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      alternarFiltro(filtro.dataset.filterDim, filtro.dataset.filterValue);
    }
  });
  $id("pages").addEventListener("pointerdown", onMercadoPointerDown);
  document.addEventListener("pointermove", onMercadoPointerMove);
  document.addEventListener("pointerup", onMercadoPointerUp);
  $id("pages").addEventListener(
    "wheel",
    (e) => {
      if (!e.target.closest(".map-svg")) return;
      e.preventDefault();
      aproximarMapa(e.deltaY > 0 ? 1.12 : 0.89);
    },
    { passive: false }
  );
  $id("exportHTML").addEventListener("click", () => DashboardExportacao.htmlAtual("educacao.html"));
  $id("printPage").addEventListener("click", () => DashboardExportacao.imprimir(false));
  $id("printAll").addEventListener("click", () => {
    gerarTodasAbas();
    DashboardExportacao.imprimir(true);
  });
  window.addEventListener("afterprint", () => document.body.classList.remove("print-all"));
}
function bootMercado() {
  const quando = new Date(DADOS.meta.gerado_em_utc).toLocaleString("pt-BR", {
    timeZone: "America/Sao_Paulo"
  });
  $id("geradoEm").textContent = "Dados gerados em " + quando;
  $id("footerGenerated").textContent = "Atualizado em " + quando;
  state.mapaCaixa = areaBaseMapa();
  inicializarListeners();
  renderAll();
  window.__dashboardDiagnostics = () => ({
    aba: state.aba,
    ano: anoAtual(),
    filtros: Object.keys(state.filtros).length,
    graficos: document.querySelectorAll(".page.active svg").length,
    familia: familiaAtual(),
    versao: DADOS.schema_version
  });
}
try {
  bootMercado();
} catch (erro) {
  document.querySelector("main").innerHTML =
    "<section class='notice'><strong>Falha ao inicializar o relatório.</strong> Confira a integridade do JSON e gere novamente o HTML.</section>";
  console.error(erro);
}
