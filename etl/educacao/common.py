"""Fluxos de ingestao do Educacional que aplicam contratos INEP.

I/O, normalizacao, hash, metadados e validacao pertencem a etl.core.common.
Nao reexportar utilitarios compartilhados deste modulo.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import polars as pl

from etl.core.common import (
    carregar_csv_fonte,
    carregar_excel_fonte,
    consolidar_bronze,
    extrair_ano_nome_arquivo,
    listar_arquivos_obrigatorios,
    preparar_parte_bronze,
)
from etl.core.logger import get_logger

log = get_logger(pipeline="educacao")


# ==============================================================================
# INGESTAO DO CENSO / INEP - CONTRATOS E COBERTURA
# ==============================================================================


def build_bronze_csv(
    *,
    pattern: str,
    output_path: str,
    dataset_name: str,
    colunas: Sequence[str],
    renomeacao: Mapping[str, str],
    schema_bronze: Mapping[str, pl.DataType | type[pl.DataType]],
    read_attempts: Sequence[Mapping[str, Any]],
    aliases_colunas: Mapping[str, str] | None = None,
    anos_esperados: Sequence[int] | set[int] | None = None,
) -> pl.DataFrame:
    """
    Builder generico para fontes CSV com contrato unico.

    Variacoes historicas apenas de nome de cabecalho devem ser tratadas
    por aliases_colunas, e nao por contratos separados por ano.
    """
    arquivos = listar_arquivos_obrigatorios(
        pattern,
        dataset_name,
        anos_esperados,
    )

    partes: list[pl.DataFrame] = []

    for arquivo in arquivos:
        caminho = Path(arquivo)
        ano = extrair_ano_nome_arquivo(caminho)

        contexto = dataset_name

        if ano is not None:
            contexto = f"{dataset_name} {ano}"

        contexto = f"{contexto} - {caminho.name}"

        df = carregar_csv_fonte(
            arquivo=arquivo,
            colunas_brutas=colunas,
            read_attempts=read_attempts,
            contexto=contexto,
            aliases_colunas=aliases_colunas,
        )

        df = preparar_parte_bronze(
            df=df,
            arquivo=arquivo,
            schema_bronze=schema_bronze,
            contexto=contexto,
            renomeacao=renomeacao,
        )

        partes.append(df)

        if ano is not None:
            log.info(
                "[BRONZE] %s | ano=%s | linhas=%s",
                dataset_name,
                ano,
                f"{df.height:,}",
            )
        else:
            log.info(
                "[BRONZE] %s | arquivo=%s | linhas=%s",
                dataset_name,
                caminho.name,
                f"{df.height:,}",
            )

    return consolidar_bronze(
        partes,
        schema_bronze,
        output_path,
        dataset_name,
    )


def build_bronze_excel(
    *,
    pattern: str,
    output_path: str,
    dataset_name: str,
    colunas: Sequence[str],
    colunas_opcionais: Sequence[str],
    aliases_colunas: Mapping[str, str] | None,
    abas_por_arquivo: Mapping[str, str],
    renomeacao: Mapping[str, str],
    schema_bronze: Mapping[str, pl.DataType | type[pl.DataType]],
    anos_esperados: Sequence[int] | set[int] | None = None,
) -> pl.DataFrame:
    """
    Builder generico para fontes Excel com contrato unico.

    Diferencas historicas de cabecalho sao tratadas por aliases_colunas.
    Campos que nao existem em todos os anos sao tratados por
    colunas_opcionais.
    """
    arquivos = listar_arquivos_obrigatorios(
        pattern,
        dataset_name,
        anos_esperados,
    )

    abas_normalizadas = {nome.casefold(): aba for nome, aba in abas_por_arquivo.items()}

    partes: list[pl.DataFrame] = []

    for arquivo in arquivos:
        caminho = Path(arquivo)
        ano = extrair_ano_nome_arquivo(caminho)

        if ano is None:
            raise RuntimeError(f"{dataset_name}: ano ausente em {caminho.name}")

        aba = abas_normalizadas.get(caminho.name.casefold())

        if aba is None:
            raise RuntimeError(f"{dataset_name}: aba nao cadastrada para o arquivo {caminho.name}.")

        contexto = f"{dataset_name} {ano} - {caminho.name}"

        df = carregar_excel_fonte(
            arquivo=arquivo,
            aba=aba,
            colunas_brutas=colunas,
            contexto=contexto,
            colunas_opcionais=colunas_opcionais,
            aliases_colunas=aliases_colunas,
        )

        # ----------------------------------------------------------------------
        # Remove rodapes e linhas auxiliares das planilhas do INEP.
        # Uma linha valida deve possuir exatamente o ano do arquivo.
        # ----------------------------------------------------------------------

        if "Ano" in df.columns:
            linhas_antes = df.height

            df = df.filter(pl.col("Ano").cast(pl.String).str.strip_chars() == str(ano))

            linhas_descartadas = linhas_antes - df.height

            if df.is_empty():
                raise RuntimeError(f"{contexto}: nenhuma linha valida encontrada para Ano={ano}.")

            if linhas_descartadas > 0:
                log.info(
                    "[BRONZE] %s | ano=%s | linhas auxiliares/rodape descartadas=%s",
                    dataset_name,
                    ano,
                    f"{linhas_descartadas:,}",
                )

        df = preparar_parte_bronze(
            df=df,
            arquivo=arquivo,
            schema_bronze=schema_bronze,
            contexto=contexto,
            renomeacao=renomeacao,
        )

        partes.append(df)

        log.info(
            "[BRONZE] %s | ano=%s | aba=%s | linhas=%s",
            dataset_name,
            ano,
            aba,
            f"{df.height:,}",
        )

    return consolidar_bronze(
        partes,
        schema_bronze,
        output_path,
        dataset_name,
    )
