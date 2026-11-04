function renderEvolucaoCurso() {
  const r=filtrarMercado({historico:true}), anos=DADOS.anos.mercado;
  definirEstatisticas("evolucaoCursoStats", [
    ["Ingressantes históricos",numero(somar(r,5)),"Soma dos anos do Censo"],
    ["Cursos distintos",numero(unicos(r,2)),"Curso analítico"],
    ["Anos disponíveis",numero(anos.length),"Censo Superior"],
    ["Último ano",String(anos.at(-1)),"Referência da série"],
  ]);
  montarFaixasMercado("faixasCurso","curso","Movimentação anual dos cursos");
  mostrarLinhaMercado("evolucaoCursoTop","Ingresso por ano",
    [...agrupar(r,0,5)].sort((a,b)=>a[0]-b[0]).map(([ano,valor])=>({rotulo:String(ano),valor})),
    {desc:"Volume anual após os filtros de curso, localidade, IES e turno."});
}
