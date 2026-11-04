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
from etl.educacao.config import (
    BRONZE_IGC,
    SILVER_IGC,
)
from etl.educacao.schema import (
    CHAVE_IGC,
    SCHEMA_IGC_BRONZE,
    SCHEMA_IGC_SILVER,
)

log = get_logger(pipeline="educacao")


def executar() -> None:
    log.info("[SILVER] Iniciando IGC.")

    if not Path(BRONZE_IGC).exists():
        raise FileNotFoundError(f"Bronze IGC nao encontrado: {BRONZE_IGC}")

    df = ler_parquet(BRONZE_IGC)

    # ==========================================================================
    # VALIDACAO DA ENTRADA
    # ==========================================================================

    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_IGC_BRONZE,
        "Entrada Silver IGC",
        validar_tipos=True,
        permitir_extras=False,
    )

    # ==========================================================================
    # TIPAGEM E LIMPEZA BASE
    # ==========================================================================

    df = df.with_columns(
        pl.col("ano_igc")
        .cast(
            pl.Int32,
            strict=False,
        )
        .alias("ano_igc"),
        pl.col("codigo_ies")
        .cast(
            pl.Int64,
            strict=False,
        )
        .alias("codigo_ies"),
        pl.col("nome_ies").cast(pl.String).str.strip_chars().alias("nome_ies"),
        pl.col("sigla_ies").cast(pl.String).str.strip_chars().alias("sigla_ies"),
        pl.col("organizacao_academica")
        .cast(pl.String)
        .str.strip_chars()
        .alias("organizacao_academica"),
        pl.col("categoria_administrativa")
        .cast(pl.String)
        .str.strip_chars()
        .alias("categoria_administrativa"),
        pl.col("uf").cast(pl.String).str.strip_chars().str.to_uppercase().alias("uf"),
    )

    # ==========================================================================
    # CHAVE NORMALIZADA
    # ==========================================================================

    df = df.with_columns(normalizar_texto_chave_expr("nome_ies").alias("chave_ies_normalizada"))

    # ==========================================================================
    # CONTRATO SILVER
    # ==========================================================================

    df = tipar_e_projetar_por_schema(
        df,
        SCHEMA_IGC_SILVER,
        "Silver IGC",
    )

    # ==========================================================================
    # INTEGRIDADE
    # ==========================================================================

    validar_chave_unica(
        df,
        CHAVE_IGC,
        "Silver IGC",
    )

    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_IGC_SILVER,
        "Saida Silver IGC",
        validar_tipos=True,
        permitir_extras=False,
    )

    # ==========================================================================
    # SAIDA
    # ==========================================================================

    gravar_parquet(SILVER_IGC, df)

    log.info(
        "[SILVER] IGC concluido | linhas=%s | saida=%s",
        f"{df.height:,}",
        SILVER_IGC,
    )


if __name__ == "__main__":
    executar()
