"""Consultas Gold autorizadas para o MVP, sem SQL gerado pela LLM."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from chatbot.services.llm import Interpretacao


@dataclass(frozen=True, slots=True)
class Indicador:
    identificador: str
    tabela: str
    coluna: str
    dominio: str
    fonte: str
    descricao: str
    ano_inicial: int
    ano_final: int


# Cada entrada é um contrato explícito, nunca um nome fornecido pelo modelo.
INDICADORES: dict[str, Indicador] = {
    "CAT-ES-023": Indicador(
        identificador="CAT-ES-023",
        tabela="fact_educacao_superior",
        coluna="matriculados",
        dominio="educacao_superior",
        fonte="INEP / Censo da Educação Superior",
        descricao="Total de matrículas da educação superior",
        ano_inicial=2018,
        ano_final=2024,
    ),
    "CAT-EB-001": Indicador(
        identificador="CAT-EB-001",
        tabela="fact_educacao_basica",
        coluna="matriculas_educacao_basica",
        dominio="educacao_basica",
        fonte="INEP / Censo Escolar",
        descricao="Total de matrículas da educação básica",
        ano_inicial=2018,
        ano_final=2025,
    ),
}

OPERACOES = frozenset({"SOMA_ANUAL", "SERIE_ANUAL"})


class ConsultaNaoSuportada(ValueError):
    """Pedido fora dos contratos analíticos atualmente implementados."""


def _normalizar_municipio(valor: str) -> str:
    nome = unicodedata.normalize("NFKD", valor.strip())
    return "".join(char for char in nome if not unicodedata.combining(char)).upper()


def validar_interpretacao(interpretacao: Interpretacao) -> Indicador:
    """Valida a intenção antes de qualquer consulta ao banco."""
    if interpretacao.filtros_nao_suportados:
        raise ConsultaNaoSuportada(
            "Os filtros solicitados ainda não estão implementados: "
            + ", ".join(interpretacao.filtros_nao_suportados[:5])
            + "."
        )
    indicador = INDICADORES.get(interpretacao.indicador_id or "")
    if indicador is None:
        raise ConsultaNaoSuportada(
            "Indicador ainda não implementado no MVP. "
            "Estão disponíveis matrículas da educação superior e básica."
        )
    if interpretacao.operacao not in OPERACOES:
        raise ConsultaNaoSuportada(
            "Operação ainda não implementada. Use total anual ou série anual."
        )
    if interpretacao.ano_inicial is None or interpretacao.ano_final is None:
        raise ConsultaNaoSuportada("Informe o ano ou o intervalo de anos da consulta.")
    if not (
        indicador.ano_inicial
        <= interpretacao.ano_inicial
        <= interpretacao.ano_final
        <= indicador.ano_final
    ):
        raise ConsultaNaoSuportada(
            f"Período inválido ou indisponível. Para este indicador: "
            f"{indicador.ano_inicial} a {indicador.ano_final}."
        )
    if interpretacao.operacao == "SOMA_ANUAL" and (
        interpretacao.ano_inicial != interpretacao.ano_final
    ):
        raise ConsultaNaoSuportada(
            "Para um total, informe um único ano; para vários anos, solicite uma série anual."
        )
    if interpretacao.municipio is not None and not interpretacao.municipio.strip():
        raise ConsultaNaoSuportada("Município inválido.")
    if interpretacao.uf is not None and not interpretacao.uf.strip():
        raise ConsultaNaoSuportada("UF inválida.")
    if bool(interpretacao.municipio) != bool(interpretacao.uf):
        raise ConsultaNaoSuportada(
            "Para consultar um município, informe também a UF; não selecionamos homônimos automaticamente."
        )
    if interpretacao.municipio is not None and not _normalizar_municipio(interpretacao.municipio):
        raise ConsultaNaoSuportada("Município inválido.")
    if interpretacao.uf is not None and (
        len(interpretacao.uf.strip()) != 2 or not interpretacao.uf.strip().isalpha()
    ):
        raise ConsultaNaoSuportada("UF inválida; informe a sigla de duas letras.")
    return indicador


def consultar_gold(interpretacao: Interpretacao) -> tuple[Indicador, list[dict[str, Any]]]:
    """Executa SOMA_ANUAL ou SERIE_ANUAL com identificadores fixos e parâmetros SQL.

    Não combina fatos, não atribui a EAD uma localização municipal e não
    transforma dados ausentes em zero. O limite temporal é validado antes do SQL.
    """
    indicador = validar_interpretacao(interpretacao)

    # Imports tardios permitem testar o contrato sem conexões/serviços externos.
    from psycopg import sql

    from chatbot.core.database import get_connection

    tabela = sql.Identifier("gold", indicador.tabela)
    coluna = sql.Identifier(indicador.coluna)
    consulta = sql.SQL(
        "SELECT {tabela}.ano, "
        "SUM({tabela}.{coluna})::bigint AS {coluna}, "
        "COUNT({tabela}.{coluna})::bigint AS registros_com_valor "
        "FROM {tabela} "
    ).format(tabela=tabela, coluna=coluna)

    assert interpretacao.ano_inicial is not None
    assert interpretacao.ano_final is not None
    parametros: list[int | str] = [interpretacao.ano_inicial, interpretacao.ano_final]
    if interpretacao.municipio:
        consulta += sql.SQL(
            "JOIN gold.dim_localidade ON "
            "gold.dim_localidade.id_localidade = {tabela}.id_localidade "
        ).format(tabela=tabela)

    consulta += sql.SQL("WHERE {tabela}.ano BETWEEN %s AND %s ").format(tabela=tabela)
    if interpretacao.municipio and interpretacao.uf:
        consulta += sql.SQL(
            "AND gold.dim_localidade.municipio_normalizado = %s AND gold.dim_localidade.uf = %s "
        )
        parametros.extend(
            (_normalizar_municipio(interpretacao.municipio), interpretacao.uf.upper())
        )
    consulta += sql.SQL("GROUP BY {tabela}.ano ORDER BY {tabela}.ano").format(tabela=tabela)

    with get_connection(read_only=True) as connection:
        connection.execute("SET LOCAL statement_timeout = '15000ms'")
        linhas = connection.execute(consulta, parametros).fetchall()
    return indicador, list(linhas)
