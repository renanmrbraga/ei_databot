function renderEvolucaoIES() {
  const r=filtrarMercado({historico:true}), anos=DADOS.anos.mercado;
  const total=somar(r,5), grupos=unicos(r,1);
  definirEstatisticas("evolucaoIESStats", [
    ["Ingressantes históricos", numero(total), "Soma dos anos do Censo"],
    ["IES distintas", numero(grupos), "Após filtros dimensionais"],
    ["Anos de análise", numero(anos.length), "Censo Superior"],
    ["Último ano", String(anos.at(-1)), "Referência da série"],
  ]);
  montarFaixasMercado("faixasIES","ies","Movimentação anual das instituições");
  const porAno=agrupar(r,0,5), lista=[...porAno].sort((a,b)=>a[0]-b[0]);
  mostrarLinhaMercado("evolucaoIESTop","Ingressantes ao longo do tempo",
    lista.map(([ano,valor])=>({rotulo:String(ano),valor})),
    {desc:"Total anual no universo selecionado, independente do ano no filtro superior."});
}
