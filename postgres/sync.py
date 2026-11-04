"""Sincroniza os dez Parquets Gold em uma publicação transacional.

Uso: python -m postgres.sync --dataset educacao
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from uuid import uuid4

from psycopg import sql

from chatbot.core.database import get_connection

from .loader import load_table
from .schema import TABLES, add_constraints, create_staging, inspect_gold

ROOT = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger("postgres.sync")


def publish(cur, stage: str) -> None:
    # Todas as mudanças de schema e tabelas ocorrem na mesma transação.
    cur.execute("CREATE SCHEMA IF NOT EXISTS gold")
    for name in TABLES[::-1]:
        cur.execute(sql.SQL("DROP TABLE IF EXISTS gold.{}").format(sql.Identifier(name)))
    for name in TABLES:
        cur.execute(
            sql.SQL("ALTER TABLE {}.{} SET SCHEMA gold").format(
                sql.Identifier(stage), sql.Identifier(name)
            )
        )
    cur.execute(sql.SQL("DROP SCHEMA {}").format(sql.Identifier(stage)))


def synchronize(dataset: str, batch_size: int = 20_000) -> None:
    if dataset != "educacao":
        raise ValueError(f"Dataset não suportado: {dataset}")
    folder = ROOT / "data" / dataset / "gold"
    schemas = inspect_gold(folder)
    stage = f"gold_stage_{uuid4().hex[:12]}"
    total = 0
    with (
        get_connection(read_only=False) as conn,
        conn.cursor() as cur,
    ):
        cur.execute("SET LOCAL statement_timeout = 0")
        # Impede duas sincronizações simultâneas do mesmo dataset.
        cur.execute("SELECT pg_advisory_xact_lock(724103, 1)")
        create_staging(cur, schemas, stage)
        for name in TABLES:
            count = load_table(
                cur, folder / f"{name}.parquet", stage, name, list(schemas[name]), batch_size
            )
            cur.execute(
                sql.SQL("SELECT count(*) FROM {}.{}").format(
                    sql.Identifier(stage), sql.Identifier(name)
                )
            )
            loaded = cur.fetchone()[0]
            if loaded != count:
                raise RuntimeError(f"Contagem divergente em {name}: {count} != {loaded}")
            total += count
            LOGGER.info("%s: %s linhas", name, f"{count:,}")
        LOGGER.info("Criando índices e validando chaves...")
        add_constraints(cur, stage, schemas)
        LOGGER.info("Publicando schema gold...")
        publish(cur, stage)
        # Commit automático ao sair do contexto sem exceção.
    LOGGER.info("Sincronização concluída: %s linhas", f"{total:,}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, choices=["educacao"])
    parser.add_argument("--batch-size", type=int, default=20_000)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size deve ser maior que zero")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    synchronize(args.dataset, args.batch_size)


if __name__ == "__main__":
    main()
