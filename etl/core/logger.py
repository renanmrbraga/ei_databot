"""Logging generico e isolado por ETL ou por dashboard do projeto BI."""

from __future__ import annotations

import logging
import re
from contextvars import ContextVar, Token
from logging.handlers import RotatingFileHandler

from etl.core.config import DEFAULT_PIPELINE, LOG_ROOT

_PIPELINE_ATIVO: ContextVar[str] = ContextVar("bi_pipeline_ativo", default=DEFAULT_PIPELINE)


def ativar_pipeline(pipeline: str) -> Token[str]:
    """Isola o logger do pipeline durante a execucao pelo orquestrador."""
    if not re.fullmatch(r"[a-z][a-z0-9_]*", pipeline):
        raise ValueError(f"Pipeline de log invalido: {pipeline!r}")
    return _PIPELINE_ATIVO.set(pipeline)


def restaurar_pipeline(token: Token[str]) -> None:
    _PIPELINE_ATIVO.reset(token)


def get_logger(
    nome_dashboard: str | None = None,
    *,
    pipeline: str | None = None,
) -> logging.Logger:
    """Retorna o logger do pipeline atual ou do dashboard informado."""
    pipeline = pipeline or _PIPELINE_ATIVO.get()
    identificador = nome_dashboard if nome_dashboard is not None else pipeline
    if not re.fullmatch(r"[a-z][a-z0-9_]*", identificador):
        raise ValueError(f"Identificador de log invalido: {identificador!r}")
    if nome_dashboard is None:
        nome = f"BI.ETL.{pipeline}"
        arquivo = LOG_ROOT / f"{pipeline}.log"
    else:
        nome = f"BI.DASHBOARD.{nome_dashboard}"
        arquivo = LOG_ROOT / f"dashboard_{nome_dashboard}.log"

    log = logging.getLogger(nome)
    log.setLevel(logging.DEBUG)
    log.propagate = False
    if log.handlers:
        return log

    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    tela = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S")
    detalhe = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(tela)
    arquivo_log = RotatingFileHandler(arquivo, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    arquivo_log.setLevel(logging.DEBUG)
    arquivo_log.setFormatter(detalhe)
    log.addHandler(console)
    log.addHandler(arquivo_log)
    return log
