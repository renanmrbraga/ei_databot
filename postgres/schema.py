"""Metadados e DDL para os Parquets Gold."""

from __future__ import annotations

from pathlib import Path

import polars as pl
from psycopg import sql

DIMENSIONS = (
    "dim_calendario",
    "dim_curso_superior",
    "dim_escola",
    "dim_ies",
    "dim_localidade",
)
FACTS = (
    "fact_avaliacao_curso_superior",
    "fact_avaliacao_ies",
    "fact_educacao_basica",
    "fact_educacao_superior",
    "fact_educacao_superior_turno",
)
TABLES = DIMENSIONS + FACTS
FOREIGN_KEYS = {
    "id_calendario": "dim_calendario",
    "id_curso_superior": "dim_curso_superior",
    "id_escola": "dim_escola",
    "id_ies": "dim_ies",
    "id_localidade": "dim_localidade",
}
UNIQUE_KEYS = {
    # As chaves de unicidade fisica devem refletir CHAVE_FACT_* do ETL.
    "fact_avaliacao_curso_superior": (
        "id_ies",
        "id_curso_superior",
        "id_localidade",
        "ano",
        "codigo_curso_avaliado",
    ),
    "fact_avaliacao_ies": ("id_ies", "ano"),
    "fact_educacao_basica": ("id_escola", "ano"),
    "fact_educacao_superior": (
        "id_ies",
        "id_curso_superior",
        "id_localidade",
        "id_calendario",
    ),
    "fact_educacao_superior_turno": (
        "id_ies",
        "id_curso_superior",
        "id_localidade",
        "id_calendario",
        "turno_curso",
    ),
}


def sql_type(dtype: pl.DataType) -> str:
    types = {
        pl.Int8: "SMALLINT",
        pl.Int16: "SMALLINT",
        pl.Int32: "INTEGER",
        pl.Int64: "BIGINT",
        pl.UInt8: "SMALLINT",
        pl.UInt16: "INTEGER",
        pl.UInt32: "BIGINT",
        pl.Float32: "REAL",
        pl.Float64: "DOUBLE PRECISION",
        pl.String: "TEXT",
        pl.Boolean: "BOOLEAN",
        pl.Date: "DATE",
    }
    try:
        return types[dtype]
    except KeyError as exc:
        raise TypeError(f"Tipo Polars não suportado: {dtype}") from exc


def inspect_gold(folder: Path) -> dict[str, dict[str, pl.DataType]]:
    if not folder.is_dir():
        raise FileNotFoundError(f"Pasta Gold não encontrada: {folder}")
    expected = {f"{name}.parquet" for name in TABLES}
    actual = {path.name for path in folder.glob("*.parquet")}
    if expected != actual:
        raise ValueError(
            f"Arquivos Gold divergentes. Ausentes: {sorted(expected - actual)}; extras: {sorted(actual - expected)}"
        )
    schemas = {}
    for name in TABLES:
        schema = dict(pl.scan_parquet(folder / f"{name}.parquet").collect_schema())
        pk = f"id_{name[4:]}" if name.startswith("dim_") else None
        if pk and (pk not in schema or schema[pk] != pl.Int32):
            raise ValueError(f"Chave primária inválida em {name}: {pk}")
        if name in FACTS:
            for key in UNIQUE_KEYS[name]:
                if key not in schema:
                    raise ValueError(f"Coluna da chave única ausente: {name}.{key}")
            for key in FOREIGN_KEYS:
                if key in schema and schema[key] != pl.Int32:
                    raise ValueError(f"FK deve ser Int32: {name}.{key}")
        for dtype in schema.values():
            sql_type(dtype)
        schemas[name] = schema
    return schemas


def create_staging(cur, schemas: dict[str, dict[str, pl.DataType]], stage: str) -> None:
    cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(stage)))
    for name in TABLES:
        cols = [
            sql.SQL("{} {}{}").format(
                sql.Identifier(column),
                sql.SQL(sql_type(dtype)),
                sql.SQL(" NOT NULL") if column.startswith("id_") else sql.SQL(""),
            )
            for column, dtype in schemas[name].items()
        ]
        cur.execute(
            sql.SQL("CREATE TABLE {}.{} ({})").format(
                sql.Identifier(stage), sql.Identifier(name), sql.SQL(", ").join(cols)
            )
        )


def add_constraints(cur, stage: str, schemas: dict[str, dict[str, pl.DataType]]) -> None:
    for name in DIMENSIONS:
        pk = f"id_{name[4:]}"
        cur.execute(
            sql.SQL("ALTER TABLE {}.{} ADD PRIMARY KEY ({})").format(
                sql.Identifier(stage), sql.Identifier(name), sql.Identifier(pk)
            )
        )
    for name in FACTS:
        keys = UNIQUE_KEYS[name]
        # NULLS NOT DISTINCT garante que chaves com valores ausentes também sejam únicas.
        cur.execute(
            sql.SQL("CREATE UNIQUE INDEX {} ON {}.{} ({}) NULLS NOT DISTINCT").format(
                sql.Identifier(f"uq_{name}"),
                sql.Identifier(stage),
                sql.Identifier(name),
                sql.SQL(", ").join(map(sql.Identifier, keys)),
            )
        )
        for key, dimension in FOREIGN_KEYS.items():
            if key not in schemas[name]:
                continue
            cur.execute(
                sql.SQL("ALTER TABLE {}.{} ADD FOREIGN KEY ({}) REFERENCES {}.{} ({})").format(
                    sql.Identifier(stage),
                    sql.Identifier(name),
                    sql.Identifier(key),
                    sql.Identifier(stage),
                    sql.Identifier(dimension),
                    sql.Identifier(key),
                )
            )
            cur.execute(
                sql.SQL("CREATE INDEX {} ON {}.{} ({})").format(
                    sql.Identifier(f"ix_{name}_{key}"),
                    sql.Identifier(stage),
                    sql.Identifier(name),
                    sql.Identifier(key),
                )
            )
