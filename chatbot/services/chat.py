"""Fluxo do chatbot MVP: RAG -> intenção -> SQL autorizado -> resposta."""

from __future__ import annotations

import logging
import os
from typing import Any
from uuid import UUID

from chatbot.core.config import get_settings
from chatbot.services.analytics import ConsultaNaoSuportada, consultar_gold
from chatbot.services.history import recuperar_historico, registrar_interacao
from chatbot.services.llm import gerar_resposta, interpretar_pergunta

logger = logging.getLogger(__name__)


def _incluir_documentos_em_revisao() -> bool:
    get_settings()  # Carrega o .env do repositório antes de ler a opção do RAG.
    return os.getenv("RAG_INCLUDE_DRAFTS", "false").strip().lower() == "true"


def responder_chat(pergunta: str, session_id: UUID) -> dict[str, Any]:
    """Atende a pergunta e persiste a troca de mensagens após concluir o fluxo."""
    historico = recuperar_historico(session_id)
    regras: list[str] = []
    fontes_documentais: list[str] = []
    avisos: list[str] = []

    try:
        from chatbot.services.rag import buscar_regras

        documentos = buscar_regras(
            pergunta,
            limite=3,
            incluir_revisao=_incluir_documentos_em_revisao(),
        )
        for documento in documentos:
            if documento.contem_pendencia or documento.alerta_documental:
                avisos.append(
                    "Trecho documental pendente ou com alerta foi desconsiderado na interpretação."
                )
                continue
            # Status, versão, caminho e avisos pertencem aos metadados da API,
            # não às instruções de redação fornecidas ao modelo.
            regras.append(documento.conteudo[:2500])
            if documento.documento not in fontes_documentais:
                fontes_documentais.append(documento.documento)
            if documento.status not in {"aprovado", "politica_vigente"}:
                avisos.append("Documentação recuperada em revisão, não aprovada.")
    except Exception:
        # O RAG é auxiliar; sua falha não autoriza consultas fora do contrato.
        logger.warning("Busca RAG indisponível; mantendo SQL restrito.", exc_info=True)
        avisos.append("RAG indisponível nesta consulta; regras não recuperadas.")

    interpretacao = interpretar_pergunta(pergunta, historico=historico, regras=regras)
    try:
        indicador, dados = consultar_gold(interpretacao)
    except ConsultaNaoSuportada as exc:
        indicador = None
        dados = []
        resposta = str(exc)
        avisos.append("Consulta não executada: fora dos contratos do MVP.")
    else:
        if not dados or all(linha[indicador.coluna] is None for linha in dados):
            resposta = (
                "Não foram encontrados valores informados para o indicador, "
                "período e recorte solicitados."
            )
        else:
            resposta = gerar_resposta(
                pergunta,
                interpretacao=interpretacao,
                dados=dados,
                fonte=indicador.fonte,
                regras=regras,
            )
        if interpretacao.municipio and indicador.dominio == "educacao_superior":
            avisos.append("O recorte municipal de educação superior não inclui EAD da região.")

    fontes = [indicador.fonte, *fontes_documentais] if indicador else fontes_documentais
    avisos = list(dict.fromkeys(avisos))
    registrar_interacao(
        session_id,
        pergunta=pergunta,
        resposta=resposta,
        indicador_id=interpretacao.indicador_id if indicador else None,
        filtros={
            "municipio": interpretacao.municipio,
            "uf": interpretacao.uf,
            "ano_inicial": interpretacao.ano_inicial,
            "ano_final": interpretacao.ano_final,
            "operacao": interpretacao.operacao,
        },
        fontes=fontes,
        avisos=avisos,
    )

    return {
        "resposta": resposta,
        "agente": "EI DataBot",
        "fontes": fontes,
        "cidade": interpretacao.municipio,
        "uf": interpretacao.uf,
        "tema": indicador.dominio if indicador else None,
        "dados_brutos": dados,
        "avisos": avisos,
    }
