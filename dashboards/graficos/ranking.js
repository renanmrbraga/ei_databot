/* Renderizador generico de ranking horizontal com series e denominadores informados. */
const DashboardRanking = Object.freeze({
    svg({id, titulo = "Ranking", dimensao = "", categorias = [], series = [],
         metrica = "quantidade", largura = 760, maximoRotulo = 33} = {}) {
        const fmt = DashboardFormatacao;
        const esc = fmt.esc;
        const grupos = series.length ? series : [{chave: "total", nome: "Total", cor: "#147e80", denominador: 0}];
        const rowH = grupos.length === 2 ? 59 : 44;
        const height = 58 + rowH * categorias.length;
        const top = 42, left = 242, area = largura - 345;
        const valor = (cat, grupo) => Number((cat.valores || {})[grupo.chave] || 0);
        const maximo = Math.max(1, ...categorias.flatMap((cat) => grupos.map((g) => valor(cat, g))));
        const escala = metrica === "percentual" ? 100 : maximo;
        let svg = `<svg class="bar-svg" id="svg-${esc(id)}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${largura} ${height}" role="img" aria-label="${esc(titulo)}">`;
        [0, .25, .5, .75, 1].forEach((t) => {
            const x = left + area * t;
            const texto = metrica === "percentual" ? Math.round(t * 100) + "%" : Math.round(t * maximo);
            svg += `<line x1="${x}" y1="32" x2="${x}" y2="${height - 5}" stroke="#dce6ec" stroke-dasharray="2 3"/><text x="${x}" y="22" text-anchor="middle" font-size="10" fill="#738797">${texto}</text>`;
        });
        categorias.forEach((cat, i) => {
            const y = top + rowH * i;
            const selecionado = Boolean(cat.selecionado);
            const rotulo = String(cat.rotulo ?? cat.valor ?? "");
            const filtro = `data-filter-dim="${esc(dimensao)}" data-filter-value="${esc(cat.valor)}"`;
            const dica = grupos.map((g) => `${g.nome}: ${valor(cat, g)} de ${g.denominador} (${fmt.percentual(valor(cat,g),g.denominador)})`).join(" | ");
            svg += `<g role="button" tabindex="0" class="bar-hit ${selecionado ? "selected" : ""}" ${filtro}>`;
            svg += `<rect class="row-band" x="1" y="${y - 9}" width="${largura - 2}" height="${rowH - 3}" rx="4" fill="${selecionado ? "#eaf6f5" : "transparent"}"/>`;
            svg += `<text x="229" y="${y + 8}" text-anchor="end" font-size="11.4" fill="#29445a" font-weight="${selecionado ? "750" : "600"}">${esc(fmt.truncar(rotulo, maximoRotulo))}</text>`;
            svg += `<title>${esc(rotulo)} · ${esc(dica)}</title>`;
            grupos.forEach((g, j) => {
                const n = valor(cat,g), d = Number(g.denominador || 0);
                const porcentagem = fmt.razao(n,d) || 0;
                const barra = metrica === "percentual" ? porcentagem : n;
                const larguraBarra = Math.max(0,Math.min(area, area * barra / escala));
                const yy = y - 2 + j * 19;
                svg += `<rect x="${left}" y="${yy}" width="${larguraBarra}" height="14" rx="3" fill="${esc(g.cor || "#147e80")}"/>`;
                svg += `<text x="${left + area + 9}" y="${yy + 11.5}" font-size="10.5" fill="#425d6d">${n} · ${fmt.percentual(n,d)}</text>`;
            });
            svg += "</g>";
        });
        return svg + "</svg>";
    },
});
