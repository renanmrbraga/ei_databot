"""Recuperacao de regras do pgvector, sem atualizar conteudo na API HTTP.

Busca em producao: somente documentos com status aprovado/politica_vigente.
Para demonstrar o MVP com documentos em revisao, habilitar explicitamente
incluir_revisao=True (ou CLI --include-drafts) e mostrar o status no resultado.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from dataclasses import dataclass

from chatbot.core.config import get_settings
from chatbot.core.database import get_connection

EMBED_MODEL = "gemini-embedding-001"
EMBED_DIMENSIONS = 768


@dataclass(frozen=True, slots=True)
class RegraRecuperada:
    documento: str
    titulo: str
    versao: str
    status: str
    secao: str
    ids_regras: tuple[str, ...]
    conteudo: str
    similaridade: float
    alerta_documental: bool
    contem_pendencia: bool


def _as_vector(values: list[float]) -> str:
    if len(values) != EMBED_DIMENSIONS or not all(math.isfinite(x) for x in values):
        raise ValueError("Vetor de consulta invalido; esperado 768 dimensoes")
    norm = math.sqrt(sum(x * x for x in values))
    if not norm:
        raise ValueError("Vetor de consulta nulo")
    return "[" + ",".join(format(x / norm, ".9g") for x in values) + "]"


def buscar_regras(
    pergunta: str,
    *,
    limite: int = 5,
    incluir_revisao: bool = False,
) -> list[RegraRecuperada]:
    """Busca semantica apenas em docs/ indexados; nao gera ou aprova regras.

    Textos em revisao aparecem somente se incluir_revisao=True; a aplicacao
    deve deixa-los identificados como material ainda nao aprovado.
    """
    from google import genai
    from google.genai import types

    pergunta = pergunta.strip()
    if not pergunta:
        raise ValueError("Pergunta vazia")
    if not 1 <= limite <= 10:
        raise ValueError("Limite deve estar entre 1 e 10")
    settings = get_settings()
    if os.getenv("RAG_EMBEDDING_MODEL", EMBED_MODEL) != EMBED_MODEL:
        raise ValueError("O MVP usa gemini-embedding-001 e 768 dimensoes.")

    # Evita consumir uma chamada de API quando nao existe conteudo pesquisavel.
    with get_connection() as conn:
        count = conn.execute(
            """SELECT COUNT(*) AS total FROM rag.chunks c
            JOIN rag.documents d ON d.id = c.document_id
            WHERE d.metadata->>'active' = 'true'
              AND c.embedding_model = %s
              AND (%s OR d.metadata->>'status' IN ('aprovado', 'politica_vigente'))
              AND (%s OR c.content !~* %s)
            """,
            (EMBED_MODEL, incluir_revisao, incluir_revisao, r"\[PENDENTE\]"),
        ).fetchone()["total"]
    if not count:
        return []

    with genai.Client(api_key=settings.require_llm_key()) as client:
        response = client.models.embed_content(
            model=EMBED_MODEL,
            contents=pergunta,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=EMBED_DIMENSIONS,
            ),
        )
    if not response.embeddings or len(response.embeddings) != 1:
        raise RuntimeError("Embedding da pergunta nao retornado")
    vector = _as_vector(response.embeddings[0].values)
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT d.source_path, d.title, d.metadata,
                      c.section, c.rule_ids, c.content,
                      1 - (c.embedding <=> %s::vector) AS similarity
            FROM rag.chunks c
            JOIN rag.documents d ON d.id = c.document_id
            WHERE d.metadata->>'active' = 'true'
              AND c.embedding_model = %s
              AND (%s OR d.metadata->>'status' IN ('aprovado', 'politica_vigente'))
              AND (%s OR c.content !~* %s)
            ORDER BY c.embedding <=> %s::vector, c.id
            LIMIT %s""",
            (
                vector,
                EMBED_MODEL,
                incluir_revisao,
                incluir_revisao,
                r"\[PENDENTE\]",
                vector,
                limite,
            ),
        ).fetchall()
    return [
        RegraRecuperada(
            documento=row["source_path"],
            titulo=row["title"],
            versao=row["metadata"].get("versao", ""),
            status=row["metadata"].get("status", "indefinido"),
            secao=row["section"],
            ids_regras=tuple(row["rule_ids"]),
            conteudo=row["content"],
            similaridade=float(row["similarity"]),
            alerta_documental=bool(row["metadata"].get("warnings")),
            contem_pendencia=bool(re.search(r"\[PENDENTE\]", row["content"], flags=re.IGNORECASE)),
        )
        for row in rows
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Teste da busca RAG")
    parser.add_argument("--query", required=True, help="Pergunta em portugues")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--include-drafts",
        action="store_true",
        help="Permite resultados de documentos em revisao (MVP)",
    )
    args = parser.parse_args()
    resultados = buscar_regras(args.query, limite=args.limit, incluir_revisao=args.include_drafts)
    print(
        json.dumps(
            [
                {
                    "documento": item.documento,
                    "status": item.status,
                    "versao": item.versao,
                    "secao": item.secao,
                    "ids_regras": item.ids_regras,
                    "similaridade": round(item.similaridade, 4),
                    "alerta_documental": item.alerta_documental,
                    "contem_pendencia": item.contem_pendencia,
                    "conteudo": item.conteudo,
                }
                for item in resultados
            ],
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
