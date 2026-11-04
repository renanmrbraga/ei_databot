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
    CODIGO_LOCALIDADE_EAD,
    GOLD_DIM_CURSO_SUPERIOR,
    GOLD_DIM_IES,
    GOLD_DIM_LOCALIDADE,
    GOLD_FACT_EDUCACAO_SUPERIOR,
    SILVER_CURSOS_SUPERIOR,
)
from etl.educacao.mapping import (
    MAPA_GRAU_ACADEMICO,
    MAPA_MODALIDADE_ENSINO,
    MAPA_NIVEL_ACADEMICO,
)
from etl.educacao.schema import (
    CHAVE_CURSO_SUPERIOR_GOLD,
    CHAVE_FACT_EDUCACAO_SUPERIOR,
    SCHEMA_CURSOS_SUPERIOR_SILVER,
    SCHEMA_DIM_CURSO_SUPERIOR,
    SCHEMA_DIM_IES,
    SCHEMA_DIM_LOCALIDADE,
    SCHEMA_FACT_EDUCACAO_SUPERIOR,
)
from health.health_etl import registrar_alerta

log = get_logger(pipeline="educacao")


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


def executar() -> None:
    log.info("[GOLD] Construindo fact_educacao_superior.")

    censo = ler_parquet(SILVER_CURSOS_SUPERIOR)
    dim_ies = ler_parquet(GOLD_DIM_IES)
    dim_curso = ler_parquet(GOLD_DIM_CURSO_SUPERIOR)
    dim_localidade = ler_parquet(GOLD_DIM_LOCALIDADE)

    validar_colunas_obrigatorias_por_schema(
        censo,
        SCHEMA_CURSOS_SUPERIOR_SILVER,
        "Entrada Gold fact_educacao_superior - silver_superior_cursos",
        validar_tipos=True,
        permitir_extras=False,
    )
    validar_colunas_obrigatorias_por_schema(
        dim_ies,
        SCHEMA_DIM_IES,
        "Entrada Gold fact_educacao_superior - dim_ies",
        validar_tipos=True,
        permitir_extras=False,
    )
    validar_colunas_obrigatorias_por_schema(
        dim_curso,
        SCHEMA_DIM_CURSO_SUPERIOR,
        "Entrada Gold fact_educacao_superior - dim_curso_superior",
        validar_tipos=True,
        permitir_extras=False,
    )
    validar_colunas_obrigatorias_por_schema(
        dim_localidade,
        SCHEMA_DIM_LOCALIDADE,
        "Entrada Gold fact_educacao_superior - dim_localidade",
        validar_tipos=True,
        permitir_extras=False,
    )

    lookup_ies = dim_ies.select("codigo_ies", "id_ies")
    lookup_localidade = dim_localidade.select("codigo_municipio", "id_localidade")
    lookup_curso = dim_curso.select("id_curso_superior", *CHAVE_CURSO_SUPERIOR_GOLD)

    validar_chave_unica(
        lookup_ies,
        ["codigo_ies"],
        "Lookup fact_educacao_superior -> dim_ies",
    )

    validar_chave_unica(
        lookup_localidade,
        ["codigo_municipio"],
        "Lookup fact_educacao_superior -> dim_localidade",
    )

    validar_chave_unica(
        lookup_curso,
        CHAVE_CURSO_SUPERIOR_GOLD,
        "Lookup fact_educacao_superior -> dim_curso_superior",
    )

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
            pl.when(pl.col("codigo_modalidade_ensino") == 2)
            .then(pl.lit(CODIGO_LOCALIDADE_EAD, dtype=pl.Int64))
            .otherwise(pl.col("codigo_municipio"))
            .alias("codigo_municipio_gold"),
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
    )

    base = base.join(lookup_ies, on="codigo_ies", how="left")
    _validar_join(
        base,
        "id_ies",
        ["codigo_ies"],
        "gold_fact_educacao_superior_ies",
        "audit_gold_fact_educacao_superior_sem_ies.csv",
        "Censo Superior -> dim_ies",
    )

    base = base.join(lookup_curso, on=CHAVE_CURSO_SUPERIOR_GOLD, how="left")
    _validar_join(
        base,
        "id_curso_superior",
        CHAVE_CURSO_SUPERIOR_GOLD,
        "gold_fact_educacao_superior_curso",
        "audit_gold_fact_educacao_superior_sem_curso.csv",
        "Censo Superior -> dim_curso_superior",
    )

    base = base.join(
        lookup_localidade,
        left_on="codigo_municipio_gold",
        right_on="codigo_municipio",
        how="left",
    )
    _validar_join(
        base,
        "id_localidade",
        ["codigo_municipio_gold", "municipio", "uf", "modalidade_curso"],
        "gold_fact_educacao_superior_localidade",
        "audit_gold_fact_educacao_superior_sem_localidade.csv",
        "Censo Superior -> dim_localidade",
    )

    # ==========================================================================
    # METRICAS DA FATO GERAL
    # ==========================================================================
    # Apenas campos que pertencem ao contrato Gold e existem na Silver.
    # Campos especificos de turno nao fazem mais parte desta fato.

    metricas = [
        coluna
        for coluna in SCHEMA_FACT_EDUCACAO_SUPERIOR
        if coluna in SCHEMA_CURSOS_SUPERIOR_SILVER
    ]

    # ==========================================================================
    # AGREGACAO
    # ==========================================================================
    # Grao:
    # IES x curso analitico x localidade x ano.
    #
    # codigo_curso_referencia deixa de participar do grao Gold.
    # Diferentes codigos tecnicos que representem a mesma combinacao
    # analitica sao consolidados.

    chave_agregacao = [
        "id_ies",
        "id_curso_superior",
        "id_localidade",
        "ano",
    ]

    fato = base.group_by(
        chave_agregacao,
        maintain_order=True,
    ).agg(
        *[
            pl.col(coluna)
            .cast(
                SCHEMA_FACT_EDUCACAO_SUPERIOR[coluna],
                strict=False,
            )
            .fill_null(0)
            .sum()
            .alias(coluna)
            for coluna in metricas
        ],
    )

    # ==========================================================================
    # CALENDARIO
    # ==========================================================================

    fato = fato.with_columns(
        pl.col("ano").cast(pl.Int32).alias("id_calendario"),
    )

    # ==========================================================================
    # CONTRATO GOLD
    # ==========================================================================

    fato = tipar_e_projetar_por_schema(
        fato,
        SCHEMA_FACT_EDUCACAO_SUPERIOR,
        "Gold fact_educacao_superior",
    )

    validar_chave_unica(
        fato,
        CHAVE_FACT_EDUCACAO_SUPERIOR,
        "Gold fact_educacao_superior",
    )

    gravar_parquet(
        GOLD_FACT_EDUCACAO_SUPERIOR,
        fato,
    )

    log.info(
        "[GOLD] fact_educacao_superior salva em %s (%s linhas).",
        GOLD_FACT_EDUCACAO_SUPERIOR,
        f"{fato.height:,}",
    )


if __name__ == "__main__":
    executar()
