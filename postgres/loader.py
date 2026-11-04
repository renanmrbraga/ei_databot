"""Carga CSV por blocos via COPY, a partir de Polars."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import polars as pl
from psycopg import sql

NULL_TOKEN = "\\N"


def load_table(
    cur, path: Path, stage: str, table: str, columns: list[str], batch_size: int = 20_000
) -> int:
    # Mantém somente um Parquet em memória por vez; COPY recebe blocos pequenos.
    frame = pl.read_parquet(path, low_memory=True)
    if frame.columns != columns:
        raise ValueError(f"Colunas divergentes: {path}")
    # Evita confundir o texto literal \\N com o marcador de NULL do COPY CSV.
    text_columns = [c for c, dtype in frame.schema.items() if dtype == pl.String]
    for column in text_columns:
        if frame.select((pl.col(column) == NULL_TOKEN).any()).item():
            raise ValueError(f"Valor reservado {NULL_TOKEN!r} encontrado em {table}.{column}")
    query = sql.SQL("COPY {}.{} ({}) FROM STDIN WITH (FORMAT CSV, HEADER FALSE, NULL {})").format(
        sql.Identifier(stage),
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.Literal(NULL_TOKEN),
    )
    count = 0
    with cur.copy(query) as copy:
        for chunk in frame.iter_slices(n_rows=batch_size):
            stream = StringIO()
            chunk.write_csv(stream, include_header=False, null_value=NULL_TOKEN)
            copy.write(stream.getvalue().encode("utf-8"))
            count += chunk.height
    return count
