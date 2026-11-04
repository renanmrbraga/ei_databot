from __future__ import annotations

from pathlib import Path

import polars as pl

from etl.core.common import (
    gravar_parquet,
    ler_parquet,
    normalizar_texto_chave_expr,
    tipar_e_projetar_por_schema,
    validar_chave_unica,
    validar_colunas_obrigatorias_por_schema,
)
from etl.core.logger import get_logger
from etl.educacao.config import BRONZE_GEO, SILVER_GEO
from etl.educacao.mapping import UF_CODIGO_PARA_SIGLA
from etl.educacao.schema import (
    CHAVE_GEO,
    SCHEMA_GEO_BRONZE,
    SCHEMA_GEO_SILVER,
)

log = get_logger(pipeline="educacao")


def _uf_from_code(
    value: int | None,
) -> str | None:
    if value is None:
        return None

    return UF_CODIGO_PARA_SIGLA.get(value)


def executar() -> None:
    log.info("[SILVER] Iniciando Base Geografica.")

    if not Path(BRONZE_GEO).exists():
        raise FileNotFoundError(f"Bronze GEO nao encontrado: {BRONZE_GEO}")

    df = ler_parquet(BRONZE_GEO)

    # ==========================================================================
    # VALIDACAO DA ENTRADA
    # ==========================================================================

    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_GEO_BRONZE,
        "Entrada Silver GEO",
        validar_tipos=True,
        permitir_extras=False,
    )

    # ==========================================================================
    # TIPAGEM E LIMPEZA
    # ==========================================================================

    df = df.with_columns(
        pl.col("codigo_municipio")
        .cast(
            pl.Int64,
            strict=False,
        )
        .alias("codigo_municipio"),
        pl.col("codigo_uf")
        .cast(
            pl.Int32,
            strict=False,
        )
        .alias("codigo_uf"),
        pl.col("municipio").cast(pl.String).str.strip_chars().alias("municipio"),
        pl.col("latitude")
        .cast(
            pl.Float64,
            strict=False,
        )
        .alias("latitude"),
        pl.col("longitude")
        .cast(
            pl.Float64,
            strict=False,
        )
        .alias("longitude"),
    )

    # ==========================================================================
    # CAMPOS DERIVADOS
    # ==========================================================================

    df = df.with_columns(
        normalizar_texto_chave_expr("municipio").alias("municipio_normalizado"),
        pl.col("codigo_uf")
        .map_elements(
            _uf_from_code,
            return_dtype=pl.String,
            skip_nulls=False,
        )
        .alias("uf"),
    )

    # ==========================================================================
    # CONTRATO SILVER
    # ==========================================================================

    df = tipar_e_projetar_por_schema(
        df,
        SCHEMA_GEO_SILVER,
        "Silver GEO",
    )

    # ==========================================================================
    # INTEGRIDADE
    # ==========================================================================

    validar_chave_unica(
        df,
        CHAVE_GEO,
        "Silver GEO",
    )

    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_GEO_SILVER,
        "Saida Silver GEO",
        validar_tipos=True,
        permitir_extras=False,
    )

    # ==========================================================================
    # SAIDA
    # ==========================================================================

    gravar_parquet(SILVER_GEO, df)

    log.info(
        "[SILVER] Base Geografica concluida | linhas=%s | saida=%s",
        f"{df.height:,}",
        SILVER_GEO,
    )


if __name__ == "__main__":
    executar()
