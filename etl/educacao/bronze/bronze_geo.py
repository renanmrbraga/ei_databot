from __future__ import annotations

from etl.educacao.common import build_bronze_csv
from etl.educacao.config import (
    BRONZE_GEO,
    RAW_GEO,
)
from etl.educacao.schema import (
    COLUNAS_GEO,
    RENOMEACAO_GEO,
    SCHEMA_GEO_BRONZE,
)

READ_ATTEMPTS = [
    {"sep": ",", "encoding": "utf-8-sig"},
    {"sep": ",", "encoding": "utf8-lossy"},
]


def executar() -> None:
    build_bronze_csv(
        pattern=RAW_GEO,
        output_path=BRONZE_GEO,
        dataset_name="Geolocalizacao",
        colunas=COLUNAS_GEO,
        renomeacao=RENOMEACAO_GEO,
        schema_bronze=SCHEMA_GEO_BRONZE,
        read_attempts=READ_ATTEMPTS,
    )


if __name__ == "__main__":
    executar()
