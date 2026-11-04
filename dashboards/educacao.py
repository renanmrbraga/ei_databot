"""Dashboard Educacional: Gold -> JSON contratual -> HTML offline.

Nao executa ETL nem le Bronze/Silver. Reaproveita dashboards.common e
os componentes gerais dashboards/core e dashboards/graficos.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from dashboards.common import (
    gravar_html_atomico,
    ler_recurso,
    ler_tabelas_gold,
    montar_html_offline,
    montar_recursos_dashboard,
)
from etl.core.common import gravar_json
from etl.core.config import DASHBOARDS_CORE_DIR, DASHBOARDS_GRAFICOS_DIR, DATA_ROOT
from etl.core.logger import get_logger
from etl.educacao.config import (
    GOLD_DIM_CURSO_SUPERIOR,
    GOLD_DIM_ESCOLA,
    GOLD_DIM_IES,
    GOLD_DIM_LOCALIDADE,
    GOLD_FACT_AVALIACAO_CURSO_SUPERIOR,
    GOLD_FACT_AVALIACAO_IES,
    GOLD_FACT_EDUCACAO_BASICA,
    GOLD_FACT_EDUCACAO_SUPERIOR,
    GOLD_FACT_EDUCACAO_SUPERIOR_TURNO,
)

logger = get_logger(pipeline="educacao")

RAIZ = Path(__file__).with_suffix("")
CORE = DASHBOARDS_CORE_DIR
GRAFICOS = DASHBOARDS_GRAFICOS_DIR
SAIDA = DATA_ROOT / "educacao" / "dashboards"
DADOS_DASHBOARD = SAIDA / "dados_educacao.json"
HTML_DASHBOARD = SAIDA / "educacao.html"

SECOES = (
    "geral",
    "mapa",
    "evolucao_ies",
    "evolucao_curso",
    "ranking_ies",
    "ranking_curso",
    "enade_mapa",
    "enade_ranking",
    "basica",
)

SCRIPTS, ESTILOS = montar_recursos_dashboard(
    raiz=RAIZ,
    core=CORE,
    graficos=GRAFICOS,
    secoes=SECOES,
    graficos_especificos=(
        "rankings_mercado.js",
        "faixas_mercado.js",
        "mapas_mercado.js",
    ),
)

TABELAS = {
    "dim_ies": GOLD_DIM_IES,
    "dim_curso_superior": GOLD_DIM_CURSO_SUPERIOR,
    "dim_localidade": GOLD_DIM_LOCALIDADE,
    "dim_escola": GOLD_DIM_ESCOLA,
    "fact_educacao_superior_turno": GOLD_FACT_EDUCACAO_SUPERIOR_TURNO,
    "fact_educacao_superior": GOLD_FACT_EDUCACAO_SUPERIOR,
    "fact_avaliacao_curso_superior": GOLD_FACT_AVALIACAO_CURSO_SUPERIOR,
    "fact_avaliacao_ies": GOLD_FACT_AVALIACAO_IES,
    "fact_educacao_basica": GOLD_FACT_EDUCACAO_BASICA,
}

COLUNAS = {
    "dim_ies": ("id_ies", "rotulo_ies", "sigla_ies", "tipo_ies", "hex_ies"),
    "dim_curso_superior": (
        "id_curso_superior",
        "nome_curso",
        "grau_curso",
        "modalidade_curso",
        "tipo_curso",
        "oferta_curso",
        "hex_curso",
    ),
    "dim_localidade": (
        "id_localidade",
        "municipio",
        "uf",
        "latitude",
        "longitude",
        "distancia_referencia_km",
    ),
    "dim_escola": ("id_escola", "rede_escola"),
    "fact_educacao_superior_turno": (
        "ano",
        "id_ies",
        "id_curso_superior",
        "id_localidade",
        "turno_curso",
        "ingressantes",
        "vagas_total",
        "inscritos_total",
        "matriculados",
        "concluintes",
        "oferta_curso",
    ),
    "fact_educacao_superior": (
        "ano",
        "id_ies",
        "id_curso_superior",
        "id_localidade",
        "ingressantes",
    ),
    "fact_avaliacao_curso_superior": (
        "ano",
        "id_ies",
        "id_curso_superior",
        "id_localidade",
        "enade_conceito_faixa",
        "enade_concluintes_inscritos_qtd",
        "enade_concluintes_participantes_qtd",
        "enade_concluintes_acima_padrao_qtd",
        "cpc_faixa",
        "idd_faixa",
        "enade_conceito_continuo",
    ),
    "fact_avaliacao_ies": ("ano", "id_ies", "igc_faixa", "igc_continuo"),
    "fact_educacao_basica": (
        "ano",
        "id_escola",
        "id_localidade",
        "matriculas_educacao_basica",
        "matriculas_educacao_infantil",
        "matriculas_fundamental_anos_iniciais",
        "matriculas_fundamental_anos_finais",
        "matriculas_ensino_medio",
        "matriculas_educacao_profissional",
        "matriculas_educacao_profissional_tecnica",
        "matriculas_eja",
    ),
}


def _ler_gold() -> dict[str, pl.DataFrame]:
    tabelas = ler_tabelas_gold(TABELAS, colunas=COLUNAS)
    for nome, df in tabelas.items():
        logger.info("DASHBOARD Educacional | %s: %s linhas", nome, f"{df.height:,}")

    for nome, chave in (
        ("dim_ies", "id_ies"),
        ("dim_curso_superior", "id_curso_superior"),
        ("dim_localidade", "id_localidade"),
        ("dim_escola", "id_escola"),
    ):
        dim = tabelas[nome]
        if dim.get_column(chave).null_count() or dim.get_column(chave).n_unique() != dim.height:
            raise ValueError(f"{nome}: chave primaria {chave} invalida")

    for nome in (
        "fact_educacao_superior_turno",
        "fact_educacao_superior",
        "fact_avaliacao_curso_superior",
    ):
        fato = tabelas[nome]
        for chave, nome_dim in (
            ("id_ies", "dim_ies"),
            ("id_curso_superior", "dim_curso_superior"),
            ("id_localidade", "dim_localidade"),
        ):
            faltantes = (
                fato.select(chave)
                .unique()
                .join(tabelas[nome_dim].select(chave), on=chave, how="anti")
            )
            if not faltantes.is_empty():
                raise ValueError(f"{nome}: {faltantes.height} FK(s) orfas para {nome_dim}")
    for nome, ligacoes in (
        ("fact_avaliacao_ies", (("id_ies", "dim_ies"),)),
        (
            "fact_educacao_basica",
            (("id_escola", "dim_escola"), ("id_localidade", "dim_localidade")),
        ),
    ):
        for chave, nome_dim in ligacoes:
            faltantes = (
                tabelas[nome]
                .select(chave)
                .unique()
                .join(tabelas[nome_dim].select(chave), on=chave, how="anti")
            )
            if not faltantes.is_empty():
                raise ValueError(f"{nome}: {faltantes.height} FK(s) orfas para {nome_dim}")
    return tabelas


def _real_opcional(valor: Any) -> float | None:
    if valor is None:
        return None
    numero = float(valor)
    return numero if math.isfinite(numero) else None


def _inteiro(valor: Any) -> int:
    return int(valor) if valor is not None else 0


def _texto(valor: Any, padrao: str = "NAO INFORMADO") -> str:
    texto = str(valor or "").strip()
    return texto if texto else padrao


def _dimensoes(t: dict[str, pl.DataFrame]) -> dict[str, list[dict[str, Any]]]:
    return {
        "ies": [
            {
                "id": row["id_ies"],
                "nome": _texto(row["rotulo_ies"]),
                "sigla": _texto(row["sigla_ies"], ""),
                "tipo": _texto(row["tipo_ies"]),
                "cor": _texto(row["hex_ies"], "#147e80"),
            }
            for row in t["dim_ies"].iter_rows(named=True)
        ],
        "cursos": [
            {
                "id": row["id_curso_superior"],
                "nome": _texto(row["nome_curso"]),
                "grau": _texto(row["grau_curso"]),
                "modalidade": _texto(row["modalidade_curso"]),
                "tipo": _texto(row["tipo_curso"]),
                "oferta": _texto(row["oferta_curso"]),
                "cor": _texto(row["hex_curso"], "#147e80"),
            }
            for row in t["dim_curso_superior"].iter_rows(named=True)
        ],
        "localidades": [
            {
                "id": row["id_localidade"],
                "cidade": _texto(row["municipio"]),
                "uf": _texto(row["uf"]),
                "lat": _real_opcional(row["latitude"]),
                "lon": _real_opcional(row["longitude"]),
                "distancia_km": _real_opcional(row["distancia_referencia_km"]),
            }
            for row in t["dim_localidade"].iter_rows(named=True)
        ],
    }


def _fatos(t: dict[str, pl.DataFrame]) -> dict[str, list[list[Any]]]:
    mercado = []
    for row in t["fact_educacao_superior_turno"].iter_rows(named=True):
        turno = row["turno_curso"]
        if turno not in {"DIURNO", "NOTURNO"}:
            raise ValueError(f"fact_educacao_superior_turno: turno nao homologado: {turno!r}")
        mercado.append(
            [
                row["ano"],
                row["id_ies"],
                row["id_curso_superior"],
                row["id_localidade"],
                0 if turno == "DIURNO" else 1,
                _inteiro(row["ingressantes"]),
                _inteiro(row["vagas_total"]),
                _inteiro(row["inscritos_total"]),
                _inteiro(row["matriculados"]),
                _inteiro(row["concluintes"]),
                1 if str(row["oferta_curso"]).strip().casefold() == "sim" else 0,
            ]
        )

    geral = [
        [ano, ies, curso, localidade, _inteiro(ing)]
        for ano, ies, curso, localidade, ing in t["fact_educacao_superior"].iter_rows()
    ]
    enade = [
        [
            ano,
            ies,
            curso,
            loc,
            nota,
            _inteiro(inscr),
            _inteiro(part),
            _inteiro(acima),
            cpc,
            idd,
            _real_opcional(continuo),
        ]
        for ano, ies, curso, loc, nota, inscr, part, acima, cpc, idd, continuo in t[
            "fact_avaliacao_curso_superior"
        ].iter_rows()
    ]
    igc = [
        [ano, ies, nota, _real_opcional(continuo)]
        for ano, ies, nota, continuo in t["fact_avaliacao_ies"].iter_rows()
    ]

    # Agregar na Gold, nao serializar ~1,8 milhao de escolas/anos no HTML.
    # O grao resultante (ano, localidade, rede) suporta filtros geograficos
    # sem somar indicadores de etapas de ensino como se fossem disjuntos.
    basica = (
        t["fact_educacao_basica"]
        .join(t["dim_escola"], on="id_escola", how="left", validate="m:1")
        .with_columns(pl.col("rede_escola").fill_null("NAO INFORMADA"))
        .group_by("ano", "id_localidade", "rede_escola")
        .agg(
            pl.col("id_escola").n_unique().alias("escolas"),
            *(
                pl.col(nome).fill_null(0).sum().alias(nome)
                for nome in COLUNAS["fact_educacao_basica"][3:]
            ),
        )
        .sort("ano", "id_localidade", "rede_escola")
    )
    escolas = [
        [ano, localidade, _texto(rede), _inteiro(qtd), *(_inteiro(n) for n in valores)]
        for ano, localidade, rede, qtd, *valores in basica.iter_rows()
    ]
    return {"mercado": mercado, "superior": geral, "enade": enade, "igc": igc, "basica": escolas}


def validar_payload(payload: dict[str, Any]) -> None:
    """Circuit breakers de publicacao, inclusive conservacao dos volumes."""
    dados = payload["dados"]
    resumo = payload["resumo"]
    for nome in ("mercado", "superior", "enade", "basica"):
        if not dados[nome]:
            raise ValueError(f"Payload vazio: {nome}")
    if len(dados["mercado"]) != resumo["linhas_mercado"]:
        raise ValueError("Quantidade de linhas do Mercado nao conservada")
    if sum(row[5] for row in dados["mercado"]) != resumo["ingressantes_turno"]:
        raise ValueError("Ingressantes por turno divergentes entre Gold e JSON")
    for nome, indice_ies, indice_curso, indice_local in (
        ("mercado", 1, 2, 3),
        ("superior", 1, 2, 3),
        ("enade", 1, 2, 3),
    ):
        ies = {d["id"] for d in payload["dimensoes"]["ies"]}
        cursos = {d["id"] for d in payload["dimensoes"]["cursos"]}
        locais = {d["id"] for d in payload["dimensoes"]["localidades"]}
        for row in dados[nome]:
            if (
                row[indice_ies] not in ies
                or row[indice_curso] not in cursos
                or row[indice_local] not in locais
            ):
                raise ValueError(f"{nome}: FK orfa no JSON")
    for family in ("mercado", "enade", "basica"):
        if payload["anos_padrao"][family] is None:
            raise ValueError(f"Familia {family} sem anos de referencia")


def construir_payload() -> dict[str, Any]:
    t = _ler_gold()
    dados = _fatos(t)
    anos = {
        nome: sorted({int(row[0]) for row in dados[fonte]})
        for nome, fonte in (("mercado", "mercado"), ("enade", "enade"), ("basica", "basica"))
    }
    # Enade e CPC possuem anos distintos e a serie foi preservada integralmente.
    # Preferimos anos de Enade com conceito valido, nao apenas CPC/IDD sem nota.
    anos_enade = sorted({int(r[0]) for r in dados["enade"] if r[4] is not None and r[4] > 0})
    if anos_enade:
        anos["enade"] = anos_enade
    payload = {
        "schema_version": "educacional-1.0",
        "meta": {
            "titulo": "Inteligência Educacional",
            "gerado_em_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "fontes": "INEP: Censo Superior, Censo Escolar, Enade/CPC/IDD/IGC",
            "nota": "Uso interno. Localidade de oferta nao equivale a sede da IES.",
        },
        "anos": anos,
        "anos_padrao": {nome: max(valores) if valores else None for nome, valores in anos.items()},
        "dimensoes": _dimensoes(t),
        "dados": dados,
        "resumo": {
            "linhas_mercado": len(dados["mercado"]),
            "ingressantes_turno": sum(row[5] for row in dados["mercado"]),
            "linhas_educacao_basica_gold": t["fact_educacao_basica"].height,
            "linhas_educacao_basica_agregadas": len(dados["basica"]),
            "escolas_distintas_gold": t["dim_escola"].height,
        },
    }
    validar_payload(payload)
    return payload


def montar_html(payload: dict[str, Any]) -> str:
    validar_payload(payload)
    dados = {
        **payload,
        "contorno_america_sul": json.loads(ler_recurso(RAIZ / "contorno_america_sul.json")),
    }
    return montar_html_offline(
        layout=RAIZ / "layout.html",
        secoes={nome: RAIZ / "secoes" / f"{nome}.html" for nome in SECOES},
        estilos=ESTILOS,
        scripts=SCRIPTS,
        dados=dados,
        titulo="Painel Educacional",
    )


def executar() -> dict[str, Any]:
    """Prepara os dois artefatos antes de publica-los nos caminhos finais."""
    payload = construir_payload()
    html = montar_html(payload)
    gravar_json(DADOS_DASHBOARD, payload)
    gravar_html_atomico(HTML_DASHBOARD, html)
    logger.info(
        "DASHBOARD Educacional: JSON=%s | HTML=%s | ingressantes=%s | registros=%s",
        DADOS_DASHBOARD,
        HTML_DASHBOARD,
        f"{payload['resumo']['ingressantes_turno']:,}",
        f"{payload['resumo']['linhas_mercado']:,}",
    )
    return {
        "json": str(DADOS_DASHBOARD),
        "html": str(HTML_DASHBOARD),
        "linhas": payload["resumo"]["linhas_mercado"],
    }


if __name__ == "__main__":
    executar()
