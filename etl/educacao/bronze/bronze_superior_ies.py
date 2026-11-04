from __future__ import annotations

from etl.educacao.common import build_bronze_csv
from etl.educacao.config import (
    ANOS_CENSO_SUPERIOR,
    BRONZE_IES,
    RAW_IES,
)
from etl.educacao.schema import (
    COLUNAS_IES,
    RENOMEACAO_IES,
    SCHEMA_IES_BRONZE,
)

READ_ATTEMPTS = [
    {"sep": ";", "encoding": "latin1"},
    {"sep": ";", "encoding": "utf-8-sig"},
]


def executar() -> None:
    build_bronze_csv(
        pattern=RAW_IES,
        output_path=BRONZE_IES,
        dataset_name="Censo Superior - IES",
        colunas=COLUNAS_IES,
        renomeacao=RENOMEACAO_IES,
        schema_bronze=SCHEMA_IES_BRONZE,
        read_attempts=READ_ATTEMPTS,
        anos_esperados=ANOS_CENSO_SUPERIOR,
    )


if __name__ == "__main__":
    executar()
