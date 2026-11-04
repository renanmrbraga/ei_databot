"""Orquestrador do BI: pipelines isolados, com Bronze, Silver, Gold e dashboards."""

from __future__ import annotations

import argparse
import importlib
import sys
import time
from collections.abc import Callable
from typing import Any

from etl.core.config import PIPELINES
from etl.core.logger import ativar_pipeline, get_logger, restaurar_pipeline
from health.health_etl import (
    iniciar_auditoria,
    registrar_falha,
    validar_integridade_gold,
    validar_parquets,
)


def _resolver_funcao(caminho: str) -> Callable[..., Any]:
    modulo, _, nome = caminho.rpartition(".")
    if not modulo:
        raise ValueError(f"Funcao sem modulo: {caminho}")
    return getattr(importlib.import_module(modulo), nome)


def escolher_etapas(
    steps: tuple[tuple[str, str, str], ...],
    *,
    phase: str | None = None,
    only: str | None = None,
    skip: str | None = None,
    skip_bronze: bool = False,
    skip_silver: bool = False,
) -> list[tuple[str, str, str]]:
    etapas = list(steps)
    if only:
        etapas = [etapa for etapa in etapas if etapa[0] == only]
    elif phase:
        etapas = [etapa for etapa in etapas if etapa[2] == phase]
    if skip:
        ignoradas = {nome.strip() for nome in skip.split(",") if nome.strip()}
        invalidas = ignoradas - {item[0] for item in steps}
        if invalidas:
            raise ValueError("Etapas invalidas: " + ", ".join(sorted(invalidas)))
        etapas = [etapa for etapa in etapas if etapa[0] not in ignoradas]
    if skip_silver:
        etapas = [etapa for etapa in etapas if etapa[2] not in {"bronze", "silver"}]
    elif skip_bronze:
        etapas = [etapa for etapa in etapas if etapa[2] != "bronze"]
    if not etapas:
        raise ValueError("Nenhuma etapa selecionada")
    return etapas


def executar_pipeline(
    pipeline: str,
    *,
    phase: str | None = None,
    only: str | None = None,
    skip: str | None = None,
    skip_bronze: bool = False,
    skip_silver: bool = False,
) -> bool:
    cfg = importlib.import_module(PIPELINES[pipeline])
    etapas = escolher_etapas(
        cfg.STEPS,
        phase=phase,
        only=only,
        skip=skip,
        skip_bronze=skip_bronze,
        skip_silver=skip_silver,
    )
    token_pipeline = ativar_pipeline(pipeline)
    try:
        log = get_logger(pipeline=pipeline)
        # Etapas Gold nao selecionadas nao sao presumidas executadas.
        gold_total = {nome for nome, _, camada in cfg.STEPS if camada == "gold"}
        gold_escolhida = {nome for nome, _, camada in etapas if camada == "gold"}
        ultima_gold = max(
            (i for i, (_, _, camada) in enumerate(etapas) if camada == "gold"),
            default=-1,
        )
        if any(camada != "dashboard" for _, _, camada in etapas):
            iniciar_auditoria(pipeline=pipeline)
        inicio_total = time.perf_counter()
        log.info("PIPELINE BI [%s] - INICIO", pipeline)
        for indice, (nome, modulo, camada) in enumerate(etapas):
            inicio = time.perf_counter()
            log.info("[%d/%d] %s / %s", indice + 1, len(etapas), camada.upper(), nome)
            health = getattr(cfg, "DASHBOARD_HEALTH", {}).get(nome)
            try:
                rotina = getattr(importlib.import_module(modulo), "executar", None)
                if not callable(rotina):
                    raise TypeError(
                        f"{modulo}: defina uma funcao executar() para integrar ao etl/etl.py"
                    )
                rotina()
                if camada in {"bronze", "silver", "gold"}:
                    validar_parquets(
                        nome,
                        (nome,),
                        pipeline=pipeline,
                        aceitar_vazios=nome.startswith("bridge_"),
                    )
                if camada == "gold" and indice == ultima_gold and gold_escolhida == gold_total:
                    validar_integridade_gold(pipeline=pipeline)
                if camada == "dashboard" and health:
                    _resolver_funcao(health[0])()
            except Exception as exc:
                if health:
                    _resolver_funcao(health[1])(exc)
                registrar_falha(nome, exc, pipeline=pipeline)
                log.exception("Falha na etapa %s", nome)
                return False
            log.info("%s concluido em %.2f s", nome, time.perf_counter() - inicio)
        log.info(
            "PIPELINE BI [%s] - CONCLUIDO em %.2f s", pipeline, time.perf_counter() - inicio_total
        )
        return True
    finally:
        restaurar_pipeline(token_pipeline)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--educacao",
        dest="pipeline",
        action="store_const",
        const="educacao",
        required=True,
    )

    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--phase", choices=("bronze", "silver", "gold", "dashboard"))
    grupo.add_argument("--only", help="Executa apenas uma etapa do pipeline")
    parser.add_argument("--skip", help="Nomes de etapas separados por virgula")
    parser.add_argument("--skip-bronze", action="store_true")
    parser.add_argument("--skip-silver", action="store_true")
    args = parser.parse_args(argv)
    selecionados = (args.pipeline,)
    for pipeline in selecionados:
        cfg = importlib.import_module(PIPELINES[pipeline])
        try:
            escolher_etapas(
                cfg.STEPS,
                phase=args.phase,
                only=args.only,
                skip=args.skip,
                skip_bronze=args.skip_bronze,
                skip_silver=args.skip_silver,
            )
        except ValueError as exc:
            parser.error(f"{pipeline}: {exc}")
    for pipeline in selecionados:
        if not executar_pipeline(
            pipeline,
            phase=args.phase,
            only=args.only,
            skip=args.skip,
            skip_bronze=args.skip_bronze,
            skip_silver=args.skip_silver,
        ):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
