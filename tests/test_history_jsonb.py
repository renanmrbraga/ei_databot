"""Testes offline do histórico em JSONB, sem conexão real ou API Gemini."""

from __future__ import annotations

import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Any, Self
from unittest.mock import patch
from uuid import UUID

from chatbot.services.history import (
    excluir_sessao,
    listar_mensagens_sessao,
    recuperar_historico,
    registrar_interacao,
)

SESSION_ID = UUID("cdde4cba-d349-4f2d-95ce-58b1b0ff3237")
ROOT = Path(__file__).resolve().parents[1]


class FakeJsonb:
    def __init__(self, obj: dict[str, Any]) -> None:
        self.obj = obj


class FakeConnection:
    def __init__(
        self,
        rows: list[dict[str, Any]] | None = None,
        row: dict[str, Any] | None = None,
    ) -> None:
        self.rows = rows or []
        self.row = row
        self.calls: list[tuple[str, Any]] = []

    def execute(self, query: str, params: Any) -> Self:
        self.calls.append((query, params))
        return self

    def fetchall(self) -> list[dict[str, Any]]:
        return self.rows

    def fetchone(self) -> dict[str, Any] | None:
        return self.row


def fake_modules(connection: FakeConnection) -> dict[str, ModuleType]:
    database = ModuleType("chatbot.core.database")

    @contextmanager
    def get_connection(*, read_only: bool = True) -> Any:
        yield connection

    database.get_connection = get_connection

    psycopg = ModuleType("psycopg")
    psycopg.__path__ = []
    psycopg_types = ModuleType("psycopg.types")
    psycopg_types.__path__ = []
    psycopg_json = ModuleType("psycopg.types.json")
    psycopg_json.Jsonb = FakeJsonb
    return {
        "chatbot.core.database": database,
        "psycopg": psycopg,
        "psycopg.types": psycopg_types,
        "psycopg.types.json": psycopg_json,
    }


class HistoryJsonbTest(unittest.TestCase):
    def test_schema_contem_duas_tabelas_e_integridade(self) -> None:
        schema = (ROOT / "postgres/app_schema.sql").read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE IF NOT EXISTS app.sessions", schema)
        self.assertIn("CREATE TABLE IF NOT EXISTS app.messages", schema)
        self.assertIn("content jsonb NOT NULL", schema)
        self.assertIn("ON DELETE CASCADE", schema)
        self.assertIn("role IN ('user', 'assistant')", schema)

    def test_recupera_texto_ordenado(self) -> None:
        connection = FakeConnection(
            [
                {"role": "user", "content": {"text": "Quantas matrículas?"}},
                {"role": "assistant", "content": {"text": "56.498"}},
            ]
        )
        with patch.dict(sys.modules, fake_modules(connection)):
            historico = recuperar_historico(SESSION_ID, limite=2)

        self.assertEqual(
            historico,
            [
                {"role": "user", "text": "Quantas matrículas?"},
                {"role": "assistant", "text": "56.498"},
            ],
        )
        self.assertEqual(connection.calls[0][1], (SESSION_ID, 2))
        self.assertIn("ORDER BY id DESC", connection.calls[0][0])
        self.assertIn("ORDER BY id ASC", connection.calls[0][0])

    def test_limite_invalido(self) -> None:
        with self.assertRaises(ValueError):
            recuperar_historico(SESSION_ID, limite=51)

    def test_persiste_pergunta_e_resposta_em_uma_transacao(self) -> None:
        connection = FakeConnection()
        with patch.dict(sys.modules, fake_modules(connection)):
            registrar_interacao(
                SESSION_ID,
                pergunta="  Quantas matrículas? ",
                resposta="  56.498  ",
                indicador_id="CAT-EB-001",
                filtros={"ano_inicial": 2025, "ano_final": 2025},
                fontes=["INEP"],
                avisos=[],
            )

        self.assertEqual(len(connection.calls), 2)
        self.assertIn("INSERT INTO app.sessions", connection.calls[0][0])
        self.assertIn("INSERT INTO app.messages", connection.calls[1][0])
        self.assertEqual(connection.calls[1][1][0], SESSION_ID)
        self.assertEqual(connection.calls[1][1][2], SESSION_ID)
        self.assertEqual(connection.calls[1][1][1].obj, {"text": "Quantas matrículas?"})
        assistant = connection.calls[1][1][3].obj
        self.assertEqual(assistant["text"], "56.498")
        self.assertEqual(assistant["indicador_id"], "CAT-EB-001")
        self.assertNotIn("dados_brutos", assistant)
        self.assertNotIn("sql", assistant)

    def test_listagem_recupera_texto_fontes_e_avisos_da_sessao(self) -> None:
        connection = FakeConnection(
            rows=[
                {"id": 1, "role": "user", "content": {"text": "Pergunta"}},
                {
                    "id": 2,
                    "role": "assistant",
                    "content": {
                        "text": "Resposta",
                        "fontes": ["INEP"],
                        "avisos": ["Nota"],
                    },
                },
            ]
        )
        with patch.dict(sys.modules, fake_modules(connection)):
            mensagens = listar_mensagens_sessao(SESSION_ID)

        self.assertEqual(
            mensagens,
            [
                {"id": "1", "role": "user", "content": "Pergunta"},
                {
                    "id": "2",
                    "role": "assistant",
                    "content": "Resposta",
                    "sources": ["INEP"],
                    "warnings": ["Nota"],
                },
            ],
        )
        consulta, parametros = connection.calls[0]
        self.assertIn("WHERE session_id = %s", consulta)
        self.assertEqual(parametros, (SESSION_ID, 100))

    def test_exclusao_atinge_apenas_uuid_informado(self) -> None:
        connection = FakeConnection(row={"id": SESSION_ID})
        with patch.dict(sys.modules, fake_modules(connection)):
            self.assertTrue(excluir_sessao(SESSION_ID))
        consulta, parametros = connection.calls[0]
        self.assertIn("DELETE FROM app.sessions WHERE id = %s RETURNING id", consulta)
        self.assertEqual(parametros, (SESSION_ID,))

        inexistente = FakeConnection(row=None)
        with patch.dict(sys.modules, fake_modules(inexistente)):
            self.assertFalse(excluir_sessao(SESSION_ID))


if __name__ == "__main__":
    unittest.main()
