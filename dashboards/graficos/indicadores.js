/* Cartoes e indicadores independentes do modelo de dados. */
const DashboardIndicadores = Object.freeze({
    stat(label, value, detail = "") {
        const esc = DashboardFormatacao.esc;
        return `<div class="statbox"><div class="lbl">${esc(label)}</div><div class="num">${esc(value)}</div><div class="details">${esc(detail)}</div></div>`;
    },
    kpi(label, value, detail = "") {
        const esc = DashboardFormatacao.esc;
        return `<div class="kpi"><div class="lbl">${esc(label)}</div><div class="num">${esc(value)}</div><div class="foot">${esc(detail)}</div></div>`;
    },
    grupo(elemento, estatisticas) {
        if (!elemento) throw Error("Elemento de indicadores inexistente");
        elemento.innerHTML = estatisticas.map((item) => this.stat(...item)).join("");
    },
});
