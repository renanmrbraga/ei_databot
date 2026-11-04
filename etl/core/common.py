"""Funcoes reutilizaveis do BI: I/O, normalizacao, Polars e validacao.

Sem importacao de config, schema ou regras de negocio de qualquer ETL.
As funcoes de cada pipeline devem ser importadas diretamente deste modulo.
"""

from __future__ import annotations

import csv
import glob
import hashlib
import json
import logging
import math
import os
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Any

import polars as pl

log = logging.getLogger(__name__)


# ==============================================================================
# ARQUIVOS, HASHES E SERIALIZACAO
# ==============================================================================


def agora_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with Path(caminho).open("rb") as arq:
        for bloco in iter(lambda: arq.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def gravar_json(caminho: str | Path, dados: Any) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temp = caminho.with_name(caminho.name + ".tmp")
    try:
        temp.write_text(
            json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False, default=str),
            encoding="utf-8",
        )
        os.replace(temp, caminho)
    finally:
        temp.unlink(missing_ok=True)


def gravar_parquet(caminho: str | Path, df: pl.DataFrame) -> None:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temp = caminho.with_name(caminho.name + ".tmp")
    try:
        df.write_parquet(temp)
        os.replace(temp, caminho)
    finally:
        temp.unlink(missing_ok=True)


def ler_json(caminho: str | Path) -> dict[str, Any]:
    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError(f"JSON ausente: {caminho}")
    return json.loads(caminho.read_text(encoding="utf-8-sig"))


def conferir_hash(caminho: Path, hash_esperado: str, contexto: str) -> None:
    if sha256_arquivo(caminho) != hash_esperado:
        raise ValueError(
            f"{contexto}: arquivo alterado desde a ultima execucao. Reprocesse a camada anterior: {caminho}"
        )


def sha256_json(dados: Any) -> str:
    """Hash SHA-256 deterministico de um JSON (ordem e formato canonicos)."""
    bruto = json.dumps(
        dados,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()


# ==============================================================================
# LEITURA CSV, EXCEL E PARQUET
# ==============================================================================


def _normalizar_encoding(encoding: str | None) -> str:
    if encoding is None:
        return "utf8"

    mapa = {
        "utf-8": "utf8",
        "utf8": "utf8",
        "utf-8-sig": "utf8-lossy",
        "latin1": "windows-1252",
        "latin-1": "windows-1252",
        "iso-8859-1": "windows-1252",
        "cp1252": "windows-1252",
    }

    return mapa.get(
        encoding.lower(),
        encoding,
    )


def ler_csv(
    filepath: str | Path,
    **kwargs: Any,
) -> pl.DataFrame:
    """
    Carrega arquivo CSV com Polars.

    Aceita aliases de leitura usados pelo ETL,
    como sep, encoding, dtype e low_memory.
    """
    params = dict(kwargs)

    if "sep" in params:
        params["separator"] = params.pop("sep")

    if "encoding" in params:
        params["encoding"] = _normalizar_encoding(params["encoding"])

    dtype = params.pop("dtype", None)
    params.pop("low_memory", None)

    if dtype in (str, "str", "string"):
        params["infer_schema"] = False

    return pl.read_csv(
        filepath,
        **params,
    )


def ler_csv_com_tentativas(
    filepath: str | Path,
    read_attempts: Iterable[Mapping[str, Any]],
    **kwargs: Any,
) -> pl.DataFrame:
    """Tenta ler um CSV usando, em ordem, combinacoes de separador/encoding.

    ``kwargs`` adicionais sao encaminhados ao ``pl.read_csv``. Isso permite,
    por exemplo, projetar somente as colunas necessarias ainda na leitura.
    """
    ultimo_erro: Exception | None = None

    for tentativa in read_attempts:
        params = dict(kwargs)
        params.update(dict(tentativa))

        try:
            return ler_csv(
                filepath,
                dtype=str,
                truncate_ragged_lines=False,
                ignore_errors=False,
                **params,
            )
        except (
            UnicodeDecodeError,
            pl.exceptions.ComputeError,
            ValueError,
        ) as exc:
            ultimo_erro = exc

    if ultimo_erro is None:
        raise ValueError("read_attempts não pode ser vazio.")

    raise RuntimeError(f"Não foi possível ler o CSV {Path(filepath).name}.") from ultimo_erro


def ler_parquet(
    filepath: str | Path,
) -> pl.DataFrame:
    """Lê arquivo Parquet com Polars."""
    return pl.read_parquet(filepath)


def ler_excel_posicional(arquivo: Path, aba: str) -> tuple[Any, list[str]]:
    bruto = pl.read_excel(
        arquivo,
        sheet_name=aba,
        engine="calamine",
        has_header=False,
        infer_schema_length=None,
    )
    if bruto.is_empty() or bruto.width == 0:
        raise ValueError(f"Aba Excel vazia: {aba} ({arquivo})")
    cabecalhos = [str(c).strip() if c is not None else "" for c in bruto.row(0)]
    colunas = [f"col_{n:03d}" for n in range(1, bruto.width + 1)]
    dados = (
        bruto.slice(1)
        .rename(dict(zip(bruto.columns, colunas, strict=True)))
        .with_row_index("_linha_fonte", offset=2)
    )
    return dados, cabecalhos


def ler_csv_posicional(caminho: Path) -> tuple[Any, list[str]]:
    """CSV textual preserva CPF/IDs e a posicao de colunas repetidas."""
    conteudo = None
    for codificacao in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            conteudo = caminho.read_text(encoding=codificacao)
            break
        except UnicodeDecodeError:
            pass
    if conteudo is None:
        raise ValueError(f"Nao foi possivel decodificar o CSV {caminho}")
    try:
        sep = csv.Sniffer().sniff(conteudo[:20000], delimiters=";,\t|").delimiter
    except csv.Error:
        sep = ";" if conteudo.splitlines()[0].count(";") else ","
    reader = csv.reader(StringIO(conteudo), delimiter=sep)
    cabecalhos = next(reader, None)
    if not cabecalhos:
        raise ValueError(f"CSV vazio: {caminho}")
    colunas = [f"col_{i:03d}" for i in range(1, len(cabecalhos) + 1)]
    linhas = []
    for valores in reader:
        indice = reader.line_num
        if len(valores) != len(colunas):
            raise ValueError(
                f"CSV {caminho.name}, linha {indice}: {len(valores)} campos; esperados {len(colunas)}"
            )
        if any(str(v).strip() for v in valores):
            linhas.append([indice, *valores])
    dados = pl.DataFrame(
        {
            "_linha_fonte": pl.Series([v[0] for v in linhas], dtype=pl.UInt32),
            **{
                nome: pl.Series([v[i + 1] for v in linhas], dtype=pl.String)
                for i, nome in enumerate(colunas)
            },
        }
    )
    return dados, [str(h).strip() for h in cabecalhos]


# ==============================================================================
# LOCALIZACAO DE ARQUIVOS E METADADOS
# ==============================================================================


def resolver_arquivos_origem(caminho: Path) -> list[Path]:
    """Aceita pasta de extracao, arquivo, ou prefixo (sem extensao)."""
    caminho = Path(caminho)
    if caminho.is_dir():
        encontrados = sorted(
            p
            for p in caminho.rglob("*")
            if p.is_file()
            and p.suffix.lower() in {".csv", ".xlsx", ".xlsm", ".parquet"}
            and not p.name.startswith("~$")
        )
    elif caminho.is_file():
        encontrados = [caminho]
    else:
        encontrados = sorted(
            p
            for p in caminho.parent.glob(caminho.name + "*")
            if p.is_file() and p.suffix.lower() in {".csv", ".xlsx", ".xlsm", ".parquet"}
        )
    if not encontrados:
        raise FileNotFoundError(f"Fonte nao encontrada: {caminho} (pasta, arquivo ou prefixo)")
    return encontrados


def extrair_ano_nome_arquivo(
    filepath: str | Path,
) -> int | None:
    """Extrai o primeiro ano no formato 20XX do nome do arquivo."""
    match = re.search(
        r"(20\d{2})",
        Path(filepath).name,
    )

    return int(match.group(1)) if match else None


def limpar_nomes_colunas(df: pl.DataFrame) -> pl.DataFrame:
    """Remove espaços acidentais dos nomes das colunas."""
    renomeacoes = {
        coluna: str(coluna).strip() for coluna in df.columns if coluna != str(coluna).strip()
    }

    return df.rename(renomeacoes) if renomeacoes else df


def adicionar_metadados_origem(
    df: pl.DataFrame,
    filepath: str | Path,
) -> pl.DataFrame:
    """Adiciona metadados técnicos de rastreabilidade do arquivo de origem."""
    caminho = Path(filepath)

    return df.with_columns(
        pl.lit(caminho.name).cast(pl.String).alias("arquivo_origem"),
        pl.lit(extrair_ano_nome_arquivo(caminho)).cast(pl.Int64, strict=False).alias("ano_arquivo"),
    )


def listar_arquivos_obrigatorios(
    pattern: str,
    dataset_name: str,
    anos_esperados: Sequence[int] | set[int] | None = None,
) -> list[str]:
    """Localiza arquivos e valida cobertura anual quando aplicavel."""
    arquivos = sorted(glob.glob(pattern))

    if not arquivos:
        raise FileNotFoundError(
            f"{dataset_name}: nenhum arquivo encontrado para o padrao: {pattern}"
        )

    if anos_esperados is None:
        return arquivos

    esperados = set(anos_esperados)
    anos_encontrados: list[int] = []
    sem_ano: list[str] = []

    for arquivo in arquivos:
        ano = extrair_ano_nome_arquivo(arquivo)
        if ano is None:
            sem_ano.append(Path(arquivo).name)
        else:
            anos_encontrados.append(ano)

    if sem_ano:
        raise RuntimeError(f"{dataset_name}: arquivo(s) sem ano 20XX no nome: {sem_ano}")

    contagem = Counter(anos_encontrados)
    duplicados = sorted(ano for ano, qtd in contagem.items() if qtd > 1)
    encontrados = set(anos_encontrados)
    faltantes = sorted(esperados - encontrados)
    inesperados = sorted(encontrados - esperados)

    problemas: list[str] = []
    if faltantes:
        problemas.append(f"anos faltantes={faltantes}")
    if inesperados:
        problemas.append(f"anos nao cadastrados={inesperados}")
    if duplicados:
        problemas.append(f"mais de um arquivo por ano={duplicados}")

    if problemas:
        raise RuntimeError(f"{dataset_name}: " + " | ".join(problemas))

    return arquivos


# ==============================================================================
# POLARS: TRANSFORMACAO E EXPRESSOES
# ==============================================================================


def classificar_texto_por_anchor_expr(
    coluna: str | pl.Expr,
    mapa: Mapping[str, str],
    valor_padrao: str = "OUTROS",
) -> pl.Expr:
    """Classifica texto pela ancora mais especifica encontrada."""

    texto = pl.col(coluna) if isinstance(coluna, str) else coluna

    texto = texto.cast(pl.String).str.strip_chars().str.to_uppercase()

    candidatos = [
        pl.when(
            texto.str.contains(
                anchor,
                literal=True,
            )
        ).then(
            pl.lit(
                mapa[anchor],
                dtype=pl.String,
            )
        )
        for anchor in sorted(
            mapa,
            key=len,
            reverse=True,
        )
    ]

    return pl.coalesce(
        [
            *candidatos,
            pl.lit(
                valor_padrao,
                dtype=pl.String,
            ),
        ]
    )


def extrair_anchor_texto_expr(
    coluna: str | pl.Expr,
    mapa: Mapping[str, object],
    valor_padrao: str = "OUTROS",
) -> pl.Expr:
    texto = pl.col(coluna) if isinstance(coluna, str) else coluna

    texto = texto.cast(pl.String).str.to_uppercase().str.strip_chars()

    candidatos = [
        pl.when(texto.str.contains(anchor, literal=True)).then(pl.lit(anchor, dtype=pl.String))
        for anchor in sorted(
            mapa,
            key=len,
            reverse=True,
        )
    ]

    return pl.coalesce(
        [
            *candidatos,
            pl.lit(valor_padrao, dtype=pl.String),
        ]
    )


def padronizar_texto_por_codigo_expr(
    coluna_codigo: str,
    coluna_texto: str,
    mapa: Mapping[int, str],
) -> pl.Expr:
    """Padroniza um texto a partir de um codigo oficial, preservando fallback textual."""

    def _resolver(
        row: dict[str, object],
    ) -> str | None:
        codigo = row.get(coluna_codigo)
        texto = row.get(coluna_texto)

        if isinstance(codigo, int):
            valor_padrao = mapa.get(codigo)

            if valor_padrao is not None:
                return valor_padrao

        if texto is None:
            return None

        return str(texto).strip().upper()

    return pl.struct(
        [
            coluna_codigo,
            coluna_texto,
        ]
    ).map_elements(
        _resolver,
        return_dtype=pl.String,
        skip_nulls=False,
    )


def mapear_alias(
    cabecalhos: list[str], aliases: dict[str, tuple[str, ...]]
) -> dict[str, str | None]:
    """Retorna a coluna posicional de cada conceito e detecta aliases ambiguos."""
    indice: dict[str, list[str]] = {}
    for i, valor in enumerate(cabecalhos, start=1):
        indice.setdefault(chave_cabecalho(valor), []).append(f"col_{i:03d}")
    resultado = {}
    for campo, opcoes in aliases.items():
        encontrados = []
        for opcao in opcoes:
            encontrados.extend(indice.get(chave_cabecalho(opcao), []))
        encontrados = list(dict.fromkeys(encontrados))
        if len(encontrados) > 1:
            raise ValueError(
                f"Ambiguidade de colunas para {campo}: {encontrados}. Revise mapping.py"
            )
        resultado[campo] = encontrados[0] if encontrados else None
    return resultado


# ==============================================================================
# NORMALIZACAO E IDENTIFICADORES
# ==============================================================================


def valor_nulo(valor: object) -> bool:
    return valor is None or (isinstance(valor, float) and math.isnan(valor))


def normalizar_texto(valor: Any) -> str | None:
    """Normaliza texto e identifica marcadores de ausencia."""
    if valor is None:
        return None

    texto = unicodedata.normalize("NFKD", str(valor).strip())
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    texto = re.sub(r"\s+", " ", texto.upper()).strip()

    if not texto or texto in {
        "N/A",
        "NULL",
        "NAN",
        "NONE",
        "-",
        "--",
        "---",
        ".",
        "NAO INFORMADO",
        "NAO INFORMADA",
        "SEM RESPOSTA",
    }:
        return None

    return texto


def normalizar_texto_chave(valor: object) -> str:
    """Normaliza texto para chaves analiticas e correspondencias."""
    if valor_nulo(valor):
        return ""

    texto = str(valor).upper().strip()

    if texto in {"", "NAN", "NONE", "NULL", "<NA>"}:
        return ""

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))

    texto = texto.replace("-", " ").replace("'", " ")

    return " ".join(texto.split())


def normalizar_texto_chave_expr(
    coluna: str | pl.Expr,
) -> pl.Expr:
    expr = pl.col(coluna) if isinstance(coluna, str) else coluna

    return expr.map_elements(
        normalizar_texto_chave,
        return_dtype=pl.String,
        skip_nulls=False,
    )


def chave_cabecalho(valor: Any) -> str:
    return re.sub(
        r"[^a-z0-9]",
        "",
        (normalizar_texto(valor) or "").lower(),
    )


def normalizar_id(valor: Any) -> str | None:
    if valor is None:
        return None

    texto = str(valor).strip()
    texto = re.sub(r"^(\d+)[.,]0+$", r"\1", texto)

    return texto or None


def normalizar_cpf(valor: Any) -> str | None:
    if valor is None:
        return None

    texto = re.sub(r"^(\d+)[.,]0+$", r"\1", str(valor).strip())
    digitos = re.sub(r"\D", "", texto)

    if not 9 <= len(digitos) <= 11:
        return None

    digitos = digitos.zfill(11)

    return digitos if len(set(digitos)) > 1 else None


def normalizar_telefone(valor: Any) -> str | None:
    if valor is None:
        return None

    digitos = re.sub(r"\D", "", str(valor))

    if len(digitos) in (12, 13) and digitos.startswith("55"):
        digitos = digitos[2:]

    return digitos if len(digitos) in (10, 11) else None


# ==============================================================================
# VALIDACAO GENERICA DE COLUNAS, CHAVES E SCHEMAS
# ==============================================================================


def validar_colunas(df: Any, obrigatorias: set[str], contexto: str) -> None:
    faltantes = obrigatorias - set(df.columns)
    if faltantes:
        raise ValueError(f"{contexto}: colunas obrigatorias ausentes: {sorted(faltantes)}")


def validar_colunas_brutas(
    df: pl.DataFrame,
    colunas_esperadas: Iterable[str],
    contexto: str,
) -> list[str]:
    """Valida a presenca das colunas minimas de uma fonte bruta."""
    colunas_esperadas = list(colunas_esperadas)
    colunas_ausentes = [coluna for coluna in colunas_esperadas if coluna not in df.columns]

    if not colunas_ausentes:
        log.debug(
            "[FONTE] %s: contrato bruto OK | colunas=%s",
            contexto,
            f"{len(colunas_esperadas):,}",
        )
        return []

    detalhe = "Colunas brutas obrigatorias ausentes: " + ", ".join(colunas_ausentes)

    log.error(
        "[FONTE] %s | %s",
        contexto,
        detalhe,
    )

    raise RuntimeError(f"{contexto}: {detalhe}")


def validar_colunas_obrigatorias_por_schema(
    df: pl.DataFrame,
    schema: Mapping[str, pl.DataType | type[pl.DataType]],
    contexto: str,
    ignorar: set[str] | None = None,
    *,
    validar_tipos: bool = False,
    permitir_extras: bool = True,
) -> None:
    """Valida colunas, extras e opcionalmente os dtypes de um contrato."""
    ignorar = ignorar or set()

    colunas_esperadas = [coluna for coluna in schema if coluna not in ignorar]

    colunas_ausentes = [coluna for coluna in colunas_esperadas if coluna not in df.columns]

    colunas_extras: list[str] = []

    if not permitir_extras:
        colunas_extras = [coluna for coluna in df.columns if coluna not in schema]

    tipos_divergentes: list[str] = []

    if validar_tipos:
        schema_atual = df.schema

        for coluna in colunas_esperadas:
            if coluna not in schema_atual:
                continue

            tipo_esperado = schema[coluna]
            tipo_atual = schema_atual[coluna]

            if tipo_atual != tipo_esperado:
                tipos_divergentes.append(f"{coluna}: esperado={tipo_esperado}, atual={tipo_atual}")

    if not colunas_ausentes and not colunas_extras and not tipos_divergentes:
        log.debug(
            "[SCHEMA] %s: contrato OK | colunas=%s | tipos=%s | extras=%s",
            contexto,
            f"{len(colunas_esperadas):,}",
            "validados" if validar_tipos else "nao validados",
            "permitidas" if permitir_extras else "nao permitidas",
        )
        return

    mensagens: list[str] = []

    if colunas_ausentes:
        mensagens.append("colunas ausentes: " + ", ".join(colunas_ausentes))

    if colunas_extras:
        mensagens.append("colunas extras: " + ", ".join(colunas_extras))

    if tipos_divergentes:
        mensagens.append("tipos divergentes: " + " | ".join(tipos_divergentes))

    detalhe = "; ".join(mensagens)

    log.critical(
        "[SCHEMA] %s: %s",
        contexto,
        detalhe,
    )

    raise RuntimeError(f"Falha no contrato de schema: {contexto}. {detalhe}")


def completar_colunas_por_schema(
    df: pl.DataFrame,
    schema: Mapping[str, pl.DataType | type[pl.DataType]],
    colunas: Iterable[str] | None = None,
) -> pl.DataFrame:
    """Cria como null apenas as colunas conhecidas que foram autorizadas."""
    candidatas = list(schema) if colunas is None else list(colunas)

    ausentes = [coluna for coluna in candidatas if coluna in schema and coluna not in df.columns]

    if not ausentes:
        return df

    return df.with_columns(
        [pl.lit(None, dtype=schema[coluna]).alias(coluna) for coluna in ausentes]
    )


def tipar_e_projetar_por_schema(
    df: pl.DataFrame,
    schema: Mapping[str, pl.DataType | type[pl.DataType]],
    contexto: str,
) -> pl.DataFrame:
    """Tipa e projeta o DataFrame exatamente na ordem definida pelo schema."""
    validar_colunas_obrigatorias_por_schema(
        df,
        schema,
        f"Validacao estrutural antes da tipagem - {contexto}",
    )

    tipos_inteiros = {
        pl.Int8,
        pl.Int16,
        pl.Int32,
        pl.Int64,
        pl.UInt8,
        pl.UInt16,
        pl.UInt32,
        pl.UInt64,
    }

    tipos_float = {
        pl.Float32,
        pl.Float64,
    }

    expressoes: list[pl.Expr] = []

    for coluna, dtype in schema.items():
        origem = pl.col(coluna)
        texto = origem.cast(pl.String).str.strip_chars()

        if dtype == pl.String:
            expressao = texto

        elif dtype == pl.Date:
            expressao = pl.coalesce(
                [
                    texto.str.to_date("%Y-%m-%d", strict=False),
                    texto.str.to_date("%d/%m/%Y", strict=False),
                    texto.str.to_datetime(strict=False).dt.date(),
                    origem.cast(pl.Date, strict=False),
                ]
            )

        elif isinstance(dtype, pl.Datetime):
            expressao = pl.coalesce(
                [
                    texto.str.to_datetime(
                        strict=False,
                        time_unit=dtype.time_unit,
                        time_zone=dtype.time_zone,
                    ),
                    origem.cast(dtype, strict=False),
                ]
            ).cast(dtype, strict=False)

        elif dtype in tipos_inteiros:
            expressao = texto.str.replace_all(r"\.0$", "").cast(
                dtype,
                strict=False,
            )

        elif dtype in tipos_float:
            numero = texto.str.replace_all(r"[^\d,.\-]", "")

            numero = (
                pl.when(numero.str.contains(",") & numero.str.contains(r"\."))
                .then(
                    numero.str.replace_all(r"\.", "").str.replace_all(
                        ",",
                        ".",
                    )
                )
                .when(numero.str.contains(","))
                .then(numero.str.replace_all(",", "."))
                .otherwise(numero)
            )

            expressao = numero.cast(dtype, strict=False)

        elif dtype == pl.Boolean:
            booleano = texto.str.to_uppercase().str.replace_all(r"\s+", "")

            expressao = (
                pl.when(
                    booleano.is_in(
                        [
                            "TRUE",
                            "T",
                            "1",
                            "SIM",
                            "S",
                            "VERDADEIRO",
                        ]
                    )
                )
                .then(True)
                .when(
                    booleano.is_in(
                        [
                            "FALSE",
                            "F",
                            "0",
                            "NAO",
                            "N",
                            "FALSO",
                        ]
                    )
                )
                .then(False)
                .otherwise(origem.cast(pl.Boolean, strict=False))
            )

        else:
            expressao = origem.cast(dtype, strict=False)

        expressoes.append(expressao.alias(coluna))

    return df.with_columns(expressoes).select(list(schema))


def validar_chave_unica(
    df: pl.DataFrame,
    chaves: str | Sequence[str],
    contexto: str,
    *,
    proibir_nulos: bool = False,
) -> None:
    """Valida chave composta.

    proibir_nulos=False preserva o comportamento do ETL Educacional.
    proibir_nulos=True preserva o contrato exigido pelo ETL Medicina.
    """
    colunas = [chaves] if isinstance(chaves, str) else list(chaves)
    if not colunas:
        raise ValueError(f"{contexto}: chave sem colunas")

    validar_colunas(df, set(colunas), contexto)

    if (
        proibir_nulos
        and df.select(pl.any_horizontal([pl.col(coluna).is_null() for coluna in colunas]))
        .to_series()
        .any()
    ):
        raise ValueError(f"{contexto}: chave {tuple(colunas)} contem valores nulos")

    duplicadas = df.group_by(colunas).agg(pl.len().alias("qtd")).filter(pl.col("qtd") > 1)
    if duplicadas.is_empty():
        return

    if proibir_nulos:
        raise ValueError(f"{contexto}: chave duplicada {tuple(colunas)}")

    raise RuntimeError(
        f"{contexto}: chave nao unica {colunas}. "
        f"Grupos duplicados={duplicadas.height}. "
        f"Amostra={duplicadas.head(10).to_dicts()}"
    )


# ==============================================================================
# INGESTAO GENERICA COM CONTRATOS
# ==============================================================================


def carregar_csv_fonte(
    arquivo: str | Path,
    colunas_brutas: Sequence[str],
    read_attempts: Sequence[Mapping[str, Any]],
    contexto: str,
    aliases_colunas: Mapping[str, str] | None = None,
) -> pl.DataFrame:
    """
    Le somente as colunas contratadas de uma fonte CSV.

    Cada tentativa de separador/encoding so e considerada valida
    quando o cabecalho encontrado satisfaz o contrato bruto.

    aliases_colunas permite harmonizar variacoes historicas de cabecalho
    sem criar contratos separados por ano.
    """
    if not read_attempts:
        raise ValueError("read_attempts nao pode ser vazio.")

    aliases_colunas = aliases_colunas or {}

    aliases_por_destino: dict[str, list[str]] = {}

    for origem, destino in aliases_colunas.items():
        aliases_por_destino.setdefault(
            destino,
            [],
        ).append(origem)

    erros_tentativas: list[str] = []

    for tentativa in read_attempts:
        params = dict(tentativa)

        # ----------------------------------------------------------------------
        # 1. Le o cabecalho com a tentativa atual.
        # A tentativa so e aceita se o contrato puder ser resolvido.
        # ----------------------------------------------------------------------

        try:
            cabecalho = ler_csv(
                arquivo,
                dtype=str,
                truncate_ragged_lines=False,
                ignore_errors=False,
                n_rows=0,
                **params,
            )

        except (
            UnicodeDecodeError,
            pl.exceptions.ComputeError,
            ValueError,
        ) as exc:
            erros_tentativas.append(f"{params}: falha na leitura do cabecalho ({exc})")
            continue

        cabecalho = limpar_nomes_colunas(cabecalho)
        colunas_disponiveis = set(cabecalho.columns)

        # ----------------------------------------------------------------------
        # 2. Resolve nomes fisicos e aliases.
        # ----------------------------------------------------------------------

        colunas_leitura: list[str] = []
        renomeacao_aliases: dict[str, str] = {}
        colunas_ausentes: list[str] = []

        for coluna in colunas_brutas:
            if coluna in colunas_disponiveis:
                colunas_leitura.append(coluna)
                continue

            candidatos = [
                alias
                for alias in aliases_por_destino.get(
                    coluna,
                    [],
                )
                if alias in colunas_disponiveis
            ]

            if len(candidatos) == 1:
                alias = candidatos[0]

                colunas_leitura.append(alias)
                renomeacao_aliases[alias] = coluna

                continue

            if len(candidatos) > 1:
                raise RuntimeError(
                    f"{contexto}: mais de um alias encontrado para {coluna}: {candidatos}"
                )

            colunas_ausentes.append(coluna)

        # Separador errado pode gerar um CSV "valido" com uma unica coluna.
        # Nesse caso nao aceitamos a tentativa e seguimos para a proxima.
        if colunas_ausentes:
            erros_tentativas.append(
                f"{params}: contrato nao atendido; colunas ausentes={colunas_ausentes}"
            )
            continue

        # ----------------------------------------------------------------------
        # 3. Le os dados com a mesma tentativa que validou o cabecalho.
        # ----------------------------------------------------------------------

        try:
            df = ler_csv(
                arquivo,
                dtype=str,
                truncate_ragged_lines=False,
                ignore_errors=False,
                columns=colunas_leitura,
                **params,
            )

        except (
            UnicodeDecodeError,
            pl.exceptions.ComputeError,
            ValueError,
        ) as exc:
            erros_tentativas.append(
                f"{params}: cabecalho valido, mas falha na leitura dos dados ({exc})"
            )
            continue

        df = limpar_nomes_colunas(df)

        # ----------------------------------------------------------------------
        # 4. Harmoniza aliases para o contrato bruto canonico.
        # ----------------------------------------------------------------------

        if renomeacao_aliases:
            df = df.rename(renomeacao_aliases)

        validar_colunas_brutas(
            df,
            colunas_brutas,
            contexto,
        )

        return df.select(list(colunas_brutas))

    detalhe = " | ".join(erros_tentativas)

    raise RuntimeError(
        f"{contexto}: nenhuma tentativa de leitura satisfez o contrato bruto. {detalhe}"
    )


def carregar_excel_fonte(
    arquivo: str,
    aba: str,
    colunas_brutas: Sequence[str],
    contexto: str,
    colunas_opcionais: Sequence[str] | None = None,
    aliases_colunas: Mapping[str, str] | None = None,
) -> pl.DataFrame:
    """
    Le uma aba Excel e harmoniza o contrato bruto.

    colunas_brutas:
        campos obrigatorios da fonte.

    colunas_opcionais:
        campos conhecidos que podem ou nao existir no arquivo.

    aliases_colunas:
        variacoes historicas de cabecalho apontando para o nome
        canonico do contrato bruto.
    """
    colunas_opcionais = list(colunas_opcionais or [])
    aliases_colunas = aliases_colunas or {}

    try:
        df = pl.read_excel(
            arquivo,
            sheet_name=aba,
            engine="calamine",
            read_options={
                "dtypes": "string",
            },
        )

    except Exception as exc:
        raise RuntimeError(f"{contexto}: falha ao ler {Path(arquivo).name} | aba={aba!r}.") from exc

    df = limpar_nomes_colunas(df)

    # --------------------------------------------------------------------------
    # Harmoniza aliases historicos
    # --------------------------------------------------------------------------

    aliases_por_destino: dict[str, list[str]] = {}

    for origem, destino in aliases_colunas.items():
        aliases_por_destino.setdefault(
            destino,
            [],
        ).append(origem)

    colunas_disponiveis = set(df.columns)
    renomeacao_aliases: dict[str, str] = {}

    colunas_contratadas = [
        *colunas_brutas,
        *colunas_opcionais,
    ]

    for coluna in colunas_contratadas:
        if coluna in colunas_disponiveis:
            continue

        candidatos = [
            alias for alias in aliases_por_destino.get(coluna, []) if alias in colunas_disponiveis
        ]

        if len(candidatos) == 1:
            renomeacao_aliases[candidatos[0]] = coluna
            continue

        if len(candidatos) > 1:
            raise RuntimeError(
                f"{contexto}: mais de um alias encontrado para {coluna}: {candidatos}"
            )

    if renomeacao_aliases:
        df = df.rename(renomeacao_aliases)

    # --------------------------------------------------------------------------
    # Somente o nucleo obrigatorio deve existir em todos os arquivos
    # --------------------------------------------------------------------------

    validar_colunas_brutas(
        df,
        colunas_brutas,
        contexto,
    )

    # --------------------------------------------------------------------------
    # Mantem obrigatorias + opcionais efetivamente presentes
    # --------------------------------------------------------------------------

    colunas_saida = [
        *colunas_brutas,
        *[coluna for coluna in colunas_opcionais if coluna in df.columns],
    ]

    return df.select(colunas_saida)


def renomear_colunas_contratadas(
    df: pl.DataFrame,
    renomeacao: Mapping[str, str] | None,
    contexto: str,
) -> pl.DataFrame:
    """Aplica somente renomeios cujas colunas estejam presentes."""
    if not renomeacao:
        return df

    mapa = {origem: destino for origem, destino in renomeacao.items() if origem in df.columns}
    if not mapa:
        return df

    destinos = list(mapa.values())
    repetidos = sorted(destino for destino, qtd in Counter(destinos).items() if qtd > 1)
    if repetidos:
        raise RuntimeError(
            f"{contexto}: mais de uma coluna bruta aponta para o mesmo campo canonico: {repetidos}"
        )

    colisoes = sorted(
        destino for origem, destino in mapa.items() if destino in df.columns and destino != origem
    )
    if colisoes:
        raise RuntimeError(
            f"{contexto}: renomeacao criaria colisao com coluna existente: {colisoes}"
        )

    return df.rename(mapa)


def preparar_parte_bronze(
    df: pl.DataFrame,
    arquivo: str | Path,
    schema_bronze: Mapping[str, pl.DataType | type[pl.DataType]],
    contexto: str,
    renomeacao: Mapping[str, str] | None = None,
) -> pl.DataFrame:
    """Harmoniza uma fonte e a projeta exatamente no contrato Bronze final."""
    df = renomear_colunas_contratadas(df, renomeacao, contexto)
    df = adicionar_metadados_origem(df, arquivo)
    df = completar_colunas_por_schema(df, schema_bronze)
    return tipar_e_projetar_por_schema(df, schema_bronze, contexto)


def projetar_parte_bronze_sem_metadados(
    df: pl.DataFrame,
    schema_bronze: Mapping[str, pl.DataType | type[pl.DataType]],
    contexto: str,
) -> pl.DataFrame:
    """Projeta um DataFrame que ja recebeu metadados customizados."""
    df = completar_colunas_por_schema(df, schema_bronze)
    return tipar_e_projetar_por_schema(df, schema_bronze, contexto)


def consolidar_bronze(
    partes: Sequence[pl.DataFrame],
    schema_bronze: Mapping[str, pl.DataType | type[pl.DataType]],
    output_path: str | Path,
    dataset_name: str,
) -> pl.DataFrame:
    """Concatena partes ja harmonizadas, valida o contrato final e salva."""
    if not partes:
        raise RuntimeError(f"{dataset_name}: nenhuma parte foi produzida.")

    df_bronze = pl.concat(list(partes), how="vertical")

    validar_colunas_obrigatorias_por_schema(
        df_bronze,
        schema_bronze,
        f"Validacao final Bronze - {dataset_name}",
        validar_tipos=True,
        permitir_extras=False,
    )

    gravar_parquet(output_path, df_bronze)

    log.info(
        "[BRONZE] %s concluido | linhas=%s | colunas=%s | saida=%s",
        dataset_name,
        f"{df_bronze.height:,}",
        len(df_bronze.columns),
        output_path,
    )

    return df_bronze


# ==============================================================================
# CORES
# ==============================================================================


def obter_cor_por_dicionario_ou_hash(
    text: object,
    dictionary: dict,
    salt: str = "",
) -> tuple[str, str]:
    """Busca cor no dicionário ou gera uma cor consistente via hash."""
    if valor_nulo(text):
        return "Cor Automática", "#CCCCCC"

    text_upper = str(text).upper().strip()

    if text_upper in {
        "NAN",
        "NONE",
        "NULL",
        "<NA>",
        "",
        "-",
    }:
        return "Cor Automática", "#CCCCCC"

    for key, val in dictionary.items():
        if key in text_upper:
            return (
                val["cor"],
                val["hex"],
            )

    hash_object = hashlib.md5((text_upper + salt).encode("utf-8"))
    hex_code = "#" + hash_object.hexdigest()[:6].upper()

    return (
        "Cor Automática",
        hex_code,
    )
