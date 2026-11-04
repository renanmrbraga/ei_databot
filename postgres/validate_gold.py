"""Valida contratos do ETL, documentação e tabelas Gold, sem alterar o banco.

Na raiz do repositório:
    python -m postgres.validate_gold --offline
    python -m postgres.validate_gold --report reports/validacao_gold.json
    python -m postgres.validate_gold --deep --report reports/validacao_gold.json

Por padrão, as consultas ao banco são somente de leitura. O modo --deep
executa verificações mais custosas em tabelas fato.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_FILE = ROOT / "etl" / "educacao" / "schema.py"
DOCS_DIR = ROOT / "docs"

# Prefixo de ID -> (tabela Gold, contrato do ETL, chave de unicidade do ETL)
FACTS = {
    "CAT-ES-": (
        "fact_educacao_superior",
        "SCHEMA_FACT_EDUCACAO_SUPERIOR",
        "CHAVE_FACT_EDUCACAO_SUPERIOR",
    ),
    "CAT-EST-": (
        "fact_educacao_superior_turno",
        "SCHEMA_FACT_EDUCACAO_SUPERIOR_TURNO",
        "CHAVE_FACT_EDUCACAO_SUPERIOR_TURNO",
    ),
    "CAT-EB-": (
        "fact_educacao_basica",
        "SCHEMA_FACT_EDUCACAO_BASICA",
        "CHAVE_FACT_EDUCACAO_BASICA",
    ),
    "CAT-AVC-": (
        "fact_avaliacao_curso_superior",
        "SCHEMA_FACT_AVALIACAO_CURSO_SUPERIOR",
        "CHAVE_FACT_AVALIACAO_CURSO_SUPERIOR",
    ),
    "CAT-AVI-": ("fact_avaliacao_ies", "SCHEMA_FACT_AVALIACAO_IES", "CHAVE_FACT_AVALIACAO_IES"),
}

RELATIONSHIPS = {
    "fact_educacao_superior": ("id_ies", "id_curso_superior", "id_localidade", "id_calendario"),
    "fact_educacao_superior_turno": (
        "id_ies",
        "id_curso_superior",
        "id_localidade",
        "id_calendario",
    ),
    "fact_educacao_basica": ("id_escola", "id_localidade", "id_calendario"),
    "fact_avaliacao_curso_superior": (
        "id_ies",
        "id_curso_superior",
        "id_localidade",
        "id_calendario",
    ),
    "fact_avaliacao_ies": ("id_ies", "id_calendario"),
}

COVERAGE_FIELDS = {
    "fact_educacao_superior": ("matriculados", "ingressantes", "concluintes"),
    "fact_educacao_superior_turno": ("matriculados",),
    "fact_educacao_basica": ("matriculas_educacao_basica",),
    "fact_avaliacao_curso_superior": ("enade_conceito_faixa", "cpc_faixa", "idd_faixa"),
    "fact_avaliacao_ies": ("igc_faixa", "igc_continuo"),
}

DOC_NAMES = (
    "educacao_superior.md",
    "educacao_basica.md",
    "avaliacoes.md",
    "indicadores.md",
    "regras_gerais.md",
)


def record(results: list[dict[str, Any]], status: str, code: str, message: str) -> None:
    results.append({"status": status, "code": code, "message": message})
    print(f"{status:<6} | {code:<20} | {message}")


def load_contracts() -> tuple[dict[str, dict[str, str]], dict[str, list[str]]]:
    """Lê somente a AST de schema.py, sem importar/rodar o ETL."""
    parsed = ast.parse(CONTRACT_FILE.read_text(encoding="utf-8-sig"))
    schemas: dict[str, dict[str, str]] = {}
    keys: dict[str, list[str]] = {}

    for node in parsed.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        name = target.id
        if name.startswith("SCHEMA_") and isinstance(node.value, ast.Dict):
            columns: dict[str, str] = {}
            for col, dtype in zip(node.value.keys, node.value.values, strict=True):
                if not isinstance(col, ast.Constant) or not isinstance(col.value, str):
                    continue
                if isinstance(dtype, ast.Attribute):
                    columns[col.value] = dtype.attr
            schemas[name] = columns
        elif name.startswith("CHAVE_") and isinstance(node.value, (ast.List, ast.Tuple)):
            try:
                raw = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
            if all(isinstance(x, str) for x in raw):
                keys[name] = raw

    return schemas, keys


def load_catalog_ids() -> dict[str, list[tuple[str, str]]]:
    """Lê linhas CAT-* da tabela Markdown, sem executar conteúdo documental."""
    text = (DOCS_DIR / "indicadores.md").read_text(encoding="utf-8-sig")
    catalog: dict[str, list[tuple[str, str]]] = {prefix: [] for prefix in FACTS}
    for line in text.splitlines():
        if not line.startswith("| `CAT-"):
            continue
        parts = [part.strip().strip("`") for part in line.strip().strip("|").split("|")]
        if len(parts) < 3:
            continue
        identifier, column = parts[:2]
        for prefix in FACTS:
            if re.fullmatch(re.escape(prefix) + r"\d{3}", identifier):
                catalog[prefix].append((identifier, column))
                break
    return catalog


def validate_offline(
    results: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, str]], dict[str, list[str]], dict[str, list[tuple[str, str]]]]:
    missing = [name for name in DOC_NAMES if not (DOCS_DIR / name).is_file()]
    if missing:
        record(results, "ERRO", "DOCS_AUSENTES", ", ".join(missing))
        raise FileNotFoundError("Documentos obrigatórios ausentes em docs/")
    record(results, "OK", "DOCS", "Cinco documentos encontrados em docs/.")

    for name in DOC_NAMES:
        content = (DOCS_DIR / name).read_text(encoding="utf-8-sig")
        match = re.search(r"(?m)^status:\s*[\"']?([^\n\"']+)", content[:1300])
        status = match.group(1).strip() if match else "não declarado"
        if status.lower() not in {"aprovado", "aprovada"}:
            record(results, "ALERTA", "DOC_REVISAO", f"{name}: status={status}")

    schemas, keys = load_contracts()
    catalog = load_catalog_ids()
    ids = [identifier for rows in catalog.values() for identifier, _ in rows]
    duplicates = sorted(i for i, count in Counter(ids).items() if count > 1)
    if duplicates:
        record(results, "ERRO", "CAT_IDS_DUPLICADOS", ", ".join(duplicates))
    else:
        record(results, "OK", "CAT_IDS", f"{len(ids)} IDs de métricas sem duplicação.")

    for prefix, (table, schema_name, key_name) in FACTS.items():
        contract = schemas.get(schema_name)
        if contract is None:
            record(results, "ERRO", "CONTRATO_AUSENTE", schema_name)
            continue
        if key_name not in keys:
            record(results, "ERRO", "CHAVE_AUSENTE", key_name)
        columns = [column for _, column in catalog[prefix]]
        missing_cols = sorted(set(columns) - set(contract))
        if missing_cols:
            record(results, "ERRO", "CAT_COLUNA", f"{table}: {missing_cols}")
        elif not columns:
            record(results, "ERRO", "CAT_VAZIO", f"{table}: nenhum campo catalogado")
        else:
            record(results, "OK", "CAT_CONTRATO", f"{table}: {len(columns)} métricas conferidas.")
        if len(columns) != len(set(columns)):
            record(results, "ERRO", "CAT_COLUNA_DUP", table)
    return schemas, keys, catalog


def validate_database(
    results: list[dict[str, Any]],
    schemas: dict[str, dict[str, str]],
    keys: dict[str, list[str]],
    catalog: dict[str, list[tuple[str, str]]],
    *,
    deep: bool,
    timeout_seconds: int,
) -> dict[str, Any]:
    from psycopg import sql

    from chatbot.core.database import get_connection

    names = [table for table, _, _ in FACTS.values()]
    lookup_names = (
        "dim_curso_superior",
        "dim_localidade",
        "dim_ies",
        "dim_escola",
        "dim_calendario",
    )
    all_names = names + list(lookup_names)
    coverage: dict[str, Any] = {}
    with get_connection() as conn:
        conn.execute(
            "SELECT pg_catalog.set_config('statement_timeout', %s, true)", (f"{timeout_seconds}s",)
        )
        physical_rows = conn.execute(
            """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'gold' AND table_name = ANY(%s)
            ORDER BY table_name, ordinal_position
            """,
            (all_names,),
        ).fetchall()
        physical: dict[str, dict[str, str]] = {name: {} for name in all_names}
        for row in physical_rows:
            physical[row["table_name"]][row["column_name"]] = row["data_type"]

        catalog_rows = conn.execute(
            """
            SELECT object_name, definition
            FROM rag.schema_catalog
            WHERE object_name = ANY(%s)
            """,
            ([f"gold.{name}" for name in names],),
        ).fetchall()
        snapshots = {row["object_name"]: row["definition"] for row in catalog_rows}

        for prefix, (table, schema_name, _) in FACTS.items():
            actual = physical[table]
            expected = schemas[schema_name]
            if not actual:
                record(results, "ERRO", "GOLD_TABELA", f"gold.{table} não localizada")
                continue
            absent = sorted(set(expected) - set(actual))
            extra = sorted(set(actual) - set(expected))
            if absent:
                record(results, "ERRO", "GOLD_COLUNAS", f"{table}: ausentes {absent}")
            elif extra:
                record(results, "ALERTA", "GOLD_EXTRAS", f"{table}: colunas extras {extra}")
            else:
                record(results, "OK", "GOLD_COLUNAS", f"{table}: {len(actual)} colunas")

            undocumented = sorted({column for _, column in catalog[prefix]} - set(actual))
            if undocumented:
                record(results, "ERRO", "GOLD_INDICADORES", f"{table}: {undocumented}")

            snapshot = snapshots.get(f"gold.{table}")
            if not isinstance(snapshot, dict):
                record(
                    results, "ERRO", "RAG_CATALOGO", f"gold.{table} ausente de rag.schema_catalog"
                )
            else:
                saved_cols = {
                    item["name"]: item["data_type"]
                    for item in snapshot.get("columns", [])
                    if isinstance(item, dict) and "name" in item and "data_type" in item
                }
                if set(saved_cols) != set(actual):
                    record(results, "ERRO", "RAG_DESATUALIZADO", f"{table}: colunas divergentes")
                else:
                    incompatible_types = sorted(
                        col for col, dtype in saved_cols.items() if dtype != actual[col]
                    )
                    if incompatible_types:
                        record(
                            results,
                            "ALERTA",
                            "RAG_TIPOS",
                            f"{table}: conferir tipos {incompatible_types}",
                        )
                    else:
                        record(results, "OK", "RAG_CATALOGO", f"gold.{table} sincronizado")

        # Dados agregados por ano: cinco scans controlados, sem trazer linhas completas.
        for table, fields in COVERAGE_FIELDS.items():
            if not physical[table] or not set(fields).issubset(physical[table]):
                continue
            columns = sql.SQL(", ").join(
                sql.SQL("COUNT({})::bigint AS {}").format(
                    sql.Identifier(field), sql.Identifier(field)
                )
                for field in fields
            )
            query = sql.SQL(
                "SELECT ano, COUNT(*)::bigint AS linhas, {} FROM {} GROUP BY ano ORDER BY ano"
            ).format(columns, sql.Identifier("gold", table))
            rows = conn.execute(query).fetchall()
            coverage[table] = rows
            if rows:
                years = ", ".join(str(row["ano"]) for row in rows)
                record(results, "OK", "COBERTURA_ANOS", f"{table}: {years}")
            else:
                record(results, "ALERTA", "SEM_REGISTROS", f"{table}: sem linhas")

        # Verifica que as FKs publicadas não estão declaradas como NOT VALID.
        constraint_rows = conn.execute(
            """
            SELECT c.conrelid::regclass::text AS object_name,
                   COUNT(*) FILTER (WHERE c.contype = 'f')::int AS fks,
                   COUNT(*) FILTER (WHERE c.contype = 'f' AND NOT c.convalidated)::int AS nao_validadas
            FROM pg_catalog.pg_constraint c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.connamespace
            WHERE n.nspname = 'gold' AND c.contype IN ('p', 'f')
            GROUP BY c.conrelid
            """
        ).fetchall()
        info = {row["object_name"]: row for row in constraint_rows}
        for table in names:
            item = info.get(f"gold.{table}")
            if item is None:
                record(results, "ALERTA", "FK_CONSTRAINT", f"{table}: nenhuma PK/FK declarada")
            elif item["nao_validadas"]:
                record(
                    results, "ALERTA", "FK_NAO_VALIDADA", f"{table}: {item['nao_validadas']} FK(s)"
                )

        if deep:
            fk_rows = conn.execute(
                """
                SELECT tbl.relname AS table_name, att.attname AS column_name,
                       con.convalidated AS validated
                FROM pg_catalog.pg_constraint con
                JOIN pg_catalog.pg_class tbl ON tbl.oid = con.conrelid
                JOIN pg_catalog.pg_namespace ns ON ns.oid = tbl.relnamespace
                JOIN LATERAL unnest(con.conkey) AS key_att(num) ON TRUE
                JOIN pg_catalog.pg_attribute att
                  ON att.attrelid = con.conrelid AND att.attnum = key_att.num
                WHERE ns.nspname = 'gold' AND con.contype = 'f'
                """
            ).fetchall()
            enforced = {
                (row["table_name"], row["column_name"]) for row in fk_rows if row["validated"]
            }
            for table, foreign_keys in RELATIONSHIPS.items():
                for foreign_key in foreign_keys:
                    dim = f"dim_{foreign_key.removeprefix('id_')}"
                    if not physical[table] or not physical[dim]:
                        record(results, "ERRO", "RELACAO_AUSENTE", f"{table}.{foreign_key} → {dim}")
                        continue
                    if foreign_key not in physical[table] or foreign_key not in physical[dim]:
                        record(results, "ERRO", "RELACAO_COLUNA", f"{table}.{foreign_key} → {dim}")
                        continue
                    if (table, foreign_key) in enforced:
                        record(results, "OK", "FK_VALIDADA", f"{table}.{foreign_key} (constraint)")
                        continue
                    # Na ausência de FK validada, a consulta verifica a integridade
                    # sem modificar o Gold. LIMIT 1 evita contar todos os órfãos.
                    check = sql.SQL(
                        "SELECT EXISTS (SELECT 1 FROM {} f "
                        "WHERE f.{} IS NULL OR NOT EXISTS "
                        "(SELECT 1 FROM {} d WHERE d.{} = f.{}) "
                        "LIMIT 1) AS orfao"
                    ).format(
                        sql.Identifier("gold", table),
                        sql.Identifier(foreign_key),
                        sql.Identifier("gold", dim),
                        sql.Identifier(foreign_key),
                        sql.Identifier(foreign_key),
                    )
                    orphan = conn.execute(check).fetchone()["orfao"]
                    record(
                        results,
                        "ERRO" if orphan else "OK",
                        "RELACAO_DADOS",
                        f"{table}.{foreign_key}: "
                        f"{'chave nula/órfã' if orphan else 'sem órfãos (consulta)'}",
                    )

            for table, _, key_name in FACTS.values():
                if not physical[table]:
                    continue
                key_columns = keys.get(key_name, [])
                if not key_columns or not set(key_columns).issubset(physical[table]):
                    record(results, "ERRO", "CHAVE_INVALIDA", f"{table}: {key_columns}")
                    continue
                fields = sql.SQL(", ").join(map(sql.Identifier, key_columns))
                query = sql.SQL(
                    "SELECT EXISTS ("
                    " SELECT 1 FROM {} GROUP BY {} HAVING COUNT(*) > 1 LIMIT 1"
                    ") AS duplicado"
                ).format(sql.Identifier("gold", table), fields)
                duplicate = conn.execute(query).fetchone()["duplicado"]
                record(
                    results,
                    "ERRO" if duplicate else "OK",
                    "UNICIDADE",
                    f"{table}: {'duplicidades encontradas' if duplicate else 'sem duplicidades'}",
                )

            if all(
                physical[t]
                for t in ("fact_educacao_superior", "dim_curso_superior", "dim_localidade")
            ):
                geo = conn.execute(
                    """
                    SELECT
                        COUNT(*) FILTER (WHERE c.modalidade_curso = 'EAD') AS total_ead,
                        COUNT(*) FILTER (
                            WHERE c.modalidade_curso = 'EAD'
                              AND l.codigo_municipio IS DISTINCT FROM -1
                        ) AS ead_localidade_inesperada,
                        COUNT(*) FILTER (
                            WHERE c.modalidade_curso = 'PRESENCIAL'
                              AND l.codigo_municipio = -1
                        ) AS presencial_na_sentinela
                    FROM gold.fact_educacao_superior f
                    JOIN gold.dim_curso_superior c ON c.id_curso_superior = f.id_curso_superior
                    JOIN gold.dim_localidade l ON l.id_localidade = f.id_localidade
                    """
                ).fetchone()
                bad = geo["ead_localidade_inesperada"] + geo["presencial_na_sentinela"]
                record(
                    results,
                    "ERRO" if bad else "OK",
                    "EAD_GEO",
                    f"EAD: {geo['total_ead']} linhas; desvios: {bad}",
                )

            if physical["fact_educacao_superior_turno"]:
                turns = conn.execute(
                    """
                    SELECT COUNT(*) FILTER (
                        WHERE t.turno_curso IS NULL
                           OR t.turno_curso NOT IN ('DIURNO', 'NOTURNO')
                           OR c.modalidade_curso IS DISTINCT FROM 'PRESENCIAL'
                    ) AS fora_regra
                    FROM gold.fact_educacao_superior_turno t
                    JOIN gold.dim_curso_superior c ON c.id_curso_superior = t.id_curso_superior
                    """
                ).fetchone()
                count = turns["fora_regra"]
                record(
                    results,
                    "ERRO" if count else "OK",
                    "TURNO_PRESENCIAL",
                    f"{count} registros fora da regra",
                )

    return coverage


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Confere documentos e contratos sem conectar ao banco",
    )
    parser.add_argument(
        "--deep", action="store_true", help="Executa testes de unicidade, EAD e turno"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout SQL por consulta, em segundos (padrão: 120)",
    )
    parser.add_argument("--report", type=Path, help="Salva relatório JSON neste caminho")
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error("--timeout deve ser maior ou igual a 1")

    results: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "executado_em_utc": datetime.now(UTC).isoformat(),
        "modo": "offline" if args.offline else "deep" if args.deep else "padrao",
        "checks": results,
    }
    try:
        schemas, keys, catalog = validate_offline(results)
        if not args.offline:
            report["cobertura"] = validate_database(
                results,
                schemas,
                keys,
                catalog,
                deep=args.deep,
                timeout_seconds=args.timeout,
            )
    except (FileNotFoundError, SyntaxError, ValueError, OSError) as exc:
        record(results, "ERRO", "EXECUCAO", f"{type(exc).__name__}: {exc}")
    except psycopg.Error as exc:
        # Não revela credenciais/DSN em logs: há erros do psycopg que expõem host/usuário.
        record(
            results, "ERRO", "BANCO", f"{type(exc).__name__}; confira o PostgreSQL e os logs locais"
        )

    counts = Counter(check["status"] for check in results)
    report["resumo"] = dict(counts)
    print(f"\nResumo: {counts['OK']} OK, {counts['ALERTA']} alertas, {counts['ERRO']} erros")

    if args.report is not None:
        target = args.report if args.report.is_absolute() else ROOT / args.report
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
        )
        print(f"Relatório: {target}")

    return 1 if counts["ERRO"] else 0


if __name__ == "__main__":
    sys.exit(main())
