from __future__ import annotations

from etl.educacao.common import build_bronze_csv
from etl.educacao.config import (
    ANOS_CENSO_SUPERIOR,
    BRONZE_CURSOS_SUPERIOR,
    RAW_CURSOS_SUPERIOR,
)
from etl.educacao.schema import (
    ALIASES_CURSOS_SUPERIOR,
    COLUNAS_CURSOS_SUPERIOR,
    RENOMEACAO_CURSOS_SUPERIOR,
    SCHEMA_CURSOS_SUPERIOR_BRONZE,
)

READ_ATTEMPTS = [
    {"sep": ";", "encoding": "latin1"},
    {"sep": ";", "encoding": "utf-8-sig"},
]


def executar() -> None:
    build_bronze_csv(
        pattern=RAW_CURSOS_SUPERIOR,
        output_path=BRONZE_CURSOS_SUPERIOR,
        dataset_name="Censo Superior - Cursos",
        colunas=COLUNAS_CURSOS_SUPERIOR,
        renomeacao=RENOMEACAO_CURSOS_SUPERIOR,
        schema_bronze=SCHEMA_CURSOS_SUPERIOR_BRONZE,
        read_attempts=READ_ATTEMPTS,
        aliases_colunas=ALIASES_CURSOS_SUPERIOR,
        anos_esperados=ANOS_CENSO_SUPERIOR,
    )


if __name__ == "__main__":
    executar()
