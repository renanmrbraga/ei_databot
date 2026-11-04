function gerarDestaquesMercado(rows) {
  const lista = [];
  const ing = somar(rows, 5);
  if (!rows.length || !ing)
    return `<div class="chart-empty">Sem ingressantes no contexto selecionado.</div>`;
  const ies = ordenarGrupos(agrupar(rows, 1, 5), nomeIES);
  const cursos = ordenarGrupos(agrupar(rows, 2, 5), nomeCurso);
  const cidades = ordenarGrupos(agrupar(rows, 3, 5), nomeCidade);
  if (ies.length)
    lista.push([
      "Liderança institucional",
      `${nomeIES(ies[0].valor)} lidera o contexto com ${numero(ies[0].quantidade)} ingressantes (${percentual(ies[0].quantidade, ing)} do total selecionado).`
    ]);
  if (cursos.length)
    lista.push([
      "Curso de maior demanda",
      `${nomeCurso(cursos[0].valor)} registra ${numero(cursos[0].quantidade)} ingressantes (${percentual(cursos[0].quantidade, ing)} do contexto).`
    ]);
  if (cidades.length)
    lista.push([
      "Principal praça de oferta",
      `${nomeCidade(cidades[0].valor)} concentra ${numero(cidades[0].quantidade)} ingressantes (${percentual(cidades[0].quantidade, ing)}). O município representa o local de oferta.`
    ]);
  const ano = state.anos.mercado;
  const antigo = filtrarMercado({ historico: true }).filter((r) => r[0] === ano - 1);
  const anterior = somar(antigo, 5);
  if (anterior > 0) {
    const diferenca = ((ing - anterior) / anterior) * 100;
    lista.push([
      "Variação anual",
      `Ingressantes ${diferenca >= 0 ? "cresceram" : "recuaram"} ${decimal(Math.abs(diferenca))}% ante ${ano - 1} (${numero(anterior)} → ${numero(ing)}). A comparação usa os mesmos filtros de dimensão.`
    ]);
  }
  const fa = rows.filter((r) => r[10] === 1),
    vf = somar(fa, 5);
  if (vf > 0)
    lista.push([
      "Portfólio institucional",
      `O conjunto de ofertas do portfólio escolhido soma ${numero(vf)} ingressantes de mercado (${percentual(vf, ing)} do volume filtrado).`
    ]);
  return lista
    .slice(0, 5)
    .map(
      ([titulo, texto], i) =>
        `<div class="insight"><span class="n">DESTAQUE ${i + 1}</span><h4>${esc(titulo)}</h4><p>${esc(texto)}</p></div>`
    )
    .join("");
}
function renderGeral() {
  const rows = filtrarMercado();
  const ing = somar(rows, 5),
    vagas = somar(rows, 6),
    inscritos = somar(rows, 7);
  const ies = unicos(rows, 1),
    cursos = unicos(rows, 2);
  definirEstatisticas("generalStats", [
    ["Inscritos", numero(inscritos), "Vagas demandadas reportadas no Censo"],
    ["Vagas ofertadas", numero(vagas), "Não confundir com matrículas"],
    ["IES no contexto", numero(ies), "Instituições distintas"],
    ["Localidades", numero(unicos(rows, 3)), "Municípios da oferta selecionada"]
  ]);
  $id("highlights").innerHTML = gerarDestaquesMercado(rows);
  const hist = filtrarMercado({ historico: true });
  const anos = ordenarGrupos(agrupar(hist, 0, 5)).sort((a, b) => a.valor - b.valor);
  mostrarLinhaMercado(
    "generalEvolution",
    "Evolução dos ingressantes · série histórica",
    anos.map((x) => ({ rotulo: String(x.valor), valor: x.quantidade })),
    { desc: "Histórico de todos os anos com os demais filtros; o ano acima é usado nos KPIs." }
  );
  mostrarRankingMercado("generalIES", "Universidades com mais ingressantes", "ies", {
    limite: 8,
    desc: `Ano ${state.anos.mercado}`
  });
  mostrarRankingMercado("generalCursos", "Cursos com mais ingressantes", "curso", {
    limite: 8,
    desc: `Ano ${state.anos.mercado}`
  });
}
