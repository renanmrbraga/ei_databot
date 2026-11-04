/* Pizza/rosca reutilizavel. Recebe segmentos com valor e cor, sem regras de negocio. */
const DashboardPizza = Object.freeze({
    anel({x = 140, y = 140, raio = 88, espessura = 26, segmentos = [], fundo = "#edf3f6"} = {}) {
        const total = segmentos.reduce((soma, item) => soma + Math.max(0, Number(item.valor) || 0), 0);
        const perimetro = 2 * Math.PI * raio;
        let posicao = 0;
        let saida = `<circle cx="${x}" cy="${y}" r="${raio}" fill="none" stroke="${DashboardFormatacao.esc(fundo)}" stroke-width="${espessura}"/>`;
        if (!total) return saida;
        for (const item of segmentos) {
            const fracao = Math.max(0, Number(item.valor) || 0) / total;
            if (!fracao) continue;
            const comprimento = perimetro * fracao;
            saida += `<circle cx="${x}" cy="${y}" r="${raio}" fill="none" stroke="${DashboardFormatacao.esc(item.cor || "#147e80")}" stroke-width="${espessura}" stroke-dasharray="${comprimento} ${perimetro}" transform="rotate(${-90 + posicao * 360} ${x} ${y})"/>`;
            posicao += fracao;
        }
        return saida;
    },
    renderizar({id = "pizza", largura = 440, altura = 320, segmentos = [], tipo = "rosca", titulo = "Gráfico de distribuição", cores = []} = {}) {
        const x = largura / 2, y = altura / 2;
        const raio = Math.max(20, Math.min(largura, altura) * 0.32);
        const valores = segmentos.map((s, i) => ({...s, cor: s.cor || cores[i] || ["#147e80", "#d58b40", "#133b58", "#6697aa"][i % 4]}));
        const espessura = tipo === "pizza" ? raio * 2 : Math.max(12, raio * 0.32);
        return `<svg id="svg-${DashboardFormatacao.esc(id)}" viewBox="0 0 ${largura} ${altura}" role="img" aria-label="${DashboardFormatacao.esc(titulo)}">${this.anel({x,y,raio,espessura,segmentos:valores})}</svg>`;
    },
});
