"""Health checks genericos; contratos sao resolvidos por pipeline registrado."""

from __future__ import annotations

import importlib
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from etl.core.config import DEFAULT_PIPELINE, PIPELINES


def _config(pipeline: str):
    try:
        return importlib.import_module(PIPELINES[pipeline])
    except KeyError as exc:
        raise ValueError(f"Pipeline nao registrado: {pipeline}") from exc


def _arquivo(pipeline: str) -> Path:
    return Path(_config(pipeline).HEALTH_ETL_FILE)


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def iniciar_auditoria(*, pipeline: str = DEFAULT_PIPELINE) -> None:
    arquivo = _arquivo(pipeline)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(
        f"AUDITORIA DE SAUDE - {pipeline.upper()}\nIniciada em UTC: {_timestamp()}\n\n",
        encoding="utf-8",
    )


def _registrar(linhas: Iterable[str], *, pipeline: str) -> None:
    arquivo = _arquivo(pipeline)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    with arquivo.open("a", encoding="utf-8") as saida:
        saida.write("\n".join(linhas) + "\n")


def registrar_falha(etapa: str, erro: Exception, *, pipeline: str = DEFAULT_PIPELINE) -> None:
    _registrar(
        (
            f"[{_timestamp()}] FALHA | {etapa}",
            f"  Tipo: {type(erro).__name__}",
            f"  Mensagem: {erro}",
            "",
        ),
        pipeline=pipeline,
    )


def _contrato_schema_educacao(cfg, nome: str):
    """Resolve o contrato declarado no schema do pipeline Educacional.

    Quando não encontra contrato compatível, explicita a ausência no relatório.
    """
    schema = importlib.import_module(cfg.ETL_SCHEMA_MODULE)
    mapa = getattr(cfg, "HEALTH_SCHEMA_NAMES", {})
    candidatos = [mapa[nome]] if nome in mapa else []
    camada, _, base = nome.partition("_")
    candidatos.extend(
        (
            f"SCHEMA_{nome.upper()}",
            f"SCHEMA_{base.upper()}_{camada.upper()}",
            f"SCHEMA_{camada.upper()}_{base.upper()}",
        )
    )
    if base == "superior_cursos":
        candidatos.append(f"SCHEMA_CURSOS_SUPERIOR_{camada.upper()}")
    if base == "superior_ies":
        candidatos.append(f"SCHEMA_IES_{camada.upper()}")
    for candidato in dict.fromkeys(candidatos):
        contrato = getattr(schema, candidato, None)
        if isinstance(contrato, dict) and contrato:
            return candidato, contrato
    return None, None


def _inspecionar_parquet_educacao(cfg, nome: str, *, aceitar_vazios: bool) -> str:
    """Auditoria leve: os microdados educacionais podem ter milhões de linhas."""
    caminho = Path(cfg.TB[nome])
    if not caminho.is_file() or caminho.stat().st_size <= 0:
        raise FileNotFoundError(f"Parquet ausente ou vazio em bytes: {caminho}")
    scan = pl.scan_parquet(str(caminho))
    tipos = scan.collect_schema()
    qtd = scan.select(pl.len()).collect().item()
    if qtd == 0 and not aceitar_vazios:
        raise ValueError(f"{nome}: Parquet sem registros")
    if not tipos:
        raise ValueError(f"{nome}: Parquet sem colunas")
    contrato_nome, contrato = _contrato_schema_educacao(cfg, nome)
    if contrato is None:
        status = "CONTRATO NAO LOCALIZADO (validar com schema.py)"
    else:
        ausentes = sorted(set(contrato) - set(tipos))
        if ausentes:
            raise ValueError(f"{nome}: colunas ausentes: {ausentes}")
        divergentes = [
            f"{coluna}: esperado={esperado} recebido={tipos[coluna]}"
            for coluna, esperado in contrato.items()
            if esperado is not None and tipos[coluna] != esperado
        ]
        if divergentes:
            raise ValueError(f"{nome}: tipos incorretos: {'; '.join(divergentes)}")
        status = f"contrato={contrato_nome} OK"
    return (
        f"  OK | {nome} | leitura=OK | linhas={qtd} | "
        f"colunas={len(tipos)} | bytes={caminho.stat().st_size} | {status}"
    )


def validar_parquets(
    etapa: str,
    nomes: tuple[str, ...],
    *,
    aceitar_vazios: bool = False,
    pipeline: str = DEFAULT_PIPELINE,
) -> None:
    """Confere Parquet e contrato; Medicina conserva suas validacoes anteriores."""
    cfg = _config(pipeline)
    detalhes = []
    try:
        if hasattr(importlib.import_module(cfg.ETL_COMMON_MODULE), "validar_contrato"):
            comum = importlib.import_module(cfg.ETL_COMMON_MODULE)
            for nome in nomes:
                caminho = Path(cfg.TB[nome])
                if not caminho.is_file() or caminho.stat().st_size <= 0:
                    raise FileNotFoundError(f"Parquet ausente ou vazio em bytes: {caminho}")
                df = pl.read_parquet(caminho)
                comum.validar_contrato(df, nome)
                if nome.startswith("bronze_"):
                    comum.lotes_bronze(df, nome)
                if df.is_empty() and not aceitar_vazios:
                    raise ValueError(f"{nome}: Parquet sem registros")
                detalhes.append(
                    f"  OK | {nome} | leitura=OK | contrato=OK | "
                    f"linhas={df.height} | colunas={df.width} | bytes={caminho.stat().st_size}"
                )
        else:
            for nome in nomes:
                detalhes.append(
                    _inspecionar_parquet_educacao(cfg, nome, aceitar_vazios=aceitar_vazios)
                )
        _registrar((f"[{_timestamp()}] OK | {etapa}", *detalhes, ""), pipeline=pipeline)
    except Exception as exc:
        registrar_falha(etapa, exc, pipeline=pipeline)
        raise


def validar_frescor(
    prerequisitos: tuple[str, ...],
    resultado: str,
    *,
    pipeline: str = DEFAULT_PIPELINE,
) -> None:
    cfg = _config(pipeline)
    saida = Path(cfg.TB[resultado])
    if not saida.is_file():
        raise FileNotFoundError(f"Etapa nao executada: {saida}")
    alteracao = saida.stat().st_mtime_ns
    atrasados = [
        nome
        for nome in prerequisitos
        if not Path(cfg.TB[nome]).is_file() or Path(cfg.TB[nome]).stat().st_mtime_ns > alteracao
    ]
    if atrasados:
        raise ValueError(
            f"{resultado} desatualizada em relacao a {', '.join(atrasados)}. "
            "Reexecute a camada dependente."
        )


def validar_integridade_gold(*, pipeline: str = DEFAULT_PIPELINE) -> None:
    """Verifica Gold. PK/FK dependem dos contratos declarados pelo pipeline."""
    cfg = _config(pipeline)
    schema = importlib.import_module(cfg.ETL_SCHEMA_MODULE)
    if hasattr(schema, "SCHEMAS_ETL") and hasattr(
        importlib.import_module(cfg.ETL_COMMON_MODULE), "validar_contrato"
    ):
        _validar_integridade_gold_com_contratos(pipeline=pipeline)
        return

    # Sem contrato central de relacoes, apenas a verificacao estrutural
    # pode ser feita. Nao reportar PKs e FKs como validadas.
    nomes = tuple(n for n in cfg.TB if n.startswith(("fact_", "dim_", "bridge_")))
    try:
        detalhes = [
            _inspecionar_parquet_educacao(cfg, nome, aceitar_vazios=nome.startswith("bridge_"))
            for nome in nomes
        ]
        _registrar(
            (
                f"[{_timestamp()}] ATENCAO | integridade_gold",
                *detalhes,
                "  [NAO EXECUTADO] PK/FK da Gold: contratos de relacoes ainda nao integrados ao health.",
                "",
            ),
            pipeline=pipeline,
        )
    except Exception as exc:
        registrar_falha("integridade_gold", exc, pipeline=pipeline)
        raise


def _validar_integridade_gold_com_contratos(*, pipeline: str) -> None:
    """Valida as PKs, contratos e referencias FK da Gold do pipeline escolhido."""
    cfg = _config(pipeline)
    comum = importlib.import_module(cfg.ETL_COMMON_MODULE)
    schema = importlib.import_module(cfg.ETL_SCHEMA_MODULE)
    nomes = tuple(n for n in cfg.TB if n.startswith(("fact_", "dim_", "bridge_")))
    tabelas = {}
    detalhes = []
    try:
        for nome in nomes:
            caminho = Path(cfg.TB[nome])
            if not caminho.is_file() or caminho.stat().st_size <= 0:
                raise FileNotFoundError(f"Gold ausente: {caminho}")
            df = pl.read_parquet(caminho)
            comum.validar_contrato(df, nome)
            if df.is_empty() and not nome.startswith("bridge_"):
                raise ValueError(f"{nome}: tabela Gold obrigatoria vazia")
            tabelas[nome] = df
            detalhes.append(f"  OK | {nome} | schema e PK validos")
        for nome, tabela in tabelas.items():
            for fk, (referenciada, pk) in schema.SCHEMAS_ETL[nome].get("fk", {}).items():
                if referenciada not in tabelas:
                    raise ValueError(f"{nome}: tabela referenciada ausente: {referenciada}")
                origem = tabela.select(pl.col(fk).alias("_fk")).drop_nulls().unique()
                destino = tabelas[referenciada].select(pl.col(pk).alias("_fk")).unique()
                orfaos = origem.join(destino, on="_fk", how="anti")
                if not orfaos.is_empty():
                    raise ValueError(
                        f"{nome}.{fk}: {orfaos.height} FKs orfas em {referenciada}.{pk}"
                    )
                detalhes.append(f"  OK | {nome}.{fk} -> {referenciada}.{pk}")
        _registrar((f"[{_timestamp()}] OK | integridade_gold", *detalhes, ""), pipeline=pipeline)
    except Exception as exc:
        registrar_falha("integridade_gold", exc, pipeline=pipeline)
        raise


def registrar_alerta(
    nome: str,
    dados: pl.DataFrame,
    arquivo_csv: str,
    descricao: str,
    *,
    pipeline: str,
) -> None:
    pasta = Path(_config(pipeline).AUDIT_DIR)
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / arquivo_csv

    if dados.is_empty():
        caminho.unlink(missing_ok=True)
    else:
        dados.write_csv(caminho, separator=";")

    _registrar(
        (
            f"[{_timestamp()}] AUDITORIA | {nome}",
            f"  Status: {'INFO' if dados.height else 'OK'}",
            f"  Descricao: {descricao}",
            f"  Registros: {dados.height}",
            f"  Arquivo: {caminho if dados.height else 'Sem ocorrencias'}",
            "",
        ),
        pipeline=pipeline,
    )
