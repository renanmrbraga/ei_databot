---
id: educacao_superior
area: educacao
categoria: regras_de_negocio
versao: "1.0.1"
status: revisao
fonte_dados: INEP/Censo da Educação Superior
periodo_configurado: "2018-2024"
tabelas_principais:
  - gold.fact_educacao_superior
  - gold.fact_educacao_superior_turno
ultima_revisao_documental: "2026-11-03"
---

# Educação Superior — Regras de negócio do EI DataBot

> **Status:** primeira versão elaborada a partir dos módulos Python do ETL fornecidos para análise. Regras classificadas como **[ETL]** são observadas no código; **[INEP]** têm respaldo nas referências oficiais listadas ao final; **[PENDENTE]** requerem confirmação metodológica, testes com dados ou decisão de negócio. Este documento não comprova que todas as estatísticas produzidas coincidam com as publicações agregadas do Inep.
>
> **Escopo:** indicadores do Censo da Educação Superior. Conceito Enade, CPC, IDD e IGC alimentam dimensões compartilhadas, mas suas métricas e formas de agregação serão documentadas separadamente em `docs/avaliacoes.md`.

## 1. Origem, cobertura e fluxo dos dados

**[ES-FON-001 | ETL]** As fontes principais são os arquivos anuais de cadastro de cursos e de IES do Censo da Educação Superior (Inep). A camada Bronze lê CSVs separados por ponto e vírgula, tenta `latin1` e `utf-8-sig`, harmoniza cabeçalhos de acordo com os contratos do projeto e grava Parquet. O alias `CO_CINE_ROTULO2 → CO_CINE_ROTULO` é aceito para cursos.

**[ES-FON-002 | ETL]** O período **configurado** para cursos e IES é **2018 a 2024, inclusive** (`range(2018, 2025)`). Trata-se da cobertura esperada pelo código, não de uma garantia de que toda combinação de instituição, curso, município e modalidade exista em todos os anos. A versão mais recente publicada pelo Inep não se torna automaticamente disponível no Gold: é preciso atualizar o ETL e suas fontes.

**[ES-FON-003 | ETL]** Linhagem operacional:

```text
Microdados anuais de cursos (INEP) ──→ bronze_superior_cursos
                                   └──→ silver_superior_cursos
                                        ├──→ gold.dim_curso_superior
                                        ├──→ gold.fact_educacao_superior
                                        └──→ gold.fact_educacao_superior_turno

Microdados anuais de IES (INEP) ──────→ bronze_superior_ies
                                   └──→ silver_superior_ies
                                        └──→ gold.dim_ies

Referência geográfica (geo.csv) ──────→ silver_geo
                                   └──→ gold.dim_localidade

Anos das fontes Silver ───────────────→ gold.dim_calendario
```

`dim_ies` e `dim_curso_superior` também admitem candidatos originários de bases de avaliação, de modo que **nem toda entidade dessas dimensões necessariamente aparece na fato censitária**.

**[ES-FON-004 | INEP]** O Censo da Educação Superior coleta informações sobre instituições, cursos, modalidades, vagas, candidatos, ingressantes, matrículas e concluintes. O modelo do projeto é uma camada analítica construída sobre parte desses dados; não é uma reprodução integral de todos os arquivos e variáveis originais do Inep.

## 2. Modelo dimensional e granularidade

| Tabela                              | Granularidade / identidade analítica                                                             | Uso principal                                                            |
| ----------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| `gold.fact_educacao_superior`       | **IES × curso analítico × localidade analítica × ano**                                           | Totais anuais e recortes por instituição, curso, modalidade e localidade |
| `gold.fact_educacao_superior_turno` | **IES × curso analítico × localidade × ano × turno**                                             | Comparação de DIURNO e NOTURNO **somente no presencial**                 |
| `gold.dim_ies`                      | Uma linha por `codigo_ies`                                                                       | Identidade institucional e atributos cadastrais mais recentes            |
| `gold.dim_curso_superior`           | Uma linha por `(tipo_curso, curso_base, nome_curso, grau_curso, modalidade_curso, nivel_ensino)` | Classificação analítica de cursos; não equivale a um código e-MEC único  |
| `gold.dim_localidade`               | Uma linha por `codigo_municipio`, incluindo sentinela EAD                                        | Município da oferta presencial, coordenadas e distância de referência    |
| `gold.dim_calendario`               | Uma linha por `ano` disponível nas fontes Silver                                                 | Agrupamento temporal anual                                               |

**[ES-GRA-001 | ETL]** `fact_educacao_superior` consolida as linhas da Silver por `id_ies`, `id_curso_superior`, `id_localidade` e `ano`. O `codigo_curso_referencia` técnico **não participa** da chave da fato; diferentes códigos de curso que se enquadram na mesma identidade analítica podem ser somados.

**[ES-GRA-002 | ETL]** `fact_educacao_superior_turno` usa a mesma chave, acrescida de `turno_curso ∈ {DIURNO, NOTURNO}`. Ela verticaliza seis indicadores de turno, descarta linhas sem qualquer indicador positivo para o turno e agrega novamente nessa chave.

**[ES-GRA-003 | ETL]** O campo `id_calendario` nas duas fatos é preenchido com o próprio `ano` inteiro. A dimensão de calendário reúne anos de **várias** fontes Silver; a existência de um ano nessa dimensão não comprova a existência de dados de educação superior naquele ano.

**[ES-GRA-004 | ETL]** As chaves `id_ies`, `id_curso_superior` e `id_localidade` são identificadores substitutos produzidos pelo ETL. Para identidade de negócio use `codigo_ies`, a combinação analítica de curso e `codigo_municipio`, respectivamente; **não** trate IDs substitutos como identificadores públicos estáveis entre reconstruções completas.

### Relacionamentos autorizados

| Fato                                | Dimensão             | Predicado                                   |
| ----------------------------------- | -------------------- | ------------------------------------------- |
| Ambas as fatos de educação superior | `dim_ies`            | `f.id_ies = i.id_ies`                       |
| Ambas                               | `dim_curso_superior` | `f.id_curso_superior = c.id_curso_superior` |
| Ambas                               | `dim_localidade`     | `f.id_localidade = l.id_localidade`         |
| Ambas                               | `dim_calendario`     | `f.id_calendario = d.id_calendario`         |

**[ES-JOIN-001 | ETL]** A construção das fatos valida unicidade das chaves de lookup e falha quando um registro não encontra IES, curso ou localidade correspondentes. As ocorrências são enviadas à auditoria do pipeline. Esse comportamento protege as chaves na transformação, mas a consistência após a carga SQL deve continuar sendo validada.

**[ES-JOIN-002 | REGRA]** Em consultas de indicadores, parta da **fato correta**, faça joins somente com dimensões de cardinalidade 1:N em relação à fato (uma dimensão para muitas linhas da fato) e não una as duas fatos diretamente pelas chaves de dimensão. A união entre fatos pode gerar multiplicação de valores; agregue cada uma separadamente antes de comparar.

## 3. Dimensões e classificação dos dados

### 3.1 Instituições de Educação Superior (IES)

**[ES-IES-001 | ETL]** `dim_ies` representa cada instituição pela informação do **último ano de Censo disponível para aquele `codigo_ies`**. Ela preserva `ano_primeiro_censo`, `ano_ultimo_censo` e `anos_censo`, mas não mantém uma versão histórica anual de nome, mantenedora, organização ou categoria. É uma dimensão de **estado mais recente**, não um histórico tipo 2 (SCD2).

**[ES-IES-002 | ETL]** `tipo_ies` é uma **classificação simplificada criada pelo projeto**, derivada de `categoria_administrativa`, com valores `Pública`, `Particular` e `Não informado`. A classificação oficial mais específica permanece em `categoria_administrativa`. Ao mencionar os dados do Inep, prefira a categoria administrativa explicitamente disponível a atribuir ao Inep a simplificação do projeto.

**[ES-IES-003 | ETL]** IES que só apareçam em bases de avaliação podem constar na dimensão com `fonte_ies = 'AVALIACAO_INEP'` e sem dados de sede ou de histórico de censo. Portanto, `COUNT(*)` sobre `dim_ies` **não** é automaticamente o número de instituições que tiveram matrículas no ano analisado.

**[ES-IES-004 | REGRA]** Uma consulta histórica agrupada por `categoria_administrativa`, `organizacao_academica`, nome ou sede da IES usa a **classificação cadastral mais recente**. Não afirme que esses atributos descreviam necessariamente a instituição em cada ano anterior. Para uma classificação histórica verdadeira, consulte a Silver por ano ou implemente uma dimensão histórica.

### 3.2 Cursos e modalidades

**[ES-CUR-001 | ETL]** A Silver prioriza `nome_curso` (após limpeza) e, quando ausente/vazio, usa `nome_cine` como `nome_curso_referencia`. Para código de referência, prioriza `codigo_curso` e, se ausente, `codigo_cine`; registra o tipo de código como `EMEC`, `CINE` ou `NAO INFORMADO`.

**[ES-CUR-002 | ETL]** A dimensão analítica normaliza nome, grau e modalidade. `curso_base` e `tipo_curso` são classificações internas baseadas em mapeamentos textuais (`DE_PARA_AREA_CONHECIMENTO`), com categoria residual `OUTROS`. **Não equivalem automaticamente à classificação oficial CINE ou a cursos individualizados do e-MEC.**

**[ES-CUR-003 | ETL]** Modalidades mapeadas por código: `1 = PRESENCIAL`, `2 = EAD`. Códigos diferentes caem em `OUTRA`. Graus conhecidos incluem bacharelado, licenciatura, tecnológico, bacharelado interdisciplinar e licenciatura interdisciplinar; os demais tornam-se `OUTRO`. O nível vem de código conhecido (`GRADUAÇÃO` ou `SEQUENCIAL`), com lógica de fallback para `GRADUAÇÃO`/`OUTROS`.

**[ES-CUR-004 | REGRA]** Para contar **categorias analíticas de curso**, utilize `COUNT(DISTINCT id_curso_superior)` com os filtros e a fato pertinentes. Isso **não mede** a quantidade de códigos de curso e-MEC nem necessariamente o número oficial de ofertas/campi. Não traduza indiscriminadamente “quantos cursos existem” em contagem de códigos e-MEC.

### 3.3 Localidade, EAD e sede institucional

**[ES-GEO-001 | ETL — CRÍTICA]** Na fato geral, toda linha EAD é vinculada a uma localidade analítica sentinela: `codigo_municipio = -1`, com `municipio = 'EAD'`, `uf = 'EAD'`. Os municípios originais são preservados na Silver, **mas não na chave geográfica da fato Gold de cursos EAD**. O sentinela EAD não é município e não possui coordenadas reais.

**[ES-GEO-002 | REGRA — CRÍTICA]** Para perguntar sobre matrículas **em determinado município**, os registros da fato Gold georreferenciados naquele município **não incluem EAD**. Esclareça que a resposta reflete a oferta presencial identificada no município. **Não atribua matrículas EAD ao município com base na sede da IES ou no sentinela.** Uma distribuição municipal de EAD exigirá outra modelagem, com local de oferta/polo adequadamente validado.

**[ES-GEO-003 | ETL]** A fato de turnos considera **somente modalidade presencial** e usa a localidade real do cadastro de cursos. Os filtros por município devem identificar, de preferência, `codigo_municipio` ou `municipio + uf`, evitando cidades homônimas.

**[ES-GEO-004 | ETL]** `municipio_sede_ies` e `uf_sede_ies`, em `dim_ies`, representam a **sede institucional** e não necessariamente o local de oferta. Para pesquisa por município **da oferta**, utilize `dim_localidade`; para pesquisa por sede, utilize os campos de sede da `dim_ies`, indicando essa mudança de critério na resposta.

**[ES-GEO-005 | ETL]** `distancia_referencia_km` é uma estimativa geodésica arredondada por Haversine, calculada a partir de **Valença/RJ** (referência parametrizada). Para EAD o pipeline define o valor convencional `3600`, **que não representa uma distância real**. Distância nula significa coordenada não disponível. Não use a distância sentinela em médias, rankings de proximidade ou roteamento.

## 4. Indicadores e agregações autorizadas

Nas duas fatos, as métricas numéricas são campos de contagem consolidados por soma. **Aditividade espacial e institucional deve ser interpretada como contagem de registros/vínculos/eventos na granularidade original do Censo, não como contagem de pessoas únicas.** Em geral, indicadores de um mesmo ano podem ser agregados em dimensões compatíveis; **não se soma estoques anuais para obter um único estoque plurianual**.

### 4.1 Indicadores principais

| Regra      | Indicador de resposta                    | Campo na fato geral | Semântica operacional                                                                                                                                               |
| ---------- | ---------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ES-MET-001 | Matrículas                               | `matriculados`      | Soma da contagem `QT_MAT` harmonizada; vínculos de matrícula informados no censo, não CPFs ou estudantes únicos                                                     |
| ES-MET-002 | Ingressantes                             | `ingressantes`      | Soma de `QT_ING`; ingressos no ano de referência                                                                                                                    |
| ES-MET-003 | Concluintes                              | `concluintes`       | Soma de `QT_CONC`; conclusões/vínculos informados na referência                                                                                                     |
| ES-MET-004 | Vagas oferecidas                         | `vagas_total`       | Soma de `QT_VG_TOTAL`; vagas reportadas, não capacidade potencial nem total de estudantes                                                                           |
| ES-MET-005 | Inscritos / candidatos                   | `inscritos_total`   | Soma de `QT_INSCRITO_TOTAL`; inscrições/candidaturas registradas, não necessariamente pessoas únicas entre instituições/cursos                                      |
| ES-MET-006 | Rematriculados (**derivado do projeto**) | `rematriculados`    | Soma de `max(matriculados_linha − ingressantes_linha, 0)` calculada na Silver para cada linha; **não** é indicador original identificado diretamente nos microdados |

**[ES-MET-007 | REGRA]** Use o campo completo de cada indicador; não recrie `matriculados` somando outras categorias, nem estime `ingressantes` a partir de `inscritos_total`. Matrículas, ingressos e concluintes medem eventos/condições diferentes.

**[ES-MET-008 | ETL]** `rematriculados` é calculado **linha a linha na Silver** antes da agregação da fato. Em geral, `SUM(max(matriculados_linha − ingressantes_linha, 0))` pode ser diferente de `max(SUM(matriculados) − SUM(ingressantes), 0)`. Não substitua o valor persistido por uma subtração direta entre totais da Gold. Não apresente `rematriculados` como definição oficial Inep sem ressalva.

### 4.2 Demais indicadores presentes na fato geral

As famílias abaixo estão disponíveis como colunas do contrato Gold. O projeto agrega cada coluna de origem isoladamente, por soma; uma relação aritmética entre componentes **não está automaticamente garantida** pelo nome.

| Família                         | Colunas disponíveis                                                                                                                                                                                                                                                                                                                               |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Vagas por processo              | `vagas_novas`, `vagas_processo_seletivo`, `vagas_remanescentes`, `vagas_programa_especial`                                                                                                                                                                                                                                                        |
| Inscritos por processo          | `inscritos_vagas_novas`, `inscritos_processo_seletivo`, `inscritos_vagas_remanescentes`, `inscritos_programa_especial`                                                                                                                                                                                                                            |
| Ingressantes por forma/processo | `ingressantes_vagas_novas`, `ingressantes_vestibular`, `ingressantes_enem`, `ingressantes_avaliacao_seriada`, `ingressantes_selecao_simplificada`, `ingressantes_egressos`, `ingressantes_outro_tipo_selecao`, `ingressantes_processo_seletivo`, `ingressantes_vagas_remanescentes`, `ingressantes_programa_especial`, `ingressantes_outra_forma` |
| Financiamento/bolsas            | `ingressantes_fies`, `ingressantes_prouni_integral`, `ingressantes_prouni_parcial`, `matriculados_fies`, `matriculados_prouni_integral`, `matriculados_prouni_parcial`, `concluintes_fies`, `concluintes_prouni_integral`, `concluintes_prouni_parcial`                                                                                           |
| Situação acadêmica              | `trancados`, `desvinculados`, `transferidos`, `falecidos`                                                                                                                                                                                                                                                                                         |
| Origem escolar                  | `ingressantes_escola_publica`, `ingressantes_escola_privada`, `ingressantes_escola_nao_informada`, `matriculados_escola_publica`, `matriculados_escola_privada`, `matriculados_escola_nao_informada`, `concluintes_escola_publica`, `concluintes_escola_privada`, `concluintes_escola_nao_informada`                                              |

**[ES-MET-009 | REGRA]** Não some campos potencialmente sobrepostos (por exemplo, `ingressantes_enem` + `ingressantes_processo_seletivo`; Fies + Prouni; ou outras formas de ingresso) para fabricar um total, sem uma prova explícita de exclusividade e exaustividade. Para “total” utilize a coluna total correspondente.

**[ES-MET-010 | INEP]** “Vagas novas”, “vagas remanescentes”, “inscritos/candidatos” e “ingressantes” não são sinônimos. O Inep esclarece que inscrições em processos seletivos e ingressos efetivos são medidas distintas. A quantidade de candidatos pode superar a de vagas, e a de vagas não equivale à capacidade autorizada não ofertada.

### 4.3 Indicadores por turno

**[ES-TUR-001 | ETL]** A fato `fact_educacao_superior_turno` expõe somente seis métricas: `vagas_total`, `inscritos_total`, `ingressantes`, `matriculados`, `rematriculados`, `concluintes`. Cada valor origina-se das colunas homólogas com sufixo `_diurno` ou `_noturno` na Silver.

**[ES-TUR-002 | ETL]** O ETL verifica a conservação da **soma dos campos de origem DIURNO + NOTURNO** após verticalização e agregação. Isso **não comprova** que `soma(DIURNO + NOTURNO) = total geral` da fato principal em toda combinação; não force essa igualdade sem teste de reconciliação.

**[ES-TUR-003 | REGRA — CRÍTICA]** Não some os indicadores da fato de turno com os indicadores da fato geral para obter um “total” — ambos podem representar partes do mesmo universo. Para totais gerais prefira `fact_educacao_superior`; para divisão diurno/noturno use `fact_educacao_superior_turno`, indicando o recorte exclusivamente presencial.

**[ES-TUR-004 | ETL]** `oferta_curso` na dimensão de curso marca correspondência ao portfólio institucional configurado por **curso + grau + modalidade**. Na fato por turno, a marca considera também `turno_curso`. Esses campos são rótulos definidos pelo projeto e **não** prova de autorização regulatória, oferta corrente ou matrícula de uma instituição específica. A lógica é parametrizada em `CURSOS_PORTFOLIO_DETALHADO`.

## 5. Tratamento de nulos, ausências e qualidade

**[ES-DAD-001 | ETL — CRÍTICA]** Na agregação das métricas da fato geral, o ETL faz `cast(..., strict=False).fill_null(0).sum()`. Para métricas por turno ocorre preenchimento nulo com zero antes da soma. Assim, na Gold, **valor zero pode resultar de ausência/nulidade no dado original**. Não descreva automaticamente todos os zeros como observações explicitamente declaradas de zero pelo Inep.

**[ES-DAD-002 | REGRA]** A inexistência de linha para uma combinação de filtros significa **sem registro na base consultada**, não necessariamente zero matrículas. Uma consulta que retorne zero linhas deve ser comunicada como “não foram encontrados registros para o recorte” e não como “não houve matrículas”.

**[ES-DAD-003 | ETL]** O ETL valida contrato e tipos da Silver e das dimensões; valida unicidade das chaves; audita instituições com siglas compartilhadas; audita municípios presenciais sem correspondência geográfica; e falha no Gold quando um lookup obrigatório produz chave órfã.

**[ES-DAD-004 | PENDENTE]** Ainda não foram verificados no banco os totais anuais contra as Sinopses e os Resumos Técnicos do Inep, nem as diferenças de granularidade por modalidade/curso. Não declarar “validação estatística oficial concluída” antes desses testes.

**[ES-DAD-005 | REGRA]** É proibido interpolar anos ausentes, preencher séries temporais com zeros artificiais ou extrapolar 2025+ sem autorização expressa e método de previsão identificado. Se o ano solicitado estiver fora da cobertura carregada, informar a limitação.

## 6. Regras de consulta e cálculo

**[ES-ANA-001 | REGRA]** O backend deve escolher a tabela fato e a coluna do **catálogo de indicadores autorizado**, nunca executar SQL livre produzido pela LLM. Valores de filtros devem ser parâmetros SQL. O catálogo de schema é metadado técnico, e este documento é a referência semântica de uso.

**[ES-ANA-002 | REGRA]** Uma série anual de matrículas retorna `SUM(matriculados)` **separadamente por ano**. O número de matrículas de 2020 mais o de 2021 não deve ser apresentado como “matrículas em 2020–2021”, pois se trata de estoque observado em censos distintos. Para comparar anos, informe cada ano ou calcule variações.

**[ES-ANA-003 | REGRA]** Variação absoluta entre dois anos: `valor_final − valor_inicial`. Variação percentual: `(valor_final / valor_inicial − 1) × 100`, **somente** se o inicial for não nulo e diferente de zero. Caso contrário, declare variação percentual indefinida/não calculável. Não confunda variação acumulada no período com taxa anualizada.

**[ES-ANA-004 | REGRA]** Taxas derivadas, como “ingressantes por vaga” ou “inscritos por vaga”, são razões calculadas sobre **totais agregados no mesmo recorte** (`SUM(numerador) / SUM(denominador)`), nunca médias simples das razões de cada curso, a menos que o usuário peça explicitamente média por curso. Esse cálculo não implica taxa oficial do Inep. Divisão por zero é não calculável.

**[ES-ANA-005 | REGRA]** Sempre informe, ou torne recuperáveis na resposta, a fonte Censo Superior/Inep, ano(s), métrica, granularidade e filtros principais: município/UF, modalidade, curso, IES e turno, quando usados. Não associe as diferenças observadas a causas econômicas, políticas ou institucionais que não tenham suporte documental.

**[ES-ANA-006 | REGRA]** Contagem de IES ativas no recorte de matrículas deve ser calculada, por exemplo, como `COUNT(DISTINCT f.id_ies)` **com filtro correspondente na fato** e, se a intenção for “instituições com matrículas”, `f.matriculados > 0`. Contar linhas em `dim_ies` responde a outra pergunta (instituições catalogadas).

### 6.1 Exemplo SQL: série anual de matrículas presenciais em Volta Redonda/RJ

Consulta de exemplo **sem números pré-definidos**. Ela explicita o recorte presencial, pois a localização municipal dos cursos EAD não está disponível na Gold.

```sql
SELECT
    f.ano,
    SUM(f.matriculados)::bigint AS matriculas
FROM gold.fact_educacao_superior AS f
JOIN gold.dim_localidade AS l
    ON l.id_localidade = f.id_localidade
JOIN gold.dim_curso_superior AS c
    ON c.id_curso_superior = f.id_curso_superior
WHERE l.municipio_normalizado = %(municipio_normalizado)s
  AND l.uf = %(uf)s
  AND c.modalidade_curso = 'PRESENCIAL'
  AND f.ano BETWEEN %(ano_inicial)s AND %(ano_final)s
GROUP BY f.ano
ORDER BY f.ano;
```

Parâmetros esperados: `municipio_normalizado = 'VOLTA REDONDA'`, `uf = 'RJ'`, `ano_inicial = 2020`, `ano_final = 2023`. A saída deve ser descrita como **matrículas em cursos presenciais localizados no município**, e não como todas as matrículas de residentes do município.

### 6.2 Exemplos de perguntas suportadas semanticamente

1. “Como evoluíram as matrículas presenciais em Volta Redonda/RJ de 2020 a 2023?” → fato geral; `matriculados`; localidade da oferta; série anual.
2. “Quantos ingressantes teve a IES X em 2022, por grau?” → fato geral; `ingressantes`; filtro de IES e agrupamento por `grau_curso`.
3. “Qual a participação de cursos EAD nas matrículas registradas em 2024?” → fato geral; recorte **sem município**; `matriculados`; agregação por modalidade.
4. “Qual a diferença de ingressantes entre diurno e noturno para Medicina em 2023?” → fato de turno, presencial; métrica `ingressantes`; confirmar a classificação analítica usada para “Medicina”.
5. “Quantas IES apresentaram matrícula em 2021 no município X?” → contagem distinta de `id_ies` com matrícula positiva no município/ano, deixando claro que isso não inclui o universo EAD da região.

### 6.3 Pedidos que exigem ressalva ou recusa fundamentada

- “Quantos alunos **únicos (CPF)** estudaram na cidade?” → as fatos são agregadas, sem identificadores individuais; não é possível inferir pessoas únicas.
- “Quantos estudantes **EAD residiam** em Volta Redonda?” → residência não é medida pela dimensão localidade Gold.
- “Quantos polos EAD de cada município?” → a Gold não preserva essa granularidade.
- “Qual era a categoria administrativa da IES em 2019?” → a dimensão IES mantém o cadastro mais recente, não histórico por ano.
- “Quantos códigos e-MEC distintos de curso há?” → a dimensão curso tem identidade analítica consolidada; o código técnico não participa da fato.
- “Qual o total de matrículas somando 2018 a 2024?” → esclarecer que soma de estoques anuais não é número de estudantes únicos nem matrícula de um ano específico.
- “Por que as matrículas cresceram?” → a série demonstra variação; atribuição causal requer fontes adicionais.

## 7. Testes de consistência propostos

Estes testes são **recomendados**, não foram executados durante a elaboração do documento.

| ID         | Teste                                                                                  | Resultado esperado                                                                |
| ---------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| ES-VAL-001 | Comparar `COUNT(*)` da fato com a quantidade de chaves analíticas distintas            | Mesma quantidade (unicidade do grão)                                              |
| ES-VAL-002 | Verificar chaves órfãs das duas fatos para as quatro dimensões                         | Zero órfãos                                                                       |
| ES-VAL-003 | Consultar anos existentes em cada fato e confrontar com a cobertura 2018–2024          | Cobertura efetiva identificada, sem presumir ano presente por causa do calendário |
| ES-VAL-004 | Verificar que cursos EAD na fato geral usam a sentinela `codigo_municipio = -1`        | Todos os registros EAD vinculados à sentinela                                     |
| ES-VAL-005 | Verificar que fato de turno contém apenas `DIURNO`/`NOTURNO` e modalidade `PRESENCIAL` | Nenhum turno ou modalidade divergente                                             |
| ES-VAL-006 | Reconciliar a fato de turno com as colunas DIURNO/NOTURNO da Silver, por métrica e ano | Totais preservados conforme validação do ETL                                      |
| ES-VAL-007 | Testar se os campos de turno conciliam com totais gerais nos mesmos recortes           | Documentar as diferenças encontradas; **não presumir igualdade**                  |
| ES-VAL-008 | Comparar matrículas/ingressantes/concluintes anuais com publicações Inep equivalentes  | Diferenças documentadas por filtro, cobertura e unidade analítica                 |
| ES-VAL-009 | Verificar compatibilidade de todas as colunas citadas aqui com `rag.schema_catalog`    | Nenhuma referência técnica inexistente                                            |

## 8. Rastreabilidade das regras

| Área                                                               | Arquivo-fonte no repositório                                                                  |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| Período, caminhos, sentinela EAD, portfólio, orquestração          | `etl/educacao/config.py`                                                                      |
| Campos brutos, aliases, renomeações, schemas e chaves de unicidade | `etl/educacao/schema.py`                                                                      |
| Grau, modalidade, nível, categoria, normalização de áreas          | `etl/educacao/mapping.py`                                                                     |
| Leitura e consolidação Bronze                                      | `etl/educacao/common.py`; `bronze/bronze_superior_cursos.py`; `bronze/bronze_superior_ies.py` |
| Curso de referência, normalização, rematriculados, auditoria       | `etl/educacao/silver/silver_superior_cursos.py`                                               |
| Cadastro institucional Silver                                      | `etl/educacao/silver/silver_superior_ies.py`                                                  |
| Estado mais recente da IES                                         | `etl/educacao/gold/dim_ies.py`                                                                |
| Curso analítico e marcação de portfólio                            | `etl/educacao/gold/dim_curso_superior.py`                                                     |
| Localidade, sentinela e distâncias                                 | `etl/educacao/gold/dim_localidade.py`                                                         |
| Calendário                                                         | `etl/educacao/gold/dim_calendario.py`                                                         |
| Granularidade, métricas e relacionamentos da fato geral            | `etl/educacao/gold/fact_educacao_superior.py`                                                 |
| Verticalização, exclusão de zeros e conservação dos turnos         | `etl/educacao/gold/fact_educacao_superior_turno.py`                                           |

### Referências públicas de domínio

- Inep. **Microdados do Censo da Educação Superior**: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior
- Inep. **Apresentação do Censo da Educação Superior**: https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/censo-da-educacao-superior/
- Inep. **Perguntas frequentes sobre o Censo da Educação Superior** (especialmente definições de vagas novas, remanescentes, candidatos e ingressantes): https://www.gov.br/inep/pt-br/acesso-a-informacao/perguntas-frequentes/censo-da-educacao-superior
- Inep. **Resultados e documentos técnicos do Censo da Educação Superior**: https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/censo-da-educacao-superior/resultados

## 9. Pendências para aprovação da versão 1.0.2

**[ES-PEN-001]** Executar os testes ES-VAL-001 a ES-VAL-009 com os dados efetivamente carregados no PostgreSQL.

**[ES-PEN-002]** Confrontar definições dos campos de interesse com os dicionários de dados **das edições do Inep utilizadas**. O projeto harmoniza 2018–2024 e há diferenças históricas de arquivos e metadados; evitar generalizações sem validar a edição.

**[ES-PEN-003]** Decidir se as perguntas genéricas sobre “matrículas por município” serão automaticamente respondidas como **presenciais**, com ressalva explícita, ou se o backend exigirá escolha do usuário. Nunca incluir EAD municipal por imputação.

**[ES-PEN-004]** Validar como o produto distinguirá “cursos analíticos”, “ofertas de cursos” e “códigos de cursos e-MEC”, já que a Gold atual agrega códigos técnicos.

**[ES-PEN-005]** Validar a comunicação do indicador interno `rematriculados`, distinguindo-o das definições oficiais e de estoques históricos de veteranos.
