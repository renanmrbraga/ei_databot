function renderRankingIES() {
  const r = filtrarMercado(),
    t = somar(r, 5);
  const top = ordenarGrupos(agrupar(r, 1, 5), nomeIES).filter((v) => v.quantidade > 0)[0];
  definirEstatisticas("rankingIESStats", [
    ["Universidades", numero(unicos(r, 1)), "No contexto atual"],
    ["Ingressantes", numero(t), `Censo ${state.anos.mercado}`],
    [
      "Líder",
      top ? numero(top.quantidade) : "—",
      top ? DashboardFormatacao.truncar(nomeIES(top.valor), 34) : "Sem volume"
    ],
    ["Share do líder", top ? percentual(top.quantidade, t) : "—", "Do volume filtrado"]
  ]);
  mostrarRankingMercado("rankingIESPrincipal", "Ingressantes por universidade", "ies", {
    limite: 15,
    desc: "Comparação por instituição. Compartilhamento (%): denominador = contexto sem filtro da IES."
  });
  const porOferta = new Map();
  for (const row of r) {
    const k = row[10] === 1 ? "Portfólio Escolhido" : "Outras ofertas";
    porOferta.set(k, (porOferta.get(k) || 0) + row[5]);
  }
  mostrarBarrasMercado(
    "rankingIESOferta",
    "Ofertas correspondentes ao portfólio escolhido",
    ordenarGrupos(porOferta).map((x) => ({ rotulo: x.valor, valor: x.quantidade })),
    { desc: "Indicador de curso+turno ofertado" }
  );
  mostrarBarrasMercado(
    "rankingIESTipo",
    "Ingresso por tipo de instituição",
    ordenarGrupos(
      new Map(
        [...agrupar(r, 1, 5)].reduce((acc, [id, ing]) => {
          const k = IES.get(id)?.tipo || "Não informado";
          acc.set(k, (acc.get(k) || 0) + ing);
          return acc;
        }, new Map())
      )
    ).map((x) => ({ rotulo: x.valor, valor: x.quantidade })),
    { desc: "Pública, particular ou sem classificação" }
  );
}
