"""Confere as chaves fisicas com os contratos logicos do ETL.

Execucao: python -m unittest discover -s tests -p test_postgres_keys.py -v
Nao precisa de PostgreSQL nem de carregar os Parquets.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ETL_NAMES = {
    "fact_avaliacao_curso_superior": "CHAVE_FACT_AVALIACAO_CURSO_SUPERIOR",
    "fact_avaliacao_ies": "CHAVE_FACT_AVALIACAO_IES",
    "fact_educacao_basica": "CHAVE_FACT_EDUCACAO_BASICA",
    "fact_educacao_superior": "CHAVE_FACT_EDUCACAO_SUPERIOR",
    "fact_educacao_superior_turno": "CHAVE_FACT_EDUCACAO_SUPERIOR_TURNO",
}


def read_constant(path: Path, constant: str):
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == constant for target in targets):
                return ast.literal_eval(node.value)
    raise AssertionError(f"Constante {constant} ausente em {path}")


class UniqueKeysTest(unittest.TestCase):
    def test_keys_match_etl_contract(self) -> None:
        physical = read_constant(ROOT / "postgres/schema.py", "UNIQUE_KEYS")
        etl_schema = ROOT / "etl/educacao/schema.py"
        self.assertEqual(set(physical), set(ETL_NAMES))
        for fact, etl_name in ETL_NAMES.items():
            with self.subTest(table=fact):
                expected = tuple(read_constant(etl_schema, etl_name))
                self.assertEqual(tuple(physical[fact]), expected)
                self.assertEqual(len(physical[fact]), len(set(physical[fact])))

    def test_unique_index_uses_mapping(self) -> None:
        source = (ROOT / "postgres/schema.py").read_text(encoding="utf-8-sig")
        self.assertIn("keys = UNIQUE_KEYS[name]", source)
        self.assertIn("NULLS NOT DISTINCT", source)


if __name__ == "__main__":
    unittest.main()
