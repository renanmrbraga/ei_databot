"""Regressao offline para o contrato dos documentos de regras do RAG."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from postgres import validate_gold
from postgres.sync_rag import load_documents


class ValidateGoldDocsTests(unittest.TestCase):
    def test_cinco_documentos_reais_sao_elegiveis_para_rag(self) -> None:
        self.assertEqual(len(validate_gold.DOC_NAMES), 5)
        self.assertFalse((validate_gold.DOCS_DIR / "governança.md").exists())
        documents = load_documents(validate_gold.DOCS_DIR)
        sources = {Path(doc.source_path).name for doc in documents}
        self.assertEqual(sources, set(validate_gold.DOC_NAMES))

    def test_validacao_offline_nao_exige_documento_excluido(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td)
            for name in validate_gold.DOC_NAMES:
                (docs_dir / name).write_text(
                    "---\nstatus: revisao_humana_pendente\n---\n# Documento\n",
                    encoding="utf-8",
                )
            results: list[dict[str, object]] = []
            with (
                patch.object(validate_gold, "DOCS_DIR", docs_dir),
                patch.object(validate_gold, "load_contracts", return_value=({}, {})),
                patch.object(validate_gold, "load_catalog_ids", return_value={}),
                patch.object(validate_gold, "FACTS", {}),
            ):
                validate_gold.validate_offline(results)
            self.assertEqual(len([r for r in results if r["code"] == "DOC_REVISAO"]), 5)
            self.assertTrue(any(r["code"] == "DOCS" and r["status"] == "OK" for r in results))
            self.assertFalse(any(r["status"] == "ERRO" for r in results))

    def test_validacao_offline_exige_documentos_restantes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td)
            for name in validate_gold.DOC_NAMES:
                if name != "indicadores.md":
                    (docs_dir / name).write_text("# Documento\n", encoding="utf-8")
            results: list[dict[str, object]] = []
            with (
                patch.object(validate_gold, "DOCS_DIR", docs_dir),
                self.assertRaises(FileNotFoundError),
            ):
                validate_gold.validate_offline(results)
            self.assertEqual(results[0]["code"], "DOCS_AUSENTES")
            self.assertIn("indicadores.md", str(results[0]["message"]))


if __name__ == "__main__":
    unittest.main()
