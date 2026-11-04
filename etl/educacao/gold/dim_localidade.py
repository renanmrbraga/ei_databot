from __future__ import annotations

import math

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
    CIDADE_REFERENCIA,
    CODIGO_LOCALIDADE_EAD,
    COLUNA_DISTANCIA,
    GOLD_DIM_LOCALIDADE,
    SENTINEL_EAD,
    SILVER_GEO,
    UF_REFERENCIA,
)
from etl.educacao.schema import (
    CHAVE_LOCALIDADE_GOLD,
    SCHEMA_DIM_LOCALIDADE,
    SCHEMA_GEO_SILVER,
)

log = get_logger(pipeline="educacao")

RAIO_TERRA_KM = 6371.0088


def _coordenadas_validas(latitude: float, longitude: float) -> bool:
    """Verifica se as coordenadas são finitas e geograficamente válidas."""
    return (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    )


def _obter_referencia(geo: pl.DataFrame) -> tuple[float, float]:
    """Localiza a cidade configurada, exigindo uma correspondência única."""
    cidade = CIDADE_REFERENCIA.strip().upper()
    uf = UF_REFERENCIA.strip().upper()

    if not cidade or not uf:
        raise ValueError("Cidade e UF de referência são obrigatórias.")

    referencia = geo.filter((pl.col("municipio_normalizado") == cidade) & (pl.col("uf") == uf))

    if referencia.height != 1:
        raise ValueError(
            f"Referência geográfica {cidade}/{uf}: "
            f"esperado 1 município, encontrados {referencia.height}."
        )

    latitude = referencia.item(0, "latitude")
    longitude = referencia.item(0, "longitude")

    if latitude is None or longitude is None:
        raise ValueError(f"Referência {cidade}/{uf} sem coordenadas.")

    lat = float(latitude)
    lon = float(longitude)

    if not _coordenadas_validas(lat, lon):
        raise ValueError(f"Referência {cidade}/{uf} com coordenadas inválidas.")

    return lat, lon


def _adicionar_distancia(
    dim: pl.DataFrame,
    latitude_referencia: float,
    longitude_referencia: float,
) -> pl.DataFrame:
    """Calcula distâncias geográficas em km, com expressões Polars."""
    fator = math.pi / 180.0

    lat = pl.col("latitude") * fator
    lon = pl.col("longitude") * fator

    lat_ref = latitude_referencia * fator
    lon_ref = longitude_referencia * fator

    delta_lat = lat - lat_ref
    delta_lon = lon - lon_ref

    a = (
        (delta_lat / 2).sin().pow(2) + lat.cos() * math.cos(lat_ref) * (delta_lon / 2).sin().pow(2)
    ).clip(0.0, 1.0)

    distancia = 2.0 * RAIO_TERRA_KM * a.sqrt().arcsin()

    coordenadas_validas = (
        pl.col("latitude").is_not_null()
        & pl.col("longitude").is_not_null()
        & pl.col("latitude").is_finite()
        & pl.col("longitude").is_finite()
        & pl.col("latitude").is_between(-90, 90)
        & pl.col("longitude").is_between(-180, 180)
        & (pl.col("codigo_municipio") != CODIGO_LOCALIDADE_EAD)
    )

    return dim.with_columns(
        pl.when(coordenadas_validas)
        .then(distancia)
        .otherwise(None)
        .cast(pl.Float64)
        .alias(COLUNA_DISTANCIA)
    )


def executar() -> None:
    """Constrói a dimensão de localidades com distância configurável."""
    log.info("[GOLD] Construindo dim_localidade.")

    geo = ler_parquet(SILVER_GEO)

    validar_colunas_obrigatorias_por_schema(
        geo,
        SCHEMA_GEO_SILVER,
        "Entrada Gold dim_localidade - silver_geo",
        validar_tipos=True,
        permitir_extras=False,
    )

    dim = geo.select(
        "codigo_municipio",
        "codigo_uf",
        "municipio",
        "municipio_normalizado",
        "uf",
        "latitude",
        "longitude",
    ).unique(
        subset=["codigo_municipio"],
        keep="first",
        maintain_order=True,
    )

    lat_ref, lon_ref = _obter_referencia(dim)

    # EAD não representa um município físico.
    ead = pl.DataFrame(
        {
            "codigo_municipio": [CODIGO_LOCALIDADE_EAD],
            "codigo_uf": [None],
            "municipio": [SENTINEL_EAD],
            "municipio_normalizado": [SENTINEL_EAD],
            "uf": [SENTINEL_EAD],
            "latitude": [None],
            "longitude": [None],
        },
        schema={
            "codigo_municipio": pl.Int64,
            "codigo_uf": pl.Int32,
            "municipio": pl.String,
            "municipio_normalizado": pl.String,
            "uf": pl.String,
            "latitude": pl.Float64,
            "longitude": pl.Float64,
        },
    )

    dim = (
        pl.concat([ead, dim], how="vertical_relaxed")
        .sort(["uf", "municipio"], nulls_last=True)
        .with_row_index("id_localidade", offset=1)
    )

    dim = _adicionar_distancia(dim, lat_ref, lon_ref)

    dim = tipar_e_projetar_por_schema(
        dim,
        SCHEMA_DIM_LOCALIDADE,
        "Gold dim_localidade",
    )
    validar_chave_unica(dim, CHAVE_LOCALIDADE_GOLD, "Gold dim_localidade")

    referencia = dim.filter(
        (pl.col("municipio_normalizado") == CIDADE_REFERENCIA.strip().upper())
        & (pl.col("uf") == UF_REFERENCIA.strip().upper())
    )

    if referencia.height != 1 or not math.isclose(
        referencia.item(0, COLUNA_DISTANCIA),
        0.0,
        abs_tol=1e-6,
    ):
        raise ValueError("Distância da cidade de referência deve ser zero.")

    gravar_parquet(GOLD_DIM_LOCALIDADE, dim)

    log.info(
        "[GOLD] dim_localidade salva em %s (%s localidades). Referência: %s/%s.",
        GOLD_DIM_LOCALIDADE,
        f"{dim.height:,}",
        CIDADE_REFERENCIA,
        UF_REFERENCIA,
    )


if __name__ == "__main__":
    executar()
