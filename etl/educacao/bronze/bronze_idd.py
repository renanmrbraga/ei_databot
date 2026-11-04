from __future__ import annotations

from etl.educacao.common import build_bronze_excel
from etl.educacao.config import (
    ABAS_IDD,
    ANOS_IDD,
    BRONZE_IDD,
    RAW_IDD,
)
from etl.educacao.schema import (
    ALIASES_IDD,
    COLUNAS_IDD,
    COLUNAS_OPCIONAIS_IDD,
    RENOMEACAO_IDD,
    SCHEMA_IDD_BRONZE,
)


def executar() -> None:
    build_bronze_excel(
        pattern=RAW_IDD,
        output_path=BRONZE_IDD,
        dataset_name="IDD",
        colunas=COLUNAS_IDD,
        colunas_opcionais=COLUNAS_OPCIONAIS_IDD,
        aliases_colunas=ALIASES_IDD,
        abas_por_arquivo=ABAS_IDD,
        renomeacao=RENOMEACAO_IDD,
        schema_bronze=SCHEMA_IDD_BRONZE,
        anos_esperados=ANOS_IDD,
    )


if __name__ == "__main__":
    executar()
