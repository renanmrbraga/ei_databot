"""Teste do contexto entregue ao Gemini sem chamadas externas."""

from __future__ import annotations

import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from chatbot.services.llm import Interpretacao, gerar_resposta


class GeracaoRespostaTest(unittest.TestCase):
    def test_prompt_e_objetivo_e_preserva_os_dados(self) -> None:
        modelo = Mock()
        modelo.generate_content.return_value = SimpleNamespace(text="10 matrículas")
        cliente = Mock()
        cliente.__enter__ = Mock(return_value=SimpleNamespace(models=modelo))
        cliente.__exit__ = Mock(return_value=False)
        genai = ModuleType("google.genai")
        genai.Client = Mock(return_value=cliente)  # type: ignore[attr-defined]
        types = ModuleType("google.genai.types")
        types.GenerateContentConfig = Mock(return_value=object())  # type: ignore[attr-defined]
        genai.types = types  # type: ignore[attr-defined]
        with (
            patch.dict(sys.modules, {"google.genai": genai, "google.genai.types": types}),
            patch(
                "chatbot.services.llm.get_settings",
                return_value=SimpleNamespace(
                    require_llm_key=lambda: "teste",
                    llm_model="modelo-teste",
                ),
            ),
        ):
            resposta = gerar_resposta(
                "Quantas matrículas em 2025?",
                interpretacao=Interpretacao(
                    indicador_id="CAT-EB-001",
                    ano_inicial=2025,
                    ano_final=2025,
                    operacao="SOMA_ANUAL",
                ),
                dados=[{"ano": 2025, "matriculas_educacao_basica": 10}],
                fonte="INEP / Censo Escolar",
                regras=["Matrículas são um estoque anual."],
            )
        self.assertEqual(resposta, "10 matrículas")
        prompt = modelo.generate_content.call_args.kwargs["contents"]
        self.assertIn("não reproduza informações administrativas", prompt)
        self.assertIn('"matriculas_educacao_basica": 10', prompt)
        self.assertIn("uma ou duas", prompt)
        self.assertIn("estoque anual", prompt)


if __name__ == "__main__":
    unittest.main()
