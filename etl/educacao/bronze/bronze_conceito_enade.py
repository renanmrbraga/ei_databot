from __future__ import annotations

from etl.educacao.common import build_bronze_excel
from etl.educacao.config import (
    ABAS_CONCEITO_ENADE,
    ANOS_CONCEITO_ENADE,
    BRONZE_CONCEITO_ENADE,
    RAW_CONCEITO_ENADE,
)
from etl.educacao.schema import (
    ALIASES_CONCEITO_ENADE,
    COLUNAS_CONCEITO_ENADE,
    COLUNAS_OPCIONAIS_CONCEITO_ENADE,
    RENOMEACAO_CONCEITO_ENADE,
    SCHEMA_CONCEITO_ENADE_BRONZE,
)


def executar() -> None:
    build_bronze_excel(
        pattern=RAW_CONCEITO_ENADE,
        output_path=BRONZE_CONCEITO_ENADE,
        dataset_name="Conceito Enade",
        colunas=COLUNAS_CONCEITO_ENADE,
        colunas_opcionais=COLUNAS_OPCIONAIS_CONCEITO_ENADE,
        aliases_colunas=ALIASES_CONCEITO_ENADE,
        abas_por_arquivo=ABAS_CONCEITO_ENADE,
        renomeacao=RENOMEACAO_CONCEITO_ENADE,
        schema_bronze=SCHEMA_CONCEITO_ENADE_BRONZE,
        anos_esperados=ANOS_CONCEITO_ENADE,
    )


if __name__ == "__main__":
    executar()
