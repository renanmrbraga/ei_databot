---
id: educacao_basica
area: educacao
categoria: regras_de_negocio
versao: "0.9.1"
status: revisao_tecnica_pendente
fonte_dados: INEP/Censo Escolar da Educação Básica
periodo_configurado: "2018-2025"
tabelas_principais:
  - gold.fact_educacao_basica
  - gold.dim_escola
  - gold.dim_localidade
  - gold.dim_calendario
ultima_revisao_documental: "2026-11-03"
---

# Educação Básica — Regras de negócio do EI DataBot

> **Status:** revisão técnica 0.9.1 após inspeção de `bronze_ed_basica.py`, `silver_ed_basica.py`, `dim_escola.py` e `fact_educacao_basica.py`. Regras marcadas **[ETL]** são verificadas nesses módulos. O relatório de validação Gold apresentado pelo responsável registrou 46 OK, 5 alertas documentais e 0 erros; **não** substitui os testes metodológicos, a confrontação com os microdados do Inep nem a aprovação humana. Permanecem **[PENDENTE]** verificações de comparabilidade histórica e de valores.
>
> **Uso:** documentação para revisão humana e futura indexação por RAG. Os identificadores `EB-*` servem para rastreabilidade. O catálogo `rag.schema_catalog` é a fonte autoritativa da **estrutura física efetivamente publicada**; este documento descreve o significado e as restrições de uso.

## 1. Fontes, escopo e cobertura

**[EB-FON-001 | INEP]** O Censo Escolar é uma pesquisa anual, declaratória, coordenada pelo Inep e realizada com escolas públicas e privadas. Na primeira etapa, registra matrículas e informações de escolas, gestores, turmas, alunos e profissionais na data de referência; a segunda trata de movimento e rendimento ao fim do ano letivo. Este Gold documentado concentra-se em matrículas, **não** em aprovação, abandono ou Ideb. A descrição da fonte não comprova que cada edição dos arquivos usada no projeto tenha exatamente as mesmas variáveis.

**[EB-FON-002 | CONTRATO]** `config.py` configura `ANOS_ED_BASICA_HISTORICO = range(2018, 2025)` (2018–2024) e `ANO_ED_BASICA_ATUAL = 2025`. Trata-se da **cobertura prevista**, não de uma medição dos anos efetivamente carregados no Gold. `dim_calendario` pode conter anos provenientes de outros conjuntos de dados; consulte a fato para identificar cobertura real.

**[EB-FON-003 | CONTRATO]** O projeto prevê os seguintes padrões de arquivos em `data/raw/microdados/censo_escolar/`:

- `microdados_ed_basica_*.csv` — histórico de estabelecimentos;
- `Tabela_Escola_*.csv` — cadastro de escolas no formato mais recente;
- `Tabela_Matricula_*.csv` — indicadores de matrícula no formato mais recente.

Os contratos de fonte de 2025 e de 2018–2024 são distintos, mas o `SCHEMA_ED_BASICA_BRONZE` estabelece um **contrato unificado**. Campos específicos de edições posteriores podem estar ausentes nas anteriores e são descritos no contrato como `null` quando não disponíveis. A leitura/junção efetiva foi confirmada em `bronze_ed_basica.py`: 2018–2024 são lidos por ano com checagem de chave escola×ano; em 2025, `Tabela_Escola` é a base de um `left join` 1:1 com `Tabela_Matricula`, também por escola×ano. Uma matrícula sem cadastro bloqueia a execução, enquanto uma escola sem matrícula mantém medidas nulas.

**[EB-FON-004 | ETL]** A Bronze de educação básica possui leitura específica (`_ler_fonte_contratada`) que examina cabeçalhos, aplica aliases e seleciona campos disponíveis. Ela tenta separadores `;` e `,` com encodings configurados. Campos obrigatórios ausentes geram erro; campos opcionais ausentes são informados em log e projetados pelo contrato. Variáveis adicionais `QT_MAT_`/`QT_TRANSP_` fora do contrato geram alerta, mas **não** são incluídas automaticamente nas 54 métricas Gold.

### Linhagem técnica prevista

```text
Censo Escolar / Inep
├── microdados_ed_basica_*.csv (histórico)
├── Tabela_Escola_*.csv (cadastro)
└── Tabela_Matricula_*.csv (matrículas)
       ↓
bronze_ed_basica → silver_ed_basica
                       ├── dim_escola
                       └── fact_educacao_basica

Referências geográficas → dim_localidade
Anos das fontes          → dim_calendario
```

**[EB-FON-005 | ETL]** Em 2025, a Bronze valida chaves únicas em Escola e Matrícula, rejeita códigos de escola com matrícula sem cadastro e faz `left join` de Escola para Matrícula (1:1). As escolas sem registro na fonte de matrícula permanecem com indicadores nulos. Em 2018–2024, a Bronze valida a chave única em cada ano e consolida as partes. No histórico, além das chaves, `CO_MUNICIPIO`, `NO_ENTIDADE` e `QT_MAT_MED` são exigidos; em 2025 `QT_MAT_MED` é exigido na fonte Matrícula. A Silver confere novamente a chave escola×ano; a Gold preserva o número de linhas da Silver. Não há soma de etapas nem deduplicação silenciosa no caminho inspecionado.

## 2. Modelo dimensional e granularidade

| Objeto                      | Definição apoiada pelo contrato                                  | Ressalva                                                                       |
| --------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `gold.fact_educacao_basica` | Grão verificado: **escola × ano**; chave lógica `id_escola, ano` | Gold verifica chave única e igualdade de linhas com Silver                     |
| `gold.dim_escola`           | Uma identidade por `codigo_escola` (`CHAVE_ESCOLA_GOLD`)         | **Atributos do ano mais recente disponível por escola; não há histórico SCD2** |
| `gold.dim_localidade`       | Identidade por `codigo_municipio` (`CHAVE_LOCALIDADE_GOLD`)      | Identifica localidade da escola/fato, não residência individual                |
| `gold.dim_calendario`       | Um registro por `ano` (`CHAVE_CALENDARIO_GOLD`)                  | Ano cadastrado no calendário não garante observação na fato                    |

**[EB-GRA-001 | CONTRATO]** `SCHEMA_FACT_EDUCACAO_BASICA` contém as chaves `id_escola`, `id_localidade`, `id_calendario` e `ano`, além de **54 métricas inteiras de matrículas** (`Int32`). No PostgreSQL, a estrutura reportada tem 58 colunas (4 identificadores/tempo + 54 métricas).

**[EB-GRA-002 | CONTRATO]** As colunas obrigatórias da fato são somente `id_escola`, `id_localidade`, `id_calendario` e `ano`. As métricas são opcionais no contrato; um indicador `null` **não deve** ser interpretado automaticamente como zero.

**[EB-GRA-003 | CONTRATO]** Para as perguntas de educação básica, é seguro utilizar a chave de negócio `codigo_escola` para identificar estabelecimentos. `id_escola` é chave interna do modelo dimensional; não equivale a um identificador público do Inep.

**[EB-GRA-004 | ETL]** A fato usa `left join` com lookups únicos de escola (`codigo_escola`) e localidade (`codigo_municipio`), com validação de cardinalidade `m:1`. Chaves órfãs são auditadas e fazem a Gold falhar. `id_calendario` recebe o valor inteiro de `ano_censo`, tal como `ano`. A fato preserva todas as linhas da Silver (`fato.height == silver.height`) e valida unicidade de `(id_escola, ano)`. A existência dos vínculos de calendário também foi reportada no resultado de validação por constraints.

### Relacionamentos analíticos propostos

| Origem                 | Destino          | Condição                            |
| ---------------------- | ---------------- | ----------------------------------- |
| `fact_educacao_basica` | `dim_escola`     | `f.id_escola = e.id_escola`         |
| `fact_educacao_basica` | `dim_localidade` | `f.id_localidade = l.id_localidade` |
| `fact_educacao_basica` | `dim_calendario` | `f.id_calendario = d.id_calendario` |

**[EB-JOIN-001 | REGRA]** Parta sempre da fato para contabilizar matrículas. Não conte as linhas da dimensão Escola como “escolas com matrículas” em um ano, pois o cadastro pode incluir estabelecimentos sem ocorrência positiva da métrica ou de outros anos.

**[EB-JOIN-002 | REGRA]** Para as métricas da educação básica, não realize join direto entre esta fato e fatos de educação superior ou de avaliações. Se uma comparação entre conjuntos for exigida, agregue cada fato separadamente por dimensões comparáveis e valide previamente a equivalência dos conceitos.

## 3. Dimensões e classificações

### 3.1 Escola

**[EB-ESC-001 | CONTRATO]** `SCHEMA_DIM_ESCOLA` possui: `id_escola`, `codigo_escola`, `nome_escola`, `rede_escola`, `categoria_escola_privada`, `localizacao_escola`, `situacao_funcionamento`, `distrito_escola`, `subdistrito_escola`, `bairro_escola`, `endereco_escola`, `numero_escola`, `complemento_escola` e `cep_escola`.

**[EB-ESC-002 | CONTRATO]** Na Silver são previstos códigos de dependência administrativa (`codigo_dependencia`), categoria privada, localização e situação de funcionamento. A fato Gold **não contém essas classificações diretamente**; filtros por elas dependem do conteúdo publicado em `dim_escola`.

**[EB-ESC-003 | ETL — CRÍTICA]** `dim_escola.py` ordena a Silver por `codigo_escola, ano_censo` e utiliza `unique(subset=["codigo_escola"], keep="last")`. Logo, nome, rede, categoria privada, localização, situação de funcionamento e endereço representam **o registro do ano mais recente disponível para a escola**. A dimensão não é histórica SCD2. Um filtro de rede sobre matrículas de 2018 usa essa classificação mais recente, **não necessariamente a classificação de 2018**. Para análise histórica exata desses atributos, seria necessário usar a Silver por ano ou modelar outra dimensão.

**[EB-ESC-004 | REGRA]** A expressão “escolas públicas/privadas” exige classificação explícita e confiável de `rede_escola` ou do código de dependência. Não inferir rede pela palavra presente no nome da escola. Uma escola “sem informação” não deve ser colocada automaticamente na rede privada.

### 3.2 Localidade

**[EB-GEO-001 | CONTRATO]** `dim_localidade` utiliza `codigo_municipio` como identidade de negócio e disponibiliza município, UF, nome normalizado e atributos geográficos. No recorte municipal, preferir o **código IBGE do município** quando informado, para evitar homônimos.

**[EB-GEO-002 | REGRA]** Matrículas por município são matrículas associadas às **escolas localizadas no município na modelagem Gold**, e não uma estimativa dos estudantes residentes nesse município. Não inferir deslocamento escolar ou residência a partir da localização institucional.

**[EB-GEO-003 | ETL]** Na Gold, a localidade de cada linha escola×ano vem do `codigo_municipio` **da Silver daquele ano**, por `left join` com `dim_localidade`; código sem correspondência é auditado e bloqueia o processamento. A localização histórica do **registro de fato** pode, portanto, diferir do cadastro mais recente da `dim_escola`. O tratamento de reclassificações municipais na fonte e a comparabilidade histórica entre edições ainda exigem conferência documental.

### 3.3 Calendário e conceitos temporais

**[EB-TEM-001 | CONTRATO]** A referência temporal é `ano` da fato, derivado do Censo Escolar. Não confundir o ano de referência do Censo com o momento de processamento do ETL ou com o ano corrente da conversa.

**[EB-TEM-002 | INEP]** A matrícula inicial do Censo Escolar é apurada com base na data de referência anual, normalmente a última quarta-feira de maio. Logo, `matriculas_educacao_basica` é um **estoque observado em um ano censitário**; não corresponde a alunos únicos acumulados ao longo de vários anos.

## 4. Catálogo de indicadores da fato

**[EB-MET-001 | CONTRATO]** O catálogo abaixo reproduz exatamente as **54 métricas** listadas em `COLUNAS_METRICAS_ED_BASICA`, com seus nomes de origem `QT_MAT_*` conforme `RENOMEACAO_ED_BASICA`. Os valores são contagens ou recortes de matrícula especificados pela fonte; **não são percentuais nem taxas** e não devem ser apresentados como medidas de desempenho escolar.

**[EB-MET-002 | REGRA — CRÍTICA]** O campo geral de matrículas e suas aberturas por etapa, série, sexo, cor/raça, idade, turno, EAD e tempo integral **não são 54 categorias exclusivas**. Uma mesma matrícula pode pertencer simultaneamente a vários recortes. Portanto, nunca some colunas de famílias diferentes para construir “total de matrículas”.

### Totais e etapas

| Coluna Gold                                     | Variável de origem (contrato) |
| ----------------------------------------------- | ----------------------------- |
| `matriculas_educacao_basica`                    | `QT_MAT_BAS`                  |
| `matriculas_educacao_infantil`                  | `QT_MAT_INF`                  |
| `matriculas_creche`                             | `QT_MAT_INF_CRE`              |
| `matriculas_pre_escola`                         | `QT_MAT_INF_PRE`              |
| `matriculas_ensino_fundamental`                 | `QT_MAT_FUND`                 |
| `matriculas_fundamental_anos_iniciais`          | `QT_MAT_FUND_AI`              |
| `matriculas_fundamental_anos_finais`            | `QT_MAT_FUND_AF`              |
| `matriculas_ensino_medio`                       | `QT_MAT_MED`                  |
| `matriculas_educacao_profissional`              | `QT_MAT_PROF`                 |
| `matriculas_educacao_profissional_tecnica`      | `QT_MAT_PROF_TEC`             |
| `matriculas_eja`                                | `QT_MAT_EJA`                  |
| `matriculas_eja_fundamental`                    | `QT_MAT_EJA_FUND`             |
| `matriculas_eja_ensino_medio`                   | `QT_MAT_EJA_MED`              |
| `matriculas_educacao_especial`                  | `QT_MAT_ESP`                  |
| `matriculas_educacao_especial_classe_comum`     | `QT_MAT_ESP_CC`               |
| `matriculas_educacao_especial_classe_exclusiva` | `QT_MAT_ESP_CE`               |

### Anos do ensino fundamental

| Coluna Gold                    | Variável de origem (contrato) |
| ------------------------------ | ----------------------------- |
| `matriculas_fundamental_ano_1` | `QT_MAT_FUND_AI_1`            |
| `matriculas_fundamental_ano_2` | `QT_MAT_FUND_AI_2`            |
| `matriculas_fundamental_ano_3` | `QT_MAT_FUND_AI_3`            |
| `matriculas_fundamental_ano_4` | `QT_MAT_FUND_AI_4`            |
| `matriculas_fundamental_ano_5` | `QT_MAT_FUND_AI_5`            |
| `matriculas_fundamental_ano_6` | `QT_MAT_FUND_AF_6`            |
| `matriculas_fundamental_ano_7` | `QT_MAT_FUND_AF_7`            |
| `matriculas_fundamental_ano_8` | `QT_MAT_FUND_AF_8`            |
| `matriculas_fundamental_ano_9` | `QT_MAT_FUND_AF_9`            |

### Séries do ensino médio

| Coluna Gold                           | Variável de origem (contrato) |
| ------------------------------------- | ----------------------------- |
| `matriculas_ensino_medio_1`           | `QT_MAT_MED_1`                |
| `matriculas_ensino_medio_2`           | `QT_MAT_MED_2`                |
| `matriculas_ensino_medio_3`           | `QT_MAT_MED_3`                |
| `matriculas_ensino_medio_4`           | `QT_MAT_MED_4`                |
| `matriculas_ensino_medio_nao_seriado` | `QT_MAT_MED_NS`               |

### Sexo

| Coluna Gold                            | Variável de origem (contrato) |
| -------------------------------------- | ----------------------------- |
| `matriculas_educacao_basica_feminino`  | `QT_MAT_BAS_FEM`              |
| `matriculas_educacao_basica_masculino` | `QT_MAT_BAS_MASC`             |

### Cor/raça

| Coluna Gold                                    | Variável de origem (contrato) |
| ---------------------------------------------- | ----------------------------- |
| `matriculas_educacao_basica_cor_nao_declarada` | `QT_MAT_BAS_ND`               |
| `matriculas_educacao_basica_cor_branca`        | `QT_MAT_BAS_BRANCA`           |
| `matriculas_educacao_basica_cor_preta`         | `QT_MAT_BAS_PRETA`            |
| `matriculas_educacao_basica_cor_parda`         | `QT_MAT_BAS_PARDA`            |
| `matriculas_educacao_basica_cor_amarela`       | `QT_MAT_BAS_AMARELA`          |
| `matriculas_educacao_basica_cor_indigena`      | `QT_MAT_BAS_INDIGENA`         |

### Faixas etárias

| Coluna Gold                                | Variável de origem (contrato) |
| ------------------------------------------ | ----------------------------- |
| `matriculas_educacao_basica_idade_0_3`     | `QT_MAT_BAS_0_3`              |
| `matriculas_educacao_basica_idade_4_5`     | `QT_MAT_BAS_4_5`              |
| `matriculas_educacao_basica_idade_6_10`    | `QT_MAT_BAS_6_10`             |
| `matriculas_educacao_basica_idade_11_14`   | `QT_MAT_BAS_11_14`            |
| `matriculas_educacao_basica_idade_15_17`   | `QT_MAT_BAS_15_17`            |
| `matriculas_educacao_basica_idade_18_mais` | `QT_MAT_BAS_18_MAIS`          |

### Turno e EAD

| Coluna Gold                          | Variável de origem (contrato) |
| ------------------------------------ | ----------------------------- |
| `matriculas_educacao_basica_diurno`  | `QT_MAT_BAS_DIURNO`           |
| `matriculas_educacao_basica_noturno` | `QT_MAT_BAS_NOTURNO`          |
| `matriculas_educacao_basica_ead`     | `QT_MAT_BAS_EAD`              |

### Tempo integral

| Coluna Gold                                           | Variável de origem (contrato) |
| ----------------------------------------------------- | ----------------------------- |
| `matriculas_educacao_infantil_tempo_integral`         | `QT_MAT_INF_INT`              |
| `matriculas_creche_tempo_integral`                    | `QT_MAT_INF_CRE_INT`          |
| `matriculas_pre_escola_tempo_integral`                | `QT_MAT_INF_PRE_INT`          |
| `matriculas_ensino_fundamental_tempo_integral`        | `QT_MAT_FUND_INT`             |
| `matriculas_fundamental_anos_iniciais_tempo_integral` | `QT_MAT_FUND_AI_INT`          |
| `matriculas_fundamental_anos_finais_tempo_integral`   | `QT_MAT_FUND_AF_INT`          |
| `matriculas_ensino_medio_tempo_integral`              | `QT_MAT_MED_INT`              |

### 4.1 Matriz de interpretação

**[EB-MET-003 | REGRA]** Use a **métrica total já fornecida** quando a pergunta solicitar o total de matrículas da educação básica (`matriculas_educacao_basica`). Não a reconstitua somando educação infantil, fundamental, médio, EJA e educação profissional sem comprovação de partições disjuntas nas edições relevantes.

**[EB-MET-004 | REGRA]** `matriculas_educacao_especial` e seus subconjuntos representam recortes transversais; não somar educação especial ao total geral, nem assumir que a soma de classes comuns e exclusivas sempre recompõe o total em todos os períodos sem uma validação por edição.

**[EB-MET-005 | REGRA]** Métricas de tempo integral são **subconjuntos** da etapa correspondente. Uma consulta de “proporção de matrículas em tempo integral no ensino médio” exige numerador `matriculas_ensino_medio_tempo_integral`, denominador `matriculas_ensino_medio` **no mesmo ano e filtros**, e denominador positivo. A definição oficial específica e a compatibilidade entre fontes/anos devem ser confirmadas na documentação do Inep antes de publicar uma taxa como oficial.

**[EB-MET-006 | REGRA]** Sexo, raça/cor, faixa etária e turnos são recortes da **matrícula da educação básica**, não dimensões individuais na fato. O modelo permite comparar totais agregados dessas categorias, mas **não** filtrar simultaneamente matrículas femininas e de determinada cor/raça como intersecção; esse cruzamento não existe nas 54 colunas de agregados.

**[EB-MET-007 | REGRA]** `matriculas_educacao_basica_ead` é uma contagem de matrículas classificadas como EAD na fonte, não uma dimensão de oferta presencial/EAD para filtrar outras métricas. Não deduza, por subtração, matrículas presenciais como `total - EAD` sem comprovar exaustividade e compatibilidade dos conceitos.

**[EB-MET-008 | REGRA]** As variáveis de anos/séries são recortes dos níveis fundamentais/médio. Não somar séries a totais de etapa sem verificar cobertura, classes não seriadas e eventuais diferenças entre edições.

## 5. Agregações e cálculos autorizados

**[EB-ANA-001 | REGRA]** Para contar matrículas da educação básica por município, UF, rede ou escola em **um único ano**, a forma básica é `SUM(f.matriculas_educacao_basica)` sobre as linhas da fato que pertencem ao mesmo recorte, desde que o modelo Gold mantenha uma única observação por escola/ano e as referências de dimensão sejam únicas. O chatbot deve usar SQL parametrizado e um catálogo de indicadores autorizado; a LLM não pode gerar SQL livre sem validação.

**[EB-ANA-002 | REGRA]** A série histórica apresenta **um total por ano**. Não some 2018–2025 para responder “quantos alunos estudaram no período”: a mesma pessoa pode aparecer em anos diferentes, e a fato não contém identificadores individuais que permitam deduplicação entre anos (ou entre escolas).

**[EB-ANA-003 | REGRA]** Variação absoluta: `valor_final - valor_inicial`. Variação percentual: `((valor_final / valor_inicial) - 1) × 100`, somente com valor inicial não nulo e diferente de zero. Para valores ausentes em qualquer extremo, não calcular variação; para valor inicial zero, a variação percentual é indefinida.

**[EB-ANA-004 | REGRA]** A taxa `matriculas_*_tempo_integral / matriculas_*` é **um indicador derivado do projeto**, não deve ser chamada de “taxa oficial do Inep” sem reproduzir o método publicado. Em percentuais, apresentar numerador, denominador e ano.

**[EB-ANA-005 | ETL + REGRA]** A Silver preserva nulos de métricas, não preenche ausência com zero e rejeita textos não vazios que não podem ser convertidos em `Int32`. Nulos indicam valores ausentes ou não contemplados no contrato da edição; não os converta silenciosamente em zero. `SUM()` ignora nulos e retorna `NULL` quando não há valores não nulos; consulte também a **cobertura** (`COUNT(campo)`) para saber quantas escolas contribuíram com indicador válido.

**[EB-ANA-006 | REGRA]** Contagem de escolas com matrícula positiva no ano: `COUNT(DISTINCT f.id_escola)` com `f.matriculas_educacao_basica > 0`. Isso não é necessariamente o número de **escolas em funcionamento** ou o universo de unidades cadastradas; essa pergunta requer regra própria para situação e disponibilidade do cadastro.

**[EB-ANA-007 | REGRA]** Nunca gerar ou atribuir diretamente ao Gold: taxa de aprovação, reprovação, abandono, distorção idade-série, Ideb, proficiência ou população em idade escolar. Essas informações não são disponibilizadas como indicadores nas 54 métricas desta fato.

### 5.1 Exemplo SQL — matrículas por ano em município

Consulta SQL de referência, sem valores fictícios:

```sql
SELECT
    f.ano,
    SUM(f.matriculas_educacao_basica)::bigint AS matriculas,
    COUNT(f.matriculas_educacao_basica) AS escolas_com_indicador_informado
FROM gold.fact_educacao_basica AS f
JOIN gold.dim_localidade AS l
    ON l.id_localidade = f.id_localidade
WHERE l.codigo_municipio = %(codigo_municipio)s
  AND f.ano BETWEEN %(ano_inicial)s AND %(ano_final)s
GROUP BY f.ano
ORDER BY f.ano;
```

**Leitura correta:** matrículas registradas nas escolas do município em cada ano, com contagem de linhas com dado informado. A coluna `escolas_com_indicador_informado` pressupõe a unicidade escola×ano e **não** mede escolas em funcionamento. Sem resultados, não inventar um zero. Se a identidade municipal variar historicamente, reavaliar a classificação conforme EB-GEO-003.

### 5.2 Exemplo SQL — escolas com matrículas positivas

```sql
SELECT
    f.ano,
    COUNT(DISTINCT f.id_escola) AS escolas_com_matriculas
FROM gold.fact_educacao_basica AS f
WHERE f.ano = %(ano)s
  AND f.matriculas_educacao_basica > 0
GROUP BY f.ano;
```

### 5.3 Perguntas respondíveis com a fato

- “Como evoluíram as matrículas da educação básica no município X entre 2020 e 2025?” → `matriculas_educacao_basica` por `ano` e `codigo_municipio`, com verificação de cobertura.
- “Quantas matrículas em creche foram registradas em 2023 na UF Y?” → `matriculas_creche` no ano e UF.
- “Qual a quantidade de matrículas no ensino médio em tempo integral em 2024?” → `matriculas_ensino_medio_tempo_integral` e filtros expressos.
- “Como variou o número de escolas com matrícula no ensino fundamental?” → contagem distinta de `id_escola` na fato com `matriculas_ensino_fundamental > 0`, sem tratar isso como cadastro total.
- “Quantas matrículas foram declaradas como cor/raça não informada?” → `matriculas_educacao_basica_cor_nao_declarada`, sem presumir valor zero quando a edição não possuir o campo.

### 5.4 Pedidos que exigem ressalvas

- “Quantos **alunos únicos** havia em 2020–2025?” → a fato está agregada por escola/ano e não tem identificação individual para deduplicação entre escolas/anos.
- “Quantos estudantes de 6 a 10 anos **moravam** no município?” → a localidade é institucional, não residência.
- “Quantas **meninas indígenas** estavam matriculadas?” → sexo e cor/raça estão em indicadores independentes; a intersecção não está neste modelo.
- “Qual a **taxa de abandono** ou aprovação?” → não disponível neste Gold; requer indicadores de movimento/rendimento.
- “Qual a proporção oficial de matrículas em tempo integral?” → exigir validação metodológica da edição e dos campos antes de atribuir caráter oficial.
- “Qual era a rede administrativa da escola em 2019?” → política histórica da dimensão Escola não confirmada.
- “Somando matrículas em educação especial, EJA e ensino médio, qual o total?” → agregação conceitualmente sobreposta; não somar.

## 6. Indicadores não materializados e variações de fonte

**[EB-EXT-001 | CONTRATO]** Existe em `schema.py` um contrato adicional `SCHEMA_FACT_EDUCACAO_BASICA_DETALHE` para representar `id_escola, id_localidade, id_calendario, ano, variavel_inep, valor` e uma chave `id_escola, ano, variavel_inep`. A intenção descrita no contrato é preservar outras variáveis quantitativas de origem. **Essa tabela não consta no inventário das dez tabelas Gold publicadas; portanto, não deve ser oferecida como disponível ao chatbot.**

**[EB-EXT-002 | CONTRATO]** Os prefixos de variáveis quantitativas adicionais previstos são `QT_MAT_` e `QT_TRANSP_`. O simples fato de existir esse contrato não demonstra que as variáveis estejam presentes na Silver ou no PostgreSQL. Não construir respostas a partir dele antes de sua materialização e validação.

**[EB-EXT-003 | CONTRATO]** Os contratos declaram aliases históricos `QT_MAT_BAS_D → QT_MAT_BAS_DIURNO` e `QT_MAT_BAS_N → QT_MAT_BAS_NOTURNO`. O processo específico de aplicação precisa ser conferido nos módulos Bronze/Silver da educação básica.

## 7. Testes de consistência recomendados

Os testes abaixo são **propostas não executadas**, não garantias de qualidade já obtidas.

| ID         | Verificação                                                                           | Resultado desejado / interpretação                                |
| ---------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| EB-VAL-001 | Unicidade da chave `id_escola, ano`                                                   | Nenhuma duplicidade; se houver, revisar transformação Gold        |
| EB-VAL-002 | Órfãos entre fato e dimensões Escola, Localidade e Calendário                         | Zero referências ausentes                                         |
| EB-VAL-003 | Anos efetivamente presentes na fato                                                   | Documentar cobertura real versus configuração 2018–2025           |
| EB-VAL-004 | Comparar nulos por métrica e ano                                                      | Identificar variáveis opcionais ausentes em cada edição           |
| EB-VAL-005 | Confrontar total de matrículas na fato com o arquivo Silver equivalente, por ano      | Diferenças explicadas por deduplicação/filtros conhecidos         |
| EB-VAL-006 | Confirmar regra de atribuição de rede, situação e município a cada escola/ano         | Registrar se atributos são históricos ou de cadastro mais recente |
| EB-VAL-007 | Conferir se somas por categorias que aparentam partição conciliam com o total         | Apenas validar; não impor igualdade sem dicionário correspondente |
| EB-VAL-008 | Validar os totais anuais contra publicações/sinopses do Inep em recortes equivalentes | Diferenças metodológicas e de cobertura explicitadas              |
| EB-VAL-009 | Confrontar as 58 colunas com `rag.schema_catalog`                                     | Nenhuma coluna mencionada como física sem existir no catálogo     |
| EB-VAL-010 | Verificar se a tabela auxiliar de detalhes existe no Gold                             | Se não existir, manter indisponível ao chatbot                    |

### SQL — unicidade da fato

```sql
SELECT
    id_escola,
    ano,
    COUNT(*) AS registros
FROM gold.fact_educacao_basica
GROUP BY id_escola, ano
HAVING COUNT(*) > 1
ORDER BY registros DESC
LIMIT 20;
```

### SQL — cobertura de anos e disponibilidade das métricas

```sql
SELECT
    ano,
    COUNT(*) AS linhas_escola_ano,
    COUNT(matriculas_educacao_basica) AS linhas_com_total_informado,
    COUNT(matriculas_educacao_basica_diurno) AS linhas_com_turno_diurno
FROM gold.fact_educacao_basica
GROUP BY ano
ORDER BY ano;
```

## 8. Rastreabilidade

| Informação                                          | Origem e evidência                                                                                          |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Anos configurados e padrões de CSV                  | `etl/educacao/config.py` (`ANOS_ED_BASICA_HISTORICO`, `ANO_ED_BASICA_ATUAL`, `RAW_ED_BASICA*`)              |
| Nomes de campos originais, aliases e mapeamentos    | `etl/educacao/schema.py` (`COLUNAS_ED_BASICA*`, `ALIASES_ED_BASICA*`, `RENOMEACAO_ED_BASICA*`)              |
| Contrato Bronze/Silver e tipos de dados             | `etl/educacao/schema.py` (`SCHEMA_ED_BASICA_BRONZE`, `SCHEMA_ED_BASICA_SILVER`)                             |
| Modelo Gold e chave escola×ano                      | `etl/educacao/schema.py` (`SCHEMA_DIM_ESCOLA`, `SCHEMA_FACT_EDUCACAO_BASICA`, `CHAVE_FACT_EDUCACAO_BASICA`) |
| Leitura e junção específicas da educação básica     | `etl/educacao/bronze/bronze_ed_basica.py` (`carregar_csv_fonte`, `consolidar_bronze`)                       |
| Leitura da fonte 2025 / fonte histórica             | **Verificado:** `etl/educacao/bronze/bronze_ed_basica.py`                                                   |
| Normalização, classificação, métricas e nulos       | **Verificado:** `etl/educacao/silver/silver_ed_basica.py`                                                   |
| Identidade e atributos mais recentes das escolas    | **Verificado:** `etl/educacao/gold/dim_escola.py`                                                           |
| Seleção sem soma; integridade e igualdade de linhas | **Verificado:** `etl/educacao/gold/fact_educacao_basica.py`                                                 |

### Referências oficiais

- Inep. **Censo Escolar – apresentação**: https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/censo-escolar
- Inep. **Microdados do Censo Escolar da Educação Básica**: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar
- Inep. **Primeira Etapa da Coleta (Matrícula Inicial)**: https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/censo-escolar/orientacoes/matricula-inicial
- Inep. **Etapas da Coleta**: https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/censo-escolar/etapas-da-coleta
- Inep. **Perguntas frequentes**: https://www.gov.br/inep/pt-br/acesso-a-informacao/perguntas-frequentes/censo-escolar

## 9. Pendências para aprovação da versão 1.0.0

**[EB-PEN-001 | PARCIALMENTE RESOLVIDA]** Os quatro módulos específicos foram inspecionados e as regras de junção, chaves, ausência de métricas, seleção da dimensão mais recente e preservação de linhas foram documentadas nesta revisão. Continua necessária uma conferência com amostras das fontes originais para verificar mudanças de layout e significado ao longo dos anos.

**[EB-PEN-002 | PARCIALMENTE RESOLVIDA]** A execução relatada de `postgres.validate_gold --deep` confirmou chave única da fato, constraints referenciais e presença de 2018–2025 na fato, sem erros no escopo testado. **Ainda falta** conferir nulos por coluna/ano e comparar valores com a Silver e com publicações equivalentes do Inep.

**[EB-PEN-003]** Verificar nos dicionários das **edições exatas** de 2018–2025 quais métricas são comparáveis historicamente e em que condições partições por sexo, cor/raça, faixa etária e séries conciliam com o total.

**[EB-PEN-004]** Decidir a política para perguntas históricas filtradas pelos atributos **mais recentes** de `dim_escola`, já que o código confirmou que ela não armazena versões anuais. Por padrão, explicitar o uso do cadastro mais recente.
