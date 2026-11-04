"""Configurações do backend, carregadas do .env na raiz do repositório."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


def _integer(name: str, default: int, minimum: int = 0) -> int:
    raw = os.getenv(name, str(default))

    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} deve ser um número inteiro.") from exc

    if value < minimum:
        raise ValueError(f"{name} deve ser maior ou igual a {minimum}.")

    return value


@dataclass(frozen=True, slots=True)
class Settings:
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str = field(repr=False)
    postgres_connect_timeout: int = 5
    llm_provider: str = "gemini"
    llm_model: str = "gemini-3.8-flash"
    llm_api_key: str = field(default="", repr=False)
    llm_max_retries: int = 2

    def require_llm_key(self) -> str:
        if not self.llm_api_key or self.llm_api_key in {
            "sua_chave_aqui",
            "Colocar_Sua_Chave_Aqui",
        }:
            raise ValueError("LLM_API_KEY não configurada no .env da raiz.")

        return self.llm_api_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Carrega a configuração sob demanda, sem iniciar serviços na importação."""
    load_dotenv(ENV_FILE, override=False)

    password = os.getenv("POSTGRES_PASSWORD", "")
    if not password or password == "Colocar_Sua_Senha_Aqui":
        raise ValueError("POSTGRES_PASSWORD não configurada no ambiente.")

    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    if provider != "gemini":
        raise ValueError(f"LLM_PROVIDER não suportado nesta etapa: {provider}")

    port = _integer("POSTGRES_PORT", 5432, minimum=1)
    if port > 65535:
        raise ValueError("POSTGRES_PORT deve ser menor ou igual a 65535.")

    return Settings(
        postgres_host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        postgres_port=port,
        postgres_db=os.getenv("POSTGRES_DB", "chatbot"),
        postgres_user=os.getenv("POSTGRES_USER", "postgres"),
        postgres_password=password,
        postgres_connect_timeout=_integer("POSTGRES_CONNECT_TIMEOUT", 5, minimum=1),
        llm_provider=provider,
        llm_model=os.getenv("LLM_MODEL", "gemini-3.8-flash"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_max_retries=_integer("LLM_MAX_RETRIES", 2),
    )
