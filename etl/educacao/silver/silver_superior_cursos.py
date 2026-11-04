from __future__ import annotations

from pathlib import Path

import polars as pl

from etl.core.common import (
    extrair_anchor_texto_expr,
    gravar_parquet,
    ler_parquet,
    normalizar_texto_chave_expr,
    tipar_e_projetar_por_schema,
    validar_colunas_obrigatorias_por_schema,
)
from etl.core.logger import get_logger
from etl.educacao.config import (
    BRONZE_CURSOS_SUPERIOR,
    SENTINEL_EAD,
    SILVER_CURSOS_SUPERIOR,
    SILVER_GEO,
)
from etl.educacao.mapping import (
    CORRECAO_MUNICIPIOS,
    DE_PARA_AREA_CONHECIMENTO,
)
from etl.educacao.schema import (
    SCHEMA_CURSOS_SUPERIOR_BRONZE,
    SCHEMA_CURSOS_SUPERIOR_SILVER,
    SCHEMA_GEO_SILVER,
)
from health.health_etl import registrar_alerta

log = get_logger(pipeline="educacao")


def _corrigir_municipio(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return CORRECAO_MUNICIPIOS.get(
        value,
        value,
    )


def _rematriculados(
    matriculados: str,
    ingressantes: str,
) -> pl.Expr:
    matriculados_expr = (
        pl.col(matriculados)
        .cast(
            pl.Int32,
            strict=False,
        )
        .fill_null(0)
    )

    ingressantes_expr = (
        pl.col(ingressantes)
        .cast(
            pl.Int32,
            strict=False,
        )
        .fill_null(0)
    )

    diferenca = matriculados_expr - ingressantes_expr

    return pl.max_horizontal(
        diferenca,
        pl.lit(0, dtype=pl.Int32),
    )


def executar() -> None:
    log.info("[SILVER] Iniciando Censo Superior - Cursos.")

    if not Path(BRONZE_CURSOS_SUPERIOR).exists():
        raise FileNotFoundError(f"Bronze Cursos Superior nao encontrado: {BRONZE_CURSOS_SUPERIOR}")

    if not Path(SILVER_GEO).exists():
        raise FileNotFoundError(
            f"Silver GEO nao encontrada: {SILVER_GEO}. Execute silver_geo primeiro."
        )

    df = ler_parquet(BRONZE_CURSOS_SUPERIOR)

    df_geo = ler_parquet(SILVER_GEO)

    # ==========================================================================
    # VALIDACAO DAS ENTRADAS
    # ==========================================================================

    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_CURSOS_SUPERIOR_BRONZE,
        "Entrada Silver Censo Superior - Cursos",
        validar_tipos=True,
        permitir_extras=False,
    )

    validar_colunas_obrigatorias_por_schema(
        df_geo,
        SCHEMA_GEO_SILVER,
        "Entrada Silver GEO em Cursos Superior",
        validar_tipos=True,
        permitir_extras=False,
    )

    # ==========================================================================
    # TIPAGEM NECESSARIA PARA AS REGRAS DA SILVER
    # ==========================================================================

    df = df.with_columns(
        pl.col("ano_censo")
        .cast(
            pl.Int32,
            strict=False,
        )
        .alias("ano_censo"),
        pl.col("codigo_ies")
        .cast(
            pl.Int64,
            strict=False,
        )
        .alias("codigo_ies"),
        pl.col("codigo_curso")
        .cast(
            pl.Int64,
            strict=False,
        )
        .alias("codigo_curso"),
        pl.col("codigo_municipio")
        .cast(
            pl.Int64,
            strict=False,
        )
        .alias("codigo_municipio"),
        pl.col("codigo_modalidade_ensino")
        .cast(
            pl.Int32,
            strict=False,
        )
        .alias("codigo_modalidade_ensino"),
    )

    # ==========================================================================
    # LIMPEZA DE TEXTO
    # ==========================================================================

    df = df.with_columns(
        pl.col("nome_curso")
        .cast(pl.String)
        .str.strip_chars()
        .str.to_uppercase()
        .alias("nome_curso"),
        pl.col("nome_cine").cast(pl.String).str.strip_chars().str.to_uppercase().alias("nome_cine"),
        pl.col("municipio").cast(pl.String).str.strip_chars().alias("municipio"),
        pl.col("uf").cast(pl.String).str.strip_chars().str.to_uppercase().alias("uf"),
    )

    # ==========================================================================
    # REFERENCIA DO CURSO
    # ==========================================================================

    nome_curso = pl.col("nome_curso")

    nome_cine = pl.col("nome_cine")

    nome_referencia = (
        pl.when(nome_curso.is_not_null() & (nome_curso != "")).then(nome_curso).otherwise(nome_cine)
    )

    df = df.with_columns(
        pl.when(pl.col("codigo_curso").is_not_null())
        .then(pl.col("codigo_curso").cast(pl.String))
        .otherwise(pl.col("codigo_cine").cast(pl.String))
        .alias("codigo_curso_referencia"),
        nome_referencia.alias("nome_curso_referencia"),
        pl.when(pl.col("codigo_curso").is_not_null())
        .then(pl.lit("EMEC"))
        .when(pl.col("codigo_cine").is_not_null())
        .then(pl.lit("CINE"))
        .otherwise(pl.lit("NAO INFORMADO"))
        .alias("tipo_codigo_curso"),
    )

    # ==========================================================================
    # CLASSIFICACAO DO CURSO
    # ==========================================================================

    df = df.with_columns(
        extrair_anchor_texto_expr(
            "nome_curso_referencia",
            DE_PARA_AREA_CONHECIMENTO,
        ).alias("curso_base")
    )

    df = df.with_columns(
        pl.col("curso_base")
        .replace_strict(
            DE_PARA_AREA_CONHECIMENTO,
            default=pl.lit("OUTROS"),
            return_dtype=pl.String,
        )
        .alias("tipo_curso")
    )

    # ==========================================================================
    # MUNICIPIO NORMALIZADO
    # ==========================================================================

    df = df.with_columns(normalizar_texto_chave_expr("municipio").alias("municipio_normalizado"))

    if CORRECAO_MUNICIPIOS:
        df = df.with_columns(
            pl.col("municipio_normalizado")
            .map_elements(
                _corrigir_municipio,
                return_dtype=pl.String,
                skip_nulls=False,
            )
            .alias("municipio_normalizado")
        )

    # ==========================================================================
    # EAD
    # ==========================================================================
    # O municipio e a UF originais sao preservados.
    # Apenas a chave analitica de municipio recebe o sentinela EAD.

    is_ead = pl.col("codigo_modalidade_ensino") == 2

    df = df.with_columns(
        pl.when(is_ead)
        .then(pl.lit(SENTINEL_EAD))
        .otherwise(pl.col("municipio_normalizado"))
        .alias("municipio_normalizado")
    )

    # ==========================================================================
    # REMATRICULADOS
    # ==========================================================================
    # Regra:
    # max(matriculados - ingressantes, 0)

    df = df.with_columns(
        _rematriculados(
            "matriculados",
            "ingressantes",
        ).alias("rematriculados"),
        _rematriculados(
            "matriculados_diurno",
            "ingressantes_diurno",
        ).alias("rematriculados_diurno"),
        _rematriculados(
            "matriculados_noturno",
            "ingressantes_noturno",
        ).alias("rematriculados_noturno"),
    )

    # ==========================================================================
    # CONTRATO SILVER
    # ==========================================================================

    df = tipar_e_projetar_por_schema(
        df,
        SCHEMA_CURSOS_SUPERIOR_SILVER,
        "Silver Censo Superior - Cursos",
    )

    # ==========================================================================
    # VALIDACAO DA SAIDA
    # ==========================================================================

    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_CURSOS_SUPERIOR_SILVER,
        "Saida Silver Censo Superior - Cursos",
        validar_tipos=True,
        permitir_extras=False,
    )

    # ==========================================================================
    # AUDITORIA DO CENSO
    # ==========================================================================

    resumo_censo = (
        df.group_by("ano_censo")
        .agg(
            pl.len().alias("registros"),
            pl.col("codigo_ies").n_unique().alias("ies"),
            pl.col("codigo_curso").n_unique().alias("cursos"),
            pl.col("ingressantes").sum().alias("ingressantes"),
        )
        .sort("ano_censo")
    )

    registrar_alerta(
        "silver_censo_por_ano",
        resumo_censo,
        "audit_silver_censo.csv",
        "Resumo anual do Censo Superior: registros, IES, cursos e ingressantes",
        pipeline="educacao",
    )

    # ==========================================================================
    # AUDITORIA GEO
    # ==========================================================================
    # O codigo IBGE passa a ser a chave principal do cruzamento geografico.
    # EAD nao entra nesta verificacao.

    geo_keys = df_geo.select("codigo_municipio").drop_nulls().unique()

    municipios_censo = (
        df.filter(pl.col("codigo_modalidade_ensino") != 2)
        .select(
            "codigo_municipio",
            "municipio",
            "municipio_normalizado",
            "uf",
        )
        .unique()
    )

    municipios_sem_geo = municipios_censo.join(
        geo_keys,
        on="codigo_municipio",
        how="anti",
    ).sort(
        [
            "uf",
            "municipio",
        ]
    )

    registrar_alerta(
        "silver_municipios_sem_geo",
        municipios_sem_geo,
        "audit_ies_municipios.csv",
        "Municipios presenciais do Censo Superior sem correspondencia na GEO",
        pipeline="educacao",
    )

    # ==========================================================================
    # SAIDA
    # ==========================================================================

    gravar_parquet(SILVER_CURSOS_SUPERIOR, df)

    log.info(
        "[SILVER] Censo Superior - Cursos concluido | linhas=%s | saida=%s",
        f"{df.height:,}",
        SILVER_CURSOS_SUPERIOR,
    )


if __name__ == "__main__":
    executar()
