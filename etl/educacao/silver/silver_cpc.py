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
    BRONZE_CPC,
    SILVER_CPC,
    SILVER_GEO,
)
from etl.educacao.mapping import (
    CORRECAO_MUNICIPIOS,
    MAPA_AREA_AVALIACAO_POR_CODIGO,
)
from etl.educacao.schema import (
    CHAVE_CPC,
    SCHEMA_CPC_BRONZE,
    SCHEMA_CPC_SILVER,
    SCHEMA_GEO_SILVER,
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
    log.info("[SILVER] Iniciando CPC.")

    if not Path(BRONZE_CPC).exists():
        raise FileNotFoundError(f"Bronze CPC nao encontrado: {BRONZE_CPC}")

    df = ler_parquet(BRONZE_CPC)

    # ==========================================================================
    # VALIDACAO DA ENTRADA
    # ==========================================================================

    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_CPC_BRONZE,
        "Entrada Silver CPC",
        validar_tipos=True,
        permitir_extras=False,
    )

    # ==========================================================================
    # TIPAGEM E LIMPEZA BASE
    # ==========================================================================

    df = df.with_columns(
        pl.col("ano_cpc")
        .cast(
            pl.Int32,
            strict=False,
        )
        .alias("ano_cpc"),
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
        pl.col("nome_ies").cast(pl.String).str.strip_chars().alias("nome_ies"),
        pl.col("codigo_area")
        .cast(
            pl.Int64,
            strict=False,
        )
        .alias("codigo_area"),
        pl.col("sigla_ies").cast(pl.String).str.strip_chars().alias("sigla_ies"),
        pl.col("municipio_curso").cast(pl.String).str.strip_chars().alias("municipio_curso"),
        pl.col("uf").cast(pl.String).str.strip_chars().str.to_uppercase().alias("uf"),
        pl.col("area_avaliacao").cast(pl.String).str.strip_chars().alias("area_avaliacao"),
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
    # VALIDACAO E CORRECAO DO CODIGO MUNICIPAL PELA GEO
    # ==========================================================================

    geo = ler_parquet(SILVER_GEO)

    validar_colunas_obrigatorias_por_schema(
        geo,
        SCHEMA_GEO_SILVER,
        "Lookup Silver CPC - silver_geo",
        validar_tipos=True,
        permitir_extras=False,
    )

    lookup_geo_base = geo.select(
        pl.col("municipio_normalizado").alias("chave_cidade_normalizada"),
        "uf",
        pl.col("codigo_municipio").alias("_codigo_municipio_geo"),
    ).drop_nulls(
        subset=[
            "chave_cidade_normalizada",
            "uf",
            "_codigo_municipio_geo",
        ]
    )

    conflitos_geo = (
        lookup_geo_base.group_by(
            [
                "chave_cidade_normalizada",
                "uf",
            ]
        )
        .agg(
            pl.col("_codigo_municipio_geo").n_unique().alias("qtd_codigos_municipio"),
            pl.col("_codigo_municipio_geo").unique().sort().alias("codigos_municipio"),
        )
        .filter(pl.col("qtd_codigos_municipio") > 1)
    )

    registrar_alerta(
        "silver_cpc_geo_chave_municipio_ambigua",
        conflitos_geo,
        "audit_silver_cpc_geo_chave_municipio_ambigua.csv",
        "Chaves municipio/UF da GEO associadas a mais de um codigo municipal",
        pipeline="educacao",
    )

    if not conflitos_geo.is_empty():
        raise RuntimeError(
            "Silver CPC: chave municipio/UF ambigua na GEO. "
            f"Amostra={conflitos_geo.head(10).to_dicts()}"
        )

    lookup_geo = lookup_geo_base.unique(
        subset=[
            "chave_cidade_normalizada",
            "uf",
        ],
        keep="first",
        maintain_order=True,
    )

    df = df.with_columns(pl.col("codigo_municipio").alias("_codigo_municipio_origem")).join(
        lookup_geo,
        on=[
            "chave_cidade_normalizada",
            "uf",
        ],
        how="left",
    )

    tem_localizacao = (
        pl.col("chave_cidade_normalizada").is_not_null()
        & (pl.col("chave_cidade_normalizada") != "")
        & pl.col("uf").is_not_null()
        & (pl.col("uf") != "")
    )

    sem_geo = (
        df.filter(tem_localizacao & pl.col("_codigo_municipio_geo").is_null())
        .select(
            "ano_cpc",
            "codigo_ies",
            "codigo_curso",
            "municipio_curso",
            "uf",
            "chave_cidade_normalizada",
            "_codigo_municipio_origem",
        )
        .unique()
    )

    registrar_alerta(
        "silver_cpc_municipio_sem_geo",
        sem_geo,
        "audit_silver_cpc_municipio_sem_geo.csv",
        "Municipios do CPC sem correspondencia na base GEO",
        pipeline="educacao",
    )

    if not sem_geo.is_empty():
        raise RuntimeError(
            "Silver CPC: municipio(s) sem correspondencia na GEO. "
            f"Amostra={sem_geo.head(10).to_dicts()}"
        )

    corrigidos = (
        df.filter(
            pl.col("_codigo_municipio_geo").is_not_null()
            & (
                pl.col("_codigo_municipio_origem").is_null()
                | (pl.col("_codigo_municipio_origem") != pl.col("_codigo_municipio_geo"))
            )
        )
        .select(
            "ano_cpc",
            "codigo_ies",
            "codigo_curso",
            "municipio_curso",
            "uf",
            pl.col("_codigo_municipio_origem").alias("codigo_municipio_origem"),
            pl.col("_codigo_municipio_geo").alias("codigo_municipio_corrigido"),
        )
        .unique()
        .sort(
            [
                "ano_cpc",
                "codigo_ies",
                "codigo_curso",
            ]
        )
    )

    registrar_alerta(
        "silver_cpc_codigo_municipio_corrigido",
        corrigidos,
        "audit_silver_cpc_codigo_municipio_corrigido.csv",
        "Codigos municipais do CPC corrigidos pela chave municipio/UF da GEO",
        pipeline="educacao",
    )

    df = df.with_columns(
        pl.coalesce(
            [
                pl.col("_codigo_municipio_geo"),
                pl.col("_codigo_municipio_origem"),
            ]
        )
        .cast(pl.Int64)
        .alias("codigo_municipio")
    ).drop(
        "_codigo_municipio_origem",
        "_codigo_municipio_geo",
    )

    # ==========================================================================
    # CONTRATO SILVER
    # ==========================================================================

    df = tipar_e_projetar_por_schema(
        df,
        SCHEMA_CPC_SILVER,
        "Silver CPC",
    )

    # ==========================================================================
    # INTEGRIDADE
    # ==========================================================================

    validar_chave_unica(
        df,
        CHAVE_CPC,
        "Silver CPC",
    )

    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_CPC_SILVER,
        "Saida Silver CPC",
        validar_tipos=True,
        permitir_extras=False,
    )

    # ==========================================================================
    # SAIDA
    # ==========================================================================

    gravar_parquet(SILVER_CPC, df)

    log.info(
        "[SILVER] CPC concluido | linhas=%s | saida=%s",
        f"{df.height:,}",
        SILVER_CPC,
    )


if __name__ == "__main__":
    executar()
