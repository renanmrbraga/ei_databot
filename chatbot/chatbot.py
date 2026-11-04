"""API mínima do EI DataBot, sem inicialização de serviços legados no import."""

from __future__ import annotations

import logging
import os
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from chatbot.services.chat import responder_chat
from chatbot.services.history import excluir_sessao, listar_mensagens_sessao

logger = logging.getLogger(__name__)

app = FastAPI(title="EI DataBot API", version="2.0.0")

origens = [
    origem.strip()
    for origem in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
    if origem.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


class ChatRequest(BaseModel):
    pergunta: str = Field(min_length=1, max_length=2000)
    session_id: UUID


@app.get("/health")
def health_check() -> dict[str, str]:
    # Este endpoint verifica somente a disponibilidade HTTP, não banco/LLM.
    return {"status": "ok"}


@app.post("/api/chat")
def chat_endpoint(requisicao: ChatRequest) -> dict[str, object]:
    try:
        return responder_chat(requisicao.pergunta, requisicao.session_id)
    except Exception as exc:
        logger.exception("Falha no atendimento do chatbot")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar os serviços de dados agora.",
        ) from exc


@app.get("/api/sessions/{session_id}/messages")
def session_messages_endpoint(session_id: UUID) -> dict[str, object]:
    """Recupera somente o histórico da sessão UUID solicitada."""
    try:
        return {"session_id": str(session_id), "messages": listar_mensagens_sessao(session_id)}
    except Exception as exc:
        logger.exception("Falha ao recuperar histórico da sessão")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível recuperar o histórico agora.",
        ) from exc


@app.delete("/api/sessions/{session_id}", status_code=204)
def delete_session_endpoint(session_id: UUID) -> None:
    """Remove definitivamente uma conversa no MVP local sem autenticação."""
    try:
        encontrada = excluir_sessao(session_id)
    except Exception as exc:
        logger.exception("Falha ao excluir a sessão")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível excluir a conversa agora.",
        ) from exc
    if not encontrada:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
