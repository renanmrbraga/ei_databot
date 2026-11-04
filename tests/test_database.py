"""Teste de composição parametrizada, sem abrir conexão PostgreSQL."""

from __future__ import annotations

import importlib.util
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from chatbot.services.analytics import consultar_gold
from chatbot.services.llm import Interpretacao


@unittest.skipUnless(importlib.util.find_spec("psycopg"), "psycopg não está instalado")
class SqlComposicaoTest(unittest.TestCase):
    def test_municipio_e_uf_sao_parametros(self) -> None:
        class ConexaoFalsa:
            consulta: object | None = None
            parametros: list[object] | None = None

            def execute(
                self, consulta: object, parametros: list[object] | None = None
            ) -> ConexaoFalsa:
                if parametros is not None:
                    self.consulta = consulta
                    self.parametros = parametros
                return self

            def fetchall(self) -> list[dict[str, int]]:
                return [{"ano": 2023, "matriculados": 123, "registros_com_valor": 2}]

        conexao = ConexaoFalsa()

        @contextmanager
        def conexao_falsa(*, read_only: bool = True):
            self.assertTrue(read_only)
            yield conexao

        interpretacao = Interpretacao(
            indicador_id="CAT-ES-023",
            municipio="Volta Redonda",
            uf="RJ",
            ano_inicial=2023,
            ano_final=2023,
            operacao="SOMA_ANUAL",
        )
        with patch("chatbot.core.database.get_connection", conexao_falsa):
            indicador, linhas = consultar_gold(interpretacao)

        self.assertEqual(indicador.coluna, "matriculados")
        self.assertEqual(linhas[0]["matriculados"], 123)
        self.assertEqual(conexao.parametros, [2023, 2023, "VOLTA REDONDA", "RJ"])
        self.assertIsNotNone(conexao.consulta)
        consulta_sql = conexao.consulta.as_string()  # type: ignore[union-attr]
        self.assertNotIn("VOLTA REDONDA", consulta_sql)
        self.assertIn("%s", consulta_sql)
        self.assertIn('"gold"."fact_educacao_superior"', consulta_sql)


if __name__ == "__main__":
    unittest.main()
