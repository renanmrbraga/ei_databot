"use strict";

function mundoX(lon) { return DashboardMapa.projetar(lon,0).x; }
function mundoY(lat) { return DashboardMapa.projetar(0,lat).y; }
function areaBaseMapa() {
  return state.mapaModo === "brasil"
    ? {x:mundoX(-76), y:mundoY(7), w:mundoX(-30)-mundoX(-76), h:mundoY(-35)-mundoY(7)}
    : {x:mundoX(-52), y:mundoY(-16.4), w:mundoX(-38.6)-mundoX(-52), h:mundoY(-26.2)-mundoY(-16.4)};
}
function areaAtualMapa() { return state.mapaCaixa || areaBaseMapa(); }
function trocarAreaMapa(modo) {
  if (!["brasil","sudeste"].includes(modo)) return;
  state.mapaModo = modo; state.mapaCaixa = areaBaseMapa(); renderAll();
}
function aproximarMapa(fator) { state.mapaCaixa = DashboardMapa.aproximar(areaAtualMapa(), fator); atualizarAreasMapa(); }
function atualizarAreasMapa() {
  const view = DashboardMapa.caixaTexto(areaAtualMapa());
  document.querySelectorAll(".map-svg").forEach((svg) => svg.setAttribute("viewBox",view));
}
const CONTORNO_MAPA = DashboardMapa.contornos(DADOS.contorno_america_sul?.poligonos || [], {
  estilo: (p) => p.nome === "Brazil" ? {fill:"#d9e8eb",stroke:"#a4bec4"}
    : {fill:"#eaf0f2",stroke:"#cddadd"}
});
function ferramentasMapa(titulo, legenda = "") {
  return `<div class="card-top"><div><div class="overline">GEOGRAFIA DA OFERTA</div><h3>${esc(titulo)}</h3></div><div class="card-buttons"><button class="btn-mini" data-export-svg="map-${familiaAtual()}">PNG ↓</button></div></div>
    <p class="card-sub">Município de oferta · bolhas proporcionais ao volume · selecione uma bolha para filtrar</p>
    <div class="map-toolbar"><div class="segment"><button data-map-mode="sudeste" class="${state.mapaModo==='sudeste'?'active':''}">Sudeste</button><button data-map-mode="brasil" class="${state.mapaModo==='brasil'?'active':''}">Brasil</button></div>
    <button class="btn-mini" data-map-zoom="in">+ Aproximar</button><button class="btn-mini" data-map-zoom="out">− Afastar</button><button class="btn-mini" data-map-zoom="reset">Redefinir</button></div>${legenda}`;
}
function svgMapaPontos(pontos, titulo, familia) {
  const maiores = Math.max(1, ...pontos.map((p)=>p.total));
  const nomeSvg = `map-${familia}`;
  let bolhas = "";
  const lista = [...pontos].filter(p=>p.local?.lat!=null && p.local?.lon!=null && p.total>0)
    .sort((a,b)=>b.total-a.total);
  for (const ponto of lista) {
    const {x,y} = DashboardMapa.projetar(ponto.local.lon, ponto.local.lat);
    const raio = Math.max(2.6, Math.min(15, 2.5 + 13*Math.sqrt(ponto.total/maiores)));
    bolhas += DashboardMapa.bolha({x,y,raio,cor:ponto.cor||corTeal,
      selecionado:filtroAtivo("cidade",ponto.local.id),dimensao:"cidade",valor:ponto.local.id,
      titulo:ponto.tooltip||`${ponto.local.cidade} / ${ponto.local.uf}: ${numero(ponto.total)}`});
  }
  return `<svg class="map-svg" id="svg-${nomeSvg}" viewBox="${DashboardMapa.caixaTexto(areaAtualMapa())}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${esc(titulo)}">${CONTORNO_MAPA}${bolhas}</svg>`;
}
function renderMapaMercado(place) {
  const r = filtrarMercado({ignorar:["cidade"]});
  const totals = new Map(), byIES = new Map(), byCurso = new Map();
  for (const row of r) {
    const loc = row[3], ing = row[5];
    if (!ing) continue;
    totals.set(loc,(totals.get(loc)||0)+ing);
    if(!byIES.has(loc)) byIES.set(loc,new Map());
    if(!byCurso.has(loc)) byCurso.set(loc,new Map());
    const ui=byIES.get(loc), co=byCurso.get(loc);
    ui.set(row[1],(ui.get(row[1])||0)+ing);
    co.set(row[2],(co.get(row[2])||0)+ing);
  }
  const pontos = [...totals].map(([id,n])=>{
    const local=LOCAIS.get(id);
    const rankingIES=ordenarGrupos(byIES.get(id),nomeIES).slice(0,5)
      .map(v=>`${nomeIES(v.valor)}: ${numero(v.quantidade)}`).join("\n");
    const rankingCursos=ordenarGrupos(byCurso.get(id),nomeCurso).slice(0,5)
      .map(v=>`${nomeCurso(v.valor)}: ${numero(v.quantidade)}`).join("\n");
    return {local,total:n,cor:corTeal,tooltip:`${nomeCidade(id)} · ${numero(n)} ingressantes\nPrincipais IES:\n${rankingIES}\nPrincipais cursos:\n${rankingCursos}`};
  });
  const el=$id(place);
  el.innerHTML = ferramentasMapa("Ingressantes por município de oferta") +
    `<div class="map-wrap">${svgMapaPontos(pontos,"Mapa de ingressantes","mercado")}
    <div class="map-legend"><span class="legend-item"><i class="legend-dot" style="background:${corTeal}"></i>Ingresso em cursos presenciais</span><span class="legend-item">${numero(totals.size)} localidades com volume</span></div></div>`;
}
function renderMapaEnade(place) {
  const reg = dadosEnadeComVolume({ignorar:["cidade"],porCidade:true});
  const locais = new Map();
  for (const r of reg) {
    const antigo=locais.get(r.localidade)||{total:0,notas:new Map(),ies:[]};
    antigo.total+=r.ingressantes;
    antigo.notas.set(r.conceito,(antigo.notas.get(r.conceito)||0)+1);
    antigo.ies.push(`${nomeIES(r.ies)}: nota ${r.conceito} · ${numero(r.ingressantes)} ingressantes (Censo ${r.ano_censo})`);
    locais.set(r.localidade,antigo);
  }
  const pontos=[...locais].map(([id,x])=>({
    local:LOCAIS.get(Number(id)),total:x.total,
    cor:CONCEITO_CORES[Math.max(...x.notas.keys())]||corTeal,
    tooltip:`${nomeCidade(id)} · ${numero(x.total)} ingressantes (Censo retroativo)\nNotas presentes: ${[...x.notas].map(([k,v])=>`${k}: ${v} IES`).join(', ')}\n${x.ies.slice(0,12).join('\n')}`
  }));
  const legenda = `<div class="map-legend" style="margin-bottom:12px">${[1,2,3,4,5].map(n=>
    `<span class="legend-item"><i class="legend-dot" style="background:${CONCEITO_CORES[n]}"></i> Conceito ${n}</span>`).join("")}</div>`;
  $id(place).innerHTML = ferramentasMapa("Enade · instituições por localidade", legenda) +
    `<div class="map-wrap">${svgMapaPontos(pontos,"Mapa do Enade","enade")}
    <div class="map-legend"><span class="legend-item">Cor = maior conceito da localidade · tamanho = ingressantes históricos válidos</span>
    <span class="legend-item">${numero(locais.size)} localidades</span></div></div>`;
}
// Um unico estado de pan/zoom para os mapas, equivalente ao Perfil Medicina.
let arrasto = null;
let suprimirClickMapa = false;
function onMercadoPointerDown(e) {
  if (e.button !== 0 || e.target.closest("[data-filter-dim]")) return;
  const svg=e.target.closest(".map-svg"); if (!svg) return;
  svg.setPointerCapture(e.pointerId);
  arrasto={x:e.clientX,y:e.clientY,base:{...areaAtualMapa()},svg,movido:false};
}
function onMercadoPointerMove(e) {
  if(!arrasto)return;
  const dx=e.clientX-arrasto.x, dy=e.clientY-arrasto.y;
  if(Math.abs(dx)+Math.abs(dy)>4)arrasto.movido=true;
  if(!arrasto.movido)return;
  const rect=arrasto.svg.getBoundingClientRect();
  const aspecto=Math.min(rect.width/arrasto.base.w,rect.height/arrasto.base.h);
  state.mapaCaixa=DashboardMapa.deslocar(arrasto.base,dx,dy,aspecto);
  atualizarAreasMapa();
}
function onMercadoPointerUp() {
  if(!arrasto)return;
  if(arrasto.movido){suprimirClickMapa=true; setTimeout(()=>suprimirClickMapa=false,100);}
  arrasto=null;
}
