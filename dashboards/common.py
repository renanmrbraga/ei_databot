"""Montagem reutilizavel de dashboards HTML totalmente offline.

Este módulo não conhece pipelines específicos, dimensões ou regras de negócio.
Centraliza recursos HTML, CSS/JS e leitura generica de Gold para dashboards.
"""

from __future__ import annotations

import html
import json
import os
import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import polars as pl


def ler_recurso(caminho: Path) -> str:
    """Leitura unica e padronizada de arquivos de layout, estilos e scripts."""
    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError(f"Recurso do dashboard ausente: {caminho}")
    return caminho.read_text(encoding="utf-8")


def _trocar_marcador(pagina: str, marcador: str, conteudo: str) -> str:
    ocorrencias = pagina.count(marcador)
    if ocorrencias != 1:
        raise ValueError(f"Marcador {marcador!r}: esperado 1, encontrado {ocorrencias}")
    return pagina.replace(marcador, conteudo)


def _json_inline(dados: Mapping[str, Any]) -> str:
    """Protege contra fechamento de script e interpretacao de tags HTML."""
    saida = json.dumps(dados, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return (
        saida.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def montar_html_offline(
    *,
    layout: Path,
    secoes: Mapping[str, Path],
    estilos: Sequence[Path],
    scripts: Sequence[Path],
    dados: Mapping[str, Any],
    titulo: str,
) -> str:
    """Retorna HTML auto-contido, com uma unica tag script para todos os JS.

    Ordenacao de CSS e JS e explicita, permitindo dependencias sem importacao
    remota e funcionamento mesmo sob o protocolo file://.
    """
    if not scripts:
        raise ValueError("Dashboard sem scripts")
    if len({Path(p).resolve() for p in scripts}) != len(scripts):
        raise ValueError("Scripts duplicados na composicao do dashboard")

    pagina = ler_recurso(layout)
    for nome, arquivo in secoes.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]*", nome):
            raise ValueError(f"Nome de secao invalido: {nome!r}")
        pagina = _trocar_marcador(pagina, f"<!-- SECAO:{nome} -->", ler_recurso(arquivo))
    if "<!-- SECAO:" in pagina:
        raise ValueError("Existem secoes no layout sem arquivo correspondente")

    css = "\n".join(f"/* {Path(p).name} */\n{ler_recurso(p)}" for p in estilos)
    js = "\n\n".join(f"// {Path(p).name}\n{ler_recurso(p)}" for p in scripts)
    if "</style" in css.lower() or "</script" in js.lower():
        raise ValueError("Recurso contem fechamento de tag inline perigoso")

    pagina = _trocar_marcador(
        pagina, "__DASHBOARD_DOCUMENT_TITLE__", html.escape(titulo, quote=True)
    )
    pagina = _trocar_marcador(pagina, "__EMBED_DASHBOARD_PAYLOAD__", _json_inline(dados))
    pagina = _trocar_marcador(pagina, "__INLINE_CSS__", "<style>\n" + css + "\n</style>")
    pagina = _trocar_marcador(pagina, "__INLINE_JS__", "<script>\n" + js + "\n</script>")
    return pagina


def gravar_html_atomico(caminho: Path, conteudo: str) -> None:
    """Substitui o HTML somente apos concluir sua geracao."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp")
    try:
        temporario.write_text(conteudo, encoding="utf-8")
        os.replace(temporario, caminho)
    finally:
        temporario.unlink(missing_ok=True)


def montar_recursos_dashboard(
    *,
    raiz: Path,
    core: Path,
    graficos: Path,
    secoes: Sequence[str],
    graficos_especificos: Sequence[str],
) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    """Compila a ordem padrao dos JS e CSS sem regras de um painel especifico.

    Todos os dashboards compartilham os mesmos componentes basicos; somente
    adaptadores graficos e secoes mudam. Mantem a ordem necessaria para os JS.
    """
    raiz = Path(raiz)
    core = Path(core)
    graficos = Path(graficos)
    scripts = (
        *(core / nome for nome in ("formatacao.js", "filtros.js", "registro.js", "exportacao.js")),
        *(
            graficos / nome
            for nome in (
                "indicadores.js",
                "ranking.js",
                "barras.js",
                "linhas.js",
                "pizza.js",
                "mapa.js",
            )
        ),
        raiz / "estado.js",
        *(raiz / "graficos" / nome for nome in graficos_especificos),
        *(raiz / "secoes" / f"{nome}.js" for nome in secoes),
        raiz / "inicializacao.js",
    )
    estilos = (core / "base.css", core / "graficos.css", raiz / "estilo.css")
    return scripts, estilos


def ler_tabelas_gold(
    arquivos: Mapping[str, Path],
    *,
    colunas: Mapping[str, Sequence[str]] | None = None,
    validar: Callable[[pl.DataFrame, str], None] | None = None,
) -> dict[str, pl.DataFrame]:
    """Le Gold por nome, valida disponibilidade e aplica contratos especificos.

    Nao define PK, FK, granularidade ou regra de negocio: cada dashboard e
    responsavel por suas validacoes analiticas e de integridade referencial.
    """
    tabelas: dict[str, pl.DataFrame] = {}
    for nome, origem in arquivos.items():
        caminho = Path(origem)
        if not caminho.is_file():
            raise FileNotFoundError(f"Gold obrigatoria ausente: {caminho}")
        df = pl.read_parquet(caminho)
        if colunas is not None:
            if nome not in colunas:
                raise KeyError(f"Sem contrato de colunas para {nome}")
            faltantes = sorted(set(colunas[nome]) - set(df.columns))
            if faltantes:
                raise ValueError(f"{nome}: colunas obrigatorias ausentes: {faltantes}")
            df = df.select(colunas[nome])
        if validar is not None:
            validar(df, nome)
        tabelas[nome] = df
    return tabelas
