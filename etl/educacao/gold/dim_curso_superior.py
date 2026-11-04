from __future__ import annotations

from pathlib import Path

import polars as pl

from etl.core.common import (
    gravar_parquet,
    ler_parquet,
    obter_cor_por_dicionario_ou_hash,
    tipar_e_projetar_por_schema,
    validar_chave_unica,
    validar_colunas_obrigatorias_por_schema,
)
from etl.core.logger import get_logger
from etl.educacao.config import (
    CURSOS_PORTFOLIO_DETALHADO,
    GOLD_DIM_CURSO_SUPERIOR,
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
    REGRA_CORES_CURSOS,
)
from etl.educacao.schema import (
    CHAVE_CURSO_SUPERIOR_GOLD,
    SCHEMA_CONCEITO_ENADE_SILVER,
    SCHEMA_CPC_SILVER,
    SCHEMA_CURSOS_SUPERIOR_SILVER,
    SCHEMA_DIM_CURSO_SUPERIOR,
    SCHEMA_IDD_SILVER,
)

log = get_logger(pipeline="educacao")

COURSE_ANCHORS = sorted(DE_PARA_AREA_CONHECIMENTO, key=len, reverse=True)
PORTFOLIO_CURSO = {
    (nome.upper().strip(), grau.upper().strip(), modalidade.upper().strip())
    for nome, grau, modalidade, _turno in CURSOS_PORTFOLIO_DETALHADO
}


def _curso_base(nome: str | None) -> str:
    if nome is None:
        return "OUTROS"

    nome_upper = str(nome).upper().strip()
    for chave in COURSE_ANCHORS:
        if chave in nome_upper:
            return chave

    return "OUTROS"


def _oferta_curso(row: dict[str, object]) -> str:
    chave = (
        str(row.get("nome_curso") or "").upper().strip(),
        str(row.get("grau_curso") or "").upper().strip(),
        str(row.get("modalidade_curso") or "").upper().strip(),
    )
    return "Sim" if chave in PORTFOLIO_CURSO else "Não"


def _cor(value: str | None) -> str:
    return obter_cor_por_dicionario_ou_hash(value, REGRA_CORES_CURSOS, salt="curso")[0]


def _hex(value: str | None) -> str:
    return obter_cor_por_dicionario_ou_hash(value, REGRA_CORES_CURSOS, salt="curso")[1]


def _build_censo_candidates(censo: pl.DataFrame) -> pl.DataFrame:
    return (
        censo.select(
            pl.col("tipo_curso").cast(pl.String).str.strip_chars().alias("tipo_curso"),
            pl.col("curso_base").cast(pl.String).str.strip_chars().alias("curso_base"),
            pl.col("nome_curso_referencia")
            .cast(pl.String)
            .str.to_uppercase()
            .str.strip_chars()
            .alias("nome_curso"),
            "codigo_grau_academico",
            "codigo_modalidade_ensino",
            "codigo_nivel_academico",
        )
        .drop_nulls(subset=["nome_curso"])
        .with_columns(
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
        .select(
            "tipo_curso",
            "curso_base",
            "nome_curso",
            "grau_curso",
            "modalidade_curso",
            "nivel_ensino",
        )
        .unique()
    )


def _parte_avaliacao(
    caminho: str,
    schema_silver: dict,
    coluna_ano: str,
    prioridade: int,
) -> pl.DataFrame | None:
    if not Path(caminho).exists():
        return None

    df = ler_parquet(caminho)
    validar_colunas_obrigatorias_por_schema(
        df,
        schema_silver,
        f"Entrada Gold dim_curso_superior - {Path(caminho).name}",
        validar_tipos=True,
        permitir_extras=False,
    )

    return df.select(
        pl.col(coluna_ano).cast(pl.Int32, strict=False).alias("ano"),
        "codigo_ies",
        "codigo_curso",
        "area_avaliacao",
        "grau_academico",
        "modalidade_ensino",
        pl.lit(prioridade, dtype=pl.Int8).alias("_prioridade"),
    )


def _build_avaliacao_candidates() -> pl.DataFrame | None:
    partes = [
        _parte_avaliacao(
            SILVER_CONCEITO_ENADE,
            SCHEMA_CONCEITO_ENADE_SILVER,
            "ano_enade",
            1,
        ),
        _parte_avaliacao(
            SILVER_CPC,
            SCHEMA_CPC_SILVER,
            "ano_cpc",
            2,
        ),
        _parte_avaliacao(
            SILVER_IDD,
            SCHEMA_IDD_SILVER,
            "ano_idd",
            3,
        ),
    ]
    partes = [parte for parte in partes if parte is not None]

    if not partes:
        return None

    chave_oficial = ["ano", "codigo_ies", "codigo_curso"]

    avaliacao = (
        pl.concat(partes, how="diagonal_relaxed")
        .sort([*chave_oficial, "_prioridade"])
        .group_by(chave_oficial, maintain_order=True)
        .agg(
            pl.col("area_avaliacao").drop_nulls().first().alias("area_avaliacao"),
            pl.col("grau_academico").drop_nulls().first().alias("grau_academico"),
            pl.col("modalidade_ensino").drop_nulls().first().alias("modalidade_ensino"),
        )
        .drop_nulls(subset=["area_avaliacao"])
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
        .select(
            "tipo_curso",
            "curso_base",
            "nome_curso",
            "grau_curso",
            "modalidade_curso",
            "nivel_ensino",
        )
        .unique()
    )

    return avaliacao


def executar() -> None:
    log.info("[GOLD] Construindo dim_curso_superior.")

    censo = ler_parquet(SILVER_CURSOS_SUPERIOR)
    validar_colunas_obrigatorias_por_schema(
        censo,
        SCHEMA_CURSOS_SUPERIOR_SILVER,
        "Entrada Gold dim_curso_superior - silver_superior_cursos",
        validar_tipos=True,
        permitir_extras=False,
    )

    partes = [_build_censo_candidates(censo)]

    avaliacao = _build_avaliacao_candidates()
    if avaliacao is not None and not avaliacao.is_empty():
        partes.append(avaliacao)

    dim = (
        pl.concat(partes, how="diagonal_relaxed")
        .unique()
        .sort(
            [
                "tipo_curso",
                "curso_base",
                "nome_curso",
                "grau_curso",
                "modalidade_curso",
                "nivel_ensino",
            ]
        )
        .with_row_index("id_curso_superior", offset=1)
    )

    dim = dim.with_columns(
        pl.concat_str([pl.col("nome_curso"), pl.lit(" - "), pl.col("modalidade_curso")]).alias(
            "rotulo_curso"
        ),
        pl.col("tipo_curso")
        .map_elements(_cor, return_dtype=pl.String, skip_nulls=False)
        .alias("cor_curso"),
        pl.col("tipo_curso")
        .map_elements(_hex, return_dtype=pl.String, skip_nulls=False)
        .alias("hex_curso"),
        pl.struct(["nome_curso", "grau_curso", "modalidade_curso"])
        .map_elements(_oferta_curso, return_dtype=pl.String, skip_nulls=False)
        .alias("oferta_curso"),
    )

    dim = tipar_e_projetar_por_schema(
        dim,
        SCHEMA_DIM_CURSO_SUPERIOR,
        "Gold dim_curso_superior",
    )
    validar_chave_unica(dim, CHAVE_CURSO_SUPERIOR_GOLD, "Gold dim_curso_superior")

    gravar_parquet(GOLD_DIM_CURSO_SUPERIOR, dim)

    log.info(
        "[GOLD] dim_curso_superior salva em %s (%s cursos analiticos).",
        GOLD_DIM_CURSO_SUPERIOR,
        f"{dim.height:,}",
    )


if __name__ == "__main__":
    executar()
