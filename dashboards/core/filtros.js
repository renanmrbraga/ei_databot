/* Selecao por multiplos valores: OR dentro da dimensao, AND entre dimensoes. */
const DashboardFiltros = Object.freeze({
    valores(registro, campo, camposMultivalor = new Set()) {
        const valor = registro[campo];
        if (camposMultivalor.has(campo)) {
            return Array.isArray(valor) ? valor.map(String) : [];
        }
        return valor === null || valor === undefined ? [] : [String(valor)];
    },
    filtrar(registros, selecoes = {}, opcoes = {}) {
        const ignorados = new Set(opcoes.ignorar || []);
        const multivalor = new Set(opcoes.multivalor || []);
        return registros.filter((registro) =>
            Object.entries(selecoes).every(([campo, escolhidos]) => {
                if (ignorados.has(campo) || !escolhidos || !escolhidos.length) return true;
                const existentes = this.valores(registro, campo, multivalor);
                return escolhidos.some((escolhido) => existentes.includes(String(escolhido)));
            }),
        );
    },
    ativo(selecoes, campo, valor) {
        return (selecoes[campo] || []).includes(String(valor));
    },
    alternar(selecoes, campo, valor) {
        const selecionados = selecoes[campo] || [];
        const texto = String(valor);
        const proximos = selecionados.includes(texto)
            ? selecionados.filter((item) => item !== texto)
            : [...selecionados, texto];
        const resultado = {...selecoes};
        if (proximos.length) resultado[campo] = proximos;
        else delete resultado[campo];
        return resultado;
    },
});
