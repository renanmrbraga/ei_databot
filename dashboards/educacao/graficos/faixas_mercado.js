"use strict";

// Ribbon chart: posicao no ranking por ano + espessura proporcional ao volume.
function montarFaixasMercado(place, eixo, titulo) {
  const dim = eixo === "ies" ? "ies" : "curso";
  const rows = filtrarMercado({ignorar:[dim], historico:true});
  const anos = DADOS.anos.mercado;
  const porAno = new Map(anos.map((a) => [a, new Map()]));
  const totais = new Map();
  for (const r of rows) {
    const id = eixo === "ies" ? r[1] : r[2];
    const grupos = porAno.get(r[0]);
    if (!grupos) continue;
    grupos.set(id, (grupos.get(id) || 0) + r[5]);
    totais.set(id, (totais.get(id) || 0) + r[5]);
  }
  const top = [...totais].filter(([,s]) => s > 0).sort((a,b)=>b[1]-a[1]).slice(0,9).map(([id])=>id);
  const idGrafico = `faixas-${eixo}`;
  const el = $id(place);
  el.classList.add("panel", "chart-card");
  if (!top.length || anos.length < 2) {
    el.innerHTML = cardHeaderMercado(titulo, "Histórico completo, ignorando o seletor de ano", idGrafico) +
      `<div class="chart-empty">O contexto não possui série histórica para o gráfico de faixas.</div>`;
    return;
  }
  const w = 1040, h = 485, x0 = 95, x1 = w - 110, y0 = 78, passoY = 42;
  const posX = (i) => x0 + (x1 - x0) * i / Math.max(1, anos.length - 1);
  const ordens = new Map();
  const maxVolume = Math.max(1, ...[...porAno.values()].flatMap((m)=>[...m.values()]));
  for (const ano of anos) {
    const ranking = [...porAno.get(ano)].filter(([id,n])=>top.includes(id) && n > 0)
      .sort((a,b)=>b[1]-a[1]);
    ordens.set(ano, new Map(ranking.map(([id],i)=>[id,i])));
  }
  let svg = `<svg id="svg-${idGrafico}" class="ribbon-svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(titulo)}">`;
  anos.forEach((ano,i)=>{
    const x=posX(i);
    svg += `<line x1="${x}" x2="${x}" y1="57" y2="${h-18}" stroke="#e0e9ed" stroke-dasharray="2 4"/>`;
    svg += `<text x="${x}" y="38" text-anchor="middle" fill="${ano===state.anos.mercado ? corTeal : '#607486'}" font-size="13" font-weight="${ano===state.anos.mercado?800:600}">${ano}</text>`;
  });
  top.forEach((id,ii)=>{
    const color = identidadeCor(id, eixo);
    const nome = eixo === "ies" ? nomeIES(id) : nomeCurso(id);
    const pontos = [];
    anos.forEach((ano,i)=>{
      const rank = ordens.get(ano).get(id);
      const quantidade = porAno.get(ano).get(id) || 0;
      if (rank!==undefined) pontos.push({x:posX(i),y:y0 + rank*passoY,ano,quantidade});
    });
    if (!pontos.length) return;
    const grosso = (n) => Math.max(4, Math.min(17, 4 + 12*Math.sqrt(n/maxVolume)));
    for (let i=1;i<pontos.length;i++) {
      const prev=pontos[i-1], curr=pontos[i], medio=(prev.x+curr.x)/2;
      const path=`M${prev.x} ${prev.y} C${medio} ${prev.y} ${medio} ${curr.y} ${curr.x} ${curr.y}`;
      const destacado = filtroAtivo(dim,id);
      svg += `<path class="ribbon-path" data-filter-dim="${dim}" data-filter-value="${esc(id)}" role="button" tabindex="0" d="${path}" fill="none" stroke="${esc(color)}" stroke-width="${grosso((prev.quantidade+curr.quantidade)/2)}" stroke-linecap="round" stroke-opacity="${destacado?1:.71}"><title>${esc(nome)}: ${prev.ano} = ${numero(prev.quantidade)}; ${curr.ano} = ${numero(curr.quantidade)}</title></path>`;
    }
    for (const p of pontos) {
      svg += `<circle data-filter-dim="${dim}" data-filter-value="${esc(id)}" role="button" tabindex="0" cx="${p.x}" cy="${p.y}" r="${Math.max(4,grosso(p.quantidade)/2)}" fill="${esc(color)}" stroke="white" stroke-width="1.2"><title>${esc(nome)} · ${p.ano}: ${numero(p.quantidade)} ingressantes</title></circle>`;
    }
  });
  svg += `</svg>`;
  const legenda = top.map((id,i)=>{
    const nome=eixo==='ies'?nomeIES(id):nomeCurso(id);
    return `<button data-filter-dim="${dim}" data-filter-value="${esc(id)}" class="${filtroAtivo(dim,id)?'chosen':''}" title="Filtrar ${esc(nome)}"><i class="legend-dot" style="background:${esc(identidadeCor(id,eixo))}"></i> ${i+1}. ${esc(DashboardFormatacao.truncar(nome,31))}</button>`;
  }).join("");
  el.innerHTML = cardHeaderMercado(titulo,
    `As 9 maiores categorias do histórico; ${anos[0]}–${anos.at(-1)}. A linha muda de altura conforme a posição e de espessura conforme o volume.`, idGrafico) +
    `<div class="ribbon-key">${legenda}</div>${svg}<p class="small-note">Clique em uma faixa ou legenda para filtrar. O ano selecionado está destacado; a evolução exibe todos os anos.</p>`;
}
