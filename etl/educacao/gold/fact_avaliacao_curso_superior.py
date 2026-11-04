from __future__ import annotations

from pathlib import Path

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
    GOLD_DIM_CURSO_SUPERIOR,
    GOLD_DIM_IES,
    GOLD_DIM_LOCALIDADE,
    GOLD_FACT_AVALIACAO_CURSO_SUPERIOR,
    SILVER_CONCEITO_ENADE,
    SILVER_CPC,
    SILVER_CURSOS_SUPERIOR,
    SILVER_IDD,
)
from etl.educacao.mapping import (
    DE_PARA_AREA_CONHECIMENTO,
    MAPA_GRAU_ACADEMICO,
    MAPA_GRAU_ACADEMICO_TEXTO,
    MAPA_MODALIDADE_ENSINO,
    MAPA_MODALIDADE_ENSINO_TEXTO,
    MAPA_NIVEL_ACADEMICO,
)
from etl.educacao.schema import (
    CHAVE_CURSO_SUPERIOR_GOLD,
    CHAVE_FACT_AVALIACAO_CURSO_SUPERIOR,
    COLUNAS_METRICAS_CPC,
    COLUNAS_METRICAS_ENADE,
    COLUNAS_METRICAS_IDD,
    SCHEMA_CONCEITO_ENADE_SILVER,
    SCHEMA_CPC_SILVER,
    SCHEMA_CURSOS_SUPERIOR_SILVER,
    SCHEMA_DIM_CURSO_SUPERIOR,
    SCHEMA_DIM_IES,
    SCHEMA_DIM_LOCALIDADE,
    SCHEMA_FACT_AVALIACAO_CURSO_SUPERIOR,
    SCHEMA_IDD_SILVER,
)
from health.health_etl import registrar_alerta

log = get_logger(pipeline="educacao")

COURSE_ANCHORS = sorted(DE_PARA_AREA_CONHECIMENTO, key=len, reverse=True)


def _curso_base(nome: str | None) -> str:
    texto = str(nome or "").upper().strip()
    for chave in COURSE_ANCHORS:
        if chave in texto:
            return chave
    return "OUTROS"


def _valor_por_fonte(
    coluna: str,
    fonte: str,
    alias: str,
) -> pl.Expr:
    return (
        pl.col(coluna).filter(pl.col("_fonte_avaliacao") == fonte).drop_nulls().first().alias(alias)
    )


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


def _parte_avaliacao(
    caminho: str,
    schema_silver: dict,
    coluna_ano: str,
    metricas: list[str],
    prefixo: str,
    prioridade: int,
) -> pl.DataFrame | None:
    if not Path(caminho).exists():
        return None

    df = ler_parquet(caminho)
    validar_colunas_obrigatorias_por_schema(
        df,
        schema_silver,
        f"Entrada Gold fact_avaliacao_curso_superior - {Path(caminho).name}",
        validar_tipos=True,
        permitir_extras=False,
    )

    colunas = [
        pl.col(coluna_ano).cast(pl.Int32, strict=False).alias("ano"),
        "codigo_ies",
        "codigo_curso",
        "codigo_area",
        "area_avaliacao",
        "grau_academico",
        "modalidade_ensino",
        "codigo_municipio",
        "municipio_curso",
        "uf",
        *metricas,
        pl.col("observacao").alias(f"observacao_{prefixo}"),
        pl.lit(prioridade, dtype=pl.Int8).alias("_prioridade"),
        pl.lit(prefixo.upper()).alias("_fonte_avaliacao"),
    ]
    return df.select(*colunas)


def _build_lookup_curso_censo(dim_curso: pl.DataFrame) -> pl.DataFrame:
    censo = ler_parquet(SILVER_CURSOS_SUPERIOR)
    validar_colunas_obrigatorias_por_schema(
        censo,
        SCHEMA_CURSOS_SUPERIOR_SILVER,
        "Lookup avaliacao -> curso via Censo Superior",
        validar_tipos=True,
        permitir_extras=False,
    )

    lookup_dim = dim_curso.select("id_curso_superior", *CHAVE_CURSO_SUPERIOR_GOLD)
    validar_chave_unica(lookup_dim, CHAVE_CURSO_SUPERIOR_GOLD, "Lookup reduzido dim_curso_superior")

    base = (
        censo.filter(pl.col("codigo_curso").is_not_null())
        .sort(
            ["codigo_ies", "codigo_curso", "ano_censo"],
            nulls_last=True,
        )
        .unique(
            subset=["codigo_ies", "codigo_curso"],
            keep="last",
            maintain_order=True,
        )
        .with_columns(
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
            pl.when(pl.col("tipo_curso").is_null() | (pl.col("tipo_curso") == ""))
            .then(
                pl.col("curso_base").replace_strict(
                    DE_PARA_AREA_CONHECIMENTO,
                    default=pl.lit("OUTROS"),
                    return_dtype=pl.String,
                )
            )
            .otherwise(pl.col("tipo_curso"))
            .alias("tipo_curso"),
        )
        .drop("_nivel_por_codigo")
        .join(
            lookup_dim,
            on=CHAVE_CURSO_SUPERIOR_GOLD,
            how="left",
        )
        .select(
            "codigo_ies",
            "codigo_curso",
            "id_curso_superior",
        )
    )

    orfaos = base.filter(pl.col("id_curso_superior").is_null())
    if not orfaos.is_empty():
        raise RuntimeError(
            "Falha interna ao construir lookup codigo_curso -> dim_curso_superior. "
            f"Amostra={orfaos.head(10).to_dicts()}"
        )

    return base


def executar() -> None:
    log.info("[GOLD] Construindo fact_avaliacao_curso_superior.")

    partes = [
        _parte_avaliacao(
            SILVER_CONCEITO_ENADE,
            SCHEMA_CONCEITO_ENADE_SILVER,
            "ano_enade",
            COLUNAS_METRICAS_ENADE,
            "enade",
            1,
        ),
        _parte_avaliacao(
            SILVER_CPC,
            SCHEMA_CPC_SILVER,
            "ano_cpc",
            COLUNAS_METRICAS_CPC,
            "cpc",
            2,
        ),
        _parte_avaliacao(
            SILVER_IDD,
            SCHEMA_IDD_SILVER,
            "ano_idd",
            COLUNAS_METRICAS_IDD,
            "idd",
            3,
        ),
    ]
    partes = [parte for parte in partes if parte is not None]

    if not partes:
        raise RuntimeError("Nenhuma base Silver de avaliacao de curso foi encontrada.")

    base = pl.concat(partes, how="diagonal_relaxed").sort(
        ["ano", "codigo_ies", "codigo_curso", "_prioridade"]
    )

    chave = [
        "ano",
        "codigo_ies",
        "codigo_curso",
    ]

    conflitos = (
        base.group_by(chave)
        .agg(
            pl.col("codigo_municipio").drop_nulls().n_unique().alias("qtd_municipios"),
            pl.col("codigo_area").drop_nulls().n_unique().alias("qtd_codigos_area"),
            pl.col("area_avaliacao").drop_nulls().n_unique().alias("qtd_areas"),
            pl.col("grau_academico").drop_nulls().n_unique().alias("qtd_graus"),
            pl.col("modalidade_ensino").drop_nulls().n_unique().alias("qtd_modalidades"),
            # --------------------------------------------------------------
            # ENADE
            # --------------------------------------------------------------
            _valor_por_fonte(
                "codigo_area",
                "ENADE",
                "codigo_area_enade",
            ),
            _valor_por_fonte(
                "area_avaliacao",
                "ENADE",
                "area_enade",
            ),
            _valor_por_fonte(
                "codigo_municipio",
                "ENADE",
                "codigo_municipio_enade",
            ),
            _valor_por_fonte(
                "municipio_curso",
                "ENADE",
                "municipio_enade",
            ),
            _valor_por_fonte(
                "uf",
                "ENADE",
                "uf_enade",
            ),
            _valor_por_fonte(
                "grau_academico",
                "ENADE",
                "grau_enade",
            ),
            _valor_por_fonte(
                "modalidade_ensino",
                "ENADE",
                "modalidade_enade",
            ),
            # --------------------------------------------------------------
            # CPC
            # --------------------------------------------------------------
            _valor_por_fonte(
                "codigo_area",
                "CPC",
                "codigo_area_cpc",
            ),
            _valor_por_fonte(
                "area_avaliacao",
                "CPC",
                "area_cpc",
            ),
            _valor_por_fonte(
                "codigo_municipio",
                "CPC",
                "codigo_municipio_cpc",
            ),
            _valor_por_fonte(
                "municipio_curso",
                "CPC",
                "municipio_cpc",
            ),
            _valor_por_fonte(
                "uf",
                "CPC",
                "uf_cpc",
            ),
            _valor_por_fonte(
                "grau_academico",
                "CPC",
                "grau_cpc",
            ),
            _valor_por_fonte(
                "modalidade_ensino",
                "CPC",
                "modalidade_cpc",
            ),
            # --------------------------------------------------------------
            # IDD
            # --------------------------------------------------------------
            _valor_por_fonte(
                "codigo_area",
                "IDD",
                "codigo_area_idd",
            ),
            _valor_por_fonte(
                "area_avaliacao",
                "IDD",
                "area_idd",
            ),
            _valor_por_fonte(
                "codigo_municipio",
                "IDD",
                "codigo_municipio_idd",
            ),
            _valor_por_fonte(
                "municipio_curso",
                "IDD",
                "municipio_idd",
            ),
            _valor_por_fonte(
                "uf",
                "IDD",
                "uf_idd",
            ),
            _valor_por_fonte(
                "grau_academico",
                "IDD",
                "grau_idd",
            ),
            _valor_por_fonte(
                "modalidade_ensino",
                "IDD",
                "modalidade_idd",
            ),
        )
        .with_columns(
            (pl.col("qtd_municipios") > 1).alias("diverge_municipio"),
            (pl.col("qtd_codigos_area") > 1).alias("diverge_codigo_area"),
            (pl.col("qtd_areas") > 1).alias("diverge_area"),
            (pl.col("qtd_graus") > 1).alias("diverge_grau"),
            (pl.col("qtd_modalidades") > 1).alias("diverge_modalidade"),
        )
        .filter(
            pl.col("diverge_municipio")
            | pl.col("diverge_codigo_area")
            | pl.col("diverge_area")
            | pl.col("diverge_grau")
            | pl.col("diverge_modalidade")
        )
        .sort(chave)
    )

    registrar_alerta(
        "gold_avaliacao_curso_descritores_brutos_divergentes",
        conflitos,
        "audit_gold_avaliacao_curso_descritores_brutos_divergentes.csv",
        "ENADE/CPC/IDD com descritores brutos divergentes para a mesma chave oficial",
        pipeline="educacao",
    )

    colunas_agregadas = [
        c
        for c in base.columns
        if c
        not in {
            *chave,
            "_prioridade",
            "_fonte_avaliacao",
        }
    ]

    avaliacao = base.group_by(chave, maintain_order=True).agg(
        *[pl.col(coluna).drop_nulls().first().alias(coluna) for coluna in colunas_agregadas]
    )

    dim_ies = ler_parquet(GOLD_DIM_IES)
    dim_curso = ler_parquet(GOLD_DIM_CURSO_SUPERIOR)
    dim_localidade = ler_parquet(GOLD_DIM_LOCALIDADE)

    validar_colunas_obrigatorias_por_schema(
        dim_ies,
        SCHEMA_DIM_IES,
        "Entrada avaliacao - dim_ies",
        validar_tipos=True,
        permitir_extras=False,
    )
    validar_colunas_obrigatorias_por_schema(
        dim_curso,
        SCHEMA_DIM_CURSO_SUPERIOR,
        "Entrada avaliacao - dim_curso_superior",
        validar_tipos=True,
        permitir_extras=False,
    )
    validar_colunas_obrigatorias_por_schema(
        dim_localidade,
        SCHEMA_DIM_LOCALIDADE,
        "Entrada avaliacao - dim_localidade",
        validar_tipos=True,
        permitir_extras=False,
    )

    avaliacao = avaliacao.join(dim_ies.select("codigo_ies", "id_ies"), on="codigo_ies", how="left")
    _validar_join(
        avaliacao,
        "id_ies",
        ["codigo_ies"],
        "gold_avaliacao_curso_ies",
        "audit_gold_avaliacao_curso_sem_ies.csv",
        "ENADE/CPC/IDD -> dim_ies",
    )

    lookup_codigo_curso = _build_lookup_curso_censo(dim_curso)
    avaliacao = avaliacao.join(
        lookup_codigo_curso,
        on=["codigo_ies", "codigo_curso"],
        how="left",
    )

    # Fallback apenas para cursos avaliados que nao possuem codigo_curso localizado
    # no historico do Censo. Usa os descritores da avaliacao para localizar um curso
    # analitico ja existente, sem criar curso artificial na dimensao.
    sem_curso = avaliacao.filter(pl.col("id_curso_superior").is_null())
    if not sem_curso.is_empty():
        lookup_dim = dim_curso.select("id_curso_superior", *CHAVE_CURSO_SUPERIOR_GOLD)
        fallback = (
            sem_curso.select(
                "ano",
                "codigo_ies",
                "codigo_curso",
                "area_avaliacao",
                "grau_academico",
                "modalidade_ensino",
            )
            .with_columns(
                pl.col("area_avaliacao")
                .cast(pl.String)
                .str.to_uppercase()
                .str.strip_chars()
                .alias("nome_curso"),
                pl.col("area_avaliacao")
                .map_elements(
                    _curso_base,
                    return_dtype=pl.String,
                    skip_nulls=False,
                )
                .alias("curso_base"),
                pl.col("grau_academico")
                .cast(pl.String)
                .str.to_uppercase()
                .str.strip_chars()
                .replace_strict(
                    MAPA_GRAU_ACADEMICO_TEXTO,
                    default=pl.lit("OUTRO"),
                    return_dtype=pl.String,
                )
                .alias("grau_curso"),
                pl.col("modalidade_ensino")
                .cast(pl.String)
                .str.to_uppercase()
                .str.strip_chars()
                .replace_strict(
                    MAPA_MODALIDADE_ENSINO_TEXTO,
                    default=pl.lit("OUTRA"),
                    return_dtype=pl.String,
                )
                .alias("modalidade_curso"),
                pl.lit("GRADUAÇÃO").alias("nivel_ensino"),
            )
            .with_columns(
                pl.col("curso_base")
                .replace_strict(
                    DE_PARA_AREA_CONHECIMENTO,
                    default=pl.lit("OUTROS"),
                    return_dtype=pl.String,
                )
                .alias("tipo_curso")
            )
            .join(lookup_dim, on=CHAVE_CURSO_SUPERIOR_GOLD, how="left")
            .select(
                "ano",
                "codigo_ies",
                "codigo_curso",
                pl.col("id_curso_superior").alias("id_curso_superior_fallback"),
            )
        )

        avaliacao = (
            avaliacao.join(fallback, on=["ano", "codigo_ies", "codigo_curso"], how="left")
            .with_columns(
                pl.coalesce(
                    [
                        pl.col("id_curso_superior"),
                        pl.col("id_curso_superior_fallback"),
                    ]
                ).alias("id_curso_superior")
            )
            .drop("id_curso_superior_fallback")
        )

    _validar_join(
        avaliacao,
        "id_curso_superior",
        [
            "ano",
            "codigo_ies",
            "codigo_curso",
            "area_avaliacao",
            "grau_academico",
            "modalidade_ensino",
        ],
        "gold_avaliacao_curso_dim_curso",
        "audit_gold_avaliacao_curso_sem_dim_curso.csv",
        "ENADE/CPC/IDD -> dim_curso_superior",
    )

    avaliacao = avaliacao.join(
        dim_localidade.select("codigo_municipio", "id_localidade"),
        on="codigo_municipio",
        how="left",
    )
    _validar_join(
        avaliacao,
        "id_localidade",
        ["codigo_municipio", "municipio_curso", "uf"],
        "gold_avaliacao_curso_localidade",
        "audit_gold_avaliacao_curso_sem_localidade.csv",
        "ENADE/CPC/IDD -> dim_localidade",
    )

    fato = avaliacao.with_columns(
        pl.col("ano").cast(pl.Int32).alias("id_calendario"),
        pl.col("codigo_curso").alias("codigo_curso_avaliado"),
        pl.col("grau_academico").alias("grau_academico_avaliacao"),
        pl.col("modalidade_ensino").alias("modalidade_ensino_avaliacao"),
    )

    fato = tipar_e_projetar_por_schema(
        fato,
        SCHEMA_FACT_AVALIACAO_CURSO_SUPERIOR,
        "Gold fact_avaliacao_curso_superior",
    )
    validar_chave_unica(
        fato,
        CHAVE_FACT_AVALIACAO_CURSO_SUPERIOR,
        "Gold fact_avaliacao_curso_superior",
    )

    gravar_parquet(GOLD_FACT_AVALIACAO_CURSO_SUPERIOR, fato)

    log.info(
        "[GOLD] fact_avaliacao_curso_superior salva em %s (%s linhas).",
        GOLD_FACT_AVALIACAO_CURSO_SUPERIOR,
        f"{fato.height:,}",
    )


if __name__ == "__main__":
    executar()
