"""Conexões PostgreSQL usando psycopg 3, sem SQLAlchemy."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from chatbot.core.config import get_settings


@contextmanager
def get_connection(*, read_only: bool = True) -> Iterator[psycopg.Connection]:
    """Abre e encerra uma conexão por operação.

    Por padrão, permite somente leitura (schemas gold/rag). Para persistir
    histórico no schema app, chame get_connection(read_only=False).
    O context manager faz commit ao concluir ou rollback em exceções.
    """
    settings = get_settings()

    with psycopg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        connect_timeout=settings.postgres_connect_timeout,
        row_factory=dict_row,
    ) as connection:
        if read_only:
            connection.execute("SET TRANSACTION READ ONLY")
        yield connection
