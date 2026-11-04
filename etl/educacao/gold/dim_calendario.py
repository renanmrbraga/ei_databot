from __future__ import annotations

from pathlib import Path

import polars as pl

from etl.core.common import (
    gravar_parquet,
    ler_parquet,
    tipar_e_projetar_por_schema,
    validar_chave_unica,
)
from etl.core.logger import get_logger
from etl.educacao.config import (
    GOLD_DIM_CALENDARIO,
    SILVER_CONCEITO_ENADE,
    SILVER_CPC,
    SILVER_CURSOS_SUPERIOR,
    SILVER_ED_BASICA,
    SILVER_IDD,
    SILVER_IGC,
)
from etl.educacao.schema import CHAVE_CALENDARIO_GOLD, SCHEMA_DIM_CALENDARIO

log = get_logger(pipeline="educacao")

FONTES_ANO = [
    (SILVER_CURSOS_SUPERIOR, "ano_censo"),
    (SILVER_ED_BASICA, "ano_censo"),
    (SILVER_CONCEITO_ENADE, "ano_enade"),
    (SILVER_CPC, "ano_cpc"),
    (SILVER_IDD, "ano_idd"),
    (SILVER_IGC, "ano_igc"),
]


def executar() -> None:
    log.info("[GOLD] Construindo dim_calendario.")

    partes: list[pl.DataFrame] = []

    for caminho, coluna_ano in FONTES_ANO:
        if not Path(caminho).exists():
            continue

        df = ler_parquet(caminho)
        if coluna_ano not in df.columns:
            raise KeyError(f"{Path(caminho).name}: coluna ausente: {coluna_ano}")

        partes.append(
            df.select(pl.col(coluna_ano).cast(pl.Int32, strict=False).alias("ano"))
            .drop_nulls()
            .filter(pl.col("ano") > 0)
            .unique()
        )

    if not partes:
        raise RuntimeError("Nenhuma fonte Silver disponivel para construir dim_calendario.")

    anos = pl.concat(partes, how="vertical_relaxed").unique().sort("ano")

    dim = anos.with_columns(
        pl.col("ano").alias("id_calendario"),
        pl.col("ano").cast(pl.String).alias("ano_texto"),
        pl.col("ano").alias("ordem_ano"),
        pl.concat_str(pl.col("ano").cast(pl.String), pl.lit("-01-01"))
        .str.to_date("%Y-%m-%d", strict=True)
        .alias("data_inicio_ano"),
        pl.concat_str(pl.col("ano").cast(pl.String), pl.lit("-12-31"))
        .str.to_date("%Y-%m-%d", strict=True)
        .alias("data_fim_ano"),
    )

    dim = tipar_e_projetar_por_schema(
        dim,
        SCHEMA_DIM_CALENDARIO,
        "Gold dim_calendario",
    )
    validar_chave_unica(dim, CHAVE_CALENDARIO_GOLD, "Gold dim_calendario")

    gravar_parquet(GOLD_DIM_CALENDARIO, dim)

    log.info(
        "[GOLD] dim_calendario salva em %s (%s anos: %s-%s).",
        GOLD_DIM_CALENDARIO,
        f"{dim.height:,}",
        dim.get_column("ano").min(),
        dim.get_column("ano").max(),
    )


if __name__ == "__main__":
    executar()
