/* Formatacao independente de fontes, campos e regras de negocio. */
const DashboardFormatacao = Object.freeze({
    esc(valor) {
        return String(valor ?? "").replace(/[&<>"']/g, (char) => ({
            "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
        })[char]);
    },
    numero(valor, locale = "pt-BR") {
        return (Number(valor) || 0).toLocaleString(locale);
    },
    decimal(valor, casas = 1, locale = "pt-BR") {
        return Number(valor).toLocaleString(locale, {
            minimumFractionDigits: casas,
            maximumFractionDigits: casas,
        });
    },
    moeda(valor, moeda = "BRL", locale = "pt-BR") {
        return Number(valor).toLocaleString(locale, {style: "currency", currency: moeda});
    },
    data(valor, {locale = "pt-BR", timeZone = "America/Sao_Paulo"} = {}) {
        if (!valor) return "—";
        const fonte = String(valor);
        const data = /^\d{4}-\d{2}-\d{2}$/.test(fonte)
            ? new Date(fonte + "T12:00:00") : new Date(valor);
        return Number.isNaN(data.getTime()) ? "—"
            : new Intl.DateTimeFormat(locale, {day: "2-digit", month: "2-digit", year: "numeric", timeZone}).format(data);
    },
    razao(numerador, denominador) {
        return denominador ? (100 * numerador) / denominador : null;
    },
    percentual(numerador, denominador, casas = 1) {
        return denominador
            ? this.decimal((100 * numerador) / denominador, casas) + "%"
            : "—";
    },
    idSeguro(valor) {
        return String(valor).replace(/[^a-zA-Z0-9_-]/g, "-").slice(0, 75);
    },
    truncar(valor, maximo = 34) {
        const texto = String(valor);
        return texto.length > maximo ? texto.slice(0, maximo - 1) + "…" : texto;
    },
});
