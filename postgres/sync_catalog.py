"""Sincroniza metadados estruturais do schema gold com rag.schema_catalog.

Execução na raiz do projeto:
    python -m postgres.sync_catalog

Não altera as tabelas Gold e não gera embeddings.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from psycopg.types.json import Jsonb

from chatbot.core.database import get_connection

LOGGER = logging.getLogger(__name__)

TABLES_SQL = """
SELECT c.oid AS table_oid, c.relname AS table_name,
       obj_description(c.oid, 'pg_class') AS description
FROM pg_catalog.pg_class AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
WHERE n.nspname = %s
  AND c.relkind IN ('r', 'p')
ORDER BY c.relname
"""

COLUMNS_SQL = """
SELECT a.attname AS name,
       pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
       a.attnotnull AS not_null,
       pg_catalog.pg_get_expr(d.adbin, d.adrelid) AS default_value,
       pg_catalog.col_description(a.attrelid, a.attnum) AS description
FROM pg_catalog.pg_attribute AS a
LEFT JOIN pg_catalog.pg_attrdef AS d
  ON d.adrelid = a.attrelid AND d.adnum = a.attnum
WHERE a.attrelid = %s::oid
  AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY a.attnum
"""

CONSTRAINTS_SQL = """
SELECT con.conname AS name,
       CASE con.contype
           WHEN 'p' THEN 'primary_key'
           WHEN 'f' THEN 'foreign_key'
           WHEN 'u' THEN 'unique'
           WHEN 'c' THEN 'check'
           WHEN 'x' THEN 'exclusion'
           ELSE con.contype::text
       END AS kind,
       pg_catalog.pg_get_constraintdef(con.oid, true) AS definition
FROM pg_catalog.pg_constraint AS con
WHERE con.conrelid = %s::oid
ORDER BY con.contype, con.conname
"""

INDEXES_SQL = """
SELECT i.relname AS name,
       ix.indisunique AS is_unique,
       ix.indisprimary AS is_primary,
       pg_catalog.pg_get_indexdef(i.oid) AS definition
FROM pg_catalog.pg_index AS ix
JOIN pg_catalog.pg_class AS i ON i.oid = ix.indexrelid
WHERE ix.indrelid = %s::oid
ORDER BY i.relname
"""

UPSERT_SQL = """
INSERT INTO rag.schema_catalog (object_name, definition, source_hash)
VALUES (%s, %s, %s)
ON CONFLICT (object_name) DO UPDATE
SET definition = EXCLUDED.definition,
    source_hash = EXCLUDED.source_hash,
    updated_at = now()
WHERE rag.schema_catalog.source_hash IS DISTINCT FROM EXCLUDED.source_hash
RETURNING object_name
"""


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sync_catalog(source_schema: str = "gold") -> tuple[int, int, int]:
    """Sincroniza catálogo por hash. Retorna (encontradas, alteradas, obsoletas).

    Entradas antigas não são apagadas automaticamente, evitando perda
    acidental de metadados. Objetos obsoletos são reportados.
    """
    with get_connection(read_only=False) as conn:
        # Não executa alterações concorrentes ao mesmo catálogo nesta transação.
        conn.execute("SELECT pg_catalog.pg_advisory_xact_lock(%s)", (81632571,))
        exists = conn.execute("SELECT to_regclass('rag.schema_catalog') AS object_id").fetchone()
        if exists is None or exists["object_id"] is None:
            raise RuntimeError(
                "Tabela rag.schema_catalog não existe. Execute rag_schema.sql antes."
            )

        tables = conn.execute(TABLES_SQL, (source_schema,)).fetchall()
        if not tables:
            raise RuntimeError(
                f"Nenhuma tabela encontrada no schema {source_schema!r}; sincronização cancelada."
            )

        updated = 0
        current_names: set[str] = set()
        for table in tables:
            oid = table["table_oid"]
            name = f"{source_schema}.{table['table_name']}"
            current_names.add(name)
            definition: dict[str, Any] = {
                "schema": source_schema,
                "table": table["table_name"],
                "description": table["description"],
                "columns": conn.execute(COLUMNS_SQL, (oid,)).fetchall(),
                "constraints": conn.execute(CONSTRAINTS_SQL, (oid,)).fetchall(),
                "indexes": conn.execute(INDEXES_SQL, (oid,)).fetchall(),
            }
            digest = hashlib.sha256(_canonical_json(definition).encode("utf-8")).hexdigest()
            result = conn.execute(UPSERT_SQL, (name, Jsonb(definition), digest)).fetchone()
            if result is not None:
                updated += 1
                LOGGER.info("Metadados atualizados: %s", name)

        existing = conn.execute(
            "SELECT object_name FROM rag.schema_catalog WHERE object_name LIKE %s ESCAPE '\\'",
            (source_schema.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + ".%",),
        ).fetchall()
        obsolete = sorted(
            row["object_name"] for row in existing if row["object_name"] not in current_names
        )
        for name in obsolete:
            LOGGER.warning("Objeto ausente no Gold (não removido): %s", name)

    return len(tables), updated, len(obsolete)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    total, updated, obsolete = sync_catalog()
    LOGGER.info(
        "Catálogo concluído: %s tabelas, %s alterações, %s entradas antigas",
        total,
        updated,
        obsolete,
    )


if __name__ == "__main__":
    main()
