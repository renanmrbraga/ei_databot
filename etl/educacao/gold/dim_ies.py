from __future__ import annotations

from pathlib import Path

import polars as pl

from etl.core.common import (
    gravar_parquet,
    ler_parquet,
    obter_cor_por_dicionario_ou_hash,
    tipar_e_projetar_por_schema,
    validar_chave_unica,
    validar_colunas_obrigatorias_por_schema,
)
from etl.core.logger import get_logger
from etl.educacao.config import (
    GOLD_DIM_IES,
    SILVER_CONCEITO_ENADE,
    SILVER_CPC,
    SILVER_IDD,
    SILVER_IES,
    SILVER_IGC,
)
from etl.educacao.mapping import (
    MAPA_CATEGORIA_ADMINISTRATIVA,
    MAPA_ORGANIZACAO_ACADEMICA,
    REGRA_CORES_IES,
)
from etl.educacao.schema import CHAVE_IES_GOLD, SCHEMA_DIM_IES, SCHEMA_IES_SILVER
from health.health_etl import registrar_alerta

log = get_logger(pipeline="educacao")

FONTES_AVALIACAO = [
    (SILVER_CONCEITO_ENADE, "ano_enade", "ENADE"),
    (SILVER_CPC, "ano_cpc", "CPC"),
    (SILVER_IDD, "ano_idd", "IDD"),
    (SILVER_IGC, "ano_igc", "IGC"),
]


def _join_anos(
    values: pl.Series | list[int] | None,
) -> str | None:
    if values is None:
        return None

    if isinstance(values, pl.Series):
        valores = values.to_list()
    else:
        valores = values

    itens = [str(valor) for valor in valores if valor is not None]

    return " | ".join(itens) if itens else None


def _tipo_ies_categoria(categoria: object) -> str:
    texto = str(categoria or "").upper()
    if (
        "PÚBLIC" in texto
        or "PUBLIC" in texto
        or "FEDERAL" in texto
        or "ESTADUAL" in texto
        or "MUNICIPAL" in texto
    ):
        return "Pública"
    if (
        "PRIVAD" in texto
        or "PARTICULAR" in texto
        or "COMUNIT" in texto
        or "CONFESS" in texto
        or "ESPECIAL" in texto
    ):
        return "Particular"
    return "Não informado"


def _rotulo(row: dict[str, object]) -> str:
    sigla = str(row.get("sigla_ies") or "").strip().upper()
    nome = str(row.get("nome_ies") or "").strip().upper()
    if sigla and sigla not in {"NAN", "NONE", "NULL", "-"}:
        return f"{sigla} - {nome}" if nome and nome != sigla else sigla
    return nome or "IES NÃO INFORMADA"


def _cor(row: dict[str, object]) -> str:
    base = row.get("sigla_ies") or row.get("nome_ies")
    return obter_cor_por_dicionario_ou_hash(base, REGRA_CORES_IES)[0]


def _hex(row: dict[str, object]) -> str:
    base = row.get("sigla_ies") or row.get("nome_ies")
    return obter_cor_por_dicionario_ou_hash(base, REGRA_CORES_IES)[1]


def _build_censo() -> pl.DataFrame:
    df = ler_parquet(SILVER_IES)
    validar_colunas_obrigatorias_por_schema(
        df,
        SCHEMA_IES_SILVER,
        "Entrada Gold dim_ies - silver_superior_ies",
        validar_tipos=True,
        permitir_extras=False,
    )

    historico = (
        df.group_by("codigo_ies")
        .agg(
            pl.col("ano_censo").min().alias("ano_primeiro_censo"),
            pl.col("ano_censo").max().alias("ano_ultimo_censo"),
            pl.col("ano_censo").drop_nulls().unique().sort().alias("_anos_censo"),
        )
        .with_columns(
            pl.col("_anos_censo")
            .map_elements(_join_anos, return_dtype=pl.String, skip_nulls=False)
            .alias("anos_censo")
        )
        .drop("_anos_censo")
    )

    # ==========================================================================
    # ESTADO INSTITUCIONAL MAIS RECENTE
    # ==========================================================================
    # A dimensao representa a IES conforme o ultimo Censo Superior disponivel.
    # O historico anual permanece preservado na camada Silver.
    atual = (
        df.sort(["codigo_ies", "ano_censo"], nulls_last=True)
        .unique(subset=["codigo_ies"], keep="last", maintain_order=True)
        .join(historico, on="codigo_ies", how="left")
        .with_columns(
            pl.col("nome_ies").cast(pl.String).str.to_uppercase().str.strip_chars(),
            pl.col("sigla_ies").cast(pl.String).str.to_uppercase().str.strip_chars(),
            pl.col("mantenedora").cast(pl.String).str.to_uppercase().str.strip_chars(),
            pl.col("codigo_organizacao_academica")
            .map_elements(
                lambda x: MAPA_ORGANIZACAO_ACADEMICA.get(x, "NÃO INFORMADO"),
                return_dtype=pl.String,
                skip_nulls=False,
            )
            .alias("organizacao_academica"),
            pl.col("codigo_categoria_administrativa")
            .map_elements(
                lambda x: MAPA_CATEGORIA_ADMINISTRATIVA.get(x, "NÃO INFORMADO"),
                return_dtype=pl.String,
                skip_nulls=False,
            )
            .alias("categoria_administrativa"),
            pl.col("uf_ies")
            .cast(pl.String)
            .str.to_uppercase()
            .str.strip_chars()
            .alias("uf_sede_ies"),
            pl.col("municipio_ies")
            .cast(pl.String)
            .str.to_uppercase()
            .str.strip_chars()
            .alias("municipio_sede_ies"),
            pl.col("chave_cidade_normalizada").alias("chave_cidade_sede_normalizada"),
            pl.lit("CENSO_SUPERIOR").alias("fonte_ies"),
        )
        .with_columns(
            pl.col("categoria_administrativa")
            .map_elements(_tipo_ies_categoria, return_dtype=pl.String, skip_nulls=False)
            .alias("tipo_ies")
        )
        .select(
            "codigo_ies",
            "chave_ies_normalizada",
            "fonte_ies",
            "ano_primeiro_censo",
            "ano_ultimo_censo",
            "anos_censo",
            "sigla_ies",
            "nome_ies",
            "mantenedora",
            "tipo_ies",
            "organizacao_academica",
            "categoria_administrativa",
            "uf_sede_ies",
            "municipio_sede_ies",
            "chave_cidade_sede_normalizada",
        )
    )

    return atual


def _build_avaliacao_exclusiva(codigos_censo: pl.DataFrame) -> pl.DataFrame | None:
    partes: list[pl.DataFrame] = []

    for caminho, coluna_ano, fonte in FONTES_AVALIACAO:
        if not Path(caminho).exists():
            continue

        df = ler_parquet(caminho)
        obrigatorias = [
            coluna_ano,
            "codigo_ies",
            "nome_ies",
            "sigla_ies",
            "organizacao_academica",
            "categoria_administrativa",
            "chave_ies_normalizada",
        ]
        faltantes = [c for c in obrigatorias if c not in df.columns]
        if faltantes:
            raise KeyError(f"{Path(caminho).name}: colunas ausentes: {faltantes}")

        partes.append(
            df.select(
                pl.col(coluna_ano).cast(pl.Int32, strict=False).alias("ano"),
                "codigo_ies",
                "nome_ies",
                "sigla_ies",
                "organizacao_academica",
                "categoria_administrativa",
                "chave_ies_normalizada",
                pl.lit(fonte).alias("_fonte_avaliacao"),
            )
        )

    if not partes:
        return None

    base_avaliacao = (
        pl.concat(
            partes,
            how="diagonal_relaxed",
        )
        .drop_nulls(
            subset=["codigo_ies"],
        )
        .join(
            codigos_censo,
            on="codigo_ies",
            how="anti",
        )
        .with_columns(
            pl.col("nome_ies").cast(pl.String).str.to_uppercase().str.strip_chars(),
            pl.col("sigla_ies").cast(pl.String).str.to_uppercase().str.strip_chars(),
            pl.col("organizacao_academica").cast(pl.String).str.to_uppercase().str.strip_chars(),
            pl.col("categoria_administrativa").cast(pl.String).str.to_uppercase().str.strip_chars(),
        )
    )

    historico = (
        base_avaliacao.group_by(
            "codigo_ies",
        )
        .agg(
            pl.col("ano").min().alias("ano_primeira_avaliacao"),
            pl.col("ano").max().alias("ano_ultima_avaliacao"),
            pl.len().alias("qtd_registros_avaliacao"),
            pl.col("ano").drop_nulls().unique().sort().alias("_anos_avaliacao"),
            pl.col("_fonte_avaliacao").drop_nulls().unique().sort().alias("_fontes_avaliacao"),
            pl.col("nome_ies").drop_nulls().unique().sort().alias("_nomes_ies_avaliacao"),
            pl.col("sigla_ies").drop_nulls().unique().sort().alias("_siglas_ies_avaliacao"),
        )
        .with_columns(
            pl.col("_anos_avaliacao")
            .list.eval(pl.element().cast(pl.String))
            .list.join(" | ")
            .alias("anos_avaliacao"),
            pl.col("_fontes_avaliacao").list.join(" | ").alias("fontes_avaliacao"),
            pl.col("_nomes_ies_avaliacao").list.join(" | ").alias("nomes_ies_avaliacao"),
            pl.col("_siglas_ies_avaliacao").list.join(" | ").alias("siglas_ies_avaliacao"),
        )
        .drop(
            "_anos_avaliacao",
            "_fontes_avaliacao",
            "_nomes_ies_avaliacao",
            "_siglas_ies_avaliacao",
        )
    )

    atual = base_avaliacao.sort(
        [
            "codigo_ies",
            "ano",
            "_fonte_avaliacao",
        ],
        nulls_last=True,
    ).unique(
        subset=["codigo_ies"],
        keep="last",
        maintain_order=True,
    )

    auditoria = (
        atual.join(
            historico,
            on="codigo_ies",
            how="left",
        )
        .select(
            "codigo_ies",
            "nome_ies",
            "sigla_ies",
            "organizacao_academica",
            "categoria_administrativa",
            "chave_ies_normalizada",
            "ano_primeira_avaliacao",
            "ano_ultima_avaliacao",
            "anos_avaliacao",
            "fontes_avaliacao",
            "qtd_registros_avaliacao",
            "nomes_ies_avaliacao",
            "siglas_ies_avaliacao",
        )
        .sort(
            [
                "ano_ultima_avaliacao",
                "codigo_ies",
            ],
            descending=[
                True,
                False,
            ],
        )
    )

    registrar_alerta(
        "gold_dim_ies_exclusivas_avaliacao",
        auditoria,
        "audit_gold_dim_ies_exclusivas_avaliacao.csv",
        "IES presentes nas bases de avaliacao, mas ausentes do Censo Superior carregado",
        pipeline="educacao",
    )

    avaliacao = (
        atual.with_columns(
            pl.lit("AVALIACAO_INEP").alias("fonte_ies"),
            pl.lit(
                None,
                dtype=pl.Int32,
            ).alias("ano_primeiro_censo"),
            pl.lit(
                None,
                dtype=pl.Int32,
            ).alias("ano_ultimo_censo"),
            pl.lit(
                None,
                dtype=pl.String,
            ).alias("anos_censo"),
            pl.lit(
                None,
                dtype=pl.String,
            ).alias("mantenedora"),
            pl.lit(
                None,
                dtype=pl.String,
            ).alias("uf_sede_ies"),
            pl.lit(
                None,
                dtype=pl.String,
            ).alias("municipio_sede_ies"),
            pl.lit(
                None,
                dtype=pl.String,
            ).alias("chave_cidade_sede_normalizada"),
        )
        .with_columns(
            pl.col("categoria_administrativa")
            .map_elements(
                _tipo_ies_categoria,
                return_dtype=pl.String,
                skip_nulls=False,
            )
            .alias("tipo_ies")
        )
        .select(
            "codigo_ies",
            "chave_ies_normalizada",
            "fonte_ies",
            "ano_primeiro_censo",
            "ano_ultimo_censo",
            "anos_censo",
            "sigla_ies",
            "nome_ies",
            "mantenedora",
            "tipo_ies",
            "organizacao_academica",
            "categoria_administrativa",
            "uf_sede_ies",
            "municipio_sede_ies",
            "chave_cidade_sede_normalizada",
        )
    )

    return avaliacao


def executar() -> None:
    log.info("[GOLD] Construindo dim_ies.")

    censo = _build_censo()
    extra = _build_avaliacao_exclusiva(censo.select("codigo_ies"))

    partes = [censo]
    if extra is not None and not extra.is_empty():
        partes.append(extra)

    dim = (
        pl.concat(partes, how="diagonal_relaxed")
        .sort(["nome_ies", "codigo_ies"], nulls_last=True)
        .with_row_index("id_ies", offset=1)
        .with_columns(
            pl.struct(["sigla_ies", "nome_ies"])
            .map_elements(_rotulo, return_dtype=pl.String, skip_nulls=False)
            .alias("rotulo_ies"),
            pl.struct(["sigla_ies", "nome_ies"])
            .map_elements(_cor, return_dtype=pl.String, skip_nulls=False)
            .alias("cor_ies"),
            pl.struct(["sigla_ies", "nome_ies"])
            .map_elements(_hex, return_dtype=pl.String, skip_nulls=False)
            .alias("hex_ies"),
        )
    )

    dim = tipar_e_projetar_por_schema(dim, SCHEMA_DIM_IES, "Gold dim_ies")
    validar_chave_unica(dim, CHAVE_IES_GOLD, "Gold dim_ies")

    gravar_parquet(GOLD_DIM_IES, dim)

    log.info(
        "[GOLD] dim_ies salva em %s (%s IES).",
        GOLD_DIM_IES,
        f"{dim.height:,}",
    )


if __name__ == "__main__":
    executar()
