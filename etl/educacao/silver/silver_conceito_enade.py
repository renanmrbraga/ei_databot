from __future__ import annotations

from pathlib import Path

import polars as pl

from etl.core.common import (
    gravar_parquet,
    ler_parquet,
    normalizar_texto_chave_expr,
    padronizar_texto_por_codigo_expr,
    tipar_e_projetar_por_schema,
    validar_chave_unica,
    validar_colunas_obrigatorias_por_schema,
)
from etl.core.logger import get_logger
from etl.educacao.config import (
    BRONZE_CONCEITO_ENADE,
    SILVER_CONCEITO_ENADE,
)
from etl.educacao.mapping import (
    CORRECAO_MUNICIPIOS,
    MAPA_AREA_AVALIACAO_POR_CODIGO,
)
from etl.educacao.schema import (
    CHAVE_ENADE,
    SCHEMA_CONCEITO_ENADE_BRONZE,
    SCHEMA_CONCEITO_ENADE_SILVER,
)

log = get_logger(pipeline="educacao")


def _corrigir_municipio(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return CORRECAO_MUNICIPIOS.get(
        value,
        value,
    )


def executar() -> None:
    log.info("[SILVER] Iniciando Conceito Enade.")

    if not Path(BRONZE_CONCEITO_ENADE).exists():
        raise FileNotFoundError(f"Bronze Conceito Enade nao encontrado: {BRONZE_CONCEITO_ENADE}")

    df = ler_parquet(BRONZE_CONCEITO_ENADE)

    # ==========================================================================
    # VALIDACAO DA ENTRADA
    # ==========================================================================

    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_CONCEITO_ENADE_BRONZE,
        "Entrada Silver Conceito Enade",
        validar_tipos=True,
        permitir_extras=False,
    )

    # ==========================================================================
    # TIPAGEM E LIMPEZA BASE
    # ==========================================================================

    df = df.with_columns(
        pl.col("ano_enade")
        .cast(
            pl.Int32,
            strict=False,
        )
        .alias("ano_enade"),
        pl.col("codigo_area")
        .cast(
            pl.Int64,
            strict=False,
        )
        .alias("codigo_area"),
        pl.col("codigo_ies")
        .cast(
            pl.Int64,
            strict=False,
        )
        .alias("codigo_ies"),
        pl.col("codigo_curso")
        .cast(
            pl.Int64,
            strict=False,
        )
        .alias("codigo_curso"),
        pl.col("codigo_municipio")
        .cast(
            pl.Int64,
            strict=False,
        )
        .alias("codigo_municipio"),
        pl.col("area_avaliacao").cast(pl.String).str.strip_chars().alias("area_avaliacao"),
        pl.col("nome_ies").cast(pl.String).str.strip_chars().alias("nome_ies"),
        pl.col("sigla_ies").cast(pl.String).str.strip_chars().alias("sigla_ies"),
        pl.col("municipio_curso").cast(pl.String).str.strip_chars().alias("municipio_curso"),
        pl.col("uf").cast(pl.String).str.strip_chars().str.to_uppercase().alias("uf"),
    )

    df = df.with_columns(
        padronizar_texto_por_codigo_expr(
            "codigo_area",
            "area_avaliacao",
            MAPA_AREA_AVALIACAO_POR_CODIGO,
        ).alias("area_avaliacao")
    )

    # ==========================================================================
    # CHAVES NORMALIZADAS
    # ==========================================================================

    df = df.with_columns(
        normalizar_texto_chave_expr("nome_ies").alias("chave_ies_normalizada"),
        normalizar_texto_chave_expr("municipio_curso").alias("chave_cidade_normalizada"),
    )

    if CORRECAO_MUNICIPIOS:
        df = df.with_columns(
            pl.col("chave_cidade_normalizada")
            .map_elements(
                _corrigir_municipio,
                return_dtype=pl.String,
                skip_nulls=False,
            )
            .alias("chave_cidade_normalizada")
        )

    # ==========================================================================
    # CONTRATO SILVER
    # ==========================================================================

    df = tipar_e_projetar_por_schema(
        df,
        SCHEMA_CONCEITO_ENADE_SILVER,
        "Silver Conceito Enade",
    )

    # ==========================================================================
    # INTEGRIDADE
    # ==========================================================================

    validar_chave_unica(
        df,
        CHAVE_ENADE,
        "Silver Conceito Enade",
    )

    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_CONCEITO_ENADE_SILVER,
        "Saida Silver Conceito Enade",
        validar_tipos=True,
        permitir_extras=False,
    )

    # ==========================================================================
    # SAIDA
    # ==========================================================================

    gravar_parquet(SILVER_CONCEITO_ENADE, df)

    log.info(
        "[SILVER] Conceito Enade concluido | linhas=%s | saida=%s",
        f"{df.height:,}",
        SILVER_CONCEITO_ENADE,
    )


if __name__ == "__main__":
    executar()
