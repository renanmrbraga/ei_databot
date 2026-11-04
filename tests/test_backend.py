"""Testes offline dos contratos SQL e HTTP; não chamam Gemini ou PostgreSQL."""

from __future__ import annotations

import sys
import unittest
from types import ModuleType
from unittest.mock import Mock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from chatbot.services.analytics import ConsultaNaoSuportada, validar_interpretacao
from chatbot.services.llm import Interpretacao


class ContratosAnaliticosTest(unittest.TestCase):
    def test_soma_anual_valida(self) -> None:
        interpretacao = Interpretacao(
            indicador_id="CAT-EB-001",
            municipio="Volta Redonda",
            uf="RJ",
            ano_inicial=2025,
            ano_final=2025,
            operacao="SOMA_ANUAL",
        )
        self.assertEqual(
            validar_interpretacao(interpretacao).coluna,
            "matriculas_educacao_basica",
        )

    def test_indicador_nao_permitido(self) -> None:
        interpretacao = Interpretacao(
            indicador_id="CAT-AVC-041",
            ano_inicial=2023,
            ano_final=2023,
            operacao="SOMA_ANUAL",
        )
        with self.assertRaises(ConsultaNaoSuportada):
            validar_interpretacao(interpretacao)

    def test_uf_ausente_bloqueia(self) -> None:
        interpretacao = Interpretacao(
            indicador_id="CAT-ES-023",
            municipio="Valença",
            ano_inicial=2023,
            ano_final=2023,
            operacao="SOMA_ANUAL",
        )
        with self.assertRaises(ConsultaNaoSuportada):
            validar_interpretacao(interpretacao)

    def test_ano_fora_da_cobertura_bloqueia(self) -> None:
        interpretacao = Interpretacao(
            indicador_id="CAT-ES-023",
            ano_inicial=2025,
            ano_final=2025,
            operacao="SOMA_ANUAL",
        )
        with self.assertRaises(ConsultaNaoSuportada):
            validar_interpretacao(interpretacao)

    def test_estoque_plurianual_nao_soma(self) -> None:
        interpretacao = Interpretacao(
            indicador_id="CAT-EB-001",
            ano_inicial=2020,
            ano_final=2025,
            operacao="SOMA_ANUAL",
        )
        with self.assertRaises(ConsultaNaoSuportada):
            validar_interpretacao(interpretacao)

    def test_serie_anual_permitida(self) -> None:
        interpretacao = Interpretacao(
            indicador_id="CAT-ES-023",
            ano_inicial=2020,
            ano_final=2024,
            operacao="SERIE_ANUAL",
        )
        self.assertEqual(validar_interpretacao(interpretacao).tabela, "fact_educacao_superior")

    def test_filtros_nao_suportados_bloqueados(self) -> None:
        interpretacao = Interpretacao(
            indicador_id="CAT-EB-001",
            ano_inicial=2024,
            ano_final=2024,
            operacao="SOMA_ANUAL",
            filtros_nao_suportados=["ensino médio"],
        )
        with self.assertRaises(ConsultaNaoSuportada):
            validar_interpretacao(interpretacao)

    def test_sem_ano_bloqueia(self) -> None:
        with self.assertRaises(ConsultaNaoSuportada):
            validar_interpretacao(Interpretacao(indicador_id="CAT-EB-001", operacao="SOMA_ANUAL"))


class ApiTest(unittest.TestCase):
    def test_health_nao_exige_banco(self) -> None:
        from chatbot.chatbot import app

        response = TestClient(app).get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_chat_preserva_contrato_frontend(self) -> None:
        from chatbot.chatbot import app

        with patch(
            "chatbot.chatbot.responder_chat",
            return_value={
                "resposta": "Teste",
                "agente": "EI DataBot",
                "fontes": [],
                "cidade": None,
                "uf": None,
                "tema": None,
                "dados_brutos": [],
                "avisos": [],
            },
        ) as service:
            response = TestClient(app).post(
                "/api/chat",
                json={
                    "pergunta": "Quantas matrículas em 2024?",
                    "session_id": "cdde4cba-d349-4f2d-95ce-58b1b0ff3237",
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["resposta"], "Teste")
        service.assert_called_once()

    def test_payload_invalido(self) -> None:
        from chatbot.chatbot import app

        response = TestClient(app).post(
            "/api/chat", json={"pergunta": "", "session_id": "cdde4cba-d349-4f2d-95ce-58b1b0ff3237"}
        )
        self.assertEqual(response.status_code, 422)

    def test_session_id_deve_ser_uuid(self) -> None:
        from chatbot.chatbot import app

        response = TestClient(app).post(
            "/api/chat",
            json={"pergunta": "Quantas matrículas?", "session_id": "teste-integracao-001"},
        )
        self.assertEqual(response.status_code, 422)

    def test_historico_recupera_somente_uuid_informado(self) -> None:
        from chatbot.chatbot import app

        session_id = UUID("5f4b8604-7f5c-42a2-8367-2645b3ef6c00")
        mensagens = [{"id": "1", "role": "user", "content": "Pergunta"}]
        with patch("chatbot.chatbot.listar_mensagens_sessao", return_value=mensagens) as leitura:
            response = TestClient(app).get(f"/api/sessions/{session_id}/messages")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"session_id": str(session_id), "messages": mensagens})
        leitura.assert_called_once_with(session_id)

    def test_historico_rejeita_uuid_invalido(self) -> None:
        from chatbot.chatbot import app

        response = TestClient(app).get("/api/sessions/nao-e-uuid/messages")
        self.assertEqual(response.status_code, 422)

    def test_historico_indisponivel_nao_expoe_detalhes(self) -> None:
        from chatbot.chatbot import app

        with (
            patch("chatbot.chatbot.listar_mensagens_sessao", side_effect=RuntimeError("segredo")),
            patch("chatbot.chatbot.logger"),
        ):
            response = TestClient(app).get(
                "/api/sessions/5f4b8604-7f5c-42a2-8367-2645b3ef6c00/messages"
            )
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("segredo", response.text)

    def test_exclusao_envia_apenas_uuid_informado(self) -> None:
        from chatbot.chatbot import app

        session_id = UUID("5f4b8604-7f5c-42a2-8367-2645b3ef6c00")
        with patch("chatbot.chatbot.excluir_sessao", return_value=True) as exclusao:
            response = TestClient(app).delete(f"/api/sessions/{session_id}")
        self.assertEqual(response.status_code, 204)
        exclusao.assert_called_once_with(session_id)

    def test_exclusao_sessao_inexistente_retorna_404(self) -> None:
        from chatbot.chatbot import app

        with patch("chatbot.chatbot.excluir_sessao", return_value=False):
            response = TestClient(app).delete("/api/sessions/5f4b8604-7f5c-42a2-8367-2645b3ef6c00")
        self.assertEqual(response.status_code, 404)

    def test_exclusao_indisponivel_nao_expoe_detalhes(self) -> None:
        from chatbot.chatbot import app

        with (
            patch("chatbot.chatbot.excluir_sessao", side_effect=RuntimeError("segredo")),
            patch("chatbot.chatbot.logger"),
        ):
            response = TestClient(app).delete("/api/sessions/5f4b8604-7f5c-42a2-8367-2645b3ef6c00")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("segredo", response.text)

    def test_exclusao_rejeita_uuid_invalido(self) -> None:
        from chatbot.chatbot import app

        response = TestClient(app).delete("/api/sessions/nao-e-uuid")
        self.assertEqual(response.status_code, 422)


class FluxoChatTest(unittest.TestCase):
    def setUp(self) -> None:
        recuperar_patch = patch("chatbot.services.chat.recuperar_historico", return_value=[])
        registrar_patch = patch("chatbot.services.chat.registrar_interacao")
        self.recuperar = recuperar_patch.start()
        self.registrar = registrar_patch.start()
        self.addCleanup(recuperar_patch.stop)
        self.addCleanup(registrar_patch.stop)

    def _preparar_rag(self) -> tuple[dict[str, ModuleType], Mock]:
        modulo = ModuleType("chatbot.services.rag")
        busca = Mock(return_value=[])
        modulo.buscar_regras = busca  # type: ignore[attr-defined]
        return {"chatbot.services.rag": modulo}, busca

    def test_resposta_com_dados_reais(self) -> None:
        from chatbot.services.analytics import INDICADORES
        from chatbot.services.chat import responder_chat

        interpretacao = Interpretacao(
            indicador_id="CAT-ES-023",
            ano_inicial=2023,
            ano_final=2023,
            operacao="SOMA_ANUAL",
        )
        imports, busca = self._preparar_rag()
        with (
            patch.dict(sys.modules, imports),
            patch("chatbot.services.chat._incluir_documentos_em_revisao", return_value=False),
            patch("chatbot.services.chat.interpretar_pergunta", return_value=interpretacao),
            patch(
                "chatbot.services.chat.consultar_gold",
                return_value=(
                    INDICADORES["CAT-ES-023"],
                    [{"ano": 2023, "matriculados": 123, "registros_com_valor": 2}],
                ),
            ),
            patch("chatbot.services.chat.gerar_resposta", return_value="123 matrículas") as gera,
        ):
            resposta = responder_chat(
                "Matrículas em 2023", UUID("cdde4cba-d349-4f2d-95ce-58b1b0ff3237")
            )
        self.assertEqual(resposta["resposta"], "123 matrículas")
        self.assertEqual(resposta["dados_brutos"][0]["matriculados"], 123)
        self.assertNotIn("chart_data", resposta)
        self.assertNotIn("pdf_base64", resposta)
        self.assertNotIn("csv_base64", resposta)
        self.registrar.assert_called_once()
        gera.assert_called_once()
        busca.assert_called_once()

    def test_rag_mantem_status_apenas_nos_avisos(self) -> None:
        from chatbot.services.analytics import INDICADORES
        from chatbot.services.chat import responder_chat
        from chatbot.services.rag import RegraRecuperada

        regra = RegraRecuperada(
            documento="docs/educacao_basica.md",
            titulo="Educação básica",
            versao="v123",
            status="revisao_humana_pendente",
            secao="Matrículas",
            ids_regras=("REG-001",),
            conteudo="Matrículas são um estoque anual.",
            similaridade=0.8,
            alerta_documental=False,
            contem_pendencia=False,
        )
        interpretacao = Interpretacao(
            indicador_id="CAT-EB-001",
            ano_inicial=2025,
            ano_final=2025,
            operacao="SOMA_ANUAL",
        )
        imports, busca = self._preparar_rag()
        busca.return_value = [regra]
        with (
            patch.dict(sys.modules, imports),
            patch("chatbot.services.chat._incluir_documentos_em_revisao", return_value=True),
            patch(
                "chatbot.services.chat.interpretar_pergunta", return_value=interpretacao
            ) as interpreta,
            patch(
                "chatbot.services.chat.consultar_gold",
                return_value=(
                    INDICADORES["CAT-EB-001"],
                    [{"ano": 2025, "matriculas_educacao_basica": 10}],
                ),
            ),
            patch("chatbot.services.chat.gerar_resposta", return_value="10 matrículas") as gera,
        ):
            resultado = responder_chat(
                "Matrículas em 2025", UUID("cdde4cba-d349-4f2d-95ce-58b1b0ff3237")
            )
        self.assertEqual(interpreta.call_args.kwargs["regras"], [regra.conteudo])
        self.assertEqual(gera.call_args.kwargs["regras"], [regra.conteudo])
        self.assertIn("Documentação recuperada em revisão, não aprovada.", resultado["avisos"])
        self.assertIn(regra.documento, resultado["fontes"])
        self.assertNotIn("v123", str(gera.call_args.kwargs["regras"]))

    def test_sem_dados_nao_chama_segunda_llm(self) -> None:
        from chatbot.services.analytics import INDICADORES
        from chatbot.services.chat import responder_chat

        interpretacao = Interpretacao(
            indicador_id="CAT-EB-001",
            ano_inicial=2023,
            ano_final=2023,
            operacao="SOMA_ANUAL",
        )
        imports, _ = self._preparar_rag()
        with (
            patch.dict(sys.modules, imports),
            patch("chatbot.services.chat._incluir_documentos_em_revisao", return_value=False),
            patch("chatbot.services.chat.interpretar_pergunta", return_value=interpretacao),
            patch(
                "chatbot.services.chat.consultar_gold",
                return_value=(
                    INDICADORES["CAT-EB-001"],
                    [],
                ),
            ),
            patch("chatbot.services.chat.gerar_resposta") as gera,
        ):
            resposta = responder_chat(
                "Matrículas em 2023", UUID("cdde4cba-d349-4f2d-95ce-58b1b0ff3237")
            )
        self.assertIn("Não foram encontrados", resposta["resposta"])
        gera.assert_not_called()

    def test_indicador_ausente_nao_executa_sql(self) -> None:
        from chatbot.services.chat import responder_chat

        interpretacao = Interpretacao(
            indicador_id="CAT-AVC-041",
            ano_inicial=2023,
            ano_final=2023,
            operacao="SOMA_ANUAL",
        )
        imports, _ = self._preparar_rag()
        with (
            patch.dict(sys.modules, imports),
            patch("chatbot.services.chat._incluir_documentos_em_revisao", return_value=False),
            patch("chatbot.services.chat.interpretar_pergunta", return_value=interpretacao),
            patch("chatbot.services.chat.gerar_resposta") as gera,
        ):
            resultado = responder_chat(
                "Qual o CPC médio em 2023?", UUID("cdde4cba-d349-4f2d-95ce-58b1b0ff3237")
            )
        self.assertIn("não implementado", resultado["resposta"])
        self.assertEqual(resultado["dados_brutos"], [])
        gera.assert_not_called()

    def test_historico_entra_na_interpretacao(self) -> None:
        from chatbot.services.chat import responder_chat

        historico = [
            {"role": "user", "text": "Quantas matrículas em 2024?"},
            {"role": "assistant", "text": "Foi o total de 2024."},
        ]
        self.recuperar.return_value = historico
        interpretacao = Interpretacao(indicador_id=None)
        imports, _ = self._preparar_rag()
        with (
            patch.dict(sys.modules, imports),
            patch("chatbot.services.chat._incluir_documentos_em_revisao", return_value=False),
            patch(
                "chatbot.services.chat.interpretar_pergunta", return_value=interpretacao
            ) as interpreta,
        ):
            responder_chat("E em 2023?", UUID("cdde4cba-d349-4f2d-95ce-58b1b0ff3237"))
        self.assertEqual(interpreta.call_args.kwargs["historico"], historico)
        self.registrar.assert_called_once()

    def test_falha_ao_registrar_nao_simula_sucesso(self) -> None:
        from chatbot.services.chat import responder_chat

        self.registrar.side_effect = RuntimeError("Sem tabela app.messages")
        interpretacao = Interpretacao(indicador_id=None)
        imports, _ = self._preparar_rag()
        with (
            patch.dict(sys.modules, imports),
            patch("chatbot.services.chat._incluir_documentos_em_revisao", return_value=False),
            patch("chatbot.services.chat.interpretar_pergunta", return_value=interpretacao),
            self.assertRaisesRegex(RuntimeError, "Sem tabela app.messages"),
        ):
            responder_chat("Teste", UUID("cdde4cba-d349-4f2d-95ce-58b1b0ff3237"))


if __name__ == "__main__":
    unittest.main()
