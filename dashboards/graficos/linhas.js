/* Serie temporal simples ou multipla: categorias e valores ja agregados. */
const DashboardLinhas = Object.freeze({
  svg({
    id = "linhas",
    titulo = "Gráfico de linhas",
    pontos = [],
    series = [],
    largura = 760,
    altura = 380
  } = {}) {
    const esc = DashboardFormatacao.esc;

    const left = 62,
      right = 22,
      top = 20,
      bottom = 56;

    const iw = largura - left - right,
      ih = altura - top - bottom;

    const colunas = series.length ? series : [{ campo: "valor", nome: "Valor", cor: "#147e80" }];

    const numeros = pontos.flatMap((p) =>
      colunas.map((s) => Number(p[s.campo])).filter(Number.isFinite)
    );

    const minimo = Math.min(0, ...numeros),
      maximo = Math.max(1, ...numeros);

    const intervalo = maximo - minimo || 1;

    const posX = (i) => left + (pontos.length > 1 ? (iw * i) / (pontos.length - 1) : iw / 2);

    const posY = (v) => top + ih - ((Number(v) - minimo) / intervalo) * ih;

    let svg = `<svg class="bar-svg" id="svg-${esc(id)}" viewBox="0 0 ${largura} ${altura}" role="img" aria-label="${esc(titulo)}">`;
    for (let i = 0; i <= 4; i++) {
      const y = top + (ih * i) / 4;
      svg += `<line x1="${left}" y1="${y}" x2="${largura - right}" y2="${y}" stroke="#dce6ec"/><text x="${left - 9}" y="${y + 4}" text-anchor="end" font-size="10" fill="#617485">${DashboardFormatacao.numero(minimo + ((maximo - minimo) * (4 - i)) / 4)}</text>`;
    }

    colunas.forEach((s) => {
      const validos = pontos
        .map((p, i) => ({
          x: posX(i),
          y: posY(p[s.campo]),
          v: Number(p[s.campo]),
          label: p.rotulo ?? p.categoria ?? i
        }))
        .filter((p) => Number.isFinite(p.v));
      if (!validos.length) return;
      svg += `<polyline points="${validos.map((p) => `${p.x},${p.y}`).join(" ")}" fill="none" stroke="${esc(s.cor || "#147e80")}" stroke-width="3"/>`;
      validos.forEach(
        (p) =>
          (svg += `<circle cx="${p.x}" cy="${p.y}" r="4" fill="${esc(s.cor || "#147e80")}"><title>${esc(p.label)} · ${esc(s.nome || s.campo)}: ${p.v}</title></circle>`)
      );
    });
    pontos.forEach(
      (p, i) =>
        (svg += `<text x="${posX(i)}" y="${altura - 28}" text-anchor="middle" font-size="10" fill="#617485">${esc(DashboardFormatacao.truncar(p.rotulo ?? p.categoria ?? "", 14))}</text>`)
    );
    return svg + "</svg>";
  }
});
