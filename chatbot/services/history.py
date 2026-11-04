"""Histórico conversacional no PostgreSQL app, com conteúdo em JSONB.

Guarda somente mensagens e metadados analíticos essenciais. Não armazena
prompts internos, chaves, vetores nem resultados SQL completos.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

MAX_MENSAGENS_CONTEXTO = 8


def recuperar_historico(
    session_id: UUID,
    *,
    limite: int = MAX_MENSAGENS_CONTEXTO,
) -> list[dict[str, str]]:
    """Busca as últimas mensagens da sessão, em ordem cronológica."""
    if not 1 <= limite <= 50:
        raise ValueError("O limite de mensagens deve estar entre 1 e 50.")

    from chatbot.core.database import get_connection

    with get_connection(read_only=True) as connection:
        linhas = connection.execute(
            """WITH mensagens_recentes AS (
                SELECT id, role, content
                FROM app.messages
                WHERE session_id = %s
                ORDER BY id DESC
                LIMIT %s
            )
            SELECT role, content
            FROM mensagens_recentes
            ORDER BY id ASC""",
            (session_id, limite),
        ).fetchall()

    return [{"role": linha["role"], "text": linha["content"]["text"]} for linha in linhas]


def registrar_interacao(
    session_id: UUID,
    *,
    pergunta: str,
    resposta: str,
    indicador_id: str | None,
    filtros: dict[str, Any],
    fontes: list[str],
    avisos: list[str],
) -> None:
    """Grava pergunta e resposta na mesma transação, sem mensagens órfãs.

    Qualquer falha de persistência aborta a transação e é propagada à API.
    """
    from psycopg.types.json import Jsonb

    from chatbot.core.database import get_connection

    conteudo_usuario = {"text": pergunta.strip()}
    conteudo_assistente = {
        "text": resposta.strip(),
        "indicador_id": indicador_id,
        "filtros": filtros,
        "fontes": fontes,
        "avisos": avisos,
    }

    with get_connection(read_only=False) as connection:
        connection.execute(
            """INSERT INTO app.sessions (id)
            VALUES (%s)
            ON CONFLICT (id) DO UPDATE
            SET updated_at = now()""",
            (session_id,),
        )
        connection.execute(
            """INSERT INTO app.messages (session_id, role, content)
            VALUES (%s, 'user', %s), (%s, 'assistant', %s)""",
            (
                session_id,
                Jsonb(conteudo_usuario),
                session_id,
                Jsonb(conteudo_assistente),
            ),
        )


def listar_mensagens_sessao(
    session_id: UUID,
    *,
    limite: int = 100,
) -> list[dict[str, Any]]:
    """Lê as mensagens de uma sessão conhecida, sem recuperar outras sessões.

    Este acesso por UUID é adequado apenas ao MVP local, sem autenticação.
    """
    if not 1 <= limite <= 100:
        raise ValueError("O limite de mensagens deve estar entre 1 e 100.")

    from chatbot.core.database import get_connection

    with get_connection(read_only=True) as connection:
        linhas = connection.execute(
            """SELECT id, role, content
            FROM (
                SELECT id, role, content
                FROM app.messages
                WHERE session_id = %s
                ORDER BY id DESC
                LIMIT %s
            ) AS recentes
            ORDER BY id ASC""",
            (session_id, limite),
        ).fetchall()

    mensagens: list[dict[str, Any]] = []
    for linha in linhas:
        conteudo = linha["content"]
        mensagem: dict[str, Any] = {
            "id": str(linha["id"]),
            "role": linha["role"],
            "content": conteudo["text"],
        }
        if linha["role"] == "assistant":
            mensagem["sources"] = conteudo.get("fontes") or []
            mensagem["warnings"] = conteudo.get("avisos") or []
        mensagens.append(mensagem)
    return mensagens


def excluir_sessao(session_id: UUID) -> bool:
    """Exclui apenas a sessão indicada e suas mensagens (FK ON DELETE CASCADE).

    Retorna False se a sessão não existir. Não afeta dados Gold ou RAG.
    Requer API local; UUID não constitui autorização de usuário.
    """
    from chatbot.core.database import get_connection

    with get_connection(read_only=False) as connection:
        excluida = connection.execute(
            "DELETE FROM app.sessions WHERE id = %s RETURNING id",
            (session_id,),
        ).fetchone()
    return excluida is not None
