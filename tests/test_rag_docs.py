"""Testes offline da preparacao do indice; nao chamam PostgreSQL nem Gemini."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any, Self
from unittest.mock import patch

from postgres.sync_rag import (
    Chunk,
    _cached_vectors,
    _partition_vectors,
    _save_cache,
    catalog_warnings,
    extract_rule_ids,
    load_documents,
    make_chunks,
    parse_frontmatter,
)


class RagDocsTests(unittest.TestCase):
    def test_frontmatter(self) -> None:
        data = parse_frontmatter('---\nid: teste\nversao: "0.9.1"\nstatus: revisao\n---\n')
        self.assertEqual(data["id"], "teste")
        self.assertEqual(data["versao"], "0.9.1")

    def test_chunking_preserva_secoes_e_ids(self) -> None:
        text = "# Titulo\n## Regras\n**[ES-MET-001 | ETL]** Matrículas.\n" + (
            "texto teste de negocios. " * 500
        )
        chunks = make_chunks(text, "Titulo")
        self.assertGreater(len(chunks), 2)
        self.assertEqual([c.position for c in chunks], list(range(len(chunks))))
        self.assertTrue(all(len(c.content) <= 2300 for c in chunks))
        self.assertIn("ES-MET-001", extract_rule_ids(text))

    def test_mesmo_texto_mesmos_hashes(self) -> None:
        text = "# Titulo\n\n## Parte\nCAT-ES-023 descreve matriculados."
        self.assertEqual(make_chunks(text, "Titulo"), make_chunks(text, "Titulo"))

    def test_cat_catalogo_alerta_coluna_ausente(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td)
            (docs_dir / "indicadores.md").write_text(
                "---\nid: indicadores\ncategoria: catalogo_de_indicadores\nversao: 0.1\nstatus: revisao\n---\n"
                "# Indicadores\n| `CAT-ES-023` | `matriculados` |\n",
                encoding="utf-8",
            )
            docs = load_documents(docs_dir)
            self.assertEqual(len(docs), 1)
            warnings = catalog_warnings(docs[0], {"gold.fact_educacao_superior": {"ano"}})
            self.assertEqual(len(warnings), 1)
            self.assertIn("CAT-ES-023", warnings[0])

    def test_documentos_sem_metadados_de_negocio_ignorados(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            docs_dir = Path(td)
            (docs_dir / "comandos.md").write_text("# Executar comandos", encoding="utf-8")
            (docs_dir / "governança.md").write_text("**Governança:** regras.\n", encoding="utf-8")
            (docs_dir / "regras.md").write_text(
                "---\nid: regras\ncategoria: regras_transversais\n"
                "versao: 1\nstatus: revisao_humana_pendente\n---\n"
                "# Regras\nRegra de negocio vigente somente apos revisao.\n",
                encoding="utf-8",
            )
            docs = load_documents(docs_dir)
            self.assertEqual([d.source_path for d in docs], ["docs/regras.md"])
            self.assertEqual(docs[0].metadata["status"], "revisao_humana_pendente")


class _FakeRagConnection:
    def __init__(self, rows: list[dict[str, str]] | None = None) -> None:
        self.rows = rows if rows is not None else []
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def execute(self, query: str, params: tuple[Any, ...]) -> Self:
        self.calls.append((query, params))
        return self

    def fetchall(self) -> list[dict[str, str]]:
        return self.rows

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        pass


class RagCacheTest(unittest.TestCase):
    """Garante que o RAG reaproveita embeddings e valida referencias reais."""

    def test_placeholder_gold_tabela_coluna_nao_alerta(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "indicadores.md").write_text(
                "---\nid: indicadores\ncategoria: catalogo_de_indicadores\n"
                "versao: 0.9.1\nstatus: revisao_humana_pendente\n---\n"
                "# Indicadores\nExemplo: `gold.tabela.coluna`.\n",
                encoding="utf-8",
            )
            documentos = load_documents(Path(directory))
        self.assertEqual(catalog_warnings(documentos[0], {}), [])

    def test_coluna_gold_desconhecida_continua_alertando(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "regras.md").write_text(
                "---\nid: regras\ncategoria: regras_transversais\n"
                "versao: 1\nstatus: revisao\n---\n"
                "# Regras\nColuna `gold.fact_educacao_basica.campo_inexistente`.\n",
                encoding="utf-8",
            )
            documentos = load_documents(Path(directory))
        alertas = catalog_warnings(documentos[0], {"gold.fact_educacao_basica": {"ano"}})
        self.assertEqual(
            alertas, ["Coluna nao identificada: gold.fact_educacao_basica.campo_inexistente"]
        )

    def test_reutiliza_cache_e_solicita_apenas_hash_novo(self) -> None:
        fragmentos = (
            Chunk(0, "secao", "primeiro", "hash_a", ("CAT-EB-001",)),
            Chunk(1, "secao", "segundo", "hash_b", ()),
            Chunk(2, "secao", "terceiro", "hash_a", ("CAT-EB-001",)),
        )
        vetores, faltantes = _partition_vectors(fragmentos, {"hash_a": "[1,0]"})
        self.assertEqual(vetores, {"hash_a": "[1,0]"})
        self.assertEqual(faltantes, [("hash_b", "segundo")])

    def test_consulta_cache_por_hash_e_modelo(self) -> None:
        connection = _FakeRagConnection([{"content_hash": "hash_a", "vector": "[1,0]"}])
        self.assertEqual(_cached_vectors(connection, ["hash_a"], "modelo"), {"hash_a": "[1,0]"})
        self.assertIn("rag.embedding_cache", connection.calls[0][0])
        self.assertEqual(connection.calls[0][1], (["hash_a"], "modelo"))
        self.assertEqual(_cached_vectors(connection, [], "modelo"), {})
        self.assertEqual(len(connection.calls), 1)

    def test_persistencia_do_lote_tem_upsert_idempotente(self) -> None:
        connection = _FakeRagConnection()
        with patch("postgres.sync_rag.get_connection", return_value=connection) as get_connection:
            _save_cache(
                [("hash_a", "texto a"), ("hash_b", "texto b")], ["[1,0]", "[0,1]"], "modelo"
            )
        get_connection.assert_called_once_with(read_only=False)
        self.assertEqual(len(connection.calls), 2)
        self.assertIn("ON CONFLICT", connection.calls[0][0])
        self.assertEqual(connection.calls[0][1], ("hash_a", "modelo", "[1,0]"))


if __name__ == "__main__":
    unittest.main()
