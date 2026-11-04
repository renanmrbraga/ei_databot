function renderBasica() {
  const r=filtrarBasica();
  definirEstatisticas("basicaStats", [
    ["Matrículas Ensino Médio",numero(somar(r,8)),`Censo Escolar ${state.anos.basica}`],
    ["Educação Profissional",numero(somar(r,9)),"Total do indicador oficial"],
    ["Educação Prof. Técnica",numero(somar(r,10)),"Subconjunto da profissional"],
    ["Escolas",numero(somar(r,3)),"Contagem por localidade e rede"],
  ]);
  const hist=filtrarBasica({historico:true});
  const anos=DADOS.anos.basica;
  const totais = anos.map(ano=>{
    const linhas=hist.filter(r=>r[0]===ano);
    return {rotulo:String(ano), medio:somar(linhas,8), profissional:somar(linhas,9),
      tecnica:somar(linhas,10)};
  });
  mostrarLinhaMercado("basicaEvolucao","Histórico de matrículas: Médio x Profissional",
    totais,{desc:"Séries independentes. Técnica está contida na profissional, e não deve ser somada a ela.",
      series:[{campo:"medio",nome:"Ensino Médio",cor:corNav},
        {campo:"profissional",nome:"Educação Profissional",cor:corTeal},
        {campo:"tecnica",nome:"Educação Profissional Técnica",cor:corAmber}]});
  mostrarRankingBasica("basicaMunicipios","Municípios por matrículas no Ensino Médio","cidade",8,
    {limite:15,desc:"Agrupado por ano, localidade e rede; clique para filtrar."});
  mostrarBarrasMercado("basicaEtapas","Matrículas por etapa (não aditivas)",[
    {rotulo:"Infantil",valor:somar(r,5)},
    {rotulo:"Fund. I",valor:somar(r,6)},
    {rotulo:"Fund. II",valor:somar(r,7)},
    {rotulo:"Médio",valor:somar(r,8)},
    {rotulo:"Prof.",valor:somar(r,9)},
    {rotulo:"Técnica",valor:somar(r,10)},
  ],{desc:"A categoria Profissional Técnica integra a Profissional. Não somar as barras."});
  const porRede=new Map();
  for(const row of r)porRede.set(row[2],(porRede.get(row[2])||0)+(row[8]||0));
  mostrarBarrasMercado("basicaRedes","Ensino Médio por rede escolar",
    ordenarGrupos(porRede).map(x=>({rotulo:x.valor,valor:x.quantidade})),
    {desc:"Rede identificada na dimensão escola",cor:corAmber});
}
