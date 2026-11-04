"""Indexa documentos de negocio em docs/ no PostgreSQL pgvector.

Uso:
    python -m postgres.sync_rag --dry-run
    python -m postgres.sync_rag

Nao modifica docs/ ou gold; nao aprova regras; documentos sem metadados
de categoria de negocio sao ignorados.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

from chatbot.core.config import PROJECT_ROOT, get_settings
from chatbot.core.database import get_connection

LOG = logging.getLogger("sync_rag")
DOCS = PROJECT_ROOT / "docs"
MODEL_DEFAULT = "gemini-embedding-001"
DIMENSIONS = 768  # rag.chunks.embedding vector(768)
MAX_CHARS = 2300
BUSINESS_CATEGORIES = {"regras_de_negocio", "catalogo_de_indicadores", "regras_transversais"}
RULE_RE = re.compile(r"\b(?:CAT|RG|ES|EB|AV)-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
QUALIFIED_COL_RE = re.compile(r"\bgold\.([a-z][a-z0-9_]*)\.([a-z][a-z0-9_]*)\b")
CATALOG_LINE_RE = re.compile(r"\|\s*`(CAT-(?:ES|EST|EB|AVC|AVI)-\d{3})`\s*\|\s*`([a-z][a-z0-9_]*)`")
CATALOG_TABLES = {
    "CAT-ES-": "gold.fact_educacao_superior",
    "CAT-EST-": "gold.fact_educacao_superior_turno",
    "CAT-EB-": "gold.fact_educacao_basica",
    "CAT-AVC-": "gold.fact_avaliacao_curso_superior",
    "CAT-AVI-": "gold.fact_avaliacao_ies",
}


class EmbeddingLimitReached(RuntimeError):
    """Limite temporario da API; dados e cache ja gravados continuam intactos."""


@dataclass(frozen=True, slots=True)
class Chunk:
    position: int
    section: str
    content: str
    digest: str
    rule_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Document:
    source_path: str
    title: str
    text: str
    digest: str
    metadata: dict[str, Any]
    chunks: tuple[Chunk, ...]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_rule_ids(text: str) -> tuple[str, ...]:
    return tuple(sorted(set(RULE_RE.findall(text))))


def parse_frontmatter(text: str) -> dict[str, str]:
    """Le apenas escalares YAML necessarios, sem dependencias extras."""
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("Frontmatter YAML nao foi fechado.")
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if line and not line.startswith((" ", "\t", "#", "-")) and ":" in line:
            key, val = line.split(":", 1)
            result[key.strip()] = val.strip().strip("\"'")
    return result


def _split_line(line: str, limit: int) -> list[str]:
    """Quebra uma linha excessivamente longa sem exceder o limite em caracteres."""
    if len(line) <= limit:
        return [line]
    pieces: list[str] = []
    while len(line) > limit:
        split_at = line.rfind(" ", 0, limit + 1)
        if split_at < limit // 2:
            split_at = limit
        pieces.append(line[:split_at].strip())
        line = line[split_at:].strip()
    if line:
        pieces.append(line)
    return pieces


def make_chunks(text: str, title: str) -> tuple[Chunk, ...]:
    """Agrupa blocos de Markdown por secao, sem misturar secoes em chunks."""
    chunks: list[Chunk] = []
    current: list[str] = []
    section_stack: list[str] = []
    current_section = "Introducao"

    def flush() -> None:
        if not current or not "".join(current).strip():
            current.clear()
            return
        content = f"Documento: {title}\nSecao: {current_section}\n\n" + "\n".join(current).strip()
        chunks.append(
            Chunk(
                position=len(chunks),
                section=current_section,
                content=content,
                digest=sha256(content),
                rule_ids=extract_rule_ids(content),
            )
        )
        current.clear()

    # Ignorar frontmatter para embedding; a mesma informacao fica em metadata.
    body = text
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end >= 0:
            body = text[end + 4 :]
    for line in body.splitlines():
        header = re.match(r"^(#{1,6})\s+(.+)$", line)
        if header:
            flush()
            depth = len(header.group(1))
            section_stack = section_stack[: depth - 1] + [header.group(2).strip()]
            current_section = " > ".join(section_stack)
            continue
        header_size = len(f"Documento: {title}\nSecao: {current_section}\n\n")
        body_limit = MAX_CHARS - header_size
        if body_limit < 500:
            raise ValueError(f"Titulo/secao demasiadamente longos: {title}")
        for part in _split_line(line, body_limit):
            if current and len("\n".join(current)) + len(part) + 1 > body_limit:
                flush()
            current.append(part)
    flush()
    return tuple(chunks)


def load_documents(docs_dir: Path = DOCS) -> tuple[Document, ...]:
    if not docs_dir.is_dir():
        raise FileNotFoundError(f"Diretorio nao encontrado: {docs_dir}")
    docs: list[Document] = []
    for path in sorted(docs_dir.glob("*.md"), key=lambda p: p.name):
        text = path.read_text(encoding="utf-8-sig")
        metadata = parse_frontmatter(text)
        if metadata.get("categoria") not in BUSINESS_CATEGORIES:
            LOG.info("IGNORADO | %s (sem categoria de regra de negocio)", path.name)
            continue
        for key in ("id", "categoria", "versao", "status"):
            if not metadata.get(key):
                raise ValueError(f"docs/{path.name}: frontmatter exige {key!r}.")
        title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else path.stem.replace("_", " ").title()
        chunks = make_chunks(text, title)
        if not chunks:
            raise ValueError(f"Arquivo sem conteudo indexavel: {path}")
        docs.append(
            Document(
                source_path=f"docs/{path.name}",
                title=title,
                text=text,
                digest=sha256(text),
                metadata={
                    **metadata,
                    "rule_ids": list(extract_rule_ids(text)),
                    "active": True,
                },
                chunks=chunks,
            )
        )
    if not docs:
        raise ValueError("Nenhum documento de negocio elegivel encontrado em docs/.")
    return tuple(docs)


def _catalog(conn: Any) -> dict[str, set[str]]:
    rows = conn.execute(
        "SELECT object_name, definition->'columns' AS cols FROM rag.schema_catalog "
        "WHERE object_name LIKE 'gold.%'"
    ).fetchall()
    if not rows:
        raise RuntimeError("rag.schema_catalog vazio. Execute python -m postgres.sync_catalog.")
    return {row["object_name"]: {col["name"] for col in row["cols"]} for row in rows}


def catalog_warnings(doc: Document, catalog: dict[str, set[str]]) -> list[str]:
    found: set[str] = set()
    for table, col in QUALIFIED_COL_RE.findall(doc.text):
        # Placeholder didatico, nao uma referencia ao schema fisico.
        if (table, col) == ("tabela", "coluna"):
            continue
        qualified = f"gold.{table}"
        if qualified not in catalog or col not in catalog[qualified]:
            found.add(f"Coluna nao identificada: {qualified}.{col}")
    if doc.source_path == "docs/indicadores.md":
        for metric_id, col in CATALOG_LINE_RE.findall(doc.text):
            table = next(
                (t for prefix, t in CATALOG_TABLES.items() if metric_id.startswith(prefix)), None
            )
            if table and col not in catalog.get(table, set()):
                found.add(f"Indicador {metric_id}: {table}.{col} nao encontrado")
    return sorted(found)


def _validate_model(conn: Any, model: str) -> None:
    models = conn.execute("SELECT DISTINCT embedding_model FROM rag.chunks").fetchall()
    others = {row["embedding_model"] for row in models if row["embedding_model"] != model}
    if others:
        raise RuntimeError(
            f"Ja existem embeddings de outro modelo: {sorted(others)}. "
            "E necessaria uma migracao/reindexacao explicita; nao misture os vetores."
        )


def _normalise(values: list[float] | tuple[float, ...]) -> str:
    if len(values) != DIMENSIONS or not all(math.isfinite(x) for x in values):
        raise ValueError(f"Embedding invalido; esperado vetor finito de {DIMENSIONS} dimensoes")
    norm = math.sqrt(sum(x * x for x in values))
    if norm == 0:
        raise ValueError("Embedding retornou vetor nulo")
    return "[" + ",".join(format(x / norm, ".9g") for x in values) + "]"


def embed_batch(client: Any, texts: list[str], *, model: str, retries: int) -> list[str]:
    from google.genai import errors, types

    for attempt in range(retries + 1):
        try:
            response = client.models.embed_content(
                model=model,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=DIMENSIONS,
                ),
            )
            embeddings = response.embeddings or []
            if len(embeddings) != len(texts):
                raise RuntimeError(
                    f"API retornou {len(embeddings)} embeddings para {len(texts)} textos"
                )
            return [_normalise(item.values) for item in embeddings]
        except errors.APIError as exc:
            if exc.code not in (429, 503):
                raise
            if attempt >= retries:
                raise EmbeddingLimitReached(
                    f"Gemini HTTP {exc.code}. Os lotes concluídos foram salvos em "
                    "rag.embedding_cache; verifique a cota no Google AI Studio "
                    "antes de retomar."
                ) from None
            wait = 2**attempt
            LOG.warning("Gemini indisponivel/limitado (HTTP %s); retry em %ss", exc.code, wait)
            time.sleep(wait)
    raise RuntimeError("Tentativas de embeddings esgotadas")


def _cached_vectors(conn: Any, digests: list[str], model: str) -> dict[str, str]:
    """Consulta o cache persistente, inclusive de execucoes interrompidas."""
    if not digests:
        return {}
    rows = conn.execute(
        "SELECT content_hash, embedding::text AS vector FROM rag.embedding_cache "
        "WHERE content_hash = ANY(%s) AND embedding_model = %s",
        (digests, model),
    ).fetchall()
    return {row["content_hash"]: row["vector"] for row in rows}


def _save_cache(batch: list[tuple[str, str]], embedded: list[str], model: str) -> None:
    """Persiste CADA lote antes de solicitar o proximo, evitando perda por HTTP 429."""
    with get_connection(read_only=False) as conn:
        for (digest, _), vector in zip(batch, embedded, strict=True):
            conn.execute(
                """INSERT INTO rag.embedding_cache (content_hash, embedding_model, embedding)
                   VALUES (%s, %s, %s::vector)
                   ON CONFLICT (content_hash, embedding_model) DO NOTHING""",
                (digest, model, vector),
            )


def _partition_vectors(
    chunks: tuple[Chunk, ...], known: dict[str, str]
) -> tuple[dict[str, str], list[tuple[str, str]]]:
    """Separa vetores ja salvos dos fragmentos que requerem a API."""
    vectors = {chunk.digest: known[chunk.digest] for chunk in chunks if chunk.digest in known}
    missing = {chunk.digest: chunk.content for chunk in chunks if chunk.digest not in known}
    return vectors, list(missing.items())


def sync_rag(
    *,
    dry_run: bool = False,
    batch_size: int = 5,
    interval: float = 0.0,
    max_batches: int | None = None,
) -> dict[str, int]:
    """Sincroniza docs com commits por documento e reutilizacao de embeddings por hash."""
    from google import genai

    if not 1 <= batch_size <= 20:
        raise ValueError("batch_size precisa estar entre 1 e 20")
    if not math.isfinite(interval) or interval < 0:
        raise ValueError("interval precisa ser >= 0 e finito")
    if max_batches is not None and max_batches < 1:
        raise ValueError("max_batches precisa ser >= 1")
    settings = get_settings()
    model = os.getenv("RAG_EMBEDDING_MODEL", MODEL_DEFAULT).strip()
    if model != MODEL_DEFAULT:
        raise ValueError("O MVP aceita somente gemini-embedding-001 em vector(768).")
    documents = load_documents()
    stats = {
        "documentos": len(documents),
        "alterados": 0,
        "metadados": 0,
        "reutilizados": 0,
        "embeddings": 0,
        "alertas": 0,
        "desativados": 0,
        "concluidos": 0,
        "lotes_api": 0,
    }
    client = None
    last_api_call_at: float | None = None
    try:
        with get_connection() as conn:
            catalog = _catalog(conn)
            _validate_model(conn, model)
            # Em dry-run, tambem e necessario ler o cache para informar trabalho real.
            if (
                conn.execute("SELECT to_regclass('rag.embedding_cache') AS cache").fetchone()[
                    "cache"
                ]
                is None
            ):
                raise RuntimeError(
                    "rag.embedding_cache ausente. Aplique postgres/rag_embedding_cache.sql."
                )
            previous = {
                row["source_path"]: row
                for row in conn.execute(
                    """SELECT d.id, d.source_path, d.content_hash, d.metadata,
                             (SELECT COUNT(*) FROM rag.chunks c WHERE c.document_id=d.id) AS chunk_count
                       FROM rag.documents d WHERE d.source_path LIKE 'docs/%'"""
                ).fetchall()
            }
        for doc in documents:
            warnings = catalog_warnings(doc, catalog)
            for item in warnings:
                LOG.warning("%s | %s", doc.source_path, item)
            stats["alertas"] += len(warnings)
            prior = previous.get(doc.source_path)
            metadata = {
                **doc.metadata,
                "warnings": warnings,
                "embedding_model": model,
                "embedding_dimensions": DIMENSIONS,
            }
            if (
                prior
                and prior["content_hash"] == doc.digest
                and prior["metadata"].get("active", True)
                and prior["chunk_count"] == len(doc.chunks)
            ):
                if prior["metadata"] != metadata:
                    stats["metadados"] += 1
                    LOG.info("METADADOS ATUALIZADOS | %s | sem novos vetores", doc.source_path)
                    if not dry_run:
                        with get_connection(read_only=False) as conn:
                            conn.execute(
                                "UPDATE rag.documents SET metadata=%s, updated_at=now() WHERE id=%s",
                                (Jsonb(metadata), prior["id"]),
                            )
                else:
                    LOG.info("SEM ALTERACAO | %s | %s chunks", doc.source_path, len(doc.chunks))
                continue
            stats["alterados"] += 1
            with get_connection() as conn:
                known = _cached_vectors(conn, [chunk.digest for chunk in doc.chunks], model)
            vectors, missing = _partition_vectors(doc.chunks, known)
            stats["reutilizados"] += len(doc.chunks) - len(missing)
            LOG.info(
                "%s | chunks=%s | reutilizaveis=%s | novos=%s",
                doc.source_path,
                len(doc.chunks),
                len(doc.chunks) - len(missing),
                len(missing),
            )
            if dry_run:
                stats["embeddings"] += len(missing)
                continue
            if missing:
                if client is None:
                    client = genai.Client(api_key=settings.require_llm_key())
                for offset in range(0, len(missing), batch_size):
                    if max_batches is not None and stats["lotes_api"] >= max_batches:
                        LOG.warning(
                            "PAUSA VOLUNTARIA | limite de %s lotes atingido; "
                            "retome executando sync_rag novamente (cache preservado)",
                            max_batches,
                        )
                        return stats
                    batch = missing[offset : offset + batch_size]
                    # Respeita o intervalo tambem ENTRE documentos, nao so entre lotes.
                    if interval and last_api_call_at is not None:
                        remaining = interval - (time.monotonic() - last_api_call_at)
                        if remaining > 0:
                            time.sleep(remaining)
                    last_api_call_at = time.monotonic()
                    embedded = embed_batch(
                        client,
                        [content for _, content in batch],
                        model=model,
                        retries=settings.llm_max_retries,
                    )
                    # O documento so e publicado quando TODOS os lotes estiverem prontos.
                    _save_cache(batch, embedded, model)
                    vectors.update(zip((digest for digest, _ in batch), embedded, strict=True))
                    stats["embeddings"] += len(batch)
                    stats["lotes_api"] += 1
            # Tudo em uma transacao por documento: falha na API preserva versao anterior.
            with get_connection(read_only=False) as conn:
                conn.execute("SELECT pg_advisory_xact_lock(%s)", (81632572,))
                row = conn.execute(
                    """INSERT INTO rag.documents (source_path, title, content_hash, metadata)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (source_path) DO UPDATE SET
                        title = EXCLUDED.title,
                        content_hash = EXCLUDED.content_hash,
                        metadata = EXCLUDED.metadata,
                        updated_at = now()
                    RETURNING id""",
                    (doc.source_path, doc.title, doc.digest, Jsonb(metadata)),
                ).fetchone()
                doc_id = row["id"]
                conn.execute("DELETE FROM rag.chunks WHERE document_id = %s", (doc_id,))
                for chunk in doc.chunks:
                    conn.execute(
                        """INSERT INTO rag.chunks (
                            document_id, position, section, rule_ids, content,
                            content_hash, embedding, embedding_model
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s)""",
                        (
                            doc_id,
                            chunk.position,
                            chunk.section,
                            list(chunk.rule_ids),
                            chunk.content,
                            chunk.digest,
                            vectors[chunk.digest],
                            model,
                        ),
                    )
                conn.execute(
                    """INSERT INTO rag.document_versions (
                        document_id, content_hash, version_label, status, rule_ids, chunk_count
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (document_id, content_hash) DO NOTHING""",
                    (
                        doc_id,
                        doc.digest,
                        metadata["versao"],
                        metadata["status"],
                        metadata["rule_ids"],
                        len(doc.chunks),
                    ),
                )
            stats["concluidos"] += 1
        # Documentos removidos de docs/ nao podem continuar recuperaveis.
        active_paths = {doc.source_path for doc in documents}
        for path, old in previous.items():
            if path not in active_paths and old["metadata"].get("active", True):
                stats["desativados"] += 1
                LOG.warning("DESATIVADO | documento nao presente em docs/: %s", path)
                if not dry_run:
                    with get_connection(read_only=False) as conn:
                        conn.execute(
                            """UPDATE rag.documents
                            SET metadata = jsonb_set(metadata, '{active}', 'false'::jsonb), updated_at = now()
                            WHERE id = %s""",
                            (old["id"],),
                        )
    finally:
        if client is not None:
            client.close()
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexacao incremental do RAG do EI DataBot")
    parser.add_argument(
        "--dry-run", action="store_true", help="Planeja sem chamar a API nem alterar o banco"
    )
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument(
        "--interval", type=float, default=0.0, help="Pausa em segundos entre lotes de um documento"
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=None,
        help="Limita chamadas da API nesta execucao (cache e persistido)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    try:
        stats = sync_rag(
            dry_run=args.dry_run,
            batch_size=args.batch_size,
            interval=args.interval,
            max_batches=args.max_batches,
        )
    except EmbeddingLimitReached as exc:
        LOG.error("INGESTAO PARCIAL | %s", exc)
        LOG.error("Nenhum dado Gold foi alterado. Retome apos verificar as cotas.")
        raise SystemExit(2) from None
    LOG.info("RESUMO | %s", json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
