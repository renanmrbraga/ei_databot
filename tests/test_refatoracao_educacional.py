"""Regressões estruturais da migração para Educacional; sem banco nem ETL."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from etl.core.config import DATA_ROOT, PIPELINES, PROJECT_DIR

ROOT = Path(__file__).resolve().parents[1]


class EstruturaEducacionalTest(unittest.TestCase):
    def test_diretorios_e_pipeline(self) -> None:
        self.assertEqual(PROJECT_DIR, ROOT)
        self.assertEqual(DATA_ROOT, ROOT / "data")
        self.assertEqual(PIPELINES, {"educacao": "etl.educacao.config"})
        self.assertTrue((ROOT / "etl/etl.py").is_file())
        self.assertTrue((ROOT / "chatbot/chatbot.py").is_file())

    def test_imports_obsoletos_ausentes(self) -> None:
        roots = ("backend", "shared", "etl.config", "etl.mercado_educacao")
        for directory in ("chatbot", "etl", "health", "postgres", "dashboards", "tests"):
            for path in (ROOT / directory).rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        self.assertFalse(node.module.startswith(roots), f"{path}: {node.module}")
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            self.assertFalse(alias.name.startswith(roots), f"{path}: {alias.name}")

    def test_distancia_geografica_configuravel(self) -> None:
        """Verifica a distância configurável sem regras institucionais fixas."""
        from etl.educacao.config import (
            CIDADE_REFERENCIA,
            CODIGO_LOCALIDADE_EAD,
            COLUNA_DISTANCIA,
            UF_REFERENCIA,
        )
        from etl.educacao.schema import SCHEMA_DIM_LOCALIDADE

        self.assertEqual(CIDADE_REFERENCIA, "RIO DE JANEIRO")
        self.assertEqual(UF_REFERENCIA, "RJ")
        self.assertEqual(COLUNA_DISTANCIA, "distancia_referencia_km")
        self.assertIn(COLUNA_DISTANCIA, SCHEMA_DIM_LOCALIDADE)

        gold = (ROOT / "etl/educacao/gold/dim_localidade.py").read_text(encoding="utf-8")

        self.assertIn("_adicionar_distancia", gold)
        self.assertIn("_obter_referencia", gold)
        self.assertIn("CODIGO_LOCALIDADE_EAD", gold)
        self.assertEqual(CODIGO_LOCALIDADE_EAD, -1)

        dashboard = (ROOT / "dashboards/educacao.py").read_text(encoding="utf-8")

        self.assertIn('"lat":', dashboard)
        self.assertIn('"lon":', dashboard)


if __name__ == "__main__":
    unittest.main()
