from __future__ import annotations

import csv
from pathlib import Path

import polars as pl

from etl.core.common import (
    carregar_csv_fonte,
    consolidar_bronze,
    extrair_ano_nome_arquivo,
    listar_arquivos_obrigatorios,
    preparar_parte_bronze,
    projetar_parte_bronze_sem_metadados,
    renomear_colunas_contratadas,
    validar_chave_unica,
)
from etl.core.logger import get_logger
from etl.educacao.config import (
    ANO_ED_BASICA_ATUAL,
    ANOS_ED_BASICA_HISTORICO,
    BRONZE_ED_BASICA,
    RAW_ED_BASICA,
    RAW_ED_BASICA_ESCOLA,
    RAW_ED_BASICA_MATRICULA,
)
from etl.educacao.schema import (
    ALIASES_ED_BASICA,
    ALIASES_ED_BASICA_MATRICULA,
    CHAVE_ESCOLA_ANO,
    COLUNAS_ED_BASICA,
    COLUNAS_ED_BASICA_ESCOLA,
    COLUNAS_ED_BASICA_MATRICULA,
    COLUNAS_OPCIONAIS_ED_BASICA,
    COLUNAS_OPCIONAIS_ED_BASICA_MATRICULA,
    PREFIXOS_METRICAS_ALUNOS_ED_BASICA,
    RENOMEACAO_ED_BASICA,
    RENOMEACAO_ED_BASICA_ESCOLA,
    RENOMEACAO_ED_BASICA_MATRICULA,
    SCHEMA_ED_BASICA_BRONZE,
)

log = get_logger(pipeline="educacao")

READ_ATTEMPTS = [
    {"sep": ";", "encoding": "latin1"},
    {"sep": ";", "encoding": "utf-8-sig"},
    {"sep": ",", "encoding": "utf-8-sig"},
]
CHAVE_ESCOLA_ANO_RAW = ["NU_ANO_CENSO", "CO_ENTIDADE"]


def _cabecalho(caminho: Path) -> list[str]:
    """Le somente o cabecalho; nao carrega o CSV inteiro em memoria."""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            with caminho.open("r", encoding=encoding, newline="") as arq:
                primeira_linha = arq.readline()
            if not primeira_linha:
                raise RuntimeError(f"Arquivo vazio: {caminho}")
            separador = max((";", ",", "\t", "|"), key=primeira_linha.count)
            colunas = next(csv.reader([primeira_linha], delimiter=separador))
            colunas = [c.strip().lstrip("\ufeff") for c in colunas]
            if len(colunas) >= 2 and len(set(colunas)) == len(colunas):
                return colunas
        except (UnicodeError, csv.Error, StopIteration):
            continue
    raise RuntimeError(f"Cabecalho nao identificado ou com colunas repetidas: {caminho}")


def _selecionar_colunas(
    caminho: Path,
    esperadas: list[str],
    opcionais: list[str],
    aliases: dict[str, str],
    obrigatorias: list[str],
    contexto: str,
) -> tuple[list[str], dict[str, str]]:
    """Seleciona os campos realmente presentes e informa ausencias do layout."""
    cabecalho = _cabecalho(caminho)
    nomes = set(cabecalho)
    contratadas = list(dict.fromkeys([*esperadas, *opcionais]))
    canonicas = set(contratadas)
    inversos: dict[str, list[str]] = {}
    for origem, destino in aliases.items():
        inversos.setdefault(destino, []).append(origem)

    selecionadas: list[str] = []
    renomear_alias: dict[str, str] = {}
    ausentes: list[str] = []
    for nome in contratadas:
        if nome in nomes:
            selecionadas.append(nome)
        else:
            alternativas = [a for a in inversos.get(nome, []) if a in nomes]
            if alternativas:
                selecionadas.append(alternativas[0])
                renomear_alias[alternativas[0]] = nome
            else:
                ausentes.append(nome)

    faltantes = sorted(
        set(obrigatorias) - set(contratadas) | {c for c in obrigatorias if c in ausentes}
    )
    if faltantes:
        raise RuntimeError(f"{contexto}: colunas essenciais ausentes: {faltantes}")

    adicionais = [
        c
        for c in cabecalho
        if c.startswith(PREFIXOS_METRICAS_ALUNOS_ED_BASICA) and aliases.get(c, c) not in canonicas
    ]
    if adicionais:
        log.warning(
            "[BRONZE] %s | %s metricas adicionais do INEP fora do schema: %s",
            contexto,
            len(adicionais),
            ", ".join(adicionais[:30]),
        )
    log.info(
        "[BRONZE] %s | campos contratados encontrados=%s | indisponiveis=%s",
        contexto,
        len(selecionadas),
        len(ausentes),
    )
    if ausentes:
        log.info("[BRONZE] %s | ausentes do layout: %s", contexto, ", ".join(ausentes))
    return selecionadas, renomear_alias


def _ler_fonte_contratada(
    arquivo: Path,
    esperadas: list[str],
    opcionais: list[str],
    aliases: dict[str, str],
    obrigatorias: list[str],
    contexto: str,
) -> pl.DataFrame:
    colunas, alias_presentes = _selecionar_colunas(
        arquivo,
        esperadas,
        opcionais,
        aliases,
        obrigatorias,
        contexto,
    )
    df = carregar_csv_fonte(
        arquivo=arquivo,
        colunas_brutas=colunas,
        read_attempts=READ_ATTEMPTS,
        contexto=contexto,
    )
    if alias_presentes:
        df = df.rename(alias_presentes)
    # A chave deve ser coerente entre as tabelas 2025, independente da inferencia.
    return df.with_columns(
        pl.col("NU_ANO_CENSO").cast(pl.String).str.strip_chars(),
        pl.col("CO_ENTIDADE").cast(pl.String).str.strip_chars(),
    )


def _processar_historico_2018_2024() -> list[pl.DataFrame]:
    anos = set(ANOS_ED_BASICA_HISTORICO)
    arquivos = listar_arquivos_obrigatorios(
        RAW_ED_BASICA,
        "Censo Escolar - Historico",
        anos,
    )
    partes: list[pl.DataFrame] = []

    for arquivo in arquivos:
        caminho = Path(arquivo)
        ano = extrair_ano_nome_arquivo(caminho)
        if ano is None or ano not in anos:
            raise RuntimeError(f"Censo Escolar - Historico: ano invalido: {caminho.name}")
        contexto = f"Censo Escolar {ano} - {caminho.name}"
        df = _ler_fonte_contratada(
            caminho,
            COLUNAS_ED_BASICA,
            COLUNAS_OPCIONAIS_ED_BASICA,
            ALIASES_ED_BASICA,
            [
                "NU_ANO_CENSO",
                "CO_ENTIDADE",
                "CO_MUNICIPIO",
                "NO_ENTIDADE",
                "QT_MAT_MED",
            ],
            contexto,
        )
        df = preparar_parte_bronze(
            df=df,
            arquivo=arquivo,
            schema_bronze=SCHEMA_ED_BASICA_BRONZE,
            contexto=contexto,
            renomeacao=RENOMEACAO_ED_BASICA,
        )
        validar_chave_unica(df, CHAVE_ESCOLA_ANO, contexto)
        partes.append(df)
        log.info("[BRONZE] Censo Escolar | ano=%s | linhas=%s", ano, f"{df.height:,}")
    return partes


def _processar_2025() -> pl.DataFrame:
    arquivo_escola = Path(
        listar_arquivos_obrigatorios(
            RAW_ED_BASICA_ESCOLA,
            f"Censo Escolar {ANO_ED_BASICA_ATUAL} - Escola",
            {ANO_ED_BASICA_ATUAL},
        )[0]
    )
    arquivo_matricula = Path(
        listar_arquivos_obrigatorios(
            RAW_ED_BASICA_MATRICULA,
            f"Censo Escolar {ANO_ED_BASICA_ATUAL} - Matricula",
            {ANO_ED_BASICA_ATUAL},
        )[0]
    )
    contexto_escola = f"Censo Escolar {ANO_ED_BASICA_ATUAL} - Escola - {arquivo_escola.name}"
    contexto_matricula = (
        f"Censo Escolar {ANO_ED_BASICA_ATUAL} - Matricula - {arquivo_matricula.name}"
    )

    df_escola = _ler_fonte_contratada(
        arquivo_escola,
        COLUNAS_ED_BASICA_ESCOLA,
        [],
        {},
        ["NU_ANO_CENSO", "CO_ENTIDADE", "CO_MUNICIPIO", "NO_ENTIDADE"],
        contexto_escola,
    )
    df_matricula = _ler_fonte_contratada(
        arquivo_matricula,
        COLUNAS_ED_BASICA_MATRICULA,
        COLUNAS_OPCIONAIS_ED_BASICA_MATRICULA,
        ALIASES_ED_BASICA_MATRICULA,
        ["NU_ANO_CENSO", "CO_ENTIDADE", "QT_MAT_MED"],
        contexto_matricula,
    )
    validar_chave_unica(df_escola, CHAVE_ESCOLA_ANO_RAW, contexto_escola)
    validar_chave_unica(df_matricula, CHAVE_ESCOLA_ANO_RAW, contexto_matricula)

    df_escola = renomear_colunas_contratadas(
        df_escola,
        RENOMEACAO_ED_BASICA_ESCOLA,
        contexto_escola,
    )
    df_matricula = renomear_colunas_contratadas(
        df_matricula,
        RENOMEACAO_ED_BASICA_MATRICULA,
        contexto_matricula,
    )

    # Detecta se a tabela de matriculas possui escolas que nao constam no cadastro.
    sem_cadastro = df_matricula.join(
        df_escola.select(CHAVE_ESCOLA_ANO),
        on=CHAVE_ESCOLA_ANO,
        how="anti",
    )
    if sem_cadastro.height:
        raise RuntimeError(
            f"{contexto_matricula}: {sem_cadastro.height} escola(s) sem cadastro. "
            f"Amostra: {sem_cadastro.select(CHAVE_ESCOLA_ANO).head(10).to_dicts()}"
        )

    df = df_escola.join(
        df_matricula,
        on=CHAVE_ESCOLA_ANO,
        how="left",
        validate="1:1",
    )
    # Se escola estiver sem linha na fonte Matricula, preservar null, nao zero.
    df = df.with_columns(
        pl.lit(None, dtype=pl.String).alias("indicador_ensino_medio"),
        pl.lit(f"{arquivo_escola.name} | {arquivo_matricula.name}")
        .cast(pl.String)
        .alias("arquivo_origem"),
        pl.lit(ANO_ED_BASICA_ATUAL).cast(pl.Int64).alias("ano_arquivo"),
    )
    df = projetar_parte_bronze_sem_metadados(
        df,
        SCHEMA_ED_BASICA_BRONZE,
        f"Censo Escolar {ANO_ED_BASICA_ATUAL} - Escola x Matricula",
    )
    validar_chave_unica(df, CHAVE_ESCOLA_ANO, "Bronze Educacao Basica 2025")
    log.info(
        "[BRONZE] Censo Escolar | ano=%s | linhas=%s | join=Escola x Matricula",
        ANO_ED_BASICA_ATUAL,
        f"{df.height:,}",
    )
    return df


def executar() -> None:
    partes = _processar_historico_2018_2024()
    partes.append(_processar_2025())
    consolidar_bronze(
        partes=partes,
        schema_bronze=SCHEMA_ED_BASICA_BRONZE,
        output_path=BRONZE_ED_BASICA,
        dataset_name="Censo Escolar - Educacao Basica",
    )


if __name__ == "__main__":
    executar()
