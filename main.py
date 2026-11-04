"""Orquestra a carga Educacional e a publicação no PostgreSQL.

Use --plan para inspecionar (padrão) ou --run para executar.
O download e a indexação RAG são operações opcionais e independentes.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class Etapa:
    nome: str
    argumentos: tuple[str, ...]


def criar_plano(
    *,
    download: bool = False,
    dashboard: bool = True,
    deep: bool = False,
    rag: bool = False,
) -> tuple[Etapa, ...]:
    etapas: list[Etapa] = []
    if download:
        etapas.append(Etapa("Atualizar fontes oficiais", ("-m", "etl.educacao.downloader")))

    comando_etl = ["-m", "etl.etl", "--educacao"]
    if not dashboard:
        comando_etl.extend(("--skip", "dashboard_educacao"))
    etapas.append(Etapa("Processar Bronze, Silver, Gold e dashboard opcional", tuple(comando_etl)))
    etapas.append(
        Etapa(
            "Publicar Parquets Gold no PostgreSQL", ("-m", "postgres.sync", "--dataset", "educacao")
        )
    )
    etapas.append(Etapa("Sincronizar catálogo técnico Gold", ("-m", "postgres.sync_catalog")))
    validar = ["-m", "postgres.validate_gold"]
    if deep:
        validar.append("--deep")
    etapas.append(Etapa("Validar Gold publicado", tuple(validar)))
    if rag:
        etapas.append(
            Etapa(
                "Sincronizar documentos RAG",
                ("-m", "postgres.sync_rag", "--batch-size", "5", "--interval", "10"),
            )
        )
    return tuple(etapas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--plan", action="store_true", help="Apenas exibe as etapas (padrão)")
    modo.add_argument("--run", action="store_true", help="Executa as etapas, em sequência")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Atualiza fontes antes do ETL (rede, potencialmente demorado)",
    )
    parser.add_argument("--no-dashboard", action="store_true", help="Não regenera o dashboard")
    parser.add_argument("--deep", action="store_true", help="Executa a validação profunda do Gold")
    parser.add_argument(
        "--rag", action="store_true", help="Sincroniza RAG após validação (pode consumir API)"
    )
    args = parser.parse_args(argv)
    plano = criar_plano(
        download=args.download, dashboard=not args.no_dashboard, deep=args.deep, rag=args.rag
    )

    if not args.run:
        print("PLANO SOMENTE LEITURA — nenhuma etapa será executada.\n")
    else:
        print(
            "EXECUÇÃO SOLICITADA — operações podem sobrescrever saídas e publicar dados.\n",
            flush=True,
        )

    for indice, etapa in enumerate(plano, start=1):
        comando = (sys.executable, *etapa.argumentos)
        print(f"[{indice}/{len(plano)}] {etapa.nome}\n  {' '.join(comando)}", flush=True)
        if not args.run:
            continue
        try:
            subprocess.run(comando, cwd=ROOT, check=True)
        except subprocess.CalledProcessError as exc:
            print(
                f"Falha na etapa {indice}: {etapa.nome} (exit code {exc.returncode}). Interrompido.",
                file=sys.stderr,
            )
            return exc.returncode if exc.returncode > 0 else 1
        except OSError as exc:
            print(
                f"Não foi possível iniciar a etapa {indice}: {type(exc).__name__}.", file=sys.stderr
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
