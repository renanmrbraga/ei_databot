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
from etl.educacao.config import GOLD_DIM_IES, GOLD_FACT_AVALIACAO_IES, SILVER_IGC
from etl.educacao.schema import (
    CHAVE_FACT_AVALIACAO_IES,
    SCHEMA_DIM_IES,
    SCHEMA_FACT_AVALIACAO_IES,
    SCHEMA_IGC_SILVER,
)
from health.health_etl import registrar_alerta

log = get_logger(pipeline="educacao")


def executar() -> None:
    log.info("[GOLD] Construindo fact_avaliacao_ies.")

    igc = ler_parquet(SILVER_IGC)
    dim_ies = ler_parquet(GOLD_DIM_IES)

    validar_colunas_obrigatorias_por_schema(
        igc,
        SCHEMA_IGC_SILVER,
        "Entrada Gold fact_avaliacao_ies - silver_igc",
        validar_tipos=True,
        permitir_extras=False,
    )
    validar_colunas_obrigatorias_por_schema(
        dim_ies,
        SCHEMA_DIM_IES,
        "Entrada Gold fact_avaliacao_ies - dim_ies",
        validar_tipos=True,
        permitir_extras=False,
    )

    lookup_ies = dim_ies.select("codigo_ies", "id_ies")
    validar_chave_unica(lookup_ies, ["codigo_ies"], "Lookup fact_avaliacao_ies -> dim_ies")

    base = igc.join(
        lookup_ies,
        on="codigo_ies",
        how="left",
    )

    chaves_orfas = (
        base.filter(pl.col("id_ies").is_null())
        .select(
            "ano_igc",
            "codigo_ies",
            "nome_ies",
            "sigla_ies",
            "chave_ies_normalizada",
        )
        .unique()
        .sort(["ano_igc", "codigo_ies"], nulls_last=True)
    )

    total_chaves = igc.select("codigo_ies").unique().height

    registrar_alerta(
        "gold_avaliacao_ies_dim_ies",
        chaves_orfas,
        "audit_gold_avaliacao_ies_sem_dim_ies.csv",
        f"IGC -> dim_ies | universo={total_chaves} | orfaos={chaves_orfas.height}",
        pipeline="educacao",
    )

    if not chaves_orfas.is_empty():
        raise RuntimeError(
            "fact_avaliacao_ies: existem IES do IGC sem correspondencia em dim_ies. "
            f"Amostra={chaves_orfas.head(10).to_dicts()}"
        )

    fato = base.with_columns(
        pl.col("ano_igc").cast(pl.Int32, strict=False).alias("ano"),
        pl.col("ano_igc").cast(pl.Int32, strict=False).alias("id_calendario"),
        pl.col("observacao").alias("observacao_igc"),
        pl.col("cebas").alias("cebas_igc"),
    )

    fato = tipar_e_projetar_por_schema(
        fato,
        SCHEMA_FACT_AVALIACAO_IES,
        "Gold fact_avaliacao_ies",
    )
    validar_chave_unica(
        fato,
        CHAVE_FACT_AVALIACAO_IES,
        "Gold fact_avaliacao_ies",
    )

    gravar_parquet(GOLD_FACT_AVALIACAO_IES, fato)

    log.info(
        "[GOLD] fact_avaliacao_ies salva em %s (%s linhas).",
        GOLD_FACT_AVALIACAO_IES,
        f"{fato.height:,}",
    )


if __name__ == "__main__":
    executar()
