/* Graficos de barras verticais (simples, agrupadas ou empilhadas). */
const DashboardBarras = Object.freeze({
    svg({id = "barras", titulo = "Gráfico de barras", categorias = [], series = [],
         largura = 760, altura = 380, empilhado = false} = {}) {
        const esc = DashboardFormatacao.esc;
        const left = 55, right = 18, top = 20, bottom = 65;
        const innerW = largura - left - right, innerH = altura - top - bottom;
        const grupos = series.length ? series : [{campo: "valor", nome: "Valor", cor: "#147e80"}];
        const valores = (cat) => grupos.map((s) => Math.max(0,Number(cat[s.campo] ?? 0)));
        const maximo = Math.max(1,...categorias.map((cat) => empilhado
            ? valores(cat).reduce((a,b) => a+b,0) : Math.max(0,...valores(cat))));
        let saida = `<svg class="bar-svg" id="svg-${esc(id)}" viewBox="0 0 ${largura} ${altura}" role="img" aria-label="${esc(titulo)}">`;
        for (let i=0;i<=4;i++) {
            const y = top + innerH * i / 4;
            saida += `<line x1="${left}" y1="${y}" x2="${largura-right}" y2="${y}" stroke="#dce6ec"/><text x="${left-8}" y="${y+4}" text-anchor="end" fill="#617485" font-size="11">${Math.round(maximo*(4-i)/4)}</text>`;
        }
        const groupW = innerW / Math.max(1,categorias.length);
        categorias.forEach((cat,i) => {
            let cumulativo=0;
            grupos.forEach((s,j) => {
                const n=valores(cat)[j];
                const w=empilhado ? groupW*.65 : groupW*.75/grupos.length;
                const h=innerH*n/maximo;
                const x=left+i*groupW + (empilhado ? groupW*.175 : groupW*.125+j*w);
                const y=top+innerH-h-(empilhado ? cumulativo : 0);
                saida += `<rect x="${x}" y="${y}" width="${Math.max(0,w-2)}" height="${h}" rx="2" fill="${esc(s.cor || "#147e80")}"><title>${esc(cat.rotulo ?? cat.categoria ?? i)} · ${esc(s.nome || s.campo)}: ${n}</title></rect>`;
                if (empilhado) cumulativo+=h;
            });
            const rotulo=DashboardFormatacao.truncar(cat.rotulo ?? cat.categoria ?? "",20);
            saida += `<text x="${left+(i+.5)*groupW}" y="${altura-36}" text-anchor="middle" fill="#425d6d" font-size="10">${esc(rotulo)}</text>`;
        });
        return saida + "</svg>";
    },
});
