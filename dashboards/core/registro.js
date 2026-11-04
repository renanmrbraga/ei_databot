/* Catalogo independente de dashboards e de componentes de visualizacao. */
class RegistroGraficos {
    constructor({tipos = [], validar = null} = {}) {
        this.itens = new Map();
        this.tipos = new Set(tipos);
        this.validar = validar;
    }

    registrar(config) {
        if (!config || typeof config.id !== "string" || !config.id.trim()) {
            throw Error("Grafico sem identificador valido");
        }
        if (!config.tipo || !this.tipos.has(config.tipo)) {
            throw Error("Tipo de grafico nao registrado: " + config.tipo);
        }
        if (this.itens.has(config.id)) {
            throw Error("Grafico duplicado: " + config.id);
        }
        if (this.validar) this.validar(config);
        this.itens.set(config.id, {...config});
        return config.id;
    }

    listar() { return [...this.itens.values()]; }
    obter(id) { return this.itens.get(id) || null; }
}
