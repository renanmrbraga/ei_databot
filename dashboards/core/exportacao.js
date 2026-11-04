/* Exportacoes do navegador, com nomes e configuracoes informados pelo dashboard. */
const DashboardExportacao = Object.freeze({
  notificar(elemento, mensagem, duracao = 3500) {
    if (!elemento) return;
    elemento.textContent = mensagem;
    elemento.classList.add("show");
    clearTimeout(this.notificar._temporizador);
    this.notificar._temporizador = setTimeout(() => elemento.classList.remove("show"), duracao);
  },
  baixar(dados, nome, tipo = "application/octet-stream") {
    const arquivo = dados instanceof Blob ? dados : new Blob([dados], { type: tipo });
    const url = URL.createObjectURL(arquivo);
    const link = document.createElement("a");
    link.href = url;
    link.download = nome;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  },
  svgParaPNG(svg, { nome = "grafico.png", fundo = "#ffffff", escala = 2 } = {}) {
    if (!svg) return Promise.reject(Error("SVG nao encontrado"));
    const copia = svg.cloneNode(true);
    copia.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    const view = svg.viewBox.baseVal;
    const largura = view.width || 760;
    const altura = view.height || 440;
    const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    bg.setAttribute("x", view.x);
    bg.setAttribute("y", view.y);
    bg.setAttribute("width", largura);
    bg.setAttribute("height", altura);
    bg.setAttribute("fill", fundo);
    copia.insertBefore(bg, copia.firstChild);
    copia.querySelectorAll(".bar-hit").forEach((elemento) => elemento.removeAttribute("class"));
    copia
      .querySelectorAll("rect.row-band")
      .forEach((elemento) => elemento.setAttribute("fill", "transparent"));
    const svgString = new XMLSerializer().serializeToString(copia);
    const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    return new Promise((resolve, reject) => {
      const imagem = new Image();
      imagem.onload = () => {
        try {
          const canvas = document.createElement("canvas");
          canvas.width = Math.max(300, Math.round(largura * escala));
          canvas.height = Math.max(200, Math.round(altura * escala));
          const contexto = canvas.getContext("2d");
          if (!contexto) throw Error("Canvas indisponivel");
          contexto.fillStyle = fundo;
          contexto.fillRect(0, 0, canvas.width, canvas.height);
          contexto.drawImage(imagem, 0, 0, canvas.width, canvas.height);
          canvas.toBlob((png) => {
            if (png) {
              this.baixar(png, nome, "image/png");
              resolve();
            } else reject(Error("Falha ao gerar PNG"));
          }, "image/png");
        } catch (erro) {
          reject(erro);
        } finally {
          URL.revokeObjectURL(url);
        }
      };
      imagem.onerror = () => {
        URL.revokeObjectURL(url);
        reject(Error("Falha ao converter SVG para imagem"));
      };
      imagem.src = url;
    });
  },
  htmlAtual(nome = "dashboard.html") {
    this.baixar(
      "<!doctype html>\n" + document.documentElement.outerHTML,
      nome,
      "text/html;charset=utf-8"
    );
  },
  imprimir(todas = false, classe = "print-all") {
    document.body.classList.toggle(classe, Boolean(todas));
    requestAnimationFrame(() => requestAnimationFrame(() => window.print()));
  }
});
