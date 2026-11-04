function renderEnadeMapa() {
  const reg=dadosEnadeComVolume(), evals=filtrarEnade();
  definirEstatisticas("enadeMapaStats", [
    ["IES com nota e volume",numero(new Set(reg.map(r=>r.ies)).size),`Enade ${state.anos.enade}`],
    ["Ingressantes (Censo)",numero(reg.reduce((s,r)=>s+r.ingressantes,0)),"Último Censo positivo por IES"],
    ["Municípios",numero(new Set(reg.map(r=>r.localidade)).size),"Oferta presente no Censo"],
    ["Avaliações válidas",numero(evals.length),"Registros de conceito 1–5"],
  ]);
  renderMapaEnade("enadeMapaPainel");
  const notas=new Map();
  for (const r of evals) notas.set(r[4],(notas.get(r[4])||0)+1);
  mostrarBarrasMercado("enadeMapaNotas","Distribuição dos conceitos",
    [1,2,3,4,5].map(n=>({rotulo:`Nota ${n}`,valor:notas.get(n)||0})),
    {desc:"Quantidade de avaliações (linhas), não participantes"});
  const porIES=new Map();
  for(const r of reg)porIES.set(r.ies,(porIES.get(r.ies)||0)+r.ingressantes);
  mostrarBarrasMercado("enadeMapaIES","IES com volume no contexto",
    ordenarGrupos(porIES,nomeIES).slice(0,10).map(x=>({rotulo:DashboardFormatacao.truncar(nomeIES(x.valor),18),valor:x.quantidade})),
    {desc:"Ingressantes obtidos do Censo com fallback, não da prova"});
  const rankingLocais=new Map();
  for (const r of dadosEnadeComVolume({ignorar:["cidade"],porCidade:true})) {
    rankingLocais.set(r.localidade,(rankingLocais.get(r.localidade)||0)+r.ingressantes);
  }
  const locais=ordenarGrupos(rankingLocais,nomeCidade).slice(0,15);
  const el=$id("enadeMapaCidades");
  el.classList.add("panel");
  el.innerHTML=`<div class="card-top"><div><div class="overline">CONCENTRAÇÃO</div><h3>Localidades com Enade e ingressantes</h3></div></div>
    <p class="card-sub">Clique em um município; o ranking ignora o filtro de município para permitir seleção cruzada.</p>
    <div class="city-pills">${locais.map((x,i)=>`<button class="action ${filtroAtivo('cidade',x.valor)?'primary':''}" data-filter-dim="cidade" data-filter-value="${esc(x.valor)}">${i+1}. ${esc(nomeCidade(x.valor))} · ${numero(x.quantidade)}</button>`).join("")}</div>`;
}
