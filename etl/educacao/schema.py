from __future__ import annotations

import polars as pl

# ==============================================================================
# CONTRATOS DAS FONTES BRUTAS
# ==============================================================================
# Cada COLUNAS_* representa uma fonte/arquivo real consumido pelo ETL.
# Os nomes abaixo sao os cabecalhos nativos das fontes.
# Variacoes historicas de cabecalho ficam concentradas nos ALIASES_*.
# Os RENOMEACAO_* convertem o contrato bruto harmonizado para o contrato canonico.


# Censo da Educacao Superior - Cursos
COLUNAS_CURSOS_SUPERIOR = [
    # Identificacao
    "NU_ANO_CENSO",
    "NO_REGIAO",
    "CO_REGIAO",
    "NO_UF",
    "SG_UF",
    "CO_UF",
    "NO_MUNICIPIO",
    "CO_MUNICIPIO",
    "IN_CAPITAL",
    "TP_ORGANIZACAO_ACADEMICA",
    "TP_CATEGORIA_ADMINISTRATIVA",
    "TP_REDE",
    "CO_IES",
    "NO_CURSO",
    "CO_CURSO",
    "NO_CINE_ROTULO",
    "CO_CINE_ROTULO",
    "TP_GRAU_ACADEMICO",
    "IN_GRATUITO",
    "TP_MODALIDADE_ENSINO",
    "TP_NIVEL_ACADEMICO",
    # Vagas
    "QT_VG_TOTAL",
    "QT_VG_TOTAL_DIURNO",
    "QT_VG_TOTAL_NOTURNO",
    "QT_VG_TOTAL_EAD",
    "QT_VG_NOVA",
    "QT_VG_PROC_SELETIVO",
    "QT_VG_REMANESC",
    "QT_VG_PROG_ESPECIAL",
    # Inscritos
    "QT_INSCRITO_TOTAL",
    "QT_INSCRITO_TOTAL_DIURNO",
    "QT_INSCRITO_TOTAL_NOTURNO",
    "QT_INSCRITO_TOTAL_EAD",
    "QT_INSC_VG_NOVA",
    "QT_INSC_PROC_SELETIVO",
    "QT_INSC_VG_REMANESC",
    "QT_INSC_VG_PROG_ESPECIAL",
    # Ingressantes
    "QT_ING",
    "QT_ING_DIURNO",
    "QT_ING_NOTURNO",
    "QT_ING_VG_NOVA",
    "QT_ING_VESTIBULAR",
    "QT_ING_ENEM",
    "QT_ING_AVALIACAO_SERIADA",
    "QT_ING_SELECAO_SIMPLIFICA",
    "QT_ING_EGR",
    "QT_ING_OUTRO_TIPO_SELECAO",
    "QT_ING_PROC_SELETIVO",
    "QT_ING_VG_REMANESC",
    "QT_ING_VG_PROG_ESPECIAL",
    "QT_ING_OUTRA_FORMA",
    # Matriculados
    "QT_MAT",
    "QT_MAT_DIURNO",
    "QT_MAT_NOTURNO",
    # Concluintes
    "QT_CONC",
    "QT_CONC_DIURNO",
    "QT_CONC_NOTURNO",
    # Financiamento
    "QT_ING_FIES",
    "QT_ING_PROUNII",
    "QT_ING_PROUNIP",
    "QT_MAT_FIES",
    "QT_MAT_PROUNII",
    "QT_MAT_PROUNIP",
    "QT_CONC_FIES",
    "QT_CONC_PROUNII",
    "QT_CONC_PROUNIP",
    # Situacao academica
    "QT_SIT_TRANCADA",
    "QT_SIT_DESVINCULADO",
    "QT_SIT_TRANSFERIDO",
    "QT_SIT_FALECIDO",
    # Procedencia escolar
    "QT_ING_PROCESCPUBLICA",
    "QT_ING_PROCESCPRIVADA",
    "QT_ING_PROCNAOINFORMADA",
    "QT_MAT_PROCESCPUBLICA",
    "QT_MAT_PROCESCPRIVADA",
    "QT_MAT_PROCNAOINFORMADA",
    "QT_CONC_PROCESCPUBLICA",
    "QT_CONC_PROCESCPRIVADA",
    "QT_CONC_PROCNAOINFORMADA",
]

ALIASES_CURSOS_SUPERIOR = {
    "CO_CINE_ROTULO2": "CO_CINE_ROTULO",
}

# Censo da Educacao Superior - IES
COLUNAS_IES = [
    "NU_ANO_CENSO",
    "CO_IES",
    "NO_IES",
    "SG_IES",
    "NO_MANTENEDORA",
    "TP_ORGANIZACAO_ACADEMICA",
    "TP_CATEGORIA_ADMINISTRATIVA",
    "NO_MUNICIPIO_IES",
    "SG_UF_IES",
]


# Censo da Educacao Basica - arquivo historico de escolas
COLUNAS_ED_BASICA = [
    "NU_ANO_CENSO",
    "SG_UF",
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "CO_ENTIDADE",
    "NO_ENTIDADE",
    "DS_ENDERECO",
    "NU_ENDERECO",
    "DS_COMPLEMENTO",
    "NO_BAIRRO",
    "CO_CEP",
    "TP_DEPENDENCIA",
    "TP_CATEGORIA_ESCOLA_PRIVADA",
    "TP_LOCALIZACAO",
    "TP_SITUACAO_FUNCIONAMENTO",
    "IN_MED",
    "QT_MAT_BAS",
    "QT_MAT_INF",
    "QT_MAT_INF_CRE",
    "QT_MAT_INF_PRE",
    "QT_MAT_FUND",
    "QT_MAT_FUND_AI",
    "QT_MAT_FUND_AF",
    "QT_MAT_MED",
    "QT_MAT_PROF",
    "QT_MAT_PROF_TEC",
    "QT_MAT_EJA",
    "QT_MAT_EJA_FUND",
    "QT_MAT_EJA_MED",
    "QT_MAT_ESP",
    "QT_MAT_ESP_CC",
    "QT_MAT_ESP_CE",
]


# Campos quantitativos adicionais potencialmente presentes em 2018-2024.
# A selecao precisa ignorar ausentes, registrando-os na auditoria.
COLUNAS_OPCIONAIS_ED_BASICA = [
    "QT_MAT_FUND_AI_1",
    "QT_MAT_FUND_AI_2",
    "QT_MAT_FUND_AI_3",
    "QT_MAT_FUND_AI_4",
    "QT_MAT_FUND_AI_5",
    "QT_MAT_FUND_AF_6",
    "QT_MAT_FUND_AF_7",
    "QT_MAT_FUND_AF_8",
    "QT_MAT_FUND_AF_9",
    "QT_MAT_MED_1",
    "QT_MAT_MED_2",
    "QT_MAT_MED_3",
    "QT_MAT_MED_4",
    "QT_MAT_MED_NS",
    "QT_MAT_BAS_FEM",
    "QT_MAT_BAS_MASC",
    "QT_MAT_BAS_ND",
    "QT_MAT_BAS_BRANCA",
    "QT_MAT_BAS_PRETA",
    "QT_MAT_BAS_PARDA",
    "QT_MAT_BAS_AMARELA",
    "QT_MAT_BAS_INDIGENA",
    "QT_MAT_BAS_0_3",
    "QT_MAT_BAS_4_5",
    "QT_MAT_BAS_6_10",
    "QT_MAT_BAS_11_14",
    "QT_MAT_BAS_15_17",
    "QT_MAT_BAS_18_MAIS",
    "QT_MAT_BAS_DIURNO",
    "QT_MAT_BAS_NOTURNO",
    "QT_MAT_BAS_EAD",
    "QT_MAT_INF_INT",
    "QT_MAT_INF_CRE_INT",
    "QT_MAT_INF_PRE_INT",
    "QT_MAT_FUND_INT",
    "QT_MAT_FUND_AI_INT",
    "QT_MAT_FUND_AF_INT",
    "QT_MAT_MED_INT",
]

# Aliases para variacoes de nomenclatura do turno no historico.
ALIASES_ED_BASICA = {
    "QT_MAT_BAS_D": "QT_MAT_BAS_DIURNO",
    "QT_MAT_BAS_N": "QT_MAT_BAS_NOTURNO",
}


# Censo da Educacao Basica - Tabela de Escola
COLUNAS_ED_BASICA_ESCOLA = [
    "NU_ANO_CENSO",
    "SG_UF",
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "CO_ENTIDADE",
    "NO_ENTIDADE",
    "NO_DISTRITO",
    "NO_SUBDISTRITO",
    "TP_DEPENDENCIA",
    "TP_CATEGORIA_ESCOLA_PRIVADA",
    "TP_LOCALIZACAO",
    "TP_SITUACAO_FUNCIONAMENTO",
]


# Censo da Educacao Basica - Tabela de Matricula
COLUNAS_ED_BASICA_MATRICULA = [
    "NU_ANO_CENSO",
    "CO_ENTIDADE",
    "QT_MAT_BAS",
    "QT_MAT_INF",
    "QT_MAT_INF_CRE",
    "QT_MAT_INF_PRE",
    "QT_MAT_FUND",
    "QT_MAT_FUND_AI",
    "QT_MAT_FUND_AF",
    "QT_MAT_MED",
    "QT_MAT_PROF",
    "QT_MAT_PROF_TEC",
    "QT_MAT_EJA",
    "QT_MAT_EJA_FUND",
    "QT_MAT_EJA_MED",
    "QT_MAT_ESP",
    "QT_MAT_ESP_CC",
    "QT_MAT_ESP_CE",
    "QT_MAT_MED_1",
    "QT_MAT_MED_2",
    "QT_MAT_MED_3",
    "QT_MAT_MED_4",
    "QT_MAT_MED_NS",
]


# Nao tratar os campos abaixo como obrigatorios sem confirmar a versao do CSV.
# Selecionar os presentes; os ausentes entram como null no contrato historico.
COLUNAS_OPCIONAIS_ED_BASICA_MATRICULA = [
    "QT_MAT_FUND_AI_1",
    "QT_MAT_FUND_AI_2",
    "QT_MAT_FUND_AI_3",
    "QT_MAT_FUND_AI_4",
    "QT_MAT_FUND_AI_5",
    "QT_MAT_FUND_AF_6",
    "QT_MAT_FUND_AF_7",
    "QT_MAT_FUND_AF_8",
    "QT_MAT_FUND_AF_9",
    "QT_MAT_BAS_FEM",
    "QT_MAT_BAS_MASC",
    "QT_MAT_BAS_ND",
    "QT_MAT_BAS_BRANCA",
    "QT_MAT_BAS_PRETA",
    "QT_MAT_BAS_PARDA",
    "QT_MAT_BAS_AMARELA",
    "QT_MAT_BAS_INDIGENA",
    "QT_MAT_BAS_0_3",
    "QT_MAT_BAS_4_5",
    "QT_MAT_BAS_6_10",
    "QT_MAT_BAS_11_14",
    "QT_MAT_BAS_15_17",
    "QT_MAT_BAS_18_MAIS",
    "QT_MAT_BAS_DIURNO",
    "QT_MAT_BAS_NOTURNO",
    "QT_MAT_BAS_EAD",
    "QT_MAT_INF_INT",
    "QT_MAT_INF_CRE_INT",
    "QT_MAT_INF_PRE_INT",
    "QT_MAT_FUND_INT",
    "QT_MAT_FUND_AI_INT",
    "QT_MAT_FUND_AF_INT",
    "QT_MAT_MED_INT",
]

ALIASES_ED_BASICA_MATRICULA = {
    "QT_MAT_BAS_D": "QT_MAT_BAS_DIURNO",
    "QT_MAT_BAS_N": "QT_MAT_BAS_NOTURNO",
}

# Variaveis QT_MAT_* nao mapeadas acima devem ser preservadas
# em fato auxiliar (escola x ano x variavel_inep) e auditadas.
PREFIXOS_METRICAS_ALUNOS_ED_BASICA = ("QT_MAT_", "QT_TRANSP_")


# Conceito Enade
COLUNAS_CONCEITO_ENADE = [
    "Ano",
    "Código da Área",
    "Área de Avaliação",
    "Código da IES",
    "Nome da IES",
    "Sigla da IES",
    "Organização Acadêmica",
    "Categoria Administrativa",
    "Código do Curso",
    "Modalidade de Ensino",
    "Código do Município",
    "Município do Curso",
    "Sigla da UF",
    "Nº de Concluintes Inscritos",
    "Nº  de Concluintes Participantes",
    "Conceito Enade (Faixa)",
]

COLUNAS_OPCIONAIS_CONCEITO_ENADE = [
    "Grau Acadêmico",
    "Nota Bruta - FG",
    "Nota Padronizada - FG",
    "Nota Bruta - CE",
    "Nota Padronizada - CE",
    "Conceito Enade (Contínuo)",
    "Observação",
    "Entidade Beneficiente de Assistência Social (CEBAS)",
    "Total Concluinte Acima do Padrão",
    "Percentual Concluintes Acima do Padrão",
]

ALIASES_CONCEITO_ENADE = {
    "Nome da IES*": "Nome da IES",
    "Sigla da IES*": "Sigla da IES",
    "Categoria Administrativa**": "Categoria Administrativa",
    "Código do Município**": "Código do Município",
    "Município do Curso**": "Município do Curso",
    "Sigla da UF**": "Sigla da UF",
    "CEBAS": "Entidade Beneficiente de Assistência Social (CEBAS)",
    "Entidade Beneficente de Assistência Social (CEBAS)": "Entidade Beneficiente de Assistência Social (CEBAS)",
}

# CPC
COLUNAS_CPC = [
    "Ano",
    "Código da Área",
    "Área de Avaliação",
    "Código da IES",
    "Nome da IES",
    "Sigla da IES",
    "Organização Acadêmica",
    "Categoria Administrativa",
    "Código do Curso",
    "Modalidade de Ensino",
    "Código do Município",
    "Município do Curso",
    "Sigla da UF",
    "Nº de Concluintes Inscritos",
    "Nº de Concluintes Participantes",
    "Nota Bruta - FG",
    "Nota Padronizada - FG",
    "Nota Bruta - CE",
    "Nota Padronizada - CE",
    "Conceito Enade (Contínuo)",
    "Concluintes participantes com nota no Enem",
    "Proporção de concluintes participantes com nota no Enem",
    "Nota Bruta - IDD",
    "Nota Padronizada - IDD",
    "Nota Bruta - Organização Didático-Pedagógica",
    "Nota Padronizada - Organização Didático-Pedagógica",
    "Nota Bruta - Infraestrutura e Instalações Físicas",
    "Nota Padronizada - Infraestrutura e Instalações Físicas",
    "Nota Bruta - Oportunidade de Ampliação da Formação",
    "Nota Padronizada - Oportunidade de Ampliação da Formação",
    "Nota Bruta - Mestres",
    "Nota Padronizada - Mestres",
    "Nota Bruta - Doutores",
    "Nota Padronizada - Doutores",
    "Nota Bruta - Regime de Trabalho",
    "Nota Padronizada - Regime de Trabalho",
    "CPC (Contínuo)",
    "CPC (Faixa)",
]

COLUNAS_OPCIONAIS_CPC = [
    "Grau Acadêmico",
    "Observação",
    "Entidade Beneficiente de Assistência Social (CEBAS)",
]

ALIASES_CPC = {
    # Grau academico
    "Grau acadêmico": "Grau Acadêmico",
    # Identificacao
    "Código da IES*": "Código da IES",
    "Nome da IES*": "Nome da IES",
    "Sigla da IES*": "Sigla da IES",
    "Organização Acadêmica*": "Organização Acadêmica",
    "Categoria Administrativa*": "Categoria Administrativa",
    "Código do Curso**": "Código do Curso",
    "Modalidade de Ensino***": "Modalidade de Ensino",
    "Código do Município***": "Código do Município",
    "Município do Curso***": "Município do Curso",
    "Sigla da UF**": "Sigla da UF",
    # Variacoes de travessao
    "Nota Bruta – Organização Didático-Pedagógica": "Nota Bruta - Organização Didático-Pedagógica",
    "Nota Bruta – Infraestrutura e Instalações Físicas": "Nota Bruta - Infraestrutura e Instalações Físicas",
    "Nota Bruta – Oportunidade de Ampliação da Formação": "Nota Bruta - Oportunidade de Ampliação da Formação",
    "Nota Bruta – Regime de Trabalho": "Nota Bruta - Regime de Trabalho",
    # CEBAS
    "Entidade Beneficente de Assistência Social (CEBAS)": "Entidade Beneficiente de Assistência Social (CEBAS)",
}

# IDD
COLUNAS_IDD = [
    "Ano",
    "Código da Área",
    "Área de Avaliação",
    "Código da IES",
    "Nome da IES",
    "Sigla da IES",
    "Organização Acadêmica",
    "Categoria Administrativa",
    "Código do Curso",
    "Modalidade de Ensino",
    "Código do Município",
    "Município do Curso",
    "Sigla da UF",
    "Nº de Concluintes Inscritos",
    "Nº de Concluintes Participantes",
    "Nº de Concluintes Participantes com nota no Enem",
    "Proporção de Concluintes participantes com nota no Enem",
    "Nota Bruta - IDD",
    "IDD (Contínuo)",
    "IDD (Faixa)",
]

COLUNAS_OPCIONAIS_IDD = [
    "Grau Acadêmico",
    "Observação",
    "Entidade Beneficiente de Assistência Social (CEBAS)",
]

ALIASES_IDD = {
    "Nome da IES*": "Nome da IES",
    "Sigla da IES*": "Sigla da IES",
    "Código do Município**": "Código do Município",
    "Município do Curso**": "Município do Curso",
    "Sigla da UF**": "Sigla da UF",
    "Entidade Beneficente de Assistência Social (CEBAS)": "Entidade Beneficiente de Assistência Social (CEBAS)",
}

# IGC
COLUNAS_IGC = [
    "Ano",
    "Código da IES",
    "Nome da IES",
    "Sigla da IES",
    "Organização Acadêmica",
    "Categoria Administrativa",
    "Sigla da UF",
    "Nº de Cursos com CPC no triênio",
    "Alfa (Proporção de Graduação)",
    "Conceito Médio de Graduação",
    "Beta (Proporção de Mestrado - Equivalente)",
    "Conceito Médio de Mestrado",
    "Gama (Proporção de Doutorandos – Equivalente)",
    "Conceito Médio do doutorado",
    "IGC (Contínuo)",
    "IGC (Faixa)",
]

COLUNAS_OPCIONAIS_IGC = [
    "Observação",
    "Entidade Beneficiente de Assistência Social (CEBAS)",
]

ALIASES_IGC = {
    # Identificacao
    "Código da IES*": "Código da IES",
    "Nome da IES*": "Nome da IES",
    "Sigla da IES*": "Sigla da IES",
    "Organização Acadêmica*": "Organização Acadêmica",
    # Observacao
    "TX_OBS (Observação)": "Observação",
    "TX_OBS": "Observação",
    "(Observação)": "Observação",
    # CEBAS
    "Entidade Beneficente de Assistência Social (CEBAS)": "Entidade Beneficiente de Assistência Social (CEBAS)",
}

# Geolocalizacao
COLUNAS_GEO = [
    "codigo_ibge",
    "codigo_uf",
    "nome",
    "latitude",
    "longitude",
]


# ==============================================================================
# DICIONARIOS DE RENOMEACAO ISOLADOS POR CONTEXTO/ARQUIVO
# ==============================================================================
# A partir daqui os nomes passam para o contrato canonico do ETL em snake_case.
# Os RENOMEACAO_* convertem apenas os nomes brutos harmonizados
# para o contrato canonico em snake_case.
# Variacoes historicas de cabecalho ficam exclusivamente nos ALIASES_*.


# Censo da Educacao Superior - Cursos
RENOMEACAO_CURSOS_SUPERIOR = {
    # Identificacao
    "NU_ANO_CENSO": "ano_censo",
    "NO_REGIAO": "regiao",
    "CO_REGIAO": "codigo_regiao",
    "NO_UF": "nome_uf",
    "SG_UF": "uf",
    "CO_UF": "codigo_uf",
    "NO_MUNICIPIO": "municipio",
    "CO_MUNICIPIO": "codigo_municipio",
    "IN_CAPITAL": "indicador_capital",
    "TP_ORGANIZACAO_ACADEMICA": "codigo_organizacao_academica",
    "TP_CATEGORIA_ADMINISTRATIVA": "codigo_categoria_administrativa",
    "TP_REDE": "codigo_rede",
    "CO_IES": "codigo_ies",
    "NO_CURSO": "nome_curso",
    "CO_CURSO": "codigo_curso",
    "NO_CINE_ROTULO": "nome_cine",
    "CO_CINE_ROTULO": "codigo_cine",
    "TP_GRAU_ACADEMICO": "codigo_grau_academico",
    "IN_GRATUITO": "indicador_gratuito",
    "TP_MODALIDADE_ENSINO": "codigo_modalidade_ensino",
    "TP_NIVEL_ACADEMICO": "codigo_nivel_academico",
    # Vagas
    "QT_VG_TOTAL": "vagas_total",
    "QT_VG_TOTAL_DIURNO": "vagas_total_diurno",
    "QT_VG_TOTAL_NOTURNO": "vagas_total_noturno",
    "QT_VG_TOTAL_EAD": "vagas_total_ead",
    "QT_VG_NOVA": "vagas_novas",
    "QT_VG_PROC_SELETIVO": "vagas_processo_seletivo",
    "QT_VG_REMANESC": "vagas_remanescentes",
    "QT_VG_PROG_ESPECIAL": "vagas_programa_especial",
    # Inscritos
    "QT_INSCRITO_TOTAL": "inscritos_total",
    "QT_INSCRITO_TOTAL_DIURNO": "inscritos_total_diurno",
    "QT_INSCRITO_TOTAL_NOTURNO": "inscritos_total_noturno",
    "QT_INSCRITO_TOTAL_EAD": "inscritos_total_ead",
    "QT_INSC_VG_NOVA": "inscritos_vagas_novas",
    "QT_INSC_PROC_SELETIVO": "inscritos_processo_seletivo",
    "QT_INSC_VG_REMANESC": "inscritos_vagas_remanescentes",
    "QT_INSC_VG_PROG_ESPECIAL": "inscritos_programa_especial",
    # Ingressantes
    "QT_ING": "ingressantes",
    "QT_ING_DIURNO": "ingressantes_diurno",
    "QT_ING_NOTURNO": "ingressantes_noturno",
    "QT_ING_VG_NOVA": "ingressantes_vagas_novas",
    "QT_ING_VESTIBULAR": "ingressantes_vestibular",
    "QT_ING_ENEM": "ingressantes_enem",
    "QT_ING_AVALIACAO_SERIADA": "ingressantes_avaliacao_seriada",
    "QT_ING_SELECAO_SIMPLIFICA": "ingressantes_selecao_simplificada",
    "QT_ING_EGR": "ingressantes_egressos",
    "QT_ING_OUTRO_TIPO_SELECAO": "ingressantes_outro_tipo_selecao",
    "QT_ING_PROC_SELETIVO": "ingressantes_processo_seletivo",
    "QT_ING_VG_REMANESC": "ingressantes_vagas_remanescentes",
    "QT_ING_VG_PROG_ESPECIAL": "ingressantes_programa_especial",
    "QT_ING_OUTRA_FORMA": "ingressantes_outra_forma",
    # Matriculados
    "QT_MAT": "matriculados",
    "QT_MAT_DIURNO": "matriculados_diurno",
    "QT_MAT_NOTURNO": "matriculados_noturno",
    # Concluintes
    "QT_CONC": "concluintes",
    "QT_CONC_DIURNO": "concluintes_diurno",
    "QT_CONC_NOTURNO": "concluintes_noturno",
    # Financiamento
    "QT_ING_FIES": "ingressantes_fies",
    "QT_ING_PROUNII": "ingressantes_prouni_integral",
    "QT_ING_PROUNIP": "ingressantes_prouni_parcial",
    "QT_MAT_FIES": "matriculados_fies",
    "QT_MAT_PROUNII": "matriculados_prouni_integral",
    "QT_MAT_PROUNIP": "matriculados_prouni_parcial",
    "QT_CONC_FIES": "concluintes_fies",
    "QT_CONC_PROUNII": "concluintes_prouni_integral",
    "QT_CONC_PROUNIP": "concluintes_prouni_parcial",
    # Situacao academica
    "QT_SIT_TRANCADA": "trancados",
    "QT_SIT_DESVINCULADO": "desvinculados",
    "QT_SIT_TRANSFERIDO": "transferidos",
    "QT_SIT_FALECIDO": "falecidos",
    # Procedencia escolar
    "QT_ING_PROCESCPUBLICA": "ingressantes_escola_publica",
    "QT_ING_PROCESCPRIVADA": "ingressantes_escola_privada",
    "QT_ING_PROCNAOINFORMADA": "ingressantes_escola_nao_informada",
    "QT_MAT_PROCESCPUBLICA": "matriculados_escola_publica",
    "QT_MAT_PROCESCPRIVADA": "matriculados_escola_privada",
    "QT_MAT_PROCNAOINFORMADA": "matriculados_escola_nao_informada",
    "QT_CONC_PROCESCPUBLICA": "concluintes_escola_publica",
    "QT_CONC_PROCESCPRIVADA": "concluintes_escola_privada",
    "QT_CONC_PROCNAOINFORMADA": "concluintes_escola_nao_informada",
}


# Censo da Educacao Superior - IES
RENOMEACAO_IES = {
    "NU_ANO_CENSO": "ano_censo",
    "CO_IES": "codigo_ies",
    "NO_IES": "nome_ies",
    "SG_IES": "sigla_ies",
    "NO_MANTENEDORA": "mantenedora",
    "TP_ORGANIZACAO_ACADEMICA": "codigo_organizacao_academica",
    "TP_CATEGORIA_ADMINISTRATIVA": "codigo_categoria_administrativa",
    "NO_MUNICIPIO_IES": "municipio_ies",
    "SG_UF_IES": "uf_ies",
}


# Censo da Educacao Basica - arquivo historico de escolas
RENOMEACAO_ED_BASICA = {
    "NU_ANO_CENSO": "ano_censo",
    "SG_UF": "uf",
    "CO_MUNICIPIO": "codigo_municipio",
    "NO_MUNICIPIO": "municipio",
    "CO_ENTIDADE": "codigo_escola",
    "NO_ENTIDADE": "nome_escola",
    "DS_ENDERECO": "endereco",
    "NU_ENDERECO": "numero_endereco",
    "DS_COMPLEMENTO": "complemento",
    "NO_BAIRRO": "bairro",
    "CO_CEP": "cep",
    "TP_DEPENDENCIA": "codigo_dependencia",
    "TP_CATEGORIA_ESCOLA_PRIVADA": "codigo_categoria_escola_privada",
    "TP_LOCALIZACAO": "codigo_localizacao",
    "TP_SITUACAO_FUNCIONAMENTO": "codigo_situacao_funcionamento",
    "IN_MED": "indicador_ensino_medio",
    "QT_MAT_BAS": "matriculas_educacao_basica",
    "QT_MAT_INF": "matriculas_educacao_infantil",
    "QT_MAT_INF_CRE": "matriculas_creche",
    "QT_MAT_INF_PRE": "matriculas_pre_escola",
    "QT_MAT_FUND": "matriculas_ensino_fundamental",
    "QT_MAT_FUND_AI": "matriculas_fundamental_anos_iniciais",
    "QT_MAT_FUND_AF": "matriculas_fundamental_anos_finais",
    "QT_MAT_MED": "matriculas_ensino_medio",
    "QT_MAT_PROF": "matriculas_educacao_profissional",
    "QT_MAT_PROF_TEC": "matriculas_educacao_profissional_tecnica",
    "QT_MAT_EJA": "matriculas_eja",
    "QT_MAT_EJA_FUND": "matriculas_eja_fundamental",
    "QT_MAT_EJA_MED": "matriculas_eja_ensino_medio",
    "QT_MAT_ESP": "matriculas_educacao_especial",
    "QT_MAT_ESP_CC": "matriculas_educacao_especial_classe_comum",
    "QT_MAT_ESP_CE": "matriculas_educacao_especial_classe_exclusiva",
    "QT_MAT_FUND_AI_1": "matriculas_fundamental_ano_1",
    "QT_MAT_FUND_AI_2": "matriculas_fundamental_ano_2",
    "QT_MAT_FUND_AI_3": "matriculas_fundamental_ano_3",
    "QT_MAT_FUND_AI_4": "matriculas_fundamental_ano_4",
    "QT_MAT_FUND_AI_5": "matriculas_fundamental_ano_5",
    "QT_MAT_FUND_AF_6": "matriculas_fundamental_ano_6",
    "QT_MAT_FUND_AF_7": "matriculas_fundamental_ano_7",
    "QT_MAT_FUND_AF_8": "matriculas_fundamental_ano_8",
    "QT_MAT_FUND_AF_9": "matriculas_fundamental_ano_9",
    "QT_MAT_MED_1": "matriculas_ensino_medio_1",
    "QT_MAT_MED_2": "matriculas_ensino_medio_2",
    "QT_MAT_MED_3": "matriculas_ensino_medio_3",
    "QT_MAT_MED_4": "matriculas_ensino_medio_4",
    "QT_MAT_MED_NS": "matriculas_ensino_medio_nao_seriado",
    "QT_MAT_BAS_FEM": "matriculas_educacao_basica_feminino",
    "QT_MAT_BAS_MASC": "matriculas_educacao_basica_masculino",
    "QT_MAT_BAS_ND": "matriculas_educacao_basica_cor_nao_declarada",
    "QT_MAT_BAS_BRANCA": "matriculas_educacao_basica_cor_branca",
    "QT_MAT_BAS_PRETA": "matriculas_educacao_basica_cor_preta",
    "QT_MAT_BAS_PARDA": "matriculas_educacao_basica_cor_parda",
    "QT_MAT_BAS_AMARELA": "matriculas_educacao_basica_cor_amarela",
    "QT_MAT_BAS_INDIGENA": "matriculas_educacao_basica_cor_indigena",
    "QT_MAT_BAS_0_3": "matriculas_educacao_basica_idade_0_3",
    "QT_MAT_BAS_4_5": "matriculas_educacao_basica_idade_4_5",
    "QT_MAT_BAS_6_10": "matriculas_educacao_basica_idade_6_10",
    "QT_MAT_BAS_11_14": "matriculas_educacao_basica_idade_11_14",
    "QT_MAT_BAS_15_17": "matriculas_educacao_basica_idade_15_17",
    "QT_MAT_BAS_18_MAIS": "matriculas_educacao_basica_idade_18_mais",
    "QT_MAT_BAS_DIURNO": "matriculas_educacao_basica_diurno",
    "QT_MAT_BAS_NOTURNO": "matriculas_educacao_basica_noturno",
    "QT_MAT_BAS_EAD": "matriculas_educacao_basica_ead",
    "QT_MAT_INF_INT": "matriculas_educacao_infantil_tempo_integral",
    "QT_MAT_INF_CRE_INT": "matriculas_creche_tempo_integral",
    "QT_MAT_INF_PRE_INT": "matriculas_pre_escola_tempo_integral",
    "QT_MAT_FUND_INT": "matriculas_ensino_fundamental_tempo_integral",
    "QT_MAT_FUND_AI_INT": "matriculas_fundamental_anos_iniciais_tempo_integral",
    "QT_MAT_FUND_AF_INT": "matriculas_fundamental_anos_finais_tempo_integral",
    "QT_MAT_MED_INT": "matriculas_ensino_medio_tempo_integral",
}


# Censo da Educacao Basica - Tabela de Escola
RENOMEACAO_ED_BASICA_ESCOLA = {
    "NU_ANO_CENSO": "ano_censo",
    "SG_UF": "uf",
    "CO_MUNICIPIO": "codigo_municipio",
    "NO_MUNICIPIO": "municipio",
    "CO_ENTIDADE": "codigo_escola",
    "NO_ENTIDADE": "nome_escola",
    "NO_DISTRITO": "distrito",
    "NO_SUBDISTRITO": "subdistrito",
    "TP_DEPENDENCIA": "codigo_dependencia",
    "TP_CATEGORIA_ESCOLA_PRIVADA": "codigo_categoria_escola_privada",
    "TP_LOCALIZACAO": "codigo_localizacao",
    "TP_SITUACAO_FUNCIONAMENTO": "codigo_situacao_funcionamento",
}


# Censo da Educacao Basica - Tabela de Matricula
RENOMEACAO_ED_BASICA_MATRICULA = {
    "NU_ANO_CENSO": "ano_censo",
    "CO_ENTIDADE": "codigo_escola",
    "QT_MAT_BAS": "matriculas_educacao_basica",
    "QT_MAT_INF": "matriculas_educacao_infantil",
    "QT_MAT_INF_CRE": "matriculas_creche",
    "QT_MAT_INF_PRE": "matriculas_pre_escola",
    "QT_MAT_FUND": "matriculas_ensino_fundamental",
    "QT_MAT_FUND_AI": "matriculas_fundamental_anos_iniciais",
    "QT_MAT_FUND_AF": "matriculas_fundamental_anos_finais",
    "QT_MAT_MED": "matriculas_ensino_medio",
    "QT_MAT_PROF": "matriculas_educacao_profissional",
    "QT_MAT_PROF_TEC": "matriculas_educacao_profissional_tecnica",
    "QT_MAT_EJA": "matriculas_eja",
    "QT_MAT_EJA_FUND": "matriculas_eja_fundamental",
    "QT_MAT_EJA_MED": "matriculas_eja_ensino_medio",
    "QT_MAT_ESP": "matriculas_educacao_especial",
    "QT_MAT_ESP_CC": "matriculas_educacao_especial_classe_comum",
    "QT_MAT_ESP_CE": "matriculas_educacao_especial_classe_exclusiva",
    "QT_MAT_FUND_AI_1": "matriculas_fundamental_ano_1",
    "QT_MAT_FUND_AI_2": "matriculas_fundamental_ano_2",
    "QT_MAT_FUND_AI_3": "matriculas_fundamental_ano_3",
    "QT_MAT_FUND_AI_4": "matriculas_fundamental_ano_4",
    "QT_MAT_FUND_AI_5": "matriculas_fundamental_ano_5",
    "QT_MAT_FUND_AF_6": "matriculas_fundamental_ano_6",
    "QT_MAT_FUND_AF_7": "matriculas_fundamental_ano_7",
    "QT_MAT_FUND_AF_8": "matriculas_fundamental_ano_8",
    "QT_MAT_FUND_AF_9": "matriculas_fundamental_ano_9",
    "QT_MAT_MED_1": "matriculas_ensino_medio_1",
    "QT_MAT_MED_2": "matriculas_ensino_medio_2",
    "QT_MAT_MED_3": "matriculas_ensino_medio_3",
    "QT_MAT_MED_4": "matriculas_ensino_medio_4",
    "QT_MAT_MED_NS": "matriculas_ensino_medio_nao_seriado",
    "QT_MAT_BAS_FEM": "matriculas_educacao_basica_feminino",
    "QT_MAT_BAS_MASC": "matriculas_educacao_basica_masculino",
    "QT_MAT_BAS_ND": "matriculas_educacao_basica_cor_nao_declarada",
    "QT_MAT_BAS_BRANCA": "matriculas_educacao_basica_cor_branca",
    "QT_MAT_BAS_PRETA": "matriculas_educacao_basica_cor_preta",
    "QT_MAT_BAS_PARDA": "matriculas_educacao_basica_cor_parda",
    "QT_MAT_BAS_AMARELA": "matriculas_educacao_basica_cor_amarela",
    "QT_MAT_BAS_INDIGENA": "matriculas_educacao_basica_cor_indigena",
    "QT_MAT_BAS_0_3": "matriculas_educacao_basica_idade_0_3",
    "QT_MAT_BAS_4_5": "matriculas_educacao_basica_idade_4_5",
    "QT_MAT_BAS_6_10": "matriculas_educacao_basica_idade_6_10",
    "QT_MAT_BAS_11_14": "matriculas_educacao_basica_idade_11_14",
    "QT_MAT_BAS_15_17": "matriculas_educacao_basica_idade_15_17",
    "QT_MAT_BAS_18_MAIS": "matriculas_educacao_basica_idade_18_mais",
    "QT_MAT_BAS_DIURNO": "matriculas_educacao_basica_diurno",
    "QT_MAT_BAS_NOTURNO": "matriculas_educacao_basica_noturno",
    "QT_MAT_BAS_EAD": "matriculas_educacao_basica_ead",
    "QT_MAT_INF_INT": "matriculas_educacao_infantil_tempo_integral",
    "QT_MAT_INF_CRE_INT": "matriculas_creche_tempo_integral",
    "QT_MAT_INF_PRE_INT": "matriculas_pre_escola_tempo_integral",
    "QT_MAT_FUND_INT": "matriculas_ensino_fundamental_tempo_integral",
    "QT_MAT_FUND_AI_INT": "matriculas_fundamental_anos_iniciais_tempo_integral",
    "QT_MAT_FUND_AF_INT": "matriculas_fundamental_anos_finais_tempo_integral",
    "QT_MAT_MED_INT": "matriculas_ensino_medio_tempo_integral",
}


# Conceito Enade
RENOMEACAO_CONCEITO_ENADE = {
    "Ano": "ano_enade",
    "Código da Área": "codigo_area",
    "Área de Avaliação": "area_avaliacao",
    "Grau Acadêmico": "grau_academico",
    "Código da IES": "codigo_ies",
    "Nome da IES": "nome_ies",
    "Sigla da IES": "sigla_ies",
    "Organização Acadêmica": "organizacao_academica",
    "Categoria Administrativa": "categoria_administrativa",
    "Código do Curso": "codigo_curso",
    "Modalidade de Ensino": "modalidade_ensino",
    "Código do Município": "codigo_municipio",
    "Município do Curso": "municipio_curso",
    "Sigla da UF": "uf",
    "Nº de Concluintes Inscritos": "enade_concluintes_inscritos_qtd",
    "Nº  de Concluintes Participantes": "enade_concluintes_participantes_qtd",
    "Nota Bruta - FG": "enade_nota_bruta_fg",
    "Nota Padronizada - FG": "enade_nota_padronizada_fg",
    "Nota Bruta - CE": "enade_nota_bruta_ce",
    "Nota Padronizada - CE": "enade_nota_padronizada_ce",
    "Conceito Enade (Contínuo)": "enade_conceito_continuo",
    "Conceito Enade (Faixa)": "enade_conceito_faixa",
    "Total Concluinte Acima do Padrão": "enade_concluintes_acima_padrao_qtd",
    "Percentual Concluintes Acima do Padrão": "enade_percentual_acima_padrao",
    "Observação": "observacao",
    "Entidade Beneficiente de Assistência Social (CEBAS)": "cebas",
}


# CPC
RENOMEACAO_CPC = {
    "Ano": "ano_cpc",
    "Código da Área": "codigo_area",
    "Área de Avaliação": "area_avaliacao",
    "Grau Acadêmico": "grau_academico",
    "Código da IES": "codigo_ies",
    "Nome da IES": "nome_ies",
    "Sigla da IES": "sigla_ies",
    "Organização Acadêmica": "organizacao_academica",
    "Categoria Administrativa": "categoria_administrativa",
    "Código do Curso": "codigo_curso",
    "Modalidade de Ensino": "modalidade_ensino",
    "Código do Município": "codigo_municipio",
    "Município do Curso": "municipio_curso",
    "Sigla da UF": "uf",
    "Nº de Concluintes Inscritos": "cpc_concluintes_inscritos_qtd",
    "Nº de Concluintes Participantes": "cpc_concluintes_participantes_qtd",
    "Nota Bruta - FG": "cpc_nota_bruta_fg",
    "Nota Padronizada - FG": "cpc_nota_padronizada_fg",
    "Nota Bruta - CE": "cpc_nota_bruta_ce",
    "Nota Padronizada - CE": "cpc_nota_padronizada_ce",
    "Conceito Enade (Contínuo)": "cpc_conceito_enade_continuo",
    "Concluintes participantes com nota no Enem": "cpc_concluintes_com_enem_qtd",
    "Proporção de concluintes participantes com nota no Enem": "cpc_proporcao_concluintes_com_enem",
    "Nota Bruta - IDD": "cpc_nota_bruta_idd",
    "Nota Padronizada - IDD": "cpc_nota_padronizada_idd",
    "Nota Bruta - Organização Didático-Pedagógica": "cpc_nota_bruta_organizacao_didatico_pedagogica",
    "Nota Padronizada - Organização Didático-Pedagógica": "cpc_nota_padronizada_organizacao_didatico_pedagogica",
    "Nota Bruta - Infraestrutura e Instalações Físicas": "cpc_nota_bruta_infraestrutura",
    "Nota Padronizada - Infraestrutura e Instalações Físicas": "cpc_nota_padronizada_infraestrutura",
    "Nota Bruta - Oportunidade de Ampliação da Formação": "cpc_nota_bruta_oportunidade_formacao",
    "Nota Padronizada - Oportunidade de Ampliação da Formação": "cpc_nota_padronizada_oportunidade_formacao",
    "Nota Bruta - Mestres": "cpc_nota_bruta_mestres",
    "Nota Padronizada - Mestres": "cpc_nota_padronizada_mestres",
    "Nota Bruta - Doutores": "cpc_nota_bruta_doutores",
    "Nota Padronizada - Doutores": "cpc_nota_padronizada_doutores",
    "Nota Bruta - Regime de Trabalho": "cpc_nota_bruta_regime_trabalho",
    "Nota Padronizada - Regime de Trabalho": "cpc_nota_padronizada_regime_trabalho",
    "CPC (Contínuo)": "cpc_continuo",
    "CPC (Faixa)": "cpc_faixa",
    "Observação": "observacao",
    "Entidade Beneficiente de Assistência Social (CEBAS)": "cebas",
}


# IDD
RENOMEACAO_IDD = {
    "Ano": "ano_idd",
    "Código da Área": "codigo_area",
    "Área de Avaliação": "area_avaliacao",
    "Grau Acadêmico": "grau_academico",
    "Código da IES": "codigo_ies",
    "Nome da IES": "nome_ies",
    "Sigla da IES": "sigla_ies",
    "Organização Acadêmica": "organizacao_academica",
    "Categoria Administrativa": "categoria_administrativa",
    "Código do Curso": "codigo_curso",
    "Modalidade de Ensino": "modalidade_ensino",
    "Código do Município": "codigo_municipio",
    "Município do Curso": "municipio_curso",
    "Sigla da UF": "uf",
    "Nº de Concluintes Inscritos": "idd_concluintes_inscritos_qtd",
    "Nº de Concluintes Participantes": "idd_concluintes_participantes_qtd",
    "Nº de Concluintes Participantes com nota no Enem": "idd_concluintes_com_enem_qtd",
    "Proporção de Concluintes participantes com nota no Enem": "idd_proporcao_concluintes_com_enem",
    "Nota Bruta - IDD": "idd_nota_bruta",
    "IDD (Contínuo)": "idd_continuo",
    "IDD (Faixa)": "idd_faixa",
    "Observação": "observacao",
    "Entidade Beneficiente de Assistência Social (CEBAS)": "cebas",
}


# IGC
RENOMEACAO_IGC = {
    "Ano": "ano_igc",
    "Código da IES": "codigo_ies",
    "Nome da IES": "nome_ies",
    "Sigla da IES": "sigla_ies",
    "Organização Acadêmica": "organizacao_academica",
    "Categoria Administrativa": "categoria_administrativa",
    "Sigla da UF": "uf",
    "Nº de Cursos com CPC no triênio": "igc_cursos_cpc_trienio_qtd",
    "Alfa (Proporção de Graduação)": "igc_alfa_graduacao",
    "Conceito Médio de Graduação": "igc_conceito_medio_graduacao",
    "Beta (Proporção de Mestrado - Equivalente)": "igc_beta_mestrado",
    "Conceito Médio de Mestrado": "igc_conceito_medio_mestrado",
    "Gama (Proporção de Doutorandos – Equivalente)": "igc_gama_doutorado",
    "Conceito Médio do doutorado": "igc_conceito_medio_doutorado",
    "IGC (Contínuo)": "igc_continuo",
    "IGC (Faixa)": "igc_faixa",
    "Observação": "observacao",
    "Entidade Beneficiente de Assistência Social (CEBAS)": "cebas",
}


# Geolocalizacao
RENOMEACAO_GEO = {
    "codigo_ibge": "codigo_municipio",
    "codigo_uf": "codigo_uf",
    "nome": "municipio",
    "latitude": "latitude",
    "longitude": "longitude",
}


# ==============================================================================
# CONTRATOS DE INTEGRIDADE E TIPAGEM DA CAMADA BRONZE
#    SAIDA BRONZE / ENTRADA SILVER
# ==============================================================================
# Na Bronze, os campos oriundos das fontes permanecem prioritariamente como
# String. A tipagem de negocio ocorre na Silver.

SCHEMA_METADATA_BRONZE = {
    "arquivo_origem": pl.String,
    "ano_arquivo": pl.Int64,
}


# Censo Superior
SCHEMA_CURSOS_SUPERIOR_BRONZE = {
    # Identificacao
    "ano_censo": pl.String,
    "regiao": pl.String,
    "codigo_regiao": pl.String,
    "nome_uf": pl.String,
    "uf": pl.String,
    "codigo_uf": pl.String,
    "municipio": pl.String,
    "codigo_municipio": pl.String,
    "indicador_capital": pl.String,
    "codigo_organizacao_academica": pl.String,
    "codigo_categoria_administrativa": pl.String,
    "codigo_rede": pl.String,
    "codigo_ies": pl.String,
    "nome_curso": pl.String,
    "codigo_curso": pl.String,
    "nome_cine": pl.String,
    "codigo_cine": pl.String,
    "codigo_grau_academico": pl.String,
    "indicador_gratuito": pl.String,
    "codigo_modalidade_ensino": pl.String,
    "codigo_nivel_academico": pl.String,
    # Vagas
    "vagas_total": pl.String,
    "vagas_total_diurno": pl.String,
    "vagas_total_noturno": pl.String,
    "vagas_total_ead": pl.String,
    "vagas_novas": pl.String,
    "vagas_processo_seletivo": pl.String,
    "vagas_remanescentes": pl.String,
    "vagas_programa_especial": pl.String,
    # Inscritos
    "inscritos_total": pl.String,
    "inscritos_total_diurno": pl.String,
    "inscritos_total_noturno": pl.String,
    "inscritos_total_ead": pl.String,
    "inscritos_vagas_novas": pl.String,
    "inscritos_processo_seletivo": pl.String,
    "inscritos_vagas_remanescentes": pl.String,
    "inscritos_programa_especial": pl.String,
    # Ingressantes
    "ingressantes": pl.String,
    "ingressantes_diurno": pl.String,
    "ingressantes_noturno": pl.String,
    "ingressantes_vagas_novas": pl.String,
    "ingressantes_vestibular": pl.String,
    "ingressantes_enem": pl.String,
    "ingressantes_avaliacao_seriada": pl.String,
    "ingressantes_selecao_simplificada": pl.String,
    "ingressantes_egressos": pl.String,
    "ingressantes_outro_tipo_selecao": pl.String,
    "ingressantes_processo_seletivo": pl.String,
    "ingressantes_vagas_remanescentes": pl.String,
    "ingressantes_programa_especial": pl.String,
    "ingressantes_outra_forma": pl.String,
    # Matriculados
    "matriculados": pl.String,
    "matriculados_diurno": pl.String,
    "matriculados_noturno": pl.String,
    # Concluintes
    "concluintes": pl.String,
    "concluintes_diurno": pl.String,
    "concluintes_noturno": pl.String,
    # Financiamento
    "ingressantes_fies": pl.String,
    "ingressantes_prouni_integral": pl.String,
    "ingressantes_prouni_parcial": pl.String,
    "matriculados_fies": pl.String,
    "matriculados_prouni_integral": pl.String,
    "matriculados_prouni_parcial": pl.String,
    "concluintes_fies": pl.String,
    "concluintes_prouni_integral": pl.String,
    "concluintes_prouni_parcial": pl.String,
    # Situacao academica
    "trancados": pl.String,
    "desvinculados": pl.String,
    "transferidos": pl.String,
    "falecidos": pl.String,
    # Procedencia escolar
    "ingressantes_escola_publica": pl.String,
    "ingressantes_escola_privada": pl.String,
    "ingressantes_escola_nao_informada": pl.String,
    "matriculados_escola_publica": pl.String,
    "matriculados_escola_privada": pl.String,
    "matriculados_escola_nao_informada": pl.String,
    "concluintes_escola_publica": pl.String,
    "concluintes_escola_privada": pl.String,
    "concluintes_escola_nao_informada": pl.String,
    **SCHEMA_METADATA_BRONZE,
}

SCHEMA_IES_BRONZE = {
    "ano_censo": pl.String,
    "codigo_ies": pl.String,
    "nome_ies": pl.String,
    "sigla_ies": pl.String,
    "mantenedora": pl.String,
    "codigo_organizacao_academica": pl.String,
    "codigo_categoria_administrativa": pl.String,
    "municipio_ies": pl.String,
    "uf_ies": pl.String,
    **SCHEMA_METADATA_BRONZE,
}

# Contrato final da Bronze unificada 2018-2025.
# Campos seriados existem diretamente a partir de 2025; nos anos anteriores
# sao completados com null para manter um unico contrato historico.
SCHEMA_ED_BASICA_BRONZE = {
    "ano_censo": pl.String,
    "uf": pl.String,
    "codigo_municipio": pl.String,
    "municipio": pl.String,
    "codigo_escola": pl.String,
    "nome_escola": pl.String,
    "distrito": pl.String,
    "subdistrito": pl.String,
    "endereco": pl.String,
    "numero_endereco": pl.String,
    "complemento": pl.String,
    "bairro": pl.String,
    "cep": pl.String,
    "codigo_dependencia": pl.String,
    "codigo_categoria_escola_privada": pl.String,
    "codigo_localizacao": pl.String,
    "codigo_situacao_funcionamento": pl.String,
    "indicador_ensino_medio": pl.String,
    # Indicadores de matriculas de educacao basica (INEP).
    # Matriculas gerais
    "matriculas_educacao_basica": pl.String,
    "matriculas_educacao_infantil": pl.String,
    "matriculas_creche": pl.String,
    "matriculas_pre_escola": pl.String,
    "matriculas_ensino_fundamental": pl.String,
    "matriculas_fundamental_anos_iniciais": pl.String,
    "matriculas_fundamental_anos_finais": pl.String,
    "matriculas_ensino_medio": pl.String,
    "matriculas_educacao_profissional": pl.String,
    "matriculas_educacao_profissional_tecnica": pl.String,
    "matriculas_eja": pl.String,
    "matriculas_eja_fundamental": pl.String,
    "matriculas_eja_ensino_medio": pl.String,
    "matriculas_educacao_especial": pl.String,
    "matriculas_educacao_especial_classe_comum": pl.String,
    "matriculas_educacao_especial_classe_exclusiva": pl.String,
    # Series do ensino fundamental
    "matriculas_fundamental_ano_1": pl.String,
    "matriculas_fundamental_ano_2": pl.String,
    "matriculas_fundamental_ano_3": pl.String,
    "matriculas_fundamental_ano_4": pl.String,
    "matriculas_fundamental_ano_5": pl.String,
    "matriculas_fundamental_ano_6": pl.String,
    "matriculas_fundamental_ano_7": pl.String,
    "matriculas_fundamental_ano_8": pl.String,
    "matriculas_fundamental_ano_9": pl.String,
    # Series do ensino medio
    "matriculas_ensino_medio_1": pl.String,
    "matriculas_ensino_medio_2": pl.String,
    "matriculas_ensino_medio_3": pl.String,
    "matriculas_ensino_medio_4": pl.String,
    "matriculas_ensino_medio_nao_seriado": pl.String,
    # Sexo - educacao basica
    "matriculas_educacao_basica_feminino": pl.String,
    "matriculas_educacao_basica_masculino": pl.String,
    # Cor/raca - educacao basica
    "matriculas_educacao_basica_cor_nao_declarada": pl.String,
    "matriculas_educacao_basica_cor_branca": pl.String,
    "matriculas_educacao_basica_cor_preta": pl.String,
    "matriculas_educacao_basica_cor_parda": pl.String,
    "matriculas_educacao_basica_cor_amarela": pl.String,
    "matriculas_educacao_basica_cor_indigena": pl.String,
    # Faixa etaria - educacao basica
    "matriculas_educacao_basica_idade_0_3": pl.String,
    "matriculas_educacao_basica_idade_4_5": pl.String,
    "matriculas_educacao_basica_idade_6_10": pl.String,
    "matriculas_educacao_basica_idade_11_14": pl.String,
    "matriculas_educacao_basica_idade_15_17": pl.String,
    "matriculas_educacao_basica_idade_18_mais": pl.String,
    # Turno e modalidade
    "matriculas_educacao_basica_diurno": pl.String,
    "matriculas_educacao_basica_noturno": pl.String,
    "matriculas_educacao_basica_ead": pl.String,
    # Tempo integral
    "matriculas_educacao_infantil_tempo_integral": pl.String,
    "matriculas_creche_tempo_integral": pl.String,
    "matriculas_pre_escola_tempo_integral": pl.String,
    "matriculas_ensino_fundamental_tempo_integral": pl.String,
    "matriculas_fundamental_anos_iniciais_tempo_integral": pl.String,
    "matriculas_fundamental_anos_finais_tempo_integral": pl.String,
    "matriculas_ensino_medio_tempo_integral": pl.String,
    **SCHEMA_METADATA_BRONZE,
}


# Conceito Enade
SCHEMA_CONCEITO_ENADE_BRONZE = {
    "ano_enade": pl.String,
    "codigo_area": pl.String,
    "area_avaliacao": pl.String,
    "grau_academico": pl.String,
    "codigo_ies": pl.String,
    "nome_ies": pl.String,
    "sigla_ies": pl.String,
    "organizacao_academica": pl.String,
    "categoria_administrativa": pl.String,
    "codigo_curso": pl.String,
    "modalidade_ensino": pl.String,
    "codigo_municipio": pl.String,
    "municipio_curso": pl.String,
    "uf": pl.String,
    "enade_concluintes_inscritos_qtd": pl.String,
    "enade_concluintes_participantes_qtd": pl.String,
    "enade_nota_bruta_fg": pl.String,
    "enade_nota_padronizada_fg": pl.String,
    "enade_nota_bruta_ce": pl.String,
    "enade_nota_padronizada_ce": pl.String,
    "enade_conceito_continuo": pl.String,
    "enade_conceito_faixa": pl.String,
    "enade_concluintes_acima_padrao_qtd": pl.String,
    "enade_percentual_acima_padrao": pl.String,
    "observacao": pl.String,
    "cebas": pl.String,
    **SCHEMA_METADATA_BRONZE,
}

# CPC
SCHEMA_CPC_BRONZE = {
    "ano_cpc": pl.String,
    "codigo_area": pl.String,
    "area_avaliacao": pl.String,
    "grau_academico": pl.String,
    "codigo_ies": pl.String,
    "nome_ies": pl.String,
    "sigla_ies": pl.String,
    "organizacao_academica": pl.String,
    "categoria_administrativa": pl.String,
    "codigo_curso": pl.String,
    "modalidade_ensino": pl.String,
    "codigo_municipio": pl.String,
    "municipio_curso": pl.String,
    "uf": pl.String,
    "cpc_concluintes_inscritos_qtd": pl.String,
    "cpc_concluintes_participantes_qtd": pl.String,
    "cpc_nota_bruta_fg": pl.String,
    "cpc_nota_padronizada_fg": pl.String,
    "cpc_nota_bruta_ce": pl.String,
    "cpc_nota_padronizada_ce": pl.String,
    "cpc_conceito_enade_continuo": pl.String,
    "cpc_concluintes_com_enem_qtd": pl.String,
    "cpc_proporcao_concluintes_com_enem": pl.String,
    "cpc_nota_bruta_idd": pl.String,
    "cpc_nota_padronizada_idd": pl.String,
    "cpc_nota_bruta_organizacao_didatico_pedagogica": pl.String,
    "cpc_nota_padronizada_organizacao_didatico_pedagogica": pl.String,
    "cpc_nota_bruta_infraestrutura": pl.String,
    "cpc_nota_padronizada_infraestrutura": pl.String,
    "cpc_nota_bruta_oportunidade_formacao": pl.String,
    "cpc_nota_padronizada_oportunidade_formacao": pl.String,
    "cpc_nota_bruta_mestres": pl.String,
    "cpc_nota_padronizada_mestres": pl.String,
    "cpc_nota_bruta_doutores": pl.String,
    "cpc_nota_padronizada_doutores": pl.String,
    "cpc_nota_bruta_regime_trabalho": pl.String,
    "cpc_nota_padronizada_regime_trabalho": pl.String,
    "cpc_continuo": pl.String,
    "cpc_faixa": pl.String,
    "observacao": pl.String,
    "cebas": pl.String,
    **SCHEMA_METADATA_BRONZE,
}


# IDD
SCHEMA_IDD_BRONZE = {
    "ano_idd": pl.String,
    "codigo_area": pl.String,
    "area_avaliacao": pl.String,
    "grau_academico": pl.String,
    "codigo_ies": pl.String,
    "nome_ies": pl.String,
    "sigla_ies": pl.String,
    "organizacao_academica": pl.String,
    "categoria_administrativa": pl.String,
    "codigo_curso": pl.String,
    "modalidade_ensino": pl.String,
    "codigo_municipio": pl.String,
    "municipio_curso": pl.String,
    "uf": pl.String,
    "idd_concluintes_inscritos_qtd": pl.String,
    "idd_concluintes_participantes_qtd": pl.String,
    "idd_concluintes_com_enem_qtd": pl.String,
    "idd_proporcao_concluintes_com_enem": pl.String,
    "idd_nota_bruta": pl.String,
    "idd_continuo": pl.String,
    "idd_faixa": pl.String,
    "observacao": pl.String,
    "cebas": pl.String,
    **SCHEMA_METADATA_BRONZE,
}


# IGC
SCHEMA_IGC_BRONZE = {
    "ano_igc": pl.String,
    "codigo_ies": pl.String,
    "nome_ies": pl.String,
    "sigla_ies": pl.String,
    "organizacao_academica": pl.String,
    "categoria_administrativa": pl.String,
    "uf": pl.String,
    "igc_cursos_cpc_trienio_qtd": pl.String,
    "igc_alfa_graduacao": pl.String,
    "igc_conceito_medio_graduacao": pl.String,
    "igc_beta_mestrado": pl.String,
    "igc_conceito_medio_mestrado": pl.String,
    "igc_gama_doutorado": pl.String,
    "igc_conceito_medio_doutorado": pl.String,
    "igc_continuo": pl.String,
    "igc_faixa": pl.String,
    "observacao": pl.String,
    "cebas": pl.String,
    **SCHEMA_METADATA_BRONZE,
}


# Geo
SCHEMA_GEO_BRONZE = {
    "codigo_municipio": pl.String,
    "codigo_uf": pl.String,
    "municipio": pl.String,
    "latitude": pl.String,
    "longitude": pl.String,
    **SCHEMA_METADATA_BRONZE,
}


# ==============================================================================
# CONTRATOS DE INTEGRIDADE E TIPAGEM DA CAMADA SILVER
#    SAIDA SILVER / ENTRADA GOLD
# ==============================================================================


# Censo Superior
SCHEMA_CURSOS_SUPERIOR_SILVER = {
    # Identificacao
    "ano_censo": pl.Int32,
    "regiao": pl.String,
    "codigo_regiao": pl.Int32,
    "nome_uf": pl.String,
    "uf": pl.String,
    "codigo_uf": pl.Int32,
    "municipio": pl.String,
    "codigo_municipio": pl.Int64,
    "indicador_capital": pl.Int32,
    "codigo_organizacao_academica": pl.Int32,
    "codigo_categoria_administrativa": pl.Int32,
    "codigo_rede": pl.Int32,
    "codigo_ies": pl.Int64,
    "nome_curso": pl.String,
    "codigo_curso": pl.Int64,
    "nome_cine": pl.String,
    "codigo_cine": pl.String,
    "codigo_grau_academico": pl.Int32,
    "indicador_gratuito": pl.Int32,
    "codigo_modalidade_ensino": pl.Int32,
    "codigo_nivel_academico": pl.Int32,
    # Vagas
    "vagas_total": pl.Int32,
    "vagas_total_diurno": pl.Int32,
    "vagas_total_noturno": pl.Int32,
    "vagas_total_ead": pl.Int32,
    "vagas_novas": pl.Int32,
    "vagas_processo_seletivo": pl.Int32,
    "vagas_remanescentes": pl.Int32,
    "vagas_programa_especial": pl.Int32,
    # Inscritos
    "inscritos_total": pl.Int32,
    "inscritos_total_diurno": pl.Int32,
    "inscritos_total_noturno": pl.Int32,
    "inscritos_total_ead": pl.Int32,
    "inscritos_vagas_novas": pl.Int32,
    "inscritos_processo_seletivo": pl.Int32,
    "inscritos_vagas_remanescentes": pl.Int32,
    "inscritos_programa_especial": pl.Int32,
    # Ingressantes
    "ingressantes": pl.Int32,
    "ingressantes_diurno": pl.Int32,
    "ingressantes_noturno": pl.Int32,
    "ingressantes_vagas_novas": pl.Int32,
    "ingressantes_vestibular": pl.Int32,
    "ingressantes_enem": pl.Int32,
    "ingressantes_avaliacao_seriada": pl.Int32,
    "ingressantes_selecao_simplificada": pl.Int32,
    "ingressantes_egressos": pl.Int32,
    "ingressantes_outro_tipo_selecao": pl.Int32,
    "ingressantes_processo_seletivo": pl.Int32,
    "ingressantes_vagas_remanescentes": pl.Int32,
    "ingressantes_programa_especial": pl.Int32,
    "ingressantes_outra_forma": pl.Int32,
    # Matriculados
    "matriculados": pl.Int32,
    "matriculados_diurno": pl.Int32,
    "matriculados_noturno": pl.Int32,
    # Rematriculados - derivados
    "rematriculados": pl.Int32,
    "rematriculados_diurno": pl.Int32,
    "rematriculados_noturno": pl.Int32,
    # Concluintes
    "concluintes": pl.Int32,
    "concluintes_diurno": pl.Int32,
    "concluintes_noturno": pl.Int32,
    # Financiamento
    "ingressantes_fies": pl.Int32,
    "ingressantes_prouni_integral": pl.Int32,
    "ingressantes_prouni_parcial": pl.Int32,
    "matriculados_fies": pl.Int32,
    "matriculados_prouni_integral": pl.Int32,
    "matriculados_prouni_parcial": pl.Int32,
    "concluintes_fies": pl.Int32,
    "concluintes_prouni_integral": pl.Int32,
    "concluintes_prouni_parcial": pl.Int32,
    # Situacao academica
    "trancados": pl.Int32,
    "desvinculados": pl.Int32,
    "transferidos": pl.Int32,
    "falecidos": pl.Int32,
    # Procedencia escolar
    "ingressantes_escola_publica": pl.Int32,
    "ingressantes_escola_privada": pl.Int32,
    "ingressantes_escola_nao_informada": pl.Int32,
    "matriculados_escola_publica": pl.Int32,
    "matriculados_escola_privada": pl.Int32,
    "matriculados_escola_nao_informada": pl.Int32,
    "concluintes_escola_publica": pl.Int32,
    "concluintes_escola_privada": pl.Int32,
    "concluintes_escola_nao_informada": pl.Int32,
    # Metadados / derivados
    "arquivo_origem": pl.String,
    "ano_arquivo": pl.Int64,
    "municipio_normalizado": pl.String,
    "codigo_curso_referencia": pl.String,
    "nome_curso_referencia": pl.String,
    "tipo_codigo_curso": pl.String,
    "curso_base": pl.String,
    "tipo_curso": pl.String,
}

SCHEMA_IES_SILVER = {
    "ano_censo": pl.Int32,
    "codigo_ies": pl.Int64,
    "nome_ies": pl.String,
    "sigla_ies": pl.String,
    "mantenedora": pl.String,
    "codigo_organizacao_academica": pl.Int32,
    "codigo_categoria_administrativa": pl.Int32,
    "municipio_ies": pl.String,
    "uf_ies": pl.String,
    "chave_ies_normalizada": pl.String,
    "chave_cidade_normalizada": pl.String,
    "arquivo_origem": pl.String,
    "ano_arquivo": pl.Int64,
}


# Educacao Basica
SCHEMA_ED_BASICA_SILVER = {
    "ano_censo": pl.Int32,
    "codigo_escola": pl.Int64,
    "nome_escola": pl.String,
    "distrito": pl.String,
    "subdistrito": pl.String,
    "endereco": pl.String,
    "numero_endereco": pl.String,
    "complemento": pl.String,
    "bairro": pl.String,
    "cep": pl.String,
    "codigo_dependencia": pl.Int32,
    "codigo_categoria_escola_privada": pl.Int32,
    "codigo_localizacao": pl.Int32,
    "codigo_situacao_funcionamento": pl.Int32,
    "codigo_municipio": pl.Int64,
    "municipio": pl.String,
    "uf": pl.String,
    "indicador_ensino_medio": pl.Int32,
    # Indicadores do Censo Escolar (null para variavel indisponivel).
    # Matriculas gerais
    "matriculas_educacao_basica": pl.Int32,
    "matriculas_educacao_infantil": pl.Int32,
    "matriculas_creche": pl.Int32,
    "matriculas_pre_escola": pl.Int32,
    "matriculas_ensino_fundamental": pl.Int32,
    "matriculas_fundamental_anos_iniciais": pl.Int32,
    "matriculas_fundamental_anos_finais": pl.Int32,
    "matriculas_ensino_medio": pl.Int32,
    "matriculas_educacao_profissional": pl.Int32,
    "matriculas_educacao_profissional_tecnica": pl.Int32,
    "matriculas_eja": pl.Int32,
    "matriculas_eja_fundamental": pl.Int32,
    "matriculas_eja_ensino_medio": pl.Int32,
    "matriculas_educacao_especial": pl.Int32,
    "matriculas_educacao_especial_classe_comum": pl.Int32,
    "matriculas_educacao_especial_classe_exclusiva": pl.Int32,
    # Series do ensino fundamental
    "matriculas_fundamental_ano_1": pl.Int32,
    "matriculas_fundamental_ano_2": pl.Int32,
    "matriculas_fundamental_ano_3": pl.Int32,
    "matriculas_fundamental_ano_4": pl.Int32,
    "matriculas_fundamental_ano_5": pl.Int32,
    "matriculas_fundamental_ano_6": pl.Int32,
    "matriculas_fundamental_ano_7": pl.Int32,
    "matriculas_fundamental_ano_8": pl.Int32,
    "matriculas_fundamental_ano_9": pl.Int32,
    # Series do ensino medio
    "matriculas_ensino_medio_1": pl.Int32,
    "matriculas_ensino_medio_2": pl.Int32,
    "matriculas_ensino_medio_3": pl.Int32,
    "matriculas_ensino_medio_4": pl.Int32,
    "matriculas_ensino_medio_nao_seriado": pl.Int32,
    # Sexo - educacao basica
    "matriculas_educacao_basica_feminino": pl.Int32,
    "matriculas_educacao_basica_masculino": pl.Int32,
    # Cor/raca - educacao basica
    "matriculas_educacao_basica_cor_nao_declarada": pl.Int32,
    "matriculas_educacao_basica_cor_branca": pl.Int32,
    "matriculas_educacao_basica_cor_preta": pl.Int32,
    "matriculas_educacao_basica_cor_parda": pl.Int32,
    "matriculas_educacao_basica_cor_amarela": pl.Int32,
    "matriculas_educacao_basica_cor_indigena": pl.Int32,
    # Faixa etaria - educacao basica
    "matriculas_educacao_basica_idade_0_3": pl.Int32,
    "matriculas_educacao_basica_idade_4_5": pl.Int32,
    "matriculas_educacao_basica_idade_6_10": pl.Int32,
    "matriculas_educacao_basica_idade_11_14": pl.Int32,
    "matriculas_educacao_basica_idade_15_17": pl.Int32,
    "matriculas_educacao_basica_idade_18_mais": pl.Int32,
    # Turno e modalidade
    "matriculas_educacao_basica_diurno": pl.Int32,
    "matriculas_educacao_basica_noturno": pl.Int32,
    "matriculas_educacao_basica_ead": pl.Int32,
    # Tempo integral
    "matriculas_educacao_infantil_tempo_integral": pl.Int32,
    "matriculas_creche_tempo_integral": pl.Int32,
    "matriculas_pre_escola_tempo_integral": pl.Int32,
    "matriculas_ensino_fundamental_tempo_integral": pl.Int32,
    "matriculas_fundamental_anos_iniciais_tempo_integral": pl.Int32,
    "matriculas_fundamental_anos_finais_tempo_integral": pl.Int32,
    "matriculas_ensino_medio_tempo_integral": pl.Int32,
    "municipio_normalizado": pl.String,
    "rede": pl.String,
    "arquivo_origem": pl.String,
    "ano_arquivo": pl.Int64,
}


# Conceito Enade
SCHEMA_CONCEITO_ENADE_SILVER = {
    "ano_enade": pl.Int32,
    "codigo_area": pl.Int64,
    "area_avaliacao": pl.String,
    "grau_academico": pl.String,
    "codigo_ies": pl.Int64,
    "nome_ies": pl.String,
    "sigla_ies": pl.String,
    "organizacao_academica": pl.String,
    "categoria_administrativa": pl.String,
    "codigo_curso": pl.Int64,
    "modalidade_ensino": pl.String,
    "codigo_municipio": pl.Int64,
    "municipio_curso": pl.String,
    "uf": pl.String,
    "enade_concluintes_inscritos_qtd": pl.Int64,
    "enade_concluintes_participantes_qtd": pl.Int64,
    "enade_nota_bruta_fg": pl.Float64,
    "enade_nota_padronizada_fg": pl.Float64,
    "enade_nota_bruta_ce": pl.Float64,
    "enade_nota_padronizada_ce": pl.Float64,
    "enade_conceito_continuo": pl.Float64,
    "enade_conceito_faixa": pl.Int32,
    "enade_concluintes_acima_padrao_qtd": pl.Int64,
    "enade_percentual_acima_padrao": pl.Float64,
    "observacao": pl.String,
    "cebas": pl.String,
    "chave_ies_normalizada": pl.String,
    "chave_cidade_normalizada": pl.String,
    "arquivo_origem": pl.String,
    "ano_arquivo": pl.Int64,
}


COLUNAS_OBRIGATORIAS_CONCEITO_ENADE_SILVER = [
    "ano_enade",
    "codigo_ies",
    "codigo_curso",
    "nome_ies",
    "municipio_curso",
    "uf",
    "enade_concluintes_inscritos_qtd",
    "enade_concluintes_participantes_qtd",
    "chave_ies_normalizada",
    "chave_cidade_normalizada",
    "arquivo_origem",
    "ano_arquivo",
]

COLUNAS_OPCIONAIS_CONCEITO_ENADE_SILVER = [
    coluna
    for coluna in SCHEMA_CONCEITO_ENADE_SILVER
    if coluna not in COLUNAS_OBRIGATORIAS_CONCEITO_ENADE_SILVER
]

# CPC
SCHEMA_CPC_SILVER = {
    "ano_cpc": pl.Int32,
    "codigo_area": pl.Int64,
    "area_avaliacao": pl.String,
    "grau_academico": pl.String,
    "codigo_ies": pl.Int64,
    "nome_ies": pl.String,
    "sigla_ies": pl.String,
    "organizacao_academica": pl.String,
    "categoria_administrativa": pl.String,
    "codigo_curso": pl.Int64,
    "modalidade_ensino": pl.String,
    "codigo_municipio": pl.Int64,
    "municipio_curso": pl.String,
    "uf": pl.String,
    "cpc_concluintes_inscritos_qtd": pl.Int64,
    "cpc_concluintes_participantes_qtd": pl.Int64,
    "cpc_nota_bruta_fg": pl.Float64,
    "cpc_nota_padronizada_fg": pl.Float64,
    "cpc_nota_bruta_ce": pl.Float64,
    "cpc_nota_padronizada_ce": pl.Float64,
    "cpc_conceito_enade_continuo": pl.Float64,
    "cpc_concluintes_com_enem_qtd": pl.Int64,
    "cpc_proporcao_concluintes_com_enem": pl.Float64,
    "cpc_nota_bruta_idd": pl.Float64,
    "cpc_nota_padronizada_idd": pl.Float64,
    "cpc_nota_bruta_organizacao_didatico_pedagogica": pl.Float64,
    "cpc_nota_padronizada_organizacao_didatico_pedagogica": pl.Float64,
    "cpc_nota_bruta_infraestrutura": pl.Float64,
    "cpc_nota_padronizada_infraestrutura": pl.Float64,
    "cpc_nota_bruta_oportunidade_formacao": pl.Float64,
    "cpc_nota_padronizada_oportunidade_formacao": pl.Float64,
    "cpc_nota_bruta_mestres": pl.Float64,
    "cpc_nota_padronizada_mestres": pl.Float64,
    "cpc_nota_bruta_doutores": pl.Float64,
    "cpc_nota_padronizada_doutores": pl.Float64,
    "cpc_nota_bruta_regime_trabalho": pl.Float64,
    "cpc_nota_padronizada_regime_trabalho": pl.Float64,
    "cpc_continuo": pl.Float64,
    "cpc_faixa": pl.Int32,
    "observacao": pl.String,
    "cebas": pl.String,
    "chave_ies_normalizada": pl.String,
    "chave_cidade_normalizada": pl.String,
    "arquivo_origem": pl.String,
    "ano_arquivo": pl.Int64,
}

COLUNAS_OBRIGATORIAS_CPC_SILVER = [
    "ano_cpc",
    "codigo_ies",
    "codigo_curso",
    "nome_ies",
    "cpc_continuo",
    "cpc_faixa",
    "chave_ies_normalizada",
    "chave_cidade_normalizada",
    "arquivo_origem",
    "ano_arquivo",
]

COLUNAS_OPCIONAIS_CPC_SILVER = [
    coluna for coluna in SCHEMA_CPC_SILVER if coluna not in COLUNAS_OBRIGATORIAS_CPC_SILVER
]


# IDD
SCHEMA_IDD_SILVER = {
    "ano_idd": pl.Int32,
    "codigo_area": pl.Int64,
    "area_avaliacao": pl.String,
    "grau_academico": pl.String,
    "codigo_ies": pl.Int64,
    "nome_ies": pl.String,
    "sigla_ies": pl.String,
    "organizacao_academica": pl.String,
    "categoria_administrativa": pl.String,
    "codigo_curso": pl.Int64,
    "modalidade_ensino": pl.String,
    "codigo_municipio": pl.Int64,
    "municipio_curso": pl.String,
    "uf": pl.String,
    "idd_concluintes_inscritos_qtd": pl.Int64,
    "idd_concluintes_participantes_qtd": pl.Int64,
    "idd_concluintes_com_enem_qtd": pl.Int64,
    "idd_proporcao_concluintes_com_enem": pl.Float64,
    "idd_nota_bruta": pl.Float64,
    "idd_continuo": pl.Float64,
    "idd_faixa": pl.Int32,
    "observacao": pl.String,
    "cebas": pl.String,
    "chave_ies_normalizada": pl.String,
    "chave_cidade_normalizada": pl.String,
    "arquivo_origem": pl.String,
    "ano_arquivo": pl.Int64,
}

COLUNAS_OBRIGATORIAS_IDD_SILVER = [
    "ano_idd",
    "codigo_ies",
    "codigo_curso",
    "nome_ies",
    "idd_continuo",
    "idd_faixa",
    "chave_ies_normalizada",
    "chave_cidade_normalizada",
    "arquivo_origem",
    "ano_arquivo",
]

COLUNAS_OPCIONAIS_IDD_SILVER = [
    coluna for coluna in SCHEMA_IDD_SILVER if coluna not in COLUNAS_OBRIGATORIAS_IDD_SILVER
]


# IGC
SCHEMA_IGC_SILVER = {
    "ano_igc": pl.Int32,
    "codigo_ies": pl.Int64,
    "nome_ies": pl.String,
    "sigla_ies": pl.String,
    "organizacao_academica": pl.String,
    "categoria_administrativa": pl.String,
    "uf": pl.String,
    "igc_cursos_cpc_trienio_qtd": pl.Int32,
    "igc_alfa_graduacao": pl.Float64,
    "igc_conceito_medio_graduacao": pl.Float64,
    "igc_beta_mestrado": pl.Float64,
    "igc_conceito_medio_mestrado": pl.Float64,
    "igc_gama_doutorado": pl.Float64,
    "igc_conceito_medio_doutorado": pl.Float64,
    "igc_continuo": pl.Float64,
    "igc_faixa": pl.Int32,
    "observacao": pl.String,
    "cebas": pl.String,
    "chave_ies_normalizada": pl.String,
    "arquivo_origem": pl.String,
    "ano_arquivo": pl.Int64,
}

COLUNAS_OBRIGATORIAS_IGC_SILVER = [
    "ano_igc",
    "codigo_ies",
    "nome_ies",
    "igc_continuo",
    "igc_faixa",
    "chave_ies_normalizada",
    "arquivo_origem",
    "ano_arquivo",
]

COLUNAS_OPCIONAIS_IGC_SILVER = [
    coluna for coluna in SCHEMA_IGC_SILVER if coluna not in COLUNAS_OBRIGATORIAS_IGC_SILVER
]


# Geo
SCHEMA_GEO_SILVER = {
    "codigo_municipio": pl.Int64,
    "codigo_uf": pl.Int32,
    "municipio": pl.String,
    "municipio_normalizado": pl.String,
    "uf": pl.String,
    "latitude": pl.Float64,
    "longitude": pl.Float64,
}


# ================================================================
# GOLD - DIMENSOES
# ================================================================
# Modelo analítico Gold do Painel Educacional orientado ao Power BI.
# As dimensoes usam nomes semanticos e as fatos preservam a granularidade
# necessaria para analise de mercado sem duplicacao de indicadores.

SCHEMA_DIM_CALENDARIO = {
    "id_calendario": pl.Int32,
    "ano": pl.Int32,
    "ano_texto": pl.String,
    "ordem_ano": pl.Int32,
    "data_inicio_ano": pl.Date,
    "data_fim_ano": pl.Date,
}


SCHEMA_DIM_IES = {
    "id_ies": pl.Int32,
    "codigo_ies": pl.Int64,
    "chave_ies_normalizada": pl.String,
    "fonte_ies": pl.String,
    "ano_primeiro_censo": pl.Int32,
    "ano_ultimo_censo": pl.Int32,
    "anos_censo": pl.String,
    "sigla_ies": pl.String,
    "rotulo_ies": pl.String,
    "nome_ies": pl.String,
    "mantenedora": pl.String,
    "tipo_ies": pl.String,
    "organizacao_academica": pl.String,
    "categoria_administrativa": pl.String,
    # Localizacao institucional/sede. Nao representa a localizacao da oferta.
    "uf_sede_ies": pl.String,
    "municipio_sede_ies": pl.String,
    "chave_cidade_sede_normalizada": pl.String,
    "cor_ies": pl.String,
    "hex_ies": pl.String,
}


SCHEMA_DIM_CURSO_SUPERIOR = {
    "id_curso_superior": pl.Int32,
    "tipo_curso": pl.String,
    "curso_base": pl.String,
    "nome_curso": pl.String,
    "grau_curso": pl.String,
    "modalidade_curso": pl.String,
    "nivel_ensino": pl.String,
    "rotulo_curso": pl.String,
    "cor_curso": pl.String,
    "hex_curso": pl.String,
    "oferta_curso": pl.String,
}


SCHEMA_DIM_LOCALIDADE = {
    "id_localidade": pl.Int32,
    "codigo_municipio": pl.Int64,
    "codigo_uf": pl.Int32,
    "municipio": pl.String,
    "municipio_normalizado": pl.String,
    "uf": pl.String,
    "latitude": pl.Float64,
    "longitude": pl.Float64,
    "distancia_referencia_km": pl.Float64,
}


SCHEMA_DIM_ESCOLA = {
    "id_escola": pl.Int32,
    "codigo_escola": pl.Int64,
    "nome_escola": pl.String,
    "rede_escola": pl.String,
    "categoria_escola_privada": pl.String,
    "localizacao_escola": pl.String,
    "situacao_funcionamento": pl.String,
    "distrito_escola": pl.String,
    "subdistrito_escola": pl.String,
    "bairro_escola": pl.String,
    "endereco_escola": pl.String,
    "numero_escola": pl.String,
    "complemento_escola": pl.String,
    "cep_escola": pl.String,
}


# ================================================================
# GOLD - FATOS
# ================================================================

# ----------------------------------------------------------------
# Educacao Superior - Censo Superior
# Grao: IES x curso analitico x localidade x ano.
# Contem apenas indicadores gerais sem abertura por turno.
# ----------------------------------------------------------------

SCHEMA_FACT_EDUCACAO_SUPERIOR = {
    # Chaves
    "id_ies": pl.Int32,
    "id_curso_superior": pl.Int32,
    "id_localidade": pl.Int32,
    "id_calendario": pl.Int32,
    "ano": pl.Int32,
    # Vagas
    "vagas_total": pl.Int32,
    "vagas_novas": pl.Int32,
    "vagas_processo_seletivo": pl.Int32,
    "vagas_remanescentes": pl.Int32,
    "vagas_programa_especial": pl.Int32,
    # Inscritos
    "inscritos_total": pl.Int32,
    "inscritos_vagas_novas": pl.Int32,
    "inscritos_processo_seletivo": pl.Int32,
    "inscritos_vagas_remanescentes": pl.Int32,
    "inscritos_programa_especial": pl.Int32,
    # Ingressantes
    "ingressantes": pl.Int32,
    "ingressantes_vagas_novas": pl.Int32,
    "ingressantes_vestibular": pl.Int32,
    "ingressantes_enem": pl.Int32,
    "ingressantes_avaliacao_seriada": pl.Int32,
    "ingressantes_selecao_simplificada": pl.Int32,
    "ingressantes_egressos": pl.Int32,
    "ingressantes_outro_tipo_selecao": pl.Int32,
    "ingressantes_processo_seletivo": pl.Int32,
    "ingressantes_vagas_remanescentes": pl.Int32,
    "ingressantes_programa_especial": pl.Int32,
    "ingressantes_outra_forma": pl.Int32,
    # Matriculados / rematriculados / concluintes
    "matriculados": pl.Int32,
    "rematriculados": pl.Int32,
    "concluintes": pl.Int32,
    # Financiamento e bolsas
    "ingressantes_fies": pl.Int32,
    "ingressantes_prouni_integral": pl.Int32,
    "ingressantes_prouni_parcial": pl.Int32,
    "matriculados_fies": pl.Int32,
    "matriculados_prouni_integral": pl.Int32,
    "matriculados_prouni_parcial": pl.Int32,
    "concluintes_fies": pl.Int32,
    "concluintes_prouni_integral": pl.Int32,
    "concluintes_prouni_parcial": pl.Int32,
    # Situação acadêmica
    "trancados": pl.Int32,
    "desvinculados": pl.Int32,
    "transferidos": pl.Int32,
    "falecidos": pl.Int32,
    # Procedência escolar
    "ingressantes_escola_publica": pl.Int32,
    "ingressantes_escola_privada": pl.Int32,
    "ingressantes_escola_nao_informada": pl.Int32,
    "matriculados_escola_publica": pl.Int32,
    "matriculados_escola_privada": pl.Int32,
    "matriculados_escola_nao_informada": pl.Int32,
    "concluintes_escola_publica": pl.Int32,
    "concluintes_escola_privada": pl.Int32,
    "concluintes_escola_nao_informada": pl.Int32,
}

SCHEMA_FACT_EDUCACAO_SUPERIOR_TURNO = {
    # Chaves
    "id_ies": pl.Int32,
    "id_curso_superior": pl.Int32,
    "id_localidade": pl.Int32,
    "id_calendario": pl.Int32,
    "ano": pl.Int32,
    # Classificacao da oferta
    "turno_curso": pl.String,
    "oferta_curso": pl.String,
    # Indicadores por turno
    "vagas_total": pl.Int32,
    "inscritos_total": pl.Int32,
    "ingressantes": pl.Int32,
    "matriculados": pl.Int32,
    "rematriculados": pl.Int32,
    "concluintes": pl.Int32,
}


# ----------------------------------------------------------------
# Avaliacao de Curso Superior - ENADE / IDD / CPC
# Grao: IES x curso avaliado INEP x classificacao analitica x localidade x ano.
# ----------------------------------------------------------------

SCHEMA_FACT_AVALIACAO_CURSO_SUPERIOR = {
    "id_ies": pl.Int32,
    "id_curso_superior": pl.Int32,
    "id_localidade": pl.Int32,
    "id_calendario": pl.Int32,
    "ano": pl.Int32,
    # Identificacao oficial da avaliacao
    "codigo_curso_avaliado": pl.Int64,
    "codigo_area": pl.Int64,
    "area_avaliacao": pl.String,
    "grau_academico_avaliacao": pl.String,
    "modalidade_ensino_avaliacao": pl.String,
    # ENADE
    "enade_concluintes_inscritos_qtd": pl.Int64,
    "enade_concluintes_participantes_qtd": pl.Int64,
    "enade_nota_bruta_fg": pl.Float64,
    "enade_nota_padronizada_fg": pl.Float64,
    "enade_nota_bruta_ce": pl.Float64,
    "enade_nota_padronizada_ce": pl.Float64,
    "enade_conceito_continuo": pl.Float64,
    "enade_conceito_faixa": pl.Int32,
    "enade_concluintes_acima_padrao_qtd": pl.Int64,
    "enade_percentual_acima_padrao": pl.Float64,
    # IDD
    "idd_concluintes_inscritos_qtd": pl.Int64,
    "idd_concluintes_participantes_qtd": pl.Int64,
    "idd_concluintes_com_enem_qtd": pl.Int64,
    "idd_proporcao_concluintes_com_enem": pl.Float64,
    "idd_nota_bruta": pl.Float64,
    "idd_continuo": pl.Float64,
    "idd_faixa": pl.Int32,
    # CPC - indicadores completos da fonte CPC
    "cpc_concluintes_inscritos_qtd": pl.Int64,
    "cpc_concluintes_participantes_qtd": pl.Int64,
    "cpc_nota_bruta_fg": pl.Float64,
    "cpc_nota_padronizada_fg": pl.Float64,
    "cpc_nota_bruta_ce": pl.Float64,
    "cpc_nota_padronizada_ce": pl.Float64,
    "cpc_conceito_enade_continuo": pl.Float64,
    "cpc_concluintes_com_enem_qtd": pl.Int64,
    "cpc_proporcao_concluintes_com_enem": pl.Float64,
    "cpc_nota_bruta_idd": pl.Float64,
    "cpc_nota_padronizada_idd": pl.Float64,
    "cpc_nota_bruta_organizacao_didatico_pedagogica": pl.Float64,
    "cpc_nota_padronizada_organizacao_didatico_pedagogica": pl.Float64,
    "cpc_nota_bruta_infraestrutura": pl.Float64,
    "cpc_nota_padronizada_infraestrutura": pl.Float64,
    "cpc_nota_bruta_oportunidade_formacao": pl.Float64,
    "cpc_nota_padronizada_oportunidade_formacao": pl.Float64,
    "cpc_nota_bruta_mestres": pl.Float64,
    "cpc_nota_padronizada_mestres": pl.Float64,
    "cpc_nota_bruta_doutores": pl.Float64,
    "cpc_nota_padronizada_doutores": pl.Float64,
    "cpc_nota_bruta_regime_trabalho": pl.Float64,
    "cpc_nota_padronizada_regime_trabalho": pl.Float64,
    "cpc_continuo": pl.Float64,
    "cpc_faixa": pl.Int32,
    # Observacoes de origem, preservadas separadamente
    "observacao_enade": pl.String,
    "observacao_idd": pl.String,
    "observacao_cpc": pl.String,
}


# ----------------------------------------------------------------
# Avaliacao Institucional - IGC
# Grao: IES x ano.
# ----------------------------------------------------------------

SCHEMA_FACT_AVALIACAO_IES = {
    "id_ies": pl.Int32,
    "id_calendario": pl.Int32,
    "ano": pl.Int32,
    "igc_cursos_cpc_trienio_qtd": pl.Int32,
    "igc_alfa_graduacao": pl.Float64,
    "igc_conceito_medio_graduacao": pl.Float64,
    "igc_beta_mestrado": pl.Float64,
    "igc_conceito_medio_mestrado": pl.Float64,
    "igc_gama_doutorado": pl.Float64,
    "igc_conceito_medio_doutorado": pl.Float64,
    "igc_continuo": pl.Float64,
    "igc_faixa": pl.Int32,
    "observacao_igc": pl.String,
    "cebas_igc": pl.String,
}


# ----------------------------------------------------------------
# Educacao Basica - Censo Escolar
# Grao: escola x ano. A localidade e compartilhada pela dim_localidade.
# ----------------------------------------------------------------

SCHEMA_FACT_EDUCACAO_BASICA = {
    "id_escola": pl.Int32,
    "id_localidade": pl.Int32,
    "id_calendario": pl.Int32,
    "ano": pl.Int32,
    # Totais e desagregacoes oficiais: cuidado com sobreposicoes.
    # Matriculas gerais
    "matriculas_educacao_basica": pl.Int32,
    "matriculas_educacao_infantil": pl.Int32,
    "matriculas_creche": pl.Int32,
    "matriculas_pre_escola": pl.Int32,
    "matriculas_ensino_fundamental": pl.Int32,
    "matriculas_fundamental_anos_iniciais": pl.Int32,
    "matriculas_fundamental_anos_finais": pl.Int32,
    "matriculas_ensino_medio": pl.Int32,
    "matriculas_educacao_profissional": pl.Int32,
    "matriculas_educacao_profissional_tecnica": pl.Int32,
    "matriculas_eja": pl.Int32,
    "matriculas_eja_fundamental": pl.Int32,
    "matriculas_eja_ensino_medio": pl.Int32,
    "matriculas_educacao_especial": pl.Int32,
    "matriculas_educacao_especial_classe_comum": pl.Int32,
    "matriculas_educacao_especial_classe_exclusiva": pl.Int32,
    # Series do ensino fundamental
    "matriculas_fundamental_ano_1": pl.Int32,
    "matriculas_fundamental_ano_2": pl.Int32,
    "matriculas_fundamental_ano_3": pl.Int32,
    "matriculas_fundamental_ano_4": pl.Int32,
    "matriculas_fundamental_ano_5": pl.Int32,
    "matriculas_fundamental_ano_6": pl.Int32,
    "matriculas_fundamental_ano_7": pl.Int32,
    "matriculas_fundamental_ano_8": pl.Int32,
    "matriculas_fundamental_ano_9": pl.Int32,
    # Series do ensino medio
    "matriculas_ensino_medio_1": pl.Int32,
    "matriculas_ensino_medio_2": pl.Int32,
    "matriculas_ensino_medio_3": pl.Int32,
    "matriculas_ensino_medio_4": pl.Int32,
    "matriculas_ensino_medio_nao_seriado": pl.Int32,
    # Sexo - educacao basica
    "matriculas_educacao_basica_feminino": pl.Int32,
    "matriculas_educacao_basica_masculino": pl.Int32,
    # Cor/raca - educacao basica
    "matriculas_educacao_basica_cor_nao_declarada": pl.Int32,
    "matriculas_educacao_basica_cor_branca": pl.Int32,
    "matriculas_educacao_basica_cor_preta": pl.Int32,
    "matriculas_educacao_basica_cor_parda": pl.Int32,
    "matriculas_educacao_basica_cor_amarela": pl.Int32,
    "matriculas_educacao_basica_cor_indigena": pl.Int32,
    # Faixa etaria - educacao basica
    "matriculas_educacao_basica_idade_0_3": pl.Int32,
    "matriculas_educacao_basica_idade_4_5": pl.Int32,
    "matriculas_educacao_basica_idade_6_10": pl.Int32,
    "matriculas_educacao_basica_idade_11_14": pl.Int32,
    "matriculas_educacao_basica_idade_15_17": pl.Int32,
    "matriculas_educacao_basica_idade_18_mais": pl.Int32,
    # Turno e modalidade
    "matriculas_educacao_basica_diurno": pl.Int32,
    "matriculas_educacao_basica_noturno": pl.Int32,
    "matriculas_educacao_basica_ead": pl.Int32,
    # Tempo integral
    "matriculas_educacao_infantil_tempo_integral": pl.Int32,
    "matriculas_creche_tempo_integral": pl.Int32,
    "matriculas_pre_escola_tempo_integral": pl.Int32,
    "matriculas_ensino_fundamental_tempo_integral": pl.Int32,
    "matriculas_fundamental_anos_iniciais_tempo_integral": pl.Int32,
    "matriculas_fundamental_anos_finais_tempo_integral": pl.Int32,
    "matriculas_ensino_medio_tempo_integral": pl.Int32,
}


# Indicadores adicionais nao contemplados na fato principal.
# Grao: escola x ano x variavel_inep. Valores nao informados permanecem null.
SCHEMA_FACT_EDUCACAO_BASICA_DETALHE = {
    "id_escola": pl.Int32,
    "id_localidade": pl.Int32,
    "id_calendario": pl.Int32,
    "ano": pl.Int32,
    "variavel_inep": pl.String,
    "valor": pl.Int64,
}


# ================================================================
# GOLD - CONTRATOS AUXILIARES
# ================================================================

COLUNAS_METRICAS_ED_BASICA = [
    "matriculas_educacao_basica",
    "matriculas_educacao_infantil",
    "matriculas_creche",
    "matriculas_pre_escola",
    "matriculas_ensino_fundamental",
    "matriculas_fundamental_anos_iniciais",
    "matriculas_fundamental_anos_finais",
    "matriculas_ensino_medio",
    "matriculas_educacao_profissional",
    "matriculas_educacao_profissional_tecnica",
    "matriculas_eja",
    "matriculas_eja_fundamental",
    "matriculas_eja_ensino_medio",
    "matriculas_educacao_especial",
    "matriculas_educacao_especial_classe_comum",
    "matriculas_educacao_especial_classe_exclusiva",
    "matriculas_fundamental_ano_1",
    "matriculas_fundamental_ano_2",
    "matriculas_fundamental_ano_3",
    "matriculas_fundamental_ano_4",
    "matriculas_fundamental_ano_5",
    "matriculas_fundamental_ano_6",
    "matriculas_fundamental_ano_7",
    "matriculas_fundamental_ano_8",
    "matriculas_fundamental_ano_9",
    "matriculas_ensino_medio_1",
    "matriculas_ensino_medio_2",
    "matriculas_ensino_medio_3",
    "matriculas_ensino_medio_4",
    "matriculas_ensino_medio_nao_seriado",
    "matriculas_educacao_basica_feminino",
    "matriculas_educacao_basica_masculino",
    "matriculas_educacao_basica_cor_nao_declarada",
    "matriculas_educacao_basica_cor_branca",
    "matriculas_educacao_basica_cor_preta",
    "matriculas_educacao_basica_cor_parda",
    "matriculas_educacao_basica_cor_amarela",
    "matriculas_educacao_basica_cor_indigena",
    "matriculas_educacao_basica_idade_0_3",
    "matriculas_educacao_basica_idade_4_5",
    "matriculas_educacao_basica_idade_6_10",
    "matriculas_educacao_basica_idade_11_14",
    "matriculas_educacao_basica_idade_15_17",
    "matriculas_educacao_basica_idade_18_mais",
    "matriculas_educacao_basica_diurno",
    "matriculas_educacao_basica_noturno",
    "matriculas_educacao_basica_ead",
    "matriculas_educacao_infantil_tempo_integral",
    "matriculas_creche_tempo_integral",
    "matriculas_pre_escola_tempo_integral",
    "matriculas_ensino_fundamental_tempo_integral",
    "matriculas_fundamental_anos_iniciais_tempo_integral",
    "matriculas_fundamental_anos_finais_tempo_integral",
    "matriculas_ensino_medio_tempo_integral",
]

COLUNAS_METRICAS_ENADE = [
    "enade_concluintes_inscritos_qtd",
    "enade_concluintes_participantes_qtd",
    "enade_nota_bruta_fg",
    "enade_nota_padronizada_fg",
    "enade_nota_bruta_ce",
    "enade_nota_padronizada_ce",
    "enade_conceito_continuo",
    "enade_conceito_faixa",
    "enade_concluintes_acima_padrao_qtd",
    "enade_percentual_acima_padrao",
]

COLUNAS_METRICAS_ENADE_INT = [
    "enade_concluintes_inscritos_qtd",
    "enade_concluintes_participantes_qtd",
    "enade_concluintes_acima_padrao_qtd",
    "enade_conceito_faixa",
]

COLUNAS_METRICAS_ENADE_FLOAT = [
    "enade_nota_bruta_fg",
    "enade_nota_padronizada_fg",
    "enade_nota_bruta_ce",
    "enade_nota_padronizada_ce",
    "enade_conceito_continuo",
    "enade_percentual_acima_padrao",
]

COLUNAS_METRICAS_IDD = [
    "idd_concluintes_inscritos_qtd",
    "idd_concluintes_participantes_qtd",
    "idd_concluintes_com_enem_qtd",
    "idd_proporcao_concluintes_com_enem",
    "idd_nota_bruta",
    "idd_continuo",
    "idd_faixa",
]

COLUNAS_METRICAS_CPC = [
    "cpc_concluintes_inscritos_qtd",
    "cpc_concluintes_participantes_qtd",
    "cpc_nota_bruta_fg",
    "cpc_nota_padronizada_fg",
    "cpc_nota_bruta_ce",
    "cpc_nota_padronizada_ce",
    "cpc_conceito_enade_continuo",
    "cpc_concluintes_com_enem_qtd",
    "cpc_proporcao_concluintes_com_enem",
    "cpc_nota_bruta_idd",
    "cpc_nota_padronizada_idd",
    "cpc_nota_bruta_organizacao_didatico_pedagogica",
    "cpc_nota_padronizada_organizacao_didatico_pedagogica",
    "cpc_nota_bruta_infraestrutura",
    "cpc_nota_padronizada_infraestrutura",
    "cpc_nota_bruta_oportunidade_formacao",
    "cpc_nota_padronizada_oportunidade_formacao",
    "cpc_nota_bruta_mestres",
    "cpc_nota_padronizada_mestres",
    "cpc_nota_bruta_doutores",
    "cpc_nota_padronizada_doutores",
    "cpc_nota_bruta_regime_trabalho",
    "cpc_nota_padronizada_regime_trabalho",
    "cpc_continuo",
    "cpc_faixa",
]

COLUNAS_METRICAS_IGC = [
    "igc_cursos_cpc_trienio_qtd",
    "igc_alfa_graduacao",
    "igc_conceito_medio_graduacao",
    "igc_beta_mestrado",
    "igc_conceito_medio_mestrado",
    "igc_gama_doutorado",
    "igc_conceito_medio_doutorado",
    "igc_continuo",
    "igc_faixa",
]


COLUNAS_OBRIGATORIAS_FACT_EDUCACAO_SUPERIOR = [
    "id_ies",
    "id_curso_superior",
    "id_localidade",
    "id_calendario",
    "ano",
]

COLUNAS_OPCIONAIS_FACT_EDUCACAO_SUPERIOR = [
    coluna
    for coluna in SCHEMA_FACT_EDUCACAO_SUPERIOR
    if coluna not in COLUNAS_OBRIGATORIAS_FACT_EDUCACAO_SUPERIOR
]

COLUNAS_OBRIGATORIAS_FACT_EDUCACAO_SUPERIOR_TURNO = [
    "id_ies",
    "id_curso_superior",
    "id_localidade",
    "id_calendario",
    "ano",
    "turno_curso",
    "oferta_curso",
]

COLUNAS_OPCIONAIS_FACT_EDUCACAO_SUPERIOR_TURNO = [
    coluna
    for coluna in SCHEMA_FACT_EDUCACAO_SUPERIOR_TURNO
    if coluna not in COLUNAS_OBRIGATORIAS_FACT_EDUCACAO_SUPERIOR_TURNO
]

COLUNAS_OBRIGATORIAS_FACT_AVALIACAO_CURSO_SUPERIOR = [
    "id_ies",
    "id_curso_superior",
    "id_localidade",
    "id_calendario",
    "ano",
    "codigo_curso_avaliado",
]

COLUNAS_OPCIONAIS_FACT_AVALIACAO_CURSO_SUPERIOR = [
    coluna
    for coluna in SCHEMA_FACT_AVALIACAO_CURSO_SUPERIOR
    if coluna not in COLUNAS_OBRIGATORIAS_FACT_AVALIACAO_CURSO_SUPERIOR
]

COLUNAS_OBRIGATORIAS_FACT_AVALIACAO_IES = [
    "id_ies",
    "id_calendario",
    "ano",
]

COLUNAS_OPCIONAIS_FACT_AVALIACAO_IES = [
    coluna
    for coluna in SCHEMA_FACT_AVALIACAO_IES
    if coluna not in COLUNAS_OBRIGATORIAS_FACT_AVALIACAO_IES
]

COLUNAS_OBRIGATORIAS_FACT_EDUCACAO_BASICA = [
    "id_escola",
    "id_localidade",
    "id_calendario",
    "ano",
]

COLUNAS_OPCIONAIS_FACT_EDUCACAO_BASICA = [
    coluna
    for coluna in SCHEMA_FACT_EDUCACAO_BASICA
    if coluna not in COLUNAS_OBRIGATORIAS_FACT_EDUCACAO_BASICA
]


COLUNAS_OBRIGATORIAS_FACT_EDUCACAO_BASICA_DETALHE = [
    "id_escola",
    "id_localidade",
    "id_calendario",
    "ano",
    "variavel_inep",
]

COLUNAS_OPCIONAIS_FACT_EDUCACAO_BASICA_DETALHE = [
    coluna
    for coluna in SCHEMA_FACT_EDUCACAO_BASICA_DETALHE
    if coluna not in COLUNAS_OBRIGATORIAS_FACT_EDUCACAO_BASICA_DETALHE
]


# ================================================================
# CHAVES SILVER
# ================================================================

CHAVE_GEO = [
    "codigo_municipio",
]

CHAVE_IES_ANO = [
    "ano_censo",
    "codigo_ies",
]

CHAVE_ESCOLA_ANO = [
    "ano_censo",
    "codigo_escola",
]

CHAVE_ENADE = [
    "ano_enade",
    "codigo_ies",
    "codigo_curso",
]

CHAVE_CPC = [
    "ano_cpc",
    "codigo_ies",
    "codigo_curso",
]

CHAVE_IDD = [
    "ano_idd",
    "codigo_ies",
    "codigo_curso",
]

CHAVE_IGC = [
    "ano_igc",
    "codigo_ies",
]


# ================================================================
# CHAVES GOLD
# ================================================================

CHAVE_IES_GOLD = [
    "codigo_ies",
]

CHAVE_CURSO_SUPERIOR_GOLD = [
    "tipo_curso",
    "curso_base",
    "nome_curso",
    "grau_curso",
    "modalidade_curso",
    "nivel_ensino",
]

CHAVE_LOCALIDADE_GOLD = [
    "codigo_municipio",
]

CHAVE_ESCOLA_GOLD = [
    "codigo_escola",
]

CHAVE_CALENDARIO_GOLD = [
    "ano",
]

CHAVE_FACT_EDUCACAO_SUPERIOR = [
    "id_ies",
    "id_curso_superior",
    "id_localidade",
    "id_calendario",
]

CHAVE_FACT_EDUCACAO_SUPERIOR_TURNO = [
    "id_ies",
    "id_curso_superior",
    "id_localidade",
    "id_calendario",
    "turno_curso",
]

CHAVE_FACT_AVALIACAO_CURSO_SUPERIOR = [
    "id_ies",
    "id_curso_superior",
    "id_localidade",
    "ano",
    "codigo_curso_avaliado",
]

CHAVE_FACT_AVALIACAO_IES = [
    "id_ies",
    "ano",
]

CHAVE_FACT_EDUCACAO_BASICA = [
    "id_escola",
    "ano",
]


# Um valor por escola/ano e variavel de origem.
CHAVE_FACT_EDUCACAO_BASICA_DETALHE = [
    "id_escola",
    "ano",
    "variavel_inep",
]
