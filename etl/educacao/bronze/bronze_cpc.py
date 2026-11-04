from __future__ import annotations

from etl.educacao.common import build_bronze_excel
from etl.educacao.config import (
    ABAS_CPC,
    ANOS_CPC,
    BRONZE_CPC,
    RAW_CPC,
)
from etl.educacao.schema import (
    ALIASES_CPC,
    COLUNAS_CPC,
    COLUNAS_OPCIONAIS_CPC,
    RENOMEACAO_CPC,
    SCHEMA_CPC_BRONZE,
)


def executar() -> None:
    build_bronze_excel(
        pattern=RAW_CPC,
        output_path=BRONZE_CPC,
        dataset_name="CPC",
        colunas=COLUNAS_CPC,
        colunas_opcionais=COLUNAS_OPCIONAIS_CPC,
        aliases_colunas=ALIASES_CPC,
        abas_por_arquivo=ABAS_CPC,
        renomeacao=RENOMEACAO_CPC,
        schema_bronze=SCHEMA_CPC_BRONZE,
        anos_esperados=ANOS_CPC,
    )


if __name__ == "__main__":
    executar()
