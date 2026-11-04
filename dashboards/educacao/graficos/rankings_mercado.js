"use strict";

// Adaptador do ranking generico: dimensoes/denominadores sao resolvidos pelo Mercado.
// O registro compartilhado garante um tipo estavel por identificador,
// mesmo que os graficos sejam rerenderizados pelos filtros.
const REGISTRO_GRAFICOS_MERCADO = new RegistroGraficos({
  tipos: ["ranking", "barras", "linhas", "rosca"]
});
function validarRegistroGraficoMercado(id, tipo) {
  const anterior = REGISTRO_GRAFICOS_MERCADO.obter(id);
  if (anterior && anterior.tipo !== tipo) {
    throw Error(`Grafico ${id}: tipo anterior ${anterior.tipo}, novo ${tipo}`);
  }
  if (!anterior) REGISTRO_GRAFICOS_MERCADO.registrar({ id, tipo });
}

function valorGrupoMercado(row, dimensao) {
  if (dimensao === "ies") return row[1];
  if (dimensao === "curso") return row[2];
  if (dimensao === "cidade") return row[3];
  if (dimensao === "uf") return LOCAIS.get(row[3])?.uf;
  if (dimensao === "turno") return row[4] === 0 ? "DIURNO" : "NOTURNO";
  if (dimensao === "oferta") return row[10] === 1 ? "Sim" : "Não";
  if (dimensao === "tipo") return IES.get(row[1])?.tipo;
  if (dimensao === "grau") return CURSOS.get(row[2])?.grau;
  return "NÃO INFORMADO";
}
function rotuloGrupoMercado(dim, valor) {
  if (dim === "ies") return nomeIES(valor);
  if (dim === "curso") return nomeCurso(valor);
  if (dim === "cidade") return nomeCidade(valor);
  return String(valor || "Não informado");
}
function cardHeaderMercado(titulo, subtitulo, id, { expandir = false, buscar = false } = {}) {
  const a = state.expandido[id];
  return `<div class="card-top"><div><div class="overline">EDUCACIONAL</div><h3>${esc(titulo)}</h3></div>
    <div class="card-buttons">${expandir ? `<button class="btn-mini" data-expand="${esc(id)}">${a ? "Top 15" : "Ver todos"}</button>` : ""}
    <button class="btn-mini" data-export-svg="${esc(id)}">PNG ↓</button></div></div>
    <p class="card-sub">${esc(subtitulo)}</p>
    ${buscar ? `<input class="chart-search" data-search-id="${esc(id)}" value="${esc(state.busca[id] || "")}" placeholder="Buscar categoria (Enter)" aria-label="Buscar categoria"/>` : ""}`;
}
function mostrarRankingMercado(
  place,
  titulo,
  dim,
  { limite = 15, desc = "", rows = null, buscar = true } = {}
) {
  const id = `mercado-${place}`;
  validarRegistroGraficoMercado(id, "ranking");
  const linhas = rows || filtrarMercado({ ignorar: [dim] });
  const totais = new Map();
  for (const row of linhas) {
    const chave = valorGrupoMercado(row, dim);
    if (chave === undefined || chave === null) continue;
    totais.set(chave, (totais.get(chave) || 0) + (row[5] || 0));
  }
  let itens = ordenarGrupos(totais, (x) => rotuloGrupoMercado(dim, x)).filter(
    (v) => v.quantidade > 0
  );
  const busca = String(state.busca[id] || "").toLocaleLowerCase("pt-BR");
  if (busca)
    itens = itens.filter((v) =>
      rotuloGrupoMercado(dim, v.valor).toLocaleLowerCase("pt-BR").includes(busca)
    );
  const disponiveis = itens.length;
  if (!state.expandido[id] && limite && itens.length > limite) itens = itens.slice(0, limite);
  else if (state.expandido[id] && itens.length > 100) itens = itens.slice(0, 100);
  const universo = somar(linhas, 5);
  const series = [{ chave: "total", nome: "Ingressantes", cor: corTeal, denominador: universo }];
  const dados = itens.map((v) => ({
    valor: v.valor,
    rotulo: rotuloGrupoMercado(dim, v.valor),
    selecionado: filtroAtivo(dim, v.valor),
    valores: { total: v.quantidade }
  }));
  const el = $id(place);
  el.classList.add("panel", "chart-card");
  el.innerHTML =
    cardHeaderMercado(
      titulo,
      `${desc}${desc ? " · " : ""}${numero(universo)} ingressantes no universo · ${disponiveis} categorias${state.expandido[id] && disponiveis > 100 ? " · Top 100 (busque para localizar as demais)" : ""}`,
      id,
      { expandir: disponiveis > limite || state.expandido[id], buscar }
    ) +
    (dados.length
      ? `<div class="chart-legend"><span><i style="background:${corTeal}"></i>Ingresso · participação no conjunto filtrado</span></div>` +
        DashboardRanking.svg({
          id,
          titulo,
          dimensao: dim,
          categorias: dados,
          series,
          metrica: state.metrica
        })
      : `<div class="chart-empty">Sem dados para os filtros selecionados.</div>`);
}
function mostrarRankingBasica(place, titulo, dim, metrica, { limite = 15, desc = "" } = {}) {
  const rows = filtrarBasica({ ignorar: [dim] });
  const grupos = new Map();
  const chave = (r) => (dim === "cidade" ? r[1] : dim === "uf" ? LOCAIS.get(r[1])?.uf : r[2]);
  for (const row of rows) {
    const k = chave(row);
    if (k === undefined) continue;
    grupos.set(k, (grupos.get(k) || 0) + (row[metrica] || 0));
  }
  const entradas = ordenarGrupos(grupos, (x) =>
    dim === "cidade" ? nomeCidade(x) : String(x)
  ).filter((x) => x.quantidade > 0);
  const id = `basica-${place}`;
  validarRegistroGraficoMercado(id, "ranking");
  let selecionados = state.expandido[id] ? entradas.slice(0, 100) : entradas.slice(0, limite);
  const dados = selecionados.map((x) => ({
    valor: x.valor,
    rotulo: dim === "cidade" ? nomeCidade(x.valor) : String(x.valor),
    selecionado: filtroAtivo(dim, x.valor),
    valores: { total: x.quantidade }
  }));
  const el = $id(place);
  el.classList.add("panel", "chart-card");
  el.innerHTML =
    cardHeaderMercado(
      titulo,
      desc || `${numero(somar(rows, metrica))} matrículas · ${entradas.length} categorias`,
      id,
      { expandir: entradas.length > limite || state.expandido[id] }
    ) +
    (dados.length
      ? DashboardRanking.svg({
          id,
          titulo,
          dimensao: dim,
          categorias: dados,
          series: [
            { chave: "total", nome: "Matrículas", cor: corTeal, denominador: somar(rows, metrica) }
          ],
          metrica: state.metrica
        })
      : `<div class="chart-empty">Sem matrículas no contexto selecionado.</div>`);
}
function mostrarBarrasMercado(
  place,
  titulo,
  categorias,
  { id = place, empilhado = false, desc = "", cor = corTeal } = {}
) {
  validarRegistroGraficoMercado(id, "barras");
  const el = $id(place);
  el.classList.add("panel", "chart-card");
  el.innerHTML =
    cardHeaderMercado(titulo, desc, id) +
    (categorias.length
      ? DashboardBarras.svg({
          id,
          titulo,
          categorias,
          series: [{ campo: "valor", nome: "Valor", cor }],
          empilhado
        })
      : `<div class="chart-empty">Sem dados.</div>`);
}
function mostrarLinhaMercado(place, titulo, pontos, { id = place, desc = "", series = null } = {}) {
  validarRegistroGraficoMercado(id, "linhas");
  const el = $id(place);
  el.classList.add("panel", "chart-card");
  el.innerHTML =
    cardHeaderMercado(titulo, desc, id) +
    (pontos.length
      ? DashboardLinhas.svg({
          id,
          titulo,
          pontos,
          series: series || [{ campo: "valor", nome: "Ingressantes", cor: corTeal }]
        })
      : `<div class="chart-empty">Sem histórico no contexto selecionado.</div>`);
}
function definirEstatisticas(place, estatisticas) {
  DashboardIndicadores.grupo($id(place), estatisticas);
}

function mostrarRoscaMercado(
  place,
  titulo,
  segmentos,
  { id = place, desc = "", dimensao = "" } = {}
) {
  validarRegistroGraficoMercado(id, "rosca");
  const el = $id(place);
  el.classList.add("panel", "chart-card");
  const total = segmentos.reduce((soma, item) => soma + Math.max(0, Number(item.valor) || 0), 0);
  if (total <= 0) {
    el.innerHTML =
      cardHeaderMercado(titulo, desc, id) +
      '<div class="chart-empty">Sem dados para os filtros selecionados.</div>';
    return;
  }
  const svg = DashboardPizza.renderizar({
    id,
    titulo,
    largura: 380,
    altura: 260,
    tipo: "rosca",
    segmentos: segmentos.map((item) => ({ valor: item.valor, cor: item.cor }))
  });
  const legenda = segmentos
    .map((item) => {
      const selecionado = dimensao && filtroAtivo(dimensao, item.filtro ?? item.rotulo);
      const atributos = dimensao
        ? `data-filter-dim="${esc(dimensao)}" data-filter-value="${esc(item.filtro ?? item.rotulo)}"`
        : "";
      return `<button type="button" class="mercado-rosca-legenda-item ${selecionado ? "active" : ""}" ${atributos}
       aria-pressed="${Boolean(selecionado)}">
       <i class="legend-dot" style="background:${esc(item.cor || corTeal)}"></i>
       <span>${esc(item.rotulo)}</span>
       <strong>${numero(item.valor)} <small>(${percentual(item.valor, total)})</small></strong>
      </button>`;
    })
    .join("");
  el.innerHTML =
    cardHeaderMercado(titulo, desc, id) +
    `<div class="mercado-rosca">${svg}<div class="mercado-rosca-legenda">${legenda}</div></div>`;
}
