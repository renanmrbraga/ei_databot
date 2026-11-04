function renderEnadeRanking() {
  const universo=dadosEnadeComVolume();
  const linhas=dadosEnadeComVolume({ignorar:["ies"]});
  const pos=linhas.sort((a,b)=>b.conceito-a.conceito || b.ingressantes-a.ingressantes ||
    nomeIES(a.ies).localeCompare(nomeIES(b.ies),"pt-BR"));
  const id="ranking-enade-ies";
  const busca=String(state.busca[id]||"").toLocaleLowerCase("pt-BR");
  const resultado=pos.filter(x=>!busca || nomeIES(x.ies).toLocaleLowerCase("pt-BR").includes(busca));
  const top=state.expandido[id]?resultado.slice(0,100):resultado.slice(0,15);
  const max=Math.max(1,...resultado.map(x=>x.ingressantes));
  const totalVolume=universo.reduce((s,r)=>s+r.ingressantes,0);
  const conceitos=universo.filter(x=>x.conceito>0);
  definirEstatisticas("enadeRankingStats", [
    ["IES com nota",numero(universo.length),`Enade ${state.anos.enade}`],
    ["Ingressantes (Censo)",numero(totalVolume),"Fallback por IES"],
    ["Nota mais alta",conceitos.length?String(Math.max(...conceitos.map(x=>x.conceito))):"—","Maior conceito válido"],
    ["Participantes",numero(conceitos.reduce((s,r)=>s+r.participantes,0)),"ENADE · soma oficial dos avaliados"],
  ]);
  const lista=top.map((r,i)=>{
    const rotulo=nomeIES(r.ies),cor=CONCEITO_CORES[r.conceito]||corTeal;
    return `<div class="ranking-row ${filtroAtivo('ies',r.ies)?'selected':''}" role="button" tabindex="0" data-filter-dim="ies" data-filter-value="${esc(r.ies)}" title="${esc(rotulo)} · Conceito ${r.conceito}, ${numero(r.ingressantes)} ingressantes (Censo ${r.ano_censo})">
      <div class="ranking-pos">${i+1}.</div>
      <div class="ranking-name">${esc(rotulo)}<span class="ranking-meta">Censo ${r.ano_censo} · ${numero(r.participantes)} participantes Enade</span></div>
      <div class="ranking-bar"><i style="width:${100*r.ingressantes/max}%;background:${esc(cor)}"></i></div>
      <div class="ranking-num">${numero(r.ingressantes)}</div>
      <div class="ranking-score" style="color:${esc(cor)}">Nota ${r.conceito}</div></div>`;
  }).join("");
  const el=$id("enadeRankingPrincipal");el.classList.add("panel","chart-card");
  el.innerHTML=`<div class="card-top"><div><div class="overline">RANKING DO ENADE</div><h3>IES ordenadas por nota e ingressantes</h3></div>
    <div class="card-buttons">${resultado.length>15 ? `<button class="btn-mini" data-expand="${id}">${state.expandido[id]?'Top 15':'Ver todos'}</button>`:''}</div></div>
    <p class="card-sub">Primeiro conceito (decrescente); empate = maior volume de ingressantes do último Censo positivo. ${resultado.length} instituições com nota válida e ingressantes${state.expandido[id]&&resultado.length>100?" · Top 100, use busca para demais":""}.</p>
    <input class="chart-search" value="${esc(state.busca[id]||'')}" data-search-id="${id}" placeholder="Buscar IES (Enter)" aria-label="Buscar instituição"/>
    <div>${lista||'<div class="chart-empty">Nenhuma universidade atende ao conceito e aos filtros.</div>'}</div>`;

  const notas=new Map();
  for(const r of filtrarEnade()) notas.set(r[4],(notas.get(r[4])||0)+1);
  $id("enadeRankingFaixas").classList.add("panel");
  $id("enadeRankingFaixas").innerHTML=`<div class="card-top"><div><div class="overline">DISTRIBUIÇÃO</div><h3>Conceitos Enade</h3></div></div>
    <p class="card-sub">Filtrar os registros de avaliação pelo conceito (não modifica o Censo).</p>
    <div class="nota-grid">${[1,2,3,4,5].map(n=>`<button class="nota-cell ${filtroAtivo('conceito',n)?'active':''}" data-filter-dim="conceito" data-filter-value="${n}"><i class="legend-dot" style="background:${CONCEITO_CORES[n]}"></i><b>${n}</b><small>${numero(notas.get(n)||0)} avaliações</small></button>`).join("")}</div>`;
  const corpo=conceitos.reduce((a,r)=>a+r.inscritos,0), acima=conceitos.reduce((a,r)=>a+r.acima,0);
  definirEstatisticas("enadeRankingCobertura", [
    ["Inscritos na avaliação",numero(corpo),"Registros avaliativos válidos"],
    ["Acima do padrão",numero(acima),"Contagem oficial"],
  ]);
}
