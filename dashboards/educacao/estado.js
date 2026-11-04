"use strict";

// Os dados ficam somente na memoria do documento; nao ha rede, CDNs nem APIs.
const DADOS = JSON.parse(document.getElementById("dashboard-data").textContent);
if (DADOS.schema_version !== "educacional-1.0") throw Error("Contrato Educacional desconhecido");
const IES = new Map(DADOS.dimensoes.ies.map((d) => [d.id, d]));
const CURSOS = new Map(DADOS.dimensoes.cursos.map((d) => [d.id, d]));
const LOCAIS = new Map(DADOS.dimensoes.localidades.map((d) => [d.id, d]));
const $id = (id) => document.getElementById(id);
const esc = DashboardFormatacao.esc;
const numero = DashboardFormatacao.numero;
const decimal = DashboardFormatacao.decimal;
const percentual = (numerador, denominador) =>
  DashboardFormatacao.percentual(numerador, denominador);
const corNav = "#133b58",
  corTeal = "#147e80",
  corAmber = "#d58b40";
const CONCEITO_CORES = { 1: "#c62828", 2: "#ef6c00", 3: "#fbc02d", 4: "#66bb6a", 5: "#2e7d32" };
const ABAS = [
  "geral",
  "mapa",
  "evolucao_ies",
  "evolucao_curso",
  "ranking_ies",
  "ranking_curso",
  "enade_mapa",
  "enade_ranking",
  "basica"
];
const FAMILIA_ABA = {
  geral: "mercado",
  mapa: "mercado",
  evolucao_ies: "mercado",
  evolucao_curso: "mercado",
  ranking_ies: "mercado",
  ranking_curso: "mercado",
  enade_mapa: "enade",
  enade_ranking: "enade",
  basica: "basica"
};
const ROTULOS = {
  ies: "Instituição",
  curso: "Curso",
  uf: "UF",
  cidade: "Município",
  tipo: "Tipo de IES",
  grau: "Grau",
  turno: "Turno",
  oferta: "Portfólio Escolhido",
  conceito: "Conceito Enade",
  rede: "Rede escolar"
};
const FILTROS_BASE = [
  "ies",
  "curso",
  "uf",
  "cidade",
  "tipo",
  "grau",
  "turno",
  "oferta"
];
const FILTROS_ENADE = [
  "ies",
  "curso",
  "uf",
  "cidade",
  "tipo",
  "grau",
  "oferta",
  "conceito"
];
const FILTROS_BASICA = ["uf", "cidade", "rede"];
const state = {
  aba: "geral",
  anos: { ...DADOS.anos_padrao },
  filtros: {},
  metrica: "quantidade",
  busca: {},
  expandido: {},
  filtrosAbertos: true,
  mapaModo: "sudeste",
  mapaCaixa: null,
  filtroAberto: null,
  buscaFiltros: {}
};

function familiaAtual() {
  return FAMILIA_ABA[state.aba];
}
function anoAtual() {
  return state.anos[familiaAtual()];
}
function filtroAtivo(campo, valor) {
  return DashboardFiltros.ativo(state.filtros, campo, String(valor));
}
function alternarFiltro(campo, valor) {
  if (!ROTULOS[campo]) throw Error("Filtro nao homologado: " + campo);
  state.filtros = DashboardFiltros.alternar(state.filtros, campo, String(valor));
  renderAll();
}
function limparFiltros() {
  state.filtros = {};
  state.busca = {};
  state.buscaFiltros = {};
  state.filtroAberto = null;
  state.expandido = {};
  renderAll();
}
function temFiltro(campo, valor, ignorar) {
  if (ignorar.includes(campo)) return true;
  const escolhidos = state.filtros[campo];
  return !escolhidos?.length || escolhidos.includes(String(valor));
}
function filtrosAplicaveis() {
  return familiaAtual() === "mercado"
    ? FILTROS_BASE
    : familiaAtual() === "enade"
      ? FILTROS_ENADE
      : FILTROS_BASICA;
}
function aceitaRegistro(row, familia, ignorar = []) {
  const local = LOCAIS.get(row[familia === "basica" ? 1 : 3]);
  if (!local) return false;
  if (
    !temFiltro("uf", local.uf, ignorar) ||
    !temFiltro("cidade", local.id, ignorar)
  )
    return false;
  if (familia === "basica") return temFiltro("rede", row[2], ignorar);
  const ies = IES.get(row[1]);
  const curso = CURSOS.get(row[2]);
  if (!ies || !curso) return false;
  if (
    !temFiltro("ies", ies.id, ignorar) ||
    !temFiltro("curso", curso.id, ignorar) ||
    !temFiltro("tipo", ies.tipo, ignorar) ||
    !temFiltro("grau", curso.grau, ignorar)
  )
    return false;
  if (familia === "mercado") {
    return (
      temFiltro("turno", row[4] === 0 ? "DIURNO" : "NOTURNO", ignorar) &&
      temFiltro("oferta", row[10] === 1 ? "Sim" : "Não", ignorar)
    );
  }
  // O filtro de portfólio do Enade usa a dimensão do curso; nao a oferta por turno.
  return (
    temFiltro("oferta", curso.oferta, ignorar) &&
    (familia !== "enade" || temFiltro("conceito", row[4], ignorar))
  );
}
function filtrarMercado({ ignorar = [], historico = false } = {}) {
  const ano = state.anos.mercado;
  return DADOS.dados.mercado.filter(
    (r) => (historico || r[0] === ano) && aceitaRegistro(r, "mercado", ignorar)
  );
}
function filtrarSuperior({ ignorar = [], ateAno = null } = {}) {
  return DADOS.dados.superior.filter(
    (r) => (ateAno == null || r[0] <= ateAno) && aceitaRegistro(r, "superior", ignorar)
  );
}
function filtrarEnade({ ignorar = [], historico = false } = {}) {
  const ano = state.anos.enade;
  return DADOS.dados.enade.filter(
    (r) => (historico || r[0] === ano) && r[4] > 0 && aceitaRegistro(r, "enade", ignorar)
  );
}
function filtrarBasica({ ignorar = [], historico = false } = {}) {
  const ano = state.anos.basica;
  return DADOS.dados.basica.filter(
    (r) => (historico || r[0] === ano) && aceitaRegistro(r, "basica", ignorar)
  );
}
function somar(rows, indice) {
  return rows.reduce((acc, row) => acc + (Number(row[indice]) || 0), 0);
}
function unicos(rows, indice) {
  return new Set(rows.map((r) => r[indice])).size;
}
function agrupar(rows, indiceGrupo, indiceValor) {
  const grupos = new Map();
  for (const row of rows) {
    const chave = row[indiceGrupo];
    grupos.set(chave, (grupos.get(chave) || 0) + (Number(row[indiceValor]) || 0));
  }
  return grupos;
}
function ordenarGrupos(grupos, rotulo = String) {
  return [...grupos]
    .map(([valor, quantidade]) => ({ valor, quantidade }))
    .sort(
      (a, b) =>
        b.quantidade - a.quantidade || rotulo(a.valor).localeCompare(rotulo(b.valor), "pt-BR")
    );
}
function nomeIES(id) {
  return IES.get(id)?.nome || "IES não identificada";
}
function nomeCurso(id) {
  return CURSOS.get(id)?.nome || "Curso não identificado";
}
function nomeCidade(id) {
  const local = LOCAIS.get(Number(id));
  return local ? `${local.cidade} / ${local.uf}` : "Município não identificado";
}
function labelFiltro(campo, valor) {
  if (campo === "ies") return nomeIES(Number(valor));
  if (campo === "curso") return nomeCurso(Number(valor));
  if (campo === "cidade") return nomeCidade(Number(valor));
  if (campo === "conceito") return `Conceito ${valor}`;
  return String(valor);
}
function identidadeCor(id, tipo = "ies") {
  return tipo === "curso" ? CURSOS.get(id)?.cor || corTeal : IES.get(id)?.cor || corTeal;
}
function _mapaUltimoAno(fatos, porCidade = false) {
  const anoRef = state.anos.enade;
  const porGrupoAno = new Map();
  for (const row of fatos) {
    if (row[0] > anoRef) continue;
    const chave = porCidade ? `${row[1]}|${row[3]}` : String(row[1]);
    if (!porGrupoAno.has(chave)) porGrupoAno.set(chave, new Map());
    const porAno = porGrupoAno.get(chave);
    porAno.set(row[0], (porAno.get(row[0]) || 0) + (Number(row[4]) || 0));
  }
  const resultado = new Map();
  for (const [chave, porAno] of porGrupoAno) {
    const positivos = [...porAno]
      .filter(([ano, n]) => ano <= anoRef && n > 0)
      .sort((a, b) => b[0] - a[0]);
    if (positivos.length)
      resultado.set(chave, { ano: positivos[0][0], ingressantes: positivos[0][1] });
  }
  return resultado;
}
function ingressantesEnade({ ignorar = [], porCidade = false } = {}) {
  // DAX: Total Ingressantes Enade e Ano Base Ingressantes Bolha.
  // Para cada IES, busca o ultimo ano <= ano Enade com soma positiva,
  // respeitando curso, IES, UF, municipio, tipo, grau e oferta.
  // PorCidade representa o mesmo calculo no contexto de cada ponto do mapa.
  return _mapaUltimoAno(filtrarSuperior({ ignorar, ateAno: state.anos.enade }), porCidade);
}
function _agregarEnade(rows, porCidade = false) {
  const grupos = new Map();
  for (const row of rows) {
    const chave = porCidade ? `${row[1]}|${row[3]}` : String(row[1]);
    const anterior = grupos.get(chave) || {
      ies: row[1],
      localidade: row[3],
      conceito: 0,
      inscritos: 0,
      participantes: 0,
      acima: 0,
      cursos: new Set(),
      avaliacoes: 0
    };
    anterior.conceito = Math.max(anterior.conceito, Number(row[4]) || 0);
    anterior.inscritos += Number(row[5]) || 0;
    anterior.participantes += Number(row[6]) || 0;
    anterior.acima += Number(row[7]) || 0;
    anterior.avaliacoes++;
    anterior.cursos.add(row[2]);
    grupos.set(chave, anterior);
  }
  return grupos;
}
function dadosEnadeComVolume({ ignorar = [], porCidade = false } = {}) {
  const avaliacoes = _agregarEnade(filtrarEnade({ ignorar }), porCidade);
  const volumes = ingressantesEnade({ ignorar, porCidade });
  return [...avaliacoes]
    .map(([chave, r]) => ({
      ...r,
      ingressantes: volumes.get(chave)?.ingressantes || 0,
      ano_censo: volumes.get(chave)?.ano ?? null
    }))
    .filter((r) => r.ingressantes > 0);
}
function tituloAba() {
  return $id("tabs")?.querySelector(`[data-tab="${state.aba}"]`)?.textContent?.trim() || "Educacional";
}
