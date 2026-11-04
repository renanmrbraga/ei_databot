# ==============================================================================
# INFRAESTRUTURA — Tabelas de domínio do INEP
# ==============================================================================
# Mapeamento IBGE Código UF -> Sigla UF
UF_CODIGO_PARA_SIGLA = {
    11: "RO",
    12: "AC",
    13: "AM",
    14: "RR",
    15: "PA",
    16: "AP",
    17: "TO",
    21: "MA",
    22: "PI",
    23: "CE",
    24: "RN",
    25: "PB",
    26: "PE",
    27: "AL",
    28: "SE",
    29: "BA",
    31: "MG",
    32: "ES",
    33: "RJ",
    35: "SP",
    41: "PR",
    42: "SC",
    43: "RS",
    50: "MS",
    51: "MT",
    52: "GO",
    53: "DF",
}

# Mapeamentos do Censo (INEP)
MAPA_GRAU_ACADEMICO = {
    1: "BACHARELADO",
    2: "LICENCIATURA",
    3: "TECNOLÓGICO",
    4: "BACHARELADO INTERDISCIPLINAR",
    5: "LICENCIATURA INTERDISCIPLINAR",
}

MAPA_MODALIDADE_ENSINO = {1: "PRESENCIAL", 2: "EAD"}

MAPA_NIVEL_ACADEMICO = {
    1: "GRADUAÇÃO",
    2: "SEQUENCIAL",
}

MAPA_ORGANIZACAO_ACADEMICA = {
    1: "UNIVERSIDADE",
    2: "CENTRO UNIVERSITÁRIO",
    3: "FACULDADE",
    4: "INSTITUTO FEDERAL / CEFET",
}

MAPA_CATEGORIA_ADMINISTRATIVA = {
    1: "PÚBLICA FEDERAL",
    2: "PÚBLICA ESTADUAL",
    3: "PÚBLICA MUNICIPAL",
    4: "PRIVADA COM FINS LUCRATIVOS",
    5: "PRIVADA SEM FINS LUCRATIVOS",
    6: "PRIVADA - PARTICULAR EM SENTIDO ESTRITO",
    7: "ESPECIAL",
    8: "PRIVADA COMUNITÁRIA",
    9: "PRIVADA CONFESSIONAL",
}

MAPA_GRAU_ACADEMICO_TEXTO = {
    "BACHARELADO": "BACHARELADO",
    "LICENCIATURA": "LICENCIATURA",
    "TECNOLÓGICO": "TECNOLÓGICO",
    "BACHARELADO INTERDISCIPLINAR": "BACHARELADO INTERDISCIPLINAR",
    "LICENCIATURA INTERDISCIPLINAR": "LICENCIATURA INTERDISCIPLINAR",
}

MAPA_MODALIDADE_ENSINO_TEXTO = {
    "EDUCAÇÃO PRESENCIAL": "PRESENCIAL",
    "PRESENCIAL": "PRESENCIAL",
    "EDUCAÇÃO A DISTÂNCIA": "EAD",
    "EDUCAÇÃO À DISTÂNCIA": "EAD",
    "A DISTÂNCIA": "EAD",
    "EAD": "EAD",
}

MAPA_CATEGORIA_ESCOLA_PRIVADA = {
    1: "PARTICULAR",
    2: "COMUNITÁRIA",
    3: "CONFESSIONAL",
    4: "FILANTRÓPICA",
}

MAPA_LOCALIZACAO_ESCOLA = {
    1: "URBANA",
    2: "RURAL",
}

MAPA_SITUACAO_FUNCIONAMENTO_ESCOLA = {
    1: "EM ATIVIDADE",
    2: "PARALISADA",
    3: "EXTINTA NO ANO DO CENSO",
    4: "EXTINTA EM ANOS ANTERIORES",
}

# ==============================================================================
# ÁREA DE CONHECIMENTO — Classificação CNPq (curso → grande área)
# Ordenar do mais específico para o mais genérico dentro de cada bloco
# para que o algoritmo de match por substring funcione corretamente.
# ==============================================================================
DE_PARA_AREA_CONHECIMENTO = {
    # CIÊNCIAS SOCIAIS APLICADAS
    "ADMINISTRAÇÃO": "CIÊNCIAS SOCIAIS APLICADAS",
    "DIREITO": "CIÊNCIAS SOCIAIS APLICADAS",
    "CONTÁBEIS": "CIÊNCIAS SOCIAIS APLICADAS",
    "CONTABILIDADE": "CIÊNCIAS SOCIAIS APLICADAS",
    "ARQUITETURA": "CIÊNCIAS SOCIAIS APLICADAS",
    "URBANISMO": "CIÊNCIAS SOCIAIS APLICADAS",
    "JORNALISMO": "CIÊNCIAS SOCIAIS APLICADAS",
    "COMUNICAÇÃO": "CIÊNCIAS SOCIAIS APLICADAS",
    "PUBLICIDADE": "CIÊNCIAS SOCIAIS APLICADAS",
    "PROPAGANDA": "CIÊNCIAS SOCIAIS APLICADAS",
    "MARKETING": "CIÊNCIAS SOCIAIS APLICADAS",
    "ECONOMIA": "CIÊNCIAS SOCIAIS APLICADAS",
    "ECONÔMICA": "CIÊNCIAS SOCIAIS APLICADAS",
    "RELAÇÕES PÚBLICAS": "CIÊNCIAS SOCIAIS APLICADAS",
    "RELAÇÕES INTERNACIONAIS": "CIÊNCIAS SOCIAIS APLICADAS",
    "SERVIÇO SOCIAL": "CIÊNCIAS SOCIAIS APLICADAS",
    "TURISMO": "CIÊNCIAS SOCIAIS APLICADAS",
    "HOTELARIA": "CIÊNCIAS SOCIAIS APLICADAS",
    "EVENTOS": "CIÊNCIAS SOCIAIS APLICADAS",
    "GASTRONOMIA": "CIÊNCIAS SOCIAIS APLICADAS",
    "BIBLIOTECONOMIA": "CIÊNCIAS SOCIAIS APLICADAS",
    "MUSEOLOGIA": "CIÊNCIAS SOCIAIS APLICADAS",
    "ARQUIVOLOGIA": "CIÊNCIAS SOCIAIS APLICADAS",
    "SECRETARIADO": "CIÊNCIAS SOCIAIS APLICADAS",
    "COMÉRCIO": "CIÊNCIAS SOCIAIS APLICADAS",
    "LOGÍSTICA": "CIÊNCIAS SOCIAIS APLICADAS",
    "PROCESSOS GERENCIAIS": "CIÊNCIAS SOCIAIS APLICADAS",
    "RECURSOS HUMANOS": "CIÊNCIAS SOCIAIS APLICADAS",
    "FINANÇAS": "CIÊNCIAS SOCIAIS APLICADAS",
    "RADIALISMO": "CIÊNCIAS SOCIAIS APLICADAS",
    "RÁDIO E TV": "CIÊNCIAS SOCIAIS APLICADAS",
    "MÍDIA": "CIÊNCIAS SOCIAIS APLICADAS",
    "COACHING": "CIÊNCIAS SOCIAIS APLICADAS",
    "SEGURANÇA PÚBLICA": "CIÊNCIAS SOCIAIS APLICADAS",
    "NEGÓCIOS": "CIÊNCIAS SOCIAIS APLICADAS",
    "GESTÃO": "CIÊNCIAS SOCIAIS APLICADAS",  # Catch-all para tecnólogos de gestão
    # CIÊNCIAS HUMANAS
    "PSICOLOGIA": "CIÊNCIAS HUMANAS",
    "PEDAGOGIA": "CIÊNCIAS HUMANAS",
    "HISTÓRIA": "CIÊNCIAS HUMANAS",
    "GEOGRAFIA": "CIÊNCIAS HUMANAS",
    "FILOSOFIA": "CIÊNCIAS HUMANAS",
    "SOCIOLOGIA": "CIÊNCIAS HUMANAS",
    "ANTROPOLOGIA": "CIÊNCIAS HUMANAS",
    "TEOLOGIA": "CIÊNCIAS HUMANAS",
    "ARQUEOLOGIA": "CIÊNCIAS HUMANAS",
    "CIÊNCIA POLÍTICA": "CIÊNCIAS HUMANAS",
    "POLÍTICAS PÚBLICAS": "CIÊNCIAS HUMANAS",
    "CIÊNCIAS SOCIAIS": "CIÊNCIAS HUMANAS",
    "PSICANALISE": "CIÊNCIAS HUMANAS",
    "PSICOPEDAGOGIA": "CIÊNCIAS HUMANAS",
    "EDUCACIONAL": "CIÊNCIAS HUMANAS",
    "EDUCAÇÃO": "CIÊNCIAS HUMANAS",  # Catch-all
    # CIÊNCIAS AGRÁRIAS
    "ENGENHARIA FLORESTAL": "CIÊNCIAS AGRÁRIAS",  # Maior que Engenharia
    "ENGENHARIA DE PESCA": "CIÊNCIAS AGRÁRIAS",  # Maior que Engenharia
    "ENGENHARIA AGRÍCOLA": "CIÊNCIAS AGRÁRIAS",  # Maior que Engenharia
    "MEDICINA VETERINÁRIA": "CIÊNCIAS AGRÁRIAS",  # Maior que Medicina
    "VETERINÁRIA": "CIÊNCIAS AGRÁRIAS",
    "AGRONOMIA": "CIÊNCIAS AGRÁRIAS",
    "ZOOTECNIA": "CIÊNCIAS AGRÁRIAS",
    "AGRÍCOLA": "CIÊNCIAS AGRÁRIAS",
    "AGRONEGÓCIO": "CIÊNCIAS AGRÁRIAS",
    "AGROECOLOGIA": "CIÊNCIAS AGRÁRIAS",
    "AGROPECUÁRIA": "CIÊNCIAS AGRÁRIAS",
    "AGRICULTURA": "CIÊNCIAS AGRÁRIAS",
    "AQUICULTURA": "CIÊNCIAS AGRÁRIAS",
    "AQÜICULTURA": "CIÊNCIAS AGRÁRIAS",
    "ALIMENTOS": "CIÊNCIAS AGRÁRIAS",
    "AGRO": "CIÊNCIAS AGRÁRIAS",
    # CIÊNCIAS DA SAÚDE
    "MEDICINA": "CIÊNCIAS DA SAÚDE",
    "ENFERMAGEM": "CIÊNCIAS DA SAÚDE",
    "ODONTOLOGIA": "CIÊNCIAS DA SAÚDE",
    "EDUCAÇÃO FÍSICA": "CIÊNCIAS DA SAÚDE",  # Maior que Educação (Humanas)
    "FISIOTERAPIA": "CIÊNCIAS DA SAÚDE",
    "NUTRIÇÃO": "CIÊNCIAS DA SAÚDE",
    "FARMÁCIA": "CIÊNCIAS DA SAÚDE",
    "BIOMEDICINA": "CIÊNCIAS DA SAÚDE",
    "FONOAUDIOLOGIA": "CIÊNCIAS DA SAÚDE",
    "TERAPIA OCUPACIONAL": "CIÊNCIAS DA SAÚDE",
    "ESTÉTICA": "CIÊNCIAS DA SAÚDE",
    "COSMETOLOGIA": "CIÊNCIAS DA SAÚDE",
    "COSMÉTIC": "CIÊNCIAS DA SAÚDE",
    "RADIOLOGIA": "CIÊNCIAS DA SAÚDE",
    "GERONTOLOGIA": "CIÊNCIAS DA SAÚDE",
    "PODOLOGIA": "CIÊNCIAS DA SAÚDE",
    "ACUPUNTURA": "CIÊNCIAS DA SAÚDE",
    "QUIROPRAXIA": "CIÊNCIAS DA SAÚDE",
    "NATUROLOGIA": "CIÊNCIAS DA SAÚDE",
    "MASSOTERAPIA": "CIÊNCIAS DA SAÚDE",
    "MUSICOTERAPIA": "CIÊNCIAS DA SAÚDE",
    "SAÚDE": "CIÊNCIAS DA SAÚDE",
    # ENGENHARIAS
    "ENGENHARIA": "ENGENHARIAS",
    "MECATRÔNICA": "ENGENHARIAS",
    "AUTOMAÇÃO": "ENGENHARIAS",
    "CONSTRUÇÃO CIVIL": "ENGENHARIAS",
    "SEGURANÇA DO TRABALHO": "ENGENHARIAS",
    "AERONÁUTICA": "ENGENHARIAS",
    "AGRIMENSURA": "ENGENHARIAS",
    # CIÊNCIAS EXATAS E DA TERRA
    "SISTEMAS DE INFORMAÇÃO": "CIÊNCIAS EXATAS E DA TERRA",
    "CIÊNCIA DA COMPUTAÇÃO": "CIÊNCIAS EXATAS E DA TERRA",
    "MATEMÁTICA": "CIÊNCIAS EXATAS E DA TERRA",
    "FÍSICA": "CIÊNCIAS EXATAS E DA TERRA",
    "QUÍMICA": "CIÊNCIAS EXATAS E DA TERRA",
    "ESTATÍSTICA": "CIÊNCIAS EXATAS E DA TERRA",
    "ASTRONOMIA": "CIÊNCIAS EXATAS E DA TERRA",
    "GEOLOGIA": "CIÊNCIAS EXATAS E DA TERRA",
    "GEOFÍSICA": "CIÊNCIAS EXATAS E DA TERRA",
    "METEOROLOGIA": "CIÊNCIAS EXATAS E DA TERRA",
    "OCEANOGRAFIA": "CIÊNCIAS EXATAS E DA TERRA",
    "COMPUTAÇÃO": "CIÊNCIAS EXATAS E DA TERRA",
    "INFORMÁTICA": "CIÊNCIAS EXATAS E DA TERRA",
    "DATA SCIENCE": "CIÊNCIAS EXATAS E DA TERRA",
    "CIÊNCIA DE DADOS": "CIÊNCIAS EXATAS E DA TERRA",
    "BIG DATA": "CIÊNCIAS EXATAS E DA TERRA",
    "INTELIGÊNCIA ARTIFICIAL": "CIÊNCIAS EXATAS E DA TERRA",
    "MACHINE LEARNING": "CIÊNCIAS EXATAS E DA TERRA",
    "CIBERSEGURANÇA": "CIÊNCIAS EXATAS E DA TERRA",
    "DEFESA CIBERNÉTICA": "CIÊNCIAS EXATAS E DA TERRA",
    "ANÁLISE E DESENVOLVIMENTO": "CIÊNCIAS EXATAS E DA TERRA",
    "DESENVOLVIMENTO DE SISTEMAS": "CIÊNCIAS EXATAS E DA TERRA",
    "DESENVOLVIMENTO DE SOFTWARE": "CIÊNCIAS EXATAS E DA TERRA",
    "SOFTWARE": "CIÊNCIAS EXATAS E DA TERRA",
    "REDES DE COMPUTADORES": "CIÊNCIAS EXATAS E DA TERRA",
    "BANCO DE DADOS": "CIÊNCIAS EXATAS E DA TERRA",
    "JOGOS DIGITAIS": "CIÊNCIAS EXATAS E DA TERRA",
    # CIÊNCIAS BIOLÓGICAS
    "CIÊNCIAS BIOLÓGICAS": "CIÊNCIAS BIOLÓGICAS",
    "BIOLOGIA": "CIÊNCIAS BIOLÓGICAS",
    "BIOTECNOLOGIA": "CIÊNCIAS BIOLÓGICAS",
    "BIOQUÍMICA": "CIÊNCIAS BIOLÓGICAS",
    "ECOLOGIA": "CIÊNCIAS BIOLÓGICAS",
    "MEIO AMBIENTE": "CIÊNCIAS BIOLÓGICAS",
    "AMBIENTAL": "CIÊNCIAS BIOLÓGICAS",
    # LINGUÍSTICA, LETRAS E ARTES
    "LETRAS": "LINGUÍSTICA, LETRAS E ARTES",
    "DESIGN": "LINGUÍSTICA, LETRAS E ARTES",
    "ARTES": "LINGUÍSTICA, LETRAS E ARTES",
    "ARTE": "LINGUÍSTICA, LETRAS E ARTES",
    "MÚSICA": "LINGUÍSTICA, LETRAS E ARTES",
    "DANÇA": "LINGUÍSTICA, LETRAS E ARTES",
    "TEATRO": "LINGUÍSTICA, LETRAS E ARTES",
    "CINEMA": "LINGUÍSTICA, LETRAS E ARTES",
    "AUDIOVISUAL": "LINGUÍSTICA, LETRAS E ARTES",
    "TRADUÇÃO": "LINGUÍSTICA, LETRAS E ARTES",
    "TRADUTOR": "LINGUÍSTICA, LETRAS E ARTES",
    "LIBRAS": "LINGUÍSTICA, LETRAS E ARTES",
    "FOTOGRAFIA": "LINGUÍSTICA, LETRAS E ARTES",
    "MODA": "LINGUÍSTICA, LETRAS E ARTES",
    "LINGUÍSTICA": "LINGUÍSTICA, LETRAS E ARTES",
    # OUTROS (MILITAR)
    "MILITAR": "CIÊNCIAS MILITARES",
    "DEFESA": "CIÊNCIAS MILITARES",
}

MAPA_AREA_AVALIACAO_POR_CODIGO = {
    702: "MATEMÁTICA",
    803: "JORNALISMO",
    804: "PUBLICIDADE E PROPAGANDA",
    904: "LETRAS-PORTUGUÊS",
    905: "LETRAS-PORTUGUÊS E INGLÊS",
    906: "LETRAS-PORTUGUÊS E ESPANHOL",
    1402: "FÍSICA",
    1501: "QUÍMICA",
    1502: "QUÍMICA",
    1601: "CIÊNCIAS BIOLÓGICAS",
    1602: "CIÊNCIAS BIOLÓGICAS",
    2001: "PEDAGOGIA",
    2401: "HISTÓRIA",
    2402: "HISTÓRIA",
    2501: "ARTES VISUAIS",
    3001: "GEOGRAFIA",
    3002: "GEOGRAFIA",
    3201: "FILOSOFIA",
    3202: "FILOSOFIA",
    3501: "EDUCAÇÃO FÍSICA",
    3502: "EDUCAÇÃO FÍSICA",
    4004: "CIÊNCIA DA COMPUTAÇÃO",
    4005: "CIÊNCIA DA COMPUTAÇÃO",
    4301: "MÚSICA",
    5401: "CIÊNCIAS SOCIAIS",
    5402: "CIÊNCIAS SOCIAIS",
    6407: "LETRAS - INGLÊS",
}

# ==============================================================================
# MUNICÍPIOS — Correções Censo INEP → base de geolocalização
# ==============================================================================
CORRECAO_MUNICIPIOS = {
    "SAO TOME DAS LETRAS": "SAO THOME DAS LETRAS",  # MG
    "FLORINEA": "FLORINIA",  # SP
    "MUQUEM DO SAO FRANCISCO": "MUQUEM DE SAO FRANCISCO",  # BA
    "SANTO ANTONIO DE LEVERGER": "SANTO ANTONIO DO LEVERGER",  # MT
    "SANTA TEREZINHA": "SANTA TERESINHA",  # BA (Z -> S)
    "PALMEIRA DO INDIOS": "PALMEIRA DOS INDIOS",
    "SAO MIGUEL DO CAMPOS": "SAO MIGUEL DOS CAMPOS",
    "SAO JOAO DO PATOS": "SAO JOAO DOS PATOS",
    "BELEM DE SAO FRANCISCO": "BELEM DO SAO FRANCISCO",
    "JABOATAO DO GUARARAPES": "JABOATAO DOS GUARARAPES",
    "SAO JOSE DO PINHAIS": "SAO JOSE DOS PINHAIS",
    "ANGRA DO REIS": "ANGRA DOS REIS",
    "PAU DO FERROS": "PAU DOS FERROS",
    "SANTANA DO LIVRAMENTO": "SANT ANA DO LIVRAMENTO",
    "SAO MIGUEL D OESTE": "SAO MIGUEL DO OESTE",
}

# ==============================================================================
# CORES
# ==============================================================================
# Paleta visual por sigla de IES
REGRA_CORES_IES = {
    "AMAN": {"cor": "Verde Oliva", "hex": "#556B2F"},
    "CEFET/RJ": {"cor": "Azul Escuro", "hex": "#0D47A1"},
    "DOCTUM": {"cor": "Azul Marinho", "hex": "#003B71"},
    "EDUCABRASIL": {"cor": "Amarelo Mostarda", "hex": "#F57F17"},
    "ENSIN.E": {"cor": "Verde Maçã", "hex": "#6FBF43"},
    "FACULDADE ANHANGUERA DE NOVA IGUAÇU": {"cor": "Laranja Escuro", "hex": "#E65100"},
    "FACULDADE DE CIÊNCIAS JURÍDICAS DE JUIZ DE FORA": {
        "cor": "Cinza Chumbo",
        "hex": "#37474F",
    },
    "FACULDADE FERNANDA BICCHIERI": {"cor": "Coral", "hex": "#FF7F50"},
    "FAETERJ B.MANSA": {"cor": "Azul Metálico", "hex": "#4682B4"},
    "FAETERJ PETRÓPOLIS": {"cor": "Azul Metálico Claro", "hex": "#5C93C4"},
    "FAMIPE": {"cor": "Cinza Azulado", "hex": "#607D8B"},
    "FASF": {"cor": "Vinho", "hex": "#880E4F"},
    "FCMS": {"cor": "Verde Garrafa", "hex": "#006838"},
    "FCMS/JF": {
        "cor": "Verde Garrafa",
        "hex": "#006838",
    },  # Mantive a cor da FCMS original
    "FER": {"cor": "Rosa Choque", "hex": "#E91E63"},
    "FFCLDB": {"cor": "Bege Escuro", "hex": "#BCAAA4"},
    "FIVJ": {"cor": "Terracota", "hex": "#E2725B"},
    "FJF": {"cor": "Violeta", "hex": "#8A2BE2"},
    "FMG": {"cor": "Ouro", "hex": "#FFD700"},
    "FMP": {"cor": "Verde Água", "hex": "#4DB6AC"},
    "FMS": {"cor": "Azul Cadete", "hex": "#5F9EA0"},
    "FPJF": {"cor": "Púrpura", "hex": "#6A1B9A"},
    "IFRJ": {"cor": "Verde Bandeira", "hex": "#009688"},
    "IFSEMG": {"cor": "Verde Escuro", "hex": "#1B5E20"},
    "ITF": {"cor": "Prata", "hex": "#B0BEC5"},
    "LNCC": {"cor": "Ciano Escuro", "hex": "#008B8B"},
    "SOBERANA": {"cor": "Roxo", "hex": "#9C27B0"},
    "SUPREMA": {"cor": "Verde Garrafa", "hex": "#006838"},
    "UBM": {"cor": "Azul Royal", "hex": "#1565C0"},
    "UCP": {"cor": "Bordô", "hex": "#800000"},
    "UERJ": {"cor": "Azul Cobalto", "hex": "#0047AB"},
    "UFF": {"cor": "Azul Marinho Claro", "hex": "#1976D2"},
    "UFJF": {"cor": "Vermelho Escuro", "hex": "#C62828"},
    "UFRRJ": {"cor": "Verde Musgo", "hex": "#33691E"},
    "UGB": {"cor": "Verde Limão", "hex": "#CDDC39"},
    "UNESA": {"cor": "Azul Petróleo", "hex": "#006064"},
    "UNIABEU": {"cor": "Turquesa Escuro", "hex": "#0097A6"},
    "UNIACADEMIA": {"cor": "Índigo", "hex": "#3F51B5"},
    "UNICSUM": {"cor": "Laranja", "hex": "#FF9800"},
    "UNIDOMBOSCO-RJ": {"cor": "Marrom", "hex": "#795548"},
    "UNIFAA": {"cor": "Esmeralda", "hex": "#00A886"},
    "UNIFASE": {"cor": "Abóbora", "hex": "#FF6F00"},
    "UNIFESO": {"cor": "Ciano", "hex": "#00BCD4"},
    "UNIFOA": {"cor": "Vermelho Tomate", "hex": "#F44336"},
    "UNIG": {"cor": "Azul Aço", "hex": "#4169E1"},
    "UNIGRANRIO": {"cor": "Laranja Claro", "hex": "#FFB74D"},
    "UNIPAC": {"cor": "Amarelo", "hex": "#FBC02D"},
    "UNIVERSO": {"cor": "Azul Celeste", "hex": "#039BE5"},
    "UNIVASSOURAS": {"cor": "Grená", "hex": "#B71C1C"},
}

# Paleta visual por grande área de conhecimento
REGRA_CORES_CURSOS = {
    "CIÊNCIAS DA SAÚDE": {"cor": "Esmeralda", "hex": "#00C853"},
    "CIÊNCIAS SOCIAIS APLICADAS": {"cor": "Azul Safira", "hex": "#0D47A1"},
    "CIÊNCIAS HUMANAS": {"cor": "Laranja Energia", "hex": "#FF6F00"},
    "CIÊNCIAS EXATAS E DA TERRA": {"cor": "Azul Celeste", "hex": "#03A9F4"},
    "ENGENHARIAS": {"cor": "Rubi", "hex": "#D32F2F"},
    "CIÊNCIAS AGRÁRIAS": {"cor": "Lima", "hex": "#AFB42B"},
    "CIÊNCIAS BIOLÓGICAS": {"cor": "Verde Água", "hex": "#009688"},
    "LINGUÍSTICA, LETRAS E ARTES": {"cor": "Rosa", "hex": "#E91E63"},
    "CIÊNCIAS MILITARES": {"cor": "Verde Oliva", "hex": "#33691E"},
    "OUTROS": {"cor": "Cinza Escuro", "hex": "#757575"},
}
