from __future__ import annotations

from pathlib import Path

from etl.core.config import AUDIT_ROOT, DATA_ROOT, PROJECT_DIR

# ==============================================================================
# DADOS EXTERNOS / RAW (Apontando para data/raw local do projeto)
# ==============================================================================

EXTERNAL_DATA_DIR = PROJECT_DIR / "data" / "raw"
ZIP_CACHE_DIR = EXTERNAL_DATA_DIR / "_zips"

MICRODADOS_DIR = EXTERNAL_DATA_DIR / "microdados"
REFERENCIAS_DIR = EXTERNAL_DATA_DIR / "referencias"

ED_BASICA_DIR = MICRODADOS_DIR / "censo_escolar"
SUPERIOR_DIR = MICRODADOS_DIR / "censo_superior"
ENADE_DIR = MICRODADOS_DIR / "enade"
CPC_DIR = MICRODADOS_DIR / "cpc"
IDD_DIR = MICRODADOS_DIR / "idd"
IGC_DIR = MICRODADOS_DIR / "igc"


# ==============================================================================
# DIRETORIOS DO PIPELINE (Mantidos no novo formato)
# ==============================================================================

DATA_OUTPUT_DIR = DATA_ROOT / "educacao"

BRONZE_DIR = DATA_OUTPUT_DIR / "bronze"
SILVER_DIR = DATA_OUTPUT_DIR / "silver"
GOLD_DIR = DATA_OUTPUT_DIR / "gold"

AUDIT_DIR = AUDIT_ROOT / "educacao"
HEALTH_ETL_FILE = AUDIT_DIR / "health_etl.txt"

ETL_COMMON_MODULE = "etl.educacao.common"
ETL_SCHEMA_MODULE = "etl.educacao.schema"


# ==============================================================================
# RAW - CENSO SUPERIOR
# ==============================================================================

RAW_CURSOS_SUPERIOR = str(SUPERIOR_DIR / "MICRODADOS_CADASTRO_CURSOS_*.CSV")

RAW_IES = str(SUPERIOR_DIR / "MICRODADOS_ED_SUP_IES_*.CSV")


# ==============================================================================
# RAW - CENSO ESCOLAR
# ==============================================================================

RAW_ED_BASICA = str(ED_BASICA_DIR / "microdados_ed_basica_*.csv")

RAW_ED_BASICA_ESCOLA = str(ED_BASICA_DIR / "Tabela_Escola_*.csv")

RAW_ED_BASICA_MATRICULA = str(ED_BASICA_DIR / "Tabela_Matricula_*.csv")


# ==============================================================================
# RAW - CONCEITO ENADE
# ==============================================================================

RAW_CONCEITO_ENADE = str(ENADE_DIR / "conceito_enade_*.xlsx")

ABAS_CONCEITO_ENADE = {
    "conceito_enade_2018.xlsx": "Conceito_Enade_2018",
    "conceito_enade_2019.xlsx": "Conceito Enade2019",
    "conceito_enade_2021.xlsx": "PLANILHA_ENADE",
    "conceito_enade_2022.xlsx": "Planilha1",
    "conceito_enade_2023.xlsx": "PLANILHA_ENADE",
    "conceito_enade_medicina_2025.xlsx": "Conceito Enade Medicina",
}


# ==============================================================================
# RAW - CPC
# ==============================================================================

RAW_CPC = str(CPC_DIR / "cpc_*.xlsx")

ABAS_CPC = {
    "cpc_2018.xlsx": "CPC",
    "cpc_2019.xlsx": "CPC2019",
    "cpc_2021.xlsx": "CPC2021",
    "cpc_2022.xlsx": "CPC 2022",
    "cpc_2023.xlsx": "CPC_2023",
}


# ==============================================================================
# RAW - IDD
# ==============================================================================

RAW_IDD = str(IDD_DIR / "idd_*.xlsx")

ABAS_IDD = {
    "idd_2018.xlsx": "IDD_2018",
    "idd_2019.xlsx": "IDD2019",
    "idd_2021.xlsx": "PLANILHA_IDD",
    "idd_2022.xlsx": "IDD 2022",
    "idd_2023.xlsx": "IDD_2023",
}


# ==============================================================================
# RAW - IGC
# ==============================================================================

RAW_IGC = str(IGC_DIR / "igc_*.xlsx")

ABAS_IGC = {
    "igc_2018.xlsx": "IGC",
    "igc_2019.xlsx": "IGC_2019",
    "igc_2021.xlsx": "IGC_2021",
    "igc_2022.xlsx": "IGC",
    "igc_2023.xlsx": "IGC",
}


# ==============================================================================
# RAW - REFERENCIAS
# ==============================================================================

RAW_GEO = str(REFERENCIAS_DIR / "geo.csv")


# ==============================================================================
# COBERTURA TEMPORAL DAS FONTES
# ==============================================================================

ANOS_CENSO_SUPERIOR = range(2018, 2025)

ANOS_ED_BASICA_HISTORICO = range(2018, 2025)
ANO_ED_BASICA_ATUAL = 2025

ANOS_CONCEITO_ENADE = {
    2018,
    2019,
    2021,
    2022,
    2023,
    2025,
}

ANOS_CPC = {
    2018,
    2019,
    2021,
    2022,
    2023,
}

ANOS_IDD = {
    2018,
    2019,
    2021,
    2022,
    2023,
}

ANOS_IGC = {
    2018,
    2019,
    2021,
    2022,
    2023,
}


# ==============================================================================
# BRONZE
# ==============================================================================

BRONZE_CURSOS_SUPERIOR = str(BRONZE_DIR / "bronze_superior_cursos.parquet")
BRONZE_IES = str(BRONZE_DIR / "bronze_superior_ies.parquet")
BRONZE_ED_BASICA = str(BRONZE_DIR / "bronze_ed_basica.parquet")
BRONZE_GEO = str(BRONZE_DIR / "bronze_geo.parquet")
BRONZE_CONCEITO_ENADE = str(BRONZE_DIR / "bronze_conceito_enade.parquet")
BRONZE_CPC = str(BRONZE_DIR / "bronze_cpc.parquet")
BRONZE_IDD = str(BRONZE_DIR / "bronze_idd.parquet")
BRONZE_IGC = str(BRONZE_DIR / "bronze_igc.parquet")


# ==============================================================================
# SILVER
# ==============================================================================

SILVER_CURSOS_SUPERIOR = str(SILVER_DIR / "silver_superior_cursos.parquet")
SILVER_IES = str(SILVER_DIR / "silver_superior_ies.parquet")
SILVER_ED_BASICA = str(SILVER_DIR / "silver_ed_basica.parquet")
SILVER_GEO = str(SILVER_DIR / "silver_geo.parquet")
SILVER_CONCEITO_ENADE = str(SILVER_DIR / "silver_conceito_enade.parquet")
SILVER_CPC = str(SILVER_DIR / "silver_cpc.parquet")
SILVER_IDD = str(SILVER_DIR / "silver_idd.parquet")
SILVER_IGC = str(SILVER_DIR / "silver_igc.parquet")


# ==============================================================================
# GOLD
# ==============================================================================

GOLD_DIM_CALENDARIO = str(GOLD_DIR / "dim_calendario.parquet")
GOLD_DIM_IES = str(GOLD_DIR / "dim_ies.parquet")
GOLD_DIM_CURSO_SUPERIOR = str(GOLD_DIR / "dim_curso_superior.parquet")
GOLD_DIM_LOCALIDADE = str(GOLD_DIR / "dim_localidade.parquet")
GOLD_DIM_ESCOLA = str(GOLD_DIR / "dim_escola.parquet")

GOLD_FACT_EDUCACAO_SUPERIOR = str(GOLD_DIR / "fact_educacao_superior.parquet")
GOLD_FACT_EDUCACAO_SUPERIOR_TURNO = str(GOLD_DIR / "fact_educacao_superior_turno.parquet")
GOLD_FACT_AVALIACAO_CURSO_SUPERIOR = str(GOLD_DIR / "fact_avaliacao_curso_superior.parquet")
GOLD_FACT_AVALIACAO_IES = str(GOLD_DIR / "fact_avaliacao_ies.parquet")
GOLD_FACT_EDUCACAO_BASICA = str(GOLD_DIR / "fact_educacao_basica.parquet")


# ==============================================================================
# PARAMETROS OPERACIONAIS
# ==============================================================================

SENTINEL_EAD = "EAD"
CODIGO_LOCALIDADE_EAD = -1

# ==============================================================================
# REFERÊNCIA GEOGRÁFICA
# ==============================================================================

CIDADE_REFERENCIA = "RIO DE JANEIRO"
UF_REFERENCIA = "RJ"

COLUNA_DISTANCIA = "distancia_referencia_km"

# ==============================================================================
# PORTFOLIO DE CURSOS MONITORADOS
# ==============================================================================
# O turno permanece no portfólio configurável para distinguir ofertas.
# Na dim_curso_superior, porem, o turno nao participa da identidade do curso.
# O builder reduz esta lista para (curso, grau, modalidade) ao calcular oferta_curso.

CURSOS_PORTFOLIO_DETALHADO = [
    ("BIOMEDICINA", "BACHARELADO", "PRESENCIAL", "NOTURNO"),
    ("DIREITO", "BACHARELADO", "PRESENCIAL", "NOTURNO"),
    ("ENFERMAGEM", "BACHARELADO", "PRESENCIAL", "NOTURNO"),
    ("EDUCAÇÃO FÍSICA", "BACHARELADO", "PRESENCIAL", "NOTURNO"),
    ("FISIOTERAPIA", "BACHARELADO", "PRESENCIAL", "NOTURNO"),
    ("MEDICINA", "BACHARELADO", "PRESENCIAL", "DIURNO"),
    ("MEDICINA VETERINÁRIA", "BACHARELADO", "PRESENCIAL", "DIURNO"),
    ("MEDICINA VETERINÁRIA", "BACHARELADO", "PRESENCIAL", "NOTURNO"),
    ("ODONTOLOGIA", "BACHARELADO", "PRESENCIAL", "DIURNO"),
    ("PSICOLOGIA", "BACHARELADO", "PRESENCIAL", "NOTURNO"),
]


# ==============================================================================
# ORQUESTRADOR - ETAPAS DO PIPELINE
# ==============================================================================
# A ordem declarada aqui e a ordem oficial de execucao do ETL.

STEPS = (
    ("bronze_superior_cursos", "etl.educacao.bronze.bronze_superior_cursos", "bronze"),
    ("bronze_superior_ies", "etl.educacao.bronze.bronze_superior_ies", "bronze"),
    ("bronze_ed_basica", "etl.educacao.bronze.bronze_ed_basica", "bronze"),
    ("bronze_geo", "etl.educacao.bronze.bronze_geo", "bronze"),
    ("bronze_conceito_enade", "etl.educacao.bronze.bronze_conceito_enade", "bronze"),
    ("bronze_cpc", "etl.educacao.bronze.bronze_cpc", "bronze"),
    ("bronze_idd", "etl.educacao.bronze.bronze_idd", "bronze"),
    ("bronze_igc", "etl.educacao.bronze.bronze_igc", "bronze"),
    ("silver_geo", "etl.educacao.silver.silver_geo", "silver"),
    ("silver_superior_cursos", "etl.educacao.silver.silver_superior_cursos", "silver"),
    ("silver_superior_ies", "etl.educacao.silver.silver_superior_ies", "silver"),
    ("silver_ed_basica", "etl.educacao.silver.silver_ed_basica", "silver"),
    ("silver_conceito_enade", "etl.educacao.silver.silver_conceito_enade", "silver"),
    ("silver_cpc", "etl.educacao.silver.silver_cpc", "silver"),
    ("silver_idd", "etl.educacao.silver.silver_idd", "silver"),
    ("silver_igc", "etl.educacao.silver.silver_igc", "silver"),
    ("dim_calendario", "etl.educacao.gold.dim_calendario", "gold"),
    ("dim_ies", "etl.educacao.gold.dim_ies", "gold"),
    ("dim_curso_superior", "etl.educacao.gold.dim_curso_superior", "gold"),
    ("dim_localidade", "etl.educacao.gold.dim_localidade", "gold"),
    ("dim_escola", "etl.educacao.gold.dim_escola", "gold"),
    ("fact_educacao_superior", "etl.educacao.gold.fact_educacao_superior", "gold"),
    (
        "fact_educacao_superior_turno",
        "etl.educacao.gold.fact_educacao_superior_turno",
        "gold",
    ),
    (
        "fact_avaliacao_curso_superior",
        "etl.educacao.gold.fact_avaliacao_curso_superior",
        "gold",
    ),
    ("fact_avaliacao_ies", "etl.educacao.gold.fact_avaliacao_ies", "gold"),
    ("fact_educacao_basica", "etl.educacao.gold.fact_educacao_basica", "gold"),
    (
        "dashboard_educacao",
        "dashboards.educacao",
        "dashboard",
    ),
)


# ==============================================================================
# TABELAS DO PIPELINE
# ==============================================================================

TB = {
    # BRONZE
    "bronze_superior_cursos": Path(BRONZE_CURSOS_SUPERIOR),
    "bronze_superior_ies": Path(BRONZE_IES),
    "bronze_ed_basica": Path(BRONZE_ED_BASICA),
    "bronze_geo": Path(BRONZE_GEO),
    "bronze_conceito_enade": Path(BRONZE_CONCEITO_ENADE),
    "bronze_cpc": Path(BRONZE_CPC),
    "bronze_idd": Path(BRONZE_IDD),
    "bronze_igc": Path(BRONZE_IGC),
    # SILVER
    "silver_superior_cursos": Path(SILVER_CURSOS_SUPERIOR),
    "silver_superior_ies": Path(SILVER_IES),
    "silver_ed_basica": Path(SILVER_ED_BASICA),
    "silver_geo": Path(SILVER_GEO),
    "silver_conceito_enade": Path(SILVER_CONCEITO_ENADE),
    "silver_cpc": Path(SILVER_CPC),
    "silver_idd": Path(SILVER_IDD),
    "silver_igc": Path(SILVER_IGC),
    # GOLD - DIMENSOES
    "dim_calendario": Path(GOLD_DIM_CALENDARIO),
    "dim_ies": Path(GOLD_DIM_IES),
    "dim_curso_superior": Path(GOLD_DIM_CURSO_SUPERIOR),
    "dim_localidade": Path(GOLD_DIM_LOCALIDADE),
    "dim_escola": Path(GOLD_DIM_ESCOLA),
    # GOLD - FATOS
    "fact_educacao_superior": Path(GOLD_FACT_EDUCACAO_SUPERIOR),
    "fact_educacao_superior_turno": Path(GOLD_FACT_EDUCACAO_SUPERIOR_TURNO),
    "fact_avaliacao_curso_superior": Path(GOLD_FACT_AVALIACAO_CURSO_SUPERIOR),
    "fact_avaliacao_ies": Path(GOLD_FACT_AVALIACAO_IES),
    "fact_educacao_basica": Path(GOLD_FACT_EDUCACAO_BASICA),
}


# ==============================================================================
# CORES DOS PASSOS NO CONSOLE
# ==============================================================================

STEP_COLORS = {
    # Bronze
    "bronze_superior_cursos": "\033[96m",
    "bronze_superior_ies": "\033[96m",
    "bronze_ed_basica": "\033[96m",
    "bronze_geo": "\033[96m",
    "bronze_conceito_enade": "\033[96m",
    "bronze_cpc": "\033[96m",
    "bronze_idd": "\033[96m",
    "bronze_igc": "\033[96m",
    # Silver
    "silver_geo": "\033[95m",
    "silver_superior_cursos": "\033[95m",
    "silver_superior_ies": "\033[95m",
    "silver_ed_basica": "\033[95m",
    "silver_conceito_enade": "\033[95m",
    "silver_cpc": "\033[95m",
    "silver_idd": "\033[95m",
    "silver_igc": "\033[95m",
    # Gold
    "dim_calendario": "\033[93m",
    "dim_ies": "\033[93m",
    "dim_curso_superior": "\033[93m",
    "dim_localidade": "\033[93m",
    "dim_escola": "\033[93m",
    "fact_educacao_superior": "\033[92m",
    "fact_educacao_superior_turno": "\033[92m",
    "fact_avaliacao_curso_superior": "\033[92m",
    "fact_avaliacao_ies": "\033[92m",
    "fact_educacao_basica": "\033[92m",
}
