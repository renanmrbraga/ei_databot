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
    BRONZE_IES,
    SILVER_IES,
)
from etl.educacao.mapping import CORRECAO_MUNICIPIOS
from etl.educacao.schema import (
    CHAVE_IES_ANO,
    SCHEMA_IES_BRONZE,
    SCHEMA_IES_SILVER,
)
from health.health_etl import registrar_alerta

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
    log.info("[SILVER] Iniciando Censo Superior - IES.")

    if not Path(BRONZE_IES).exists():
        raise FileNotFoundError(f"Bronze IES nao encontrado: {BRONZE_IES}")

    df = ler_parquet(BRONZE_IES)

    # ==========================================================================
    # VALIDACAO DA ENTRADA
    # ==========================================================================

    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_IES_BRONZE,
        "Entrada Silver Censo Superior - IES",
        validar_tipos=True,
        permitir_extras=False,
    )

    # ==========================================================================
    # TIPAGEM E LIMPEZA INICIAL
    # ==========================================================================

    df = df.with_columns(
        pl.col("ano_censo")
        .cast(
            pl.Int32,
            strict=False,
        )
        .alias("ano_censo"),
        pl.col("codigo_ies")
        .cast(
            pl.Int64,
            strict=False,
        )
        .alias("codigo_ies"),
        pl.col("nome_ies").cast(pl.String).str.strip_chars().alias("nome_ies"),
        pl.col("sigla_ies").cast(pl.String).str.strip_chars().str.to_uppercase().alias("sigla_ies"),
        pl.col("mantenedora").cast(pl.String).str.strip_chars().alias("mantenedora"),
        pl.col("municipio_ies").cast(pl.String).str.strip_chars().alias("municipio_ies"),
        pl.col("uf_ies").cast(pl.String).str.strip_chars().str.to_uppercase().alias("uf_ies"),
    )

    # ==========================================================================
    # SIGLAS COMPARTILHADAS
    # ==========================================================================

    df_ultimas = (
        df.sort("ano_censo")
        .unique(
            subset=[
                "codigo_ies",
            ],
            keep="last",
            maintain_order=True,
        )
        .select(
            "codigo_ies",
            "nome_ies",
            "sigla_ies",
        )
    )

    siglas_compartilhadas = (
        df_ultimas.filter(
            pl.col("sigla_ies").is_not_null() & (pl.col("sigla_ies").str.strip_chars() != "")
        )
        .group_by("sigla_ies")
        .agg(pl.col("codigo_ies").n_unique().alias("qtd_ids"))
        .filter(pl.col("qtd_ids") > 1)
        .select("sigla_ies")
    )

    df_siglas_compartilhadas = (
        df_ultimas.join(
            siglas_compartilhadas,
            on="sigla_ies",
            how="semi",
        )
        .rename(
            {
                "sigla_ies": "sigla_ies_final",
                "nome_ies": "nome_ies_final",
            }
        )
        .select(
            "sigla_ies_final",
            "codigo_ies",
            "nome_ies_final",
        )
        .sort(
            [
                "sigla_ies_final",
                "codigo_ies",
            ]
        )
    )

    registrar_alerta(
        "silver_ies_siglas_compartilhadas",
        df_siglas_compartilhadas,
        "audit_ies_siglas_compartilhadas.csv",
        "Siglas utilizadas por mais de um codigo_ies; ocorrencia informativa",
        pipeline="educacao",
    )

    # ==========================================================================
    # CHAVES NORMALIZADAS
    # ==========================================================================

    df = df.with_columns(
        normalizar_texto_chave_expr("nome_ies").alias("chave_ies_normalizada"),
        normalizar_texto_chave_expr("municipio_ies").alias("chave_cidade_normalizada"),
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
        SCHEMA_IES_SILVER,
        "Silver Censo Superior - IES",
    )

    # ==========================================================================
    # INTEGRIDADE
    # ==========================================================================

    validar_chave_unica(
        df,
        CHAVE_IES_ANO,
        "Silver Censo Superior - IES",
    )

    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_IES_SILVER,
        "Saida Silver Censo Superior - IES",
        validar_tipos=True,
        permitir_extras=False,
    )

    # ==========================================================================
    # SAIDA
    # ==========================================================================

    gravar_parquet(SILVER_IES, df)

    log.info(
        "[SILVER] Censo Superior - IES concluido | linhas=%s | saida=%s",
        f"{df.height:,}",
        SILVER_IES,
    )


if __name__ == "__main__":
    executar()
