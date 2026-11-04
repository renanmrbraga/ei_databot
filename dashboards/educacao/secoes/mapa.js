function renderMapa() {
  const r=filtrarMercado();
  const total=somar(r,5), grupos=unicos(r,3);
  definirEstatisticas("mapaStats", [
    ["Ingressantes",numero(total),`Censo ${state.anos.mercado}`],
    ["Municípios",numero(grupos),"Localidades da oferta"],
    ["Universidades",numero(unicos(r,1)),"No filtro espacial"],
    ["Cursos",numero(unicos(r,2)),"Ofertas analíticas"],
  ]);
  renderMapaMercado("mercadoMapa");
  mostrarRankingMercado("mercadoCidades","Ranking de municípios","cidade",
    {limite:15,desc:"Clique para filtrar a localidade"});
  mostrarRankingMercado("mercadoMapaIES","Principais instituições","ies",
    {limite:10,buscar:false});
  mostrarRankingMercado("mercadoMapaCurso","Principais cursos","curso",
    {limite:10,buscar:false});
}
