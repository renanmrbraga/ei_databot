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
from etl.educacao.config import GOLD_DIM_ESCOLA, SILVER_ED_BASICA
from etl.educacao.mapping import (
    MAPA_CATEGORIA_ESCOLA_PRIVADA,
    MAPA_LOCALIZACAO_ESCOLA,
    MAPA_SITUACAO_FUNCIONAMENTO_ESCOLA,
)
from etl.educacao.schema import (
    CHAVE_ESCOLA_GOLD,
    SCHEMA_DIM_ESCOLA,
    SCHEMA_ED_BASICA_SILVER,
)

log = get_logger(pipeline="educacao")


def executar() -> None:
    log.info("[GOLD] Construindo dim_escola.")

    escolas = ler_parquet(SILVER_ED_BASICA)
    validar_colunas_obrigatorias_por_schema(
        escolas,
        SCHEMA_ED_BASICA_SILVER,
        "Entrada Gold dim_escola - silver_ed_basica",
        validar_tipos=True,
        permitir_extras=False,
    )

    dim = (
        escolas.sort(["codigo_escola", "ano_censo"], nulls_last=True)
        .unique(subset=["codigo_escola"], keep="last", maintain_order=True)
        .with_columns(
            pl.col("nome_escola").cast(pl.String).str.to_uppercase().str.strip_chars(),
            pl.col("rede")
            .cast(pl.String)
            .str.to_uppercase()
            .str.strip_chars()
            .alias("rede_escola"),
            pl.col("codigo_categoria_escola_privada")
            .replace_strict(
                MAPA_CATEGORIA_ESCOLA_PRIVADA,
                default=pl.lit("NÃO SE APLICA"),
                return_dtype=pl.String,
            )
            .alias("categoria_escola_privada"),
            pl.col("codigo_localizacao")
            .replace_strict(
                MAPA_LOCALIZACAO_ESCOLA,
                default=pl.lit("NÃO INFORMADO"),
                return_dtype=pl.String,
            )
            .alias("localizacao_escola"),
            pl.col("codigo_situacao_funcionamento")
            .replace_strict(
                MAPA_SITUACAO_FUNCIONAMENTO_ESCOLA,
                default=pl.lit("NÃO INFORMADO"),
                return_dtype=pl.String,
            )
            .alias("situacao_funcionamento"),
            pl.col("distrito")
            .cast(pl.String)
            .str.to_uppercase()
            .str.strip_chars()
            .alias("distrito_escola"),
            pl.col("subdistrito")
            .cast(pl.String)
            .str.to_uppercase()
            .str.strip_chars()
            .alias("subdistrito_escola"),
            pl.col("bairro")
            .cast(pl.String)
            .str.to_uppercase()
            .str.strip_chars()
            .alias("bairro_escola"),
            pl.col("endereco")
            .cast(pl.String)
            .str.to_uppercase()
            .str.strip_chars()
            .alias("endereco_escola"),
            pl.col("numero_endereco").cast(pl.String).str.strip_chars().alias("numero_escola"),
            pl.col("complemento")
            .cast(pl.String)
            .str.to_uppercase()
            .str.strip_chars()
            .alias("complemento_escola"),
            pl.col("cep").cast(pl.String).str.strip_chars().alias("cep_escola"),
        )
        .select(
            "codigo_escola",
            "nome_escola",
            "rede_escola",
            "categoria_escola_privada",
            "localizacao_escola",
            "situacao_funcionamento",
            "distrito_escola",
            "subdistrito_escola",
            "bairro_escola",
            "endereco_escola",
            "numero_escola",
            "complemento_escola",
            "cep_escola",
        )
        .sort(["nome_escola", "codigo_escola"], nulls_last=True)
        .with_row_index("id_escola", offset=1)
    )

    dim = tipar_e_projetar_por_schema(dim, SCHEMA_DIM_ESCOLA, "Gold dim_escola")
    validar_chave_unica(dim, CHAVE_ESCOLA_GOLD, "Gold dim_escola")

    gravar_parquet(GOLD_DIM_ESCOLA, dim)

    log.info(
        "[GOLD] dim_escola salva em %s | escolas=%s | todas as etapas de ensino.",
        GOLD_DIM_ESCOLA,
        f"{dim.height:,}",
    )


if __name__ == "__main__":
    executar()
