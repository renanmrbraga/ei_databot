from __future__ import annotations

import polars as pl

from etl.core.common import (
    gravar_parquet,
    ler_parquet,
    tipar_e_projetar_por_schema,
    validar_chave_unica,
    validar_colunas_obrigatorias_por_schema,
)
from etl.core.logger import get_logger
from etl.educacao.config import (
    CURSOS_PORTFOLIO_DETALHADO,
    GOLD_DIM_CURSO_SUPERIOR,
    GOLD_DIM_IES,
    GOLD_DIM_LOCALIDADE,
    GOLD_FACT_EDUCACAO_SUPERIOR_TURNO,
    SILVER_CURSOS_SUPERIOR,
)
from etl.educacao.mapping import (
    MAPA_GRAU_ACADEMICO,
    MAPA_MODALIDADE_ENSINO,
    MAPA_NIVEL_ACADEMICO,
)
from etl.educacao.schema import (
    CHAVE_CURSO_SUPERIOR_GOLD,
    CHAVE_FACT_EDUCACAO_SUPERIOR_TURNO,
    SCHEMA_CURSOS_SUPERIOR_SILVER,
    SCHEMA_DIM_CURSO_SUPERIOR,
    SCHEMA_DIM_IES,
    SCHEMA_DIM_LOCALIDADE,
    SCHEMA_FACT_EDUCACAO_SUPERIOR_TURNO,
)
from health.health_etl import registrar_alerta

log = get_logger(pipeline="educacao")


# ==============================================================================
# INDICADORES COM ABERTURA POR TURNO
# ==============================================================================

METRICAS_TURNO = {
    "vagas_total": {
        "DIURNO": "vagas_total_diurno",
        "NOTURNO": "vagas_total_noturno",
    },
    "inscritos_total": {
        "DIURNO": "inscritos_total_diurno",
        "NOTURNO": "inscritos_total_noturno",
    },
    "ingressantes": {
        "DIURNO": "ingressantes_diurno",
        "NOTURNO": "ingressantes_noturno",
    },
    "matriculados": {
        "DIURNO": "matriculados_diurno",
        "NOTURNO": "matriculados_noturno",
    },
    "rematriculados": {
        "DIURNO": "rematriculados_diurno",
        "NOTURNO": "rematriculados_noturno",
    },
    "concluintes": {
        "DIURNO": "concluintes_diurno",
        "NOTURNO": "concluintes_noturno",
    },
}


# ==============================================================================
# VALIDACOES
# ==============================================================================


def _validar_join(
    df: pl.DataFrame,
    id_col: str,
    chaves: list[str],
    nome_etapa: str,
    nome_arquivo: str,
    descricao: str,
) -> None:
    universo = df.select(chaves).unique().height
    orfaos = df.filter(pl.col(id_col).is_null()).select(chaves).unique()

    registrar_alerta(
        nome_etapa,
        orfaos,
        nome_arquivo,
        f"{descricao} | universo={universo} | orfaos={orfaos.height}",
        pipeline="educacao",
    )

    if not orfaos.is_empty():
        raise RuntimeError(
            f"{descricao}: {orfaos.height} chave(s) sem correspondencia. "
            f"Amostra={orfaos.head(10).to_dicts()}"
        )


def _validar_conservacao_turnos(
    base: pl.DataFrame,
    fato: pl.DataFrame,
) -> None:
    """
    Garante que a verticalizacao DIURNO/NOTURNO nao alterou os totais
    existentes nas respectivas colunas de turno da Silver.
    """

    divergencias: list[str] = []

    for metrica_destino, colunas_origem in METRICAS_TURNO.items():
        esperado = base.select(
            (
                pl.col(colunas_origem["DIURNO"]).fill_null(0).sum()
                + pl.col(colunas_origem["NOTURNO"]).fill_null(0).sum()
            ).alias("total")
        ).item()

        encontrado = fato.select(pl.col(metrica_destino).fill_null(0).sum().alias("total")).item()

        esperado = int(esperado or 0)
        encontrado = int(encontrado or 0)

        if esperado != encontrado:
            divergencias.append(f"{metrica_destino}: esperado={esperado} | encontrado={encontrado}")

    if divergencias:
        raise RuntimeError(
            "fact_educacao_superior_turno: divergencia na conservacao "
            "dos indicadores por turno. " + " | ".join(divergencias)
        )

    log.info(
        "[GOLD] fact_educacao_superior_turno: conservacao dos indicadores DIURNO/NOTURNO validada."
    )


# ==============================================================================
# PORTFOLIO POR TURNO
# ==============================================================================


def _build_lookup_portfolio_turno(
    dim_curso: pl.DataFrame,
) -> pl.DataFrame:
    """
    Converte o portfolio configurado para:
        id_curso_superior x turno_curso

    Dessa forma, oferta_curso passa a respeitar o turno.
    """

    portfolio = pl.DataFrame(
        CURSOS_PORTFOLIO_DETALHADO,
        schema=[
            "nome_curso",
            "grau_curso",
            "modalidade_curso",
            "turno_curso",
        ],
        orient="row",
    ).with_columns(
        pl.col("nome_curso").cast(pl.String).str.to_uppercase().str.strip_chars(),
        pl.col("grau_curso").cast(pl.String).str.to_uppercase().str.strip_chars(),
        pl.col("modalidade_curso").cast(pl.String).str.to_uppercase().str.strip_chars(),
        pl.col("turno_curso").cast(pl.String).str.to_uppercase().str.strip_chars(),
    )

    lookup = (
        dim_curso.select(
            "id_curso_superior",
            "nome_curso",
            "grau_curso",
            "modalidade_curso",
        )
        .join(
            portfolio,
            on=[
                "nome_curso",
                "grau_curso",
                "modalidade_curso",
            ],
            how="inner",
        )
        .select(
            "id_curso_superior",
            "turno_curso",
        )
        .unique()
        .with_columns(pl.lit("Sim").alias("oferta_curso"))
    )

    validar_chave_unica(
        lookup,
        [
            "id_curso_superior",
            "turno_curso",
        ],
        "Lookup portfolio por turno",
    )

    return lookup


# ==============================================================================
# VERTICALIZACAO
# ==============================================================================


def _build_parte_turno(
    base: pl.DataFrame,
    turno: str,
) -> pl.DataFrame:
    """
    Transforma as colunas fisicas de um turno em indicadores canonicos.

    Exemplo:
        ingressantes_diurno -> ingressantes
        ingressantes_noturno -> ingressantes
    """

    parte = base.select(
        "id_ies",
        "id_curso_superior",
        "id_localidade",
        "ano",
        pl.lit(turno).alias("turno_curso"),
        *[
            pl.col(METRICAS_TURNO[metrica][turno])
            .cast(
                SCHEMA_FACT_EDUCACAO_SUPERIOR_TURNO[metrica],
                strict=False,
            )
            .fill_null(0)
            .alias(metrica)
            for metrica in METRICAS_TURNO
        ],
    )

    # Nao cria uma linha artificial de turno quando nao existe
    # nenhum indicador registrado para aquele turno.
    return parte.filter(
        pl.max_horizontal([pl.col(metrica).fill_null(0) for metrica in METRICAS_TURNO]) > 0
    )


# ==============================================================================
# BUILD
# ==============================================================================


def executar() -> None:
    log.info("[GOLD] Construindo fact_educacao_superior_turno.")

    censo = ler_parquet(SILVER_CURSOS_SUPERIOR)
    dim_ies = ler_parquet(GOLD_DIM_IES)
    dim_curso = ler_parquet(GOLD_DIM_CURSO_SUPERIOR)
    dim_localidade = ler_parquet(GOLD_DIM_LOCALIDADE)

    # ==========================================================================
    # VALIDACAO DAS ENTRADAS
    # ==========================================================================

    validar_colunas_obrigatorias_por_schema(
        censo,
        SCHEMA_CURSOS_SUPERIOR_SILVER,
        "Entrada Gold fact_educacao_superior_turno - silver_superior_cursos",
        validar_tipos=True,
        permitir_extras=False,
    )

    validar_colunas_obrigatorias_por_schema(
        dim_ies,
        SCHEMA_DIM_IES,
        "Entrada Gold fact_educacao_superior_turno - dim_ies",
        validar_tipos=True,
        permitir_extras=False,
    )

    validar_colunas_obrigatorias_por_schema(
        dim_curso,
        SCHEMA_DIM_CURSO_SUPERIOR,
        "Entrada Gold fact_educacao_superior_turno - dim_curso_superior",
        validar_tipos=True,
        permitir_extras=False,
    )

    validar_colunas_obrigatorias_por_schema(
        dim_localidade,
        SCHEMA_DIM_LOCALIDADE,
        "Entrada Gold fact_educacao_superior_turno - dim_localidade",
        validar_tipos=True,
        permitir_extras=False,
    )

    # ==========================================================================
    # LOOKUPS
    # ==========================================================================

    lookup_ies = dim_ies.select(
        "codigo_ies",
        "id_ies",
    )

    lookup_localidade = dim_localidade.select(
        "codigo_municipio",
        "id_localidade",
    )

    lookup_curso = dim_curso.select(
        "id_curso_superior",
        *CHAVE_CURSO_SUPERIOR_GOLD,
    )

    validar_chave_unica(
        lookup_ies,
        ["codigo_ies"],
        "Lookup fact_educacao_superior_turno -> dim_ies",
    )

    validar_chave_unica(
        lookup_localidade,
        ["codigo_municipio"],
        "Lookup fact_educacao_superior_turno -> dim_localidade",
    )

    validar_chave_unica(
        lookup_curso,
        CHAVE_CURSO_SUPERIOR_GOLD,
        "Lookup fact_educacao_superior_turno -> dim_curso_superior",
    )

    # ==========================================================================
    # PREPARACAO DA BASE
    # ==========================================================================

    base = (
        censo.with_columns(
            pl.col("nome_curso_referencia")
            .cast(pl.String)
            .str.to_uppercase()
            .str.strip_chars()
            .alias("nome_curso"),
            pl.col("codigo_grau_academico")
            .replace_strict(
                MAPA_GRAU_ACADEMICO,
                default=pl.lit("OUTRO"),
                return_dtype=pl.String,
            )
            .alias("grau_curso"),
            pl.col("codigo_modalidade_ensino")
            .replace_strict(
                MAPA_MODALIDADE_ENSINO,
                default=pl.lit("OUTRA"),
                return_dtype=pl.String,
            )
            .alias("modalidade_curso"),
            pl.col("codigo_nivel_academico")
            .replace_strict(
                MAPA_NIVEL_ACADEMICO,
                default=pl.lit(None, dtype=pl.String),
                return_dtype=pl.String,
            )
            .alias("_nivel_por_codigo"),
            pl.col("ano_censo").cast(pl.Int32).alias("ano"),
        )
        .with_columns(
            pl.coalesce(
                [
                    pl.col("_nivel_por_codigo"),
                    pl.when(pl.col("grau_curso").is_in(list(MAPA_GRAU_ACADEMICO.values())))
                    .then(pl.lit("GRADUAÇÃO"))
                    .otherwise(pl.lit("OUTROS")),
                ]
            ).alias("nivel_ensino"),
        )
        .drop("_nivel_por_codigo")
        # A fato de turno e exclusivamente presencial.
        .filter(pl.col("modalidade_curso") == "PRESENCIAL")
    )

    # ==========================================================================
    # DIM IES
    # ==========================================================================

    base = base.join(
        lookup_ies,
        on="codigo_ies",
        how="left",
    )

    _validar_join(
        base,
        "id_ies",
        ["codigo_ies"],
        "gold_fact_educacao_superior_turno_ies",
        "audit_gold_fact_educacao_superior_turno_sem_ies.csv",
        "Censo Superior por turno -> dim_ies",
    )

    # ==========================================================================
    # DIM CURSO
    # ==========================================================================

    base = base.join(
        lookup_curso,
        on=CHAVE_CURSO_SUPERIOR_GOLD,
        how="left",
    )

    _validar_join(
        base,
        "id_curso_superior",
        CHAVE_CURSO_SUPERIOR_GOLD,
        "gold_fact_educacao_superior_turno_curso",
        "audit_gold_fact_educacao_superior_turno_sem_curso.csv",
        "Censo Superior por turno -> dim_curso_superior",
    )

    # ==========================================================================
    # DIM LOCALIDADE
    # ==========================================================================

    base = base.join(
        lookup_localidade,
        on="codigo_municipio",
        how="left",
    )

    _validar_join(
        base,
        "id_localidade",
        [
            "codigo_municipio",
            "municipio",
            "uf",
            "modalidade_curso",
        ],
        "gold_fact_educacao_superior_turno_localidade",
        "audit_gold_fact_educacao_superior_turno_sem_localidade.csv",
        "Censo Superior por turno -> dim_localidade",
    )

    # ==========================================================================
    # VERTICALIZACAO DIURNO / NOTURNO
    # ==========================================================================

    fato = pl.concat(
        [
            _build_parte_turno(
                base,
                "DIURNO",
            ),
            _build_parte_turno(
                base,
                "NOTURNO",
            ),
        ],
        how="vertical_relaxed",
    )

    # ==========================================================================
    # CONSOLIDACAO DO GRAO ANALITICO
    # ==========================================================================

    chave_agregacao = [
        "id_ies",
        "id_curso_superior",
        "id_localidade",
        "ano",
        "turno_curso",
    ]

    fato = fato.group_by(
        chave_agregacao,
        maintain_order=True,
    ).agg(*[pl.col(metrica).fill_null(0).sum().alias(metrica) for metrica in METRICAS_TURNO])

    # ==========================================================================
    # CALENDARIO
    # ==========================================================================

    fato = fato.with_columns(
        pl.col("ano").cast(pl.Int32).alias("id_calendario"),
    )

    # ==========================================================================
    # OFERTA POR CURSO + TURNO
    # ==========================================================================

    lookup_portfolio = _build_lookup_portfolio_turno(dim_curso)

    fato = fato.join(
        lookup_portfolio,
        on=[
            "id_curso_superior",
            "turno_curso",
        ],
        how="left",
    ).with_columns(pl.col("oferta_curso").fill_null("Não").alias("oferta_curso"))

    # ==========================================================================
    # CONTRATO GOLD
    # ==========================================================================

    fato = tipar_e_projetar_por_schema(
        fato,
        SCHEMA_FACT_EDUCACAO_SUPERIOR_TURNO,
        "Gold fact_educacao_superior_turno",
    )

    validar_chave_unica(
        fato,
        CHAVE_FACT_EDUCACAO_SUPERIOR_TURNO,
        "Gold fact_educacao_superior_turno",
    )

    # ==========================================================================
    # CONSERVACAO DOS INDICADORES
    # ==========================================================================

    _validar_conservacao_turnos(
        base,
        fato,
    )

    # ==========================================================================
    # SAIDA
    # ==========================================================================

    gravar_parquet(
        GOLD_FACT_EDUCACAO_SUPERIOR_TURNO,
        fato,
    )

    log.info(
        "[GOLD] fact_educacao_superior_turno salva em %s (%s linhas).",
        GOLD_FACT_EDUCACAO_SUPERIOR_TURNO,
        f"{fato.height:,}",
    )

    resumo_turnos = (
        fato.group_by("turno_curso")
        .agg(
            pl.len().alias("linhas"),
            pl.col("id_ies").n_unique().alias("ies"),
            pl.col("id_curso_superior").n_unique().alias("cursos"),
            pl.col("ingressantes").sum().alias("ingressantes"),
        )
        .sort("turno_curso")
    )

    log.info(
        "[GOLD] Resumo fact_educacao_superior_turno: %s",
        resumo_turnos.to_dicts(),
    )


if __name__ == "__main__":
    executar()
