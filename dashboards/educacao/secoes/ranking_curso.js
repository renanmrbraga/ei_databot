function renderRankingCurso() {
  const r=filtrarMercado(),t=somar(r,5);
  const top=ordenarGrupos(agrupar(r,2,5),nomeCurso).filter(v=>v.quantidade>0)[0];
  definirEstatisticas("rankingCursoStats", [
    ["Cursos distintos",numero(unicos(r,2)),"No contexto atual"],
    ["Ingressantes",numero(t),`Censo ${state.anos.mercado}`],
    ["Maior curso",top?numero(top.quantidade):"—",top?DashboardFormatacao.truncar(nomeCurso(top.valor),34):"Sem volume"],
    ["Share do líder",top?percentual(top.quantidade,t):"—","Do volume filtrado"],
  ]);
  mostrarRankingMercado("rankingCursoPrincipal","Ingressantes por curso analítico","curso",
    {limite:15,desc:"Comparação por curso. Cursos homônimos com grau distinto são chaves distintas."});
  const gra={}; const turno=new Map();
  for(const r0 of r){
    const key=CURSOS.get(r0[2])?.grau||"NÃO INFORMADO";
    gra[key]=(gra[key]||0)+r0[5];
  }
  mostrarBarrasMercado("rankingCursoGrau","Ingresso por grau acadêmico",
    Object.entries(gra).sort((a,b)=>b[1]-a[1]).map(([rotulo,valor])=>({rotulo,valor})),
    {desc:"Cursos presenciais da Gold"});
  // Mantem os dois turnos visiveis mesmo quando um deles esta filtrado.
  for (const linha of filtrarMercado({ignorar:["turno"]})) {
    const chave=linha[4]===0?"DIURNO":"NOTURNO";
    turno.set(chave,(turno.get(chave)||0)+linha[5]);
  }
  mostrarRoscaMercado("rankingCursoTurno","Ingressantes por turno",[
    {rotulo:"Diurno",filtro:"DIURNO",valor:turno.get("DIURNO")||0,cor:corTeal},
    {rotulo:"Noturno",filtro:"NOTURNO",valor:turno.get("NOTURNO")||0,cor:corAmber},
  ],{desc:"Participacao no ano e demais filtros; a rosca ignora apenas o filtro de turno. Clique na legenda para selecionar.",
      dimensao:"turno"});
}
