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
from etl.educacao.config import (
    GOLD_DIM_ESCOLA,
    GOLD_DIM_LOCALIDADE,
    GOLD_FACT_EDUCACAO_BASICA,
    SILVER_ED_BASICA,
)
from etl.educacao.schema import (
    CHAVE_FACT_EDUCACAO_BASICA,
    COLUNAS_METRICAS_ED_BASICA,
    SCHEMA_DIM_ESCOLA,
    SCHEMA_DIM_LOCALIDADE,
    SCHEMA_ED_BASICA_SILVER,
    SCHEMA_FACT_EDUCACAO_BASICA,
)
from health.health_etl import registrar_alerta

log = get_logger(pipeline="educacao")


def _validar_orfaos(
    df: pl.DataFrame,
    id_col: str,
    colunas_audit: list[str],
    nome_etapa: str,
    nome_arquivo: str,
    descricao: str,
) -> None:
    audit_cols = [c for c in colunas_audit if c in df.columns]
    universo = df.select(audit_cols).unique().height
    orfaos = df.filter(pl.col(id_col).is_null()).select(audit_cols).unique()

    registrar_alerta(
        nome_etapa,
        orfaos,
        nome_arquivo,
        f"{descricao} | universo={universo} | orfaos={orfaos.height}",
        pipeline="educacao",
    )

    if not orfaos.is_empty():
        raise RuntimeError(
            f"{descricao}: {orfaos.height} chave(s) sem correspondencia. "
            f"Amostra={orfaos.head(10).to_dicts()}"
        )


def executar() -> None:
    log.info("[GOLD] Construindo fact_educacao_basica (todas as etapas).")
    silver = ler_parquet(SILVER_ED_BASICA)
    dim_escola = ler_parquet(GOLD_DIM_ESCOLA)
    dim_localidade = ler_parquet(GOLD_DIM_LOCALIDADE)

    validar_colunas_obrigatorias_por_schema(
        silver,
        SCHEMA_ED_BASICA_SILVER,
        "Entrada Gold fact_educacao_basica - silver_ed_basica",
        validar_tipos=True,
        permitir_extras=False,
    )
    validar_colunas_obrigatorias_por_schema(
        dim_escola,
        SCHEMA_DIM_ESCOLA,
        "Entrada Gold fact_educacao_basica - dim_escola",
        validar_tipos=True,
        permitir_extras=False,
    )
    validar_colunas_obrigatorias_por_schema(
        dim_localidade,
        SCHEMA_DIM_LOCALIDADE,
        "Entrada Gold fact_educacao_basica - dim_localidade",
        validar_tipos=True,
        permitir_extras=False,
    )
    # NAO filtrar por ensino medio: todas as escolas devem ser representadas.
    base = silver
    lookup_escola = dim_escola.select("codigo_escola", "id_escola")
    validar_chave_unica(
        lookup_escola,
        ["codigo_escola"],
        "Lookup fact_educacao_basica -> dim_escola",
    )
    lookup_localidade = dim_localidade.select("codigo_municipio", "id_localidade")
    validar_chave_unica(
        lookup_localidade,
        ["codigo_municipio"],
        "Lookup fact_educacao_basica -> dim_localidade",
    )

    base = base.join(lookup_escola, on="codigo_escola", how="left", validate="m:1")
    _validar_orfaos(
        base,
        "id_escola",
        ["codigo_escola", "nome_escola"],
        "gold_educacao_basica_dim_escola",
        "audit_gold_educacao_basica_sem_dim_escola.csv",
        "Educacao Basica -> dim_escola",
    )
    base = base.join(lookup_localidade, on="codigo_municipio", how="left", validate="m:1")
    _validar_orfaos(
        base,
        "id_localidade",
        ["codigo_municipio", "municipio", "uf"],
        "gold_educacao_basica_dim_localidade",
        "audit_gold_educacao_basica_sem_dim_localidade.csv",
        "Educacao Basica -> dim_localidade",
    )

    # Uma linha por escola e ano, sem soma artificial de modalidades sobrepostas.
    fato = base.select(
        "id_escola",
        "id_localidade",
        pl.col("ano_censo").cast(pl.Int32, strict=False).alias("id_calendario"),
        pl.col("ano_censo").cast(pl.Int32, strict=False).alias("ano"),
        *COLUNAS_METRICAS_ED_BASICA,
    )
    fato = tipar_e_projetar_por_schema(
        fato,
        SCHEMA_FACT_EDUCACAO_BASICA,
        "Gold fact_educacao_basica",
    )
    validar_chave_unica(
        fato,
        CHAVE_FACT_EDUCACAO_BASICA,
        "Gold fact_educacao_basica",
    )
    if fato.height != silver.height:
        raise RuntimeError(
            f"Gold Educacao Basica perdeu ou duplicou escolas/anos: "
            f"silver={silver.height}, gold={fato.height}"
        )
    gravar_parquet(GOLD_FACT_EDUCACAO_BASICA, fato)
    log.info(
        "[GOLD] fact_educacao_basica salva em %s | linhas=%s | indicadores=%s",
        GOLD_FACT_EDUCACAO_BASICA,
        f"{fato.height:,}",
        len(COLUNAS_METRICAS_ED_BASICA),
    )


if __name__ == "__main__":
    executar()
