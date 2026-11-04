"""Regressões para limpeza estrutural, sem acessar PostgreSQL ou API Gemini."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from chatbot.services.analytics import INDICADORES, OPERACOES
from etl.core.config import DEFAULT_PIPELINE, PIPELINES

ROOT = Path(__file__).resolve().parents[1]


class LimpezaArquiteturaTest(unittest.TestCase):
    def test_pipeline_unico_tem_config_real(self) -> None:
        self.assertEqual(DEFAULT_PIPELINE, "educacao")
        self.assertEqual(PIPELINES, {"educacao": "etl.educacao.config"})
        self.assertTrue((ROOT / "etl/educacao/config.py").is_file())

    def test_orquestrador_nao_oferece_pipeline_inexistente(self) -> None:
        texto = (ROOT / "etl/etl.py").read_text(encoding="utf-8")
        ast.parse(texto)
        self.assertNotIn("--perfil_medicina", texto)

    def test_catalogo_sql_e_gemini_tem_uma_fonte(self) -> None:
        codigo = (ROOT / "chatbot/services/llm.py").read_text(encoding="utf-8")
        self.assertIn("from chatbot.services.analytics import INDICADORES, OPERACOES", codigo)
        self.assertNotIn('"CAT-ES-023":', codigo)
        self.assertNotIn('"CAT-EB-001":', codigo)
        self.assertEqual(set(OPERACOES), {"SOMA_ANUAL", "SERIE_ANUAL"})
        self.assertTrue(all(item.descricao for item in INDICADORES.values()))

    def test_backend_nao_importa_legado(self) -> None:
        for caminho in (ROOT / "chatbot").rglob("*.py"):
            codigo = caminho.read_text(encoding="utf-8")
            arvore = ast.parse(codigo)
            modulos = [
                parte.module
                for parte in ast.walk(arvore)
                if isinstance(parte, ast.ImportFrom) and parte.module
            ]
            self.assertFalse(
                any(
                    modulo.startswith(("core.handlers", "core.router", "database.", "utils."))
                    for modulo in modulos
                ),
                str(caminho),
            )


if __name__ == "__main__":
    unittest.main()
