from __future__ import annotations

from etl.educacao.common import build_bronze_excel
from etl.educacao.config import (
    ABAS_IGC,
    ANOS_IGC,
    BRONZE_IGC,
    RAW_IGC,
)
from etl.educacao.schema import (
    ALIASES_IGC,
    COLUNAS_IGC,
    COLUNAS_OPCIONAIS_IGC,
    RENOMEACAO_IGC,
    SCHEMA_IGC_BRONZE,
)


def executar() -> None:
    build_bronze_excel(
        pattern=RAW_IGC,
        output_path=BRONZE_IGC,
        dataset_name="IGC",
        colunas=COLUNAS_IGC,
        colunas_opcionais=COLUNAS_OPCIONAIS_IGC,
        aliases_colunas=ALIASES_IGC,
        abas_por_arquivo=ABAS_IGC,
        renomeacao=RENOMEACAO_IGC,
        schema_bronze=SCHEMA_IGC_BRONZE,
        anos_esperados=ANOS_IGC,
    )


if __name__ == "__main__":
    executar()
