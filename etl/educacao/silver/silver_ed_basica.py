from __future__ import annotations

from pathlib import Path

import polars as pl

from etl.core.common import (
    gravar_parquet,
    ler_parquet,
    normalizar_texto_chave_expr,
    tipar_e_projetar_por_schema,
    validar_chave_unica,
    validar_colunas_obrigatorias_por_schema,
)
from etl.core.logger import get_logger
from etl.educacao.config import BRONZE_ED_BASICA, SILVER_ED_BASICA
from etl.educacao.schema import (
    CHAVE_ESCOLA_ANO,
    COLUNAS_METRICAS_ED_BASICA,
    SCHEMA_ED_BASICA_BRONZE,
    SCHEMA_ED_BASICA_SILVER,
)

log = get_logger(pipeline="educacao")


def _expr_rede() -> pl.Expr:
    dependencia = pl.col("codigo_dependencia").cast(pl.Int32, strict=False)
    return (
        pl.when(dependencia == 1)
        .then(pl.lit("FEDERAL"))
        .when(dependencia == 2)
        .then(pl.lit("ESTADUAL"))
        .when(dependencia == 3)
        .then(pl.lit("MUNICIPAL"))
        .when(dependencia == 4)
        .then(pl.lit("PRIVADA"))
        .otherwise(pl.lit("NÃO INFORMADO"))
        .alias("rede")
    )


def _validar_metricas_numericas(df: pl.DataFrame) -> None:
    """Impedir que cast(strict=False) apague silenciosamente valores invalidos."""
    expressoes = []
    for campo in COLUNAS_METRICAS_ED_BASICA:
        texto = pl.col(campo).cast(pl.String).str.strip_chars()
        numerico = texto.cast(pl.Int32, strict=False)
        expressoes.append(
            (texto.is_not_null() & (texto != "") & numerico.is_null()).sum().alias(campo)
        )
    contagens = df.select(expressoes).row(0, named=True)
    invalidos = {campo: n for campo, n in contagens.items() if n}
    if invalidos:
        raise RuntimeError(
            "Silver Educacao Basica: valores nao numericos nas metricas; "
            f"revisar origem antes de publicar: {invalidos}"
        )


def executar() -> None:
    log.info("[SILVER] Iniciando Censo Escolar - Educacao Basica.")
    if not Path(BRONZE_ED_BASICA).exists():
        raise FileNotFoundError(f"Bronze Educacao Basica nao encontrado: {BRONZE_ED_BASICA}")
    df = ler_parquet(BRONZE_ED_BASICA)
    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_ED_BASICA_BRONZE,
        "Entrada Silver Educacao Basica",
        validar_tipos=True,
        permitir_extras=False,
    )
    _validar_metricas_numericas(df)

    # Ausencia no layout historico = null (nunca zero artificial).
    df = df.with_columns(
        pl.col("ano_censo").cast(pl.Int32, strict=False),
        pl.col("codigo_escola").cast(pl.Int64, strict=False),
        pl.col("codigo_municipio").cast(pl.Int64, strict=False),
        *[
            pl.col(campo).cast(pl.Int32, strict=False).alias(campo)
            for campo in COLUNAS_METRICAS_ED_BASICA
        ],
        pl.col("indicador_ensino_medio").cast(pl.Int32, strict=False),
    )
    df = df.with_columns(
        pl.when(
            pl.col("indicador_ensino_medio").is_null()
            & pl.col("matriculas_ensino_medio").is_not_null()
        )
        .then((pl.col("matriculas_ensino_medio") > 0).cast(pl.Int32))
        .otherwise(pl.col("indicador_ensino_medio"))
        .alias("indicador_ensino_medio")
    )

    textos = [
        "nome_escola",
        "distrito",
        "subdistrito",
        "endereco",
        "numero_endereco",
        "complemento",
        "bairro",
        "cep",
        "municipio",
        "uf",
    ]
    df = df.with_columns(
        [
            pl.col(coluna).cast(pl.String).str.strip_chars().str.to_uppercase().alias(coluna)
            if coluna == "uf"
            else pl.col(coluna).cast(pl.String).str.strip_chars().alias(coluna)
            for coluna in textos
        ]
    )
    df = df.with_columns(
        normalizar_texto_chave_expr("municipio").alias("municipio_normalizado"),
        _expr_rede(),
    )

    df = tipar_e_projetar_por_schema(
        df,
        SCHEMA_ED_BASICA_SILVER,
        "Silver Educacao Basica",
    )
    validar_chave_unica(df, CHAVE_ESCOLA_ANO, "Silver Educacao Basica")
    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_ED_BASICA_SILVER,
        "Saida Silver Educacao Basica",
        validar_tipos=True,
        permitir_extras=False,
    )
    gravar_parquet(SILVER_ED_BASICA, df)
    log.info(
        "[SILVER] Educacao Basica concluida | linhas=%s | indicadores=%s | saida=%s",
        f"{df.height:,}",
        len(COLUNAS_METRICAS_ED_BASICA),
        SILVER_ED_BASICA,
    )


if __name__ == "__main__":
    executar()
