"""Diretorios e registro de pipelines ativos do projeto BI.

Adicionar novos projetos ao PIPELINES somente apos seu modulo config existir.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_DIR / "data"
AUDIT_ROOT = PROJECT_DIR / "audit"
LOG_ROOT = PROJECT_DIR / "log"
DASHBOARDS_SOURCE_DIR = PROJECT_DIR / "dashboards"
DASHBOARDS_CORE_DIR = DASHBOARDS_SOURCE_DIR / "core"
DASHBOARDS_GRAFICOS_DIR = DASHBOARDS_SOURCE_DIR / "graficos"

DEFAULT_PIPELINE = "educacao"

PIPELINES = {
    "educacao": "etl.educacao.config",
}
