---
id: avaliacoes
area: educacao
categoria: regras_de_negocio
versao: "0.9.1"
status: revisao_tecnica_pendente
fonte_dados: INEP/Indicadores de Qualidade da Educação Superior
periodo_configurado: "Conceito Enade: 2018, 2019, 2021, 2022, 2023, 2025; CPC, IDD e IGC: 2018, 2019, 2021, 2022, 2023"
tabelas_principais:
  - gold.fact_avaliacao_curso_superior
  - gold.fact_avaliacao_ies
ultima_revisao_documental: "2026-11-03"
---

# Avaliações da Educação Superior — Regras de negócio do EI DataBot

> **Status:** revisão técnica 0.9.1. Foram inspecionados os quatro módulos Bronze, os quatro Silver e as fatos Gold de avaliação anexados nesta etapa, além dos contratos anteriores. O código confirma chaves e estratégias de consolidação, mas **não** comprova equivalência metodológica com os XLSX/notas técnicas do Inep. Permanecem pendentes validações de valores, de registros auditados e aprovação humana.
>
> **Classificação das evidências:** **[CONTRATO]** = campos, fontes, chaves e tipos explícitos no código recebido; **[INEP]** = definição da fonte oficial indicada nas referências; **[REGRA]** = política de consumo analítico recomendada para evitar inferências indevidas; **[PENDENTE]** = depende de conferência adicional dos microdados originais, das rotinas compartilhadas ou de testes de valores; os transformadores específicos de avaliações já foram inspecionados nesta revisão.
>
> O catálogo `rag.schema_catalog` contém o estado físico publicado do PostgreSQL. Este documento é responsável pela semântica e pelas limitações; **não substitui a estrutura SQL nem as notas técnicas vigentes para cada edição**.

## 1. Escopo, fontes e abrangência

**[AV-FON-001 | INEP]** O conjunto de indicadores de qualidade da educação superior inclui **Conceito Enade**, **Indicador de Diferença entre os Desempenhos Observado e Esperado (IDD)**, **Conceito Preliminar de Curso (CPC)** e **Índice Geral de Cursos Avaliados da Instituição (IGC)**. Os três primeiros se referem a cursos de graduação; o IGC refere-se à instituição de educação superior (IES). Os indicadores são divulgados em resultados contínuos e faixas, observadas as metodologias e os requisitos da edição.

**[AV-FON-002 | CONTRATO]** `config.py` prevê leitura de planilhas XLSX nas pastas `data/raw/microdados/enade/`, `cpc/`, `idd/` e `igc/`, com padrões, respectivamente, `conceito_enade_*.xlsx`, `cpc_*.xlsx`, `idd_*.xlsx` e `igc_*.xlsx`. As abas dependem de mapeamentos individuais (`ABAS_CONCEITO_ENADE`, `ABAS_CPC`, `ABAS_IDD`, `ABAS_IGC`). O conteúdo efetivamente publicado no Gold ainda precisa ser confrontado com as linhas carregadas.

**[AV-FON-003 | CONTRATO]** Anos configurados: Conceito Enade = **2018, 2019, 2021, 2022, 2023 e 2025**; CPC/IDD/IGC = **2018, 2019, 2021, 2022 e 2023**. Esses conjuntos **não** são intervalos contínuos e **não** provam que todas as áreas, cursos e instituições estejam presentes em todos os anos. O ano 2020 não deve ser interpolado.

**[AV-FON-004 | CONTRATO + INEP]** O mapeamento de abas contém `conceito_enade_medicina_2025.xlsx` e a configuração inclui 2025 em Conceito Enade, **mas isso não garante cobertura integral de todas as áreas em 2025**. O Inep tem publicações próprias de Conceito Enade de Medicina e Licenciaturas em 2025. Na ausência de testes dos arquivos carregados, não extrapolar a presença de Medicina para outras áreas.

**[AV-FON-005 | REGRA]** O ano de referência de um indicador não é necessariamente o ano de divulgação pública. Respostas devem dizer **“edição/referência de 2023”**, por exemplo, e não atribuir automaticamente a divulgação a 2023.

### Linhagem prevista pelos contratos

```text
Planilhas Inep: Conceito Enade / CPC / IDD
    ↓ Bronze (bronze_conceito_enade, bronze_cpc, bronze_idd)
    ↓ Silver (silver_conceito_enade, silver_cpc, silver_idd)
    ↓ Gold: gold.fact_avaliacao_curso_superior
           ├── gold.dim_ies
           ├── gold.dim_curso_superior
           ├── gold.dim_localidade
           └── gold.dim_calendario

Planilhas Inep: IGC
    ↓ Bronze (bronze_igc)
    ↓ Silver (silver_igc)
    ↓ Gold: gold.fact_avaliacao_ies
           ├── gold.dim_ies
           └── gold.dim_calendario
```

**[AV-FON-006 | ETL]** A linhagem foi confirmada nos módulos recebidos. As quatro Bronze chamam `build_bronze_excel` com seus contratos, arquivos e abas configurados. As Silver tipam e normalizam chaves, verificam a unicidade por fonte e gravam Parquet. Na Gold, Enade/CPC/IDD são conciliados por `(ano, codigo_ies, codigo_curso)`, enquanto IGC alimenta fato independente por `(id_ies, ano)`. O tratamento de valores especiais da planilha depende também das funções compartilhadas de leitura/tipagem e deve ser confrontado com a origem.

## 2. Modelo dimensional, granularidade e chaves

| Tabela Gold                          | Grão definido no contrato                                         | Chave lógica contratada                                                  | Finalidade                                         |
| ------------------------------------ | ----------------------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------- |
| `gold.fact_avaliacao_curso_superior` | IES × curso analítico × localidade × ano × curso avaliado do Inep | `(id_ies, id_curso_superior, id_localidade, ano, codigo_curso_avaliado)` | Conceito Enade, IDD, CPC e respectivos componentes |
| `gold.fact_avaliacao_ies`            | IES × ano                                                         | `(id_ies, ano)`                                                          | IGC e seus componentes institucionais              |
| `gold.dim_ies`                       | IES por código de negócio                                         | `codigo_ies`                                                             | Identidade, classificação e sede institucional     |
| `gold.dim_curso_superior`            | Categoria analítica de curso                                      | Classificação analítica composta, não e-MEC único                        | Enriquecimento e filtros para cursos               |
| `gold.dim_localidade`                | Município por código                                              | `codigo_municipio`                                                       | Localidade atribuída à avaliação de curso          |
| `gold.dim_calendario`                | Ano                                                               | `ano`                                                                    | Referência temporal                                |

**[AV-GRA-001 | CONTRATO]** A fato de avaliação de curso contém **55 colunas** no schema do ETL. A fato institucional contém **14 colunas**. Os campos obrigatórios da primeira são `id_ies`, `id_curso_superior`, `id_localidade`, `id_calendario`, `ano`, `codigo_curso_avaliado`; os da segunda são `id_ies`, `id_calendario`, `ano`. A lista de obrigatórios **não** torna uma nota individual obrigatória.

**[AV-GRA-002 | CONTRATO]** A chave Gold de curso usa `codigo_curso_avaliado`, diferentemente da dimensão `dim_curso_superior`, cuja classificação é analítica e pode reunir vários códigos oficiais. **Não use `id_curso_superior` sozinho como identificador oficial de curso avaliado.** Prefira a combinação com `id_ies`, `ano` e `codigo_curso_avaliado` ao apresentar resultados oficiais.

**[AV-GRA-003 | ETL]** Cada Silver de Enade, CPC, IDD e IGC valida sua respectiva chave de contrato com `validar_chave_unica`; **não há deduplicação silenciosa** nesses módulos. Na fato de curso, as três fontes são concatenadas e agrupadas por `(ano, codigo_ies, codigo_curso)`. Na fato IGC, o código faz lookup por `codigo_ies`, usa `ano_igc` para `ano/id_calendario` e valida a chave final.

**[AV-GRA-004 | REGRA]** Para consultar IGC por UF, a dimensão `dim_ies` pode oferecer `uf_sede_ies`, isto é, **UF da sede da instituição**, não o município do curso avaliado. `fact_avaliacao_ies` não possui `id_localidade`. Não apresentar o IGC como indicador de um campus ou município de oferta.

**[AV-GRA-005 | ETL + REGRA]** A fato de avaliação de cursos usa `codigo_municipio` consolidado dos arquivos de avaliação e faz `left join` com `dim_localidade`, bloqueando chaves sem correspondência. Não aplica a regra de sentinela EAD da **fato censitária** nesse módulo. O CPC Silver também pode **corrigir o código municipal** a partir do par município normalizado + UF presente na GEO, registrando auditoria da mudança. Não associe essa localidade ao local de residência dos estudantes.

### Relacionamentos previstos

| Fato               | Dimensão        | Condição                                    |
| ------------------ | --------------- | ------------------------------------------- |
| Avaliação de curso | IES             | `f.id_ies = i.id_ies`                       |
| Avaliação de curso | Curso analítico | `f.id_curso_superior = c.id_curso_superior` |
| Avaliação de curso | Localidade      | `f.id_localidade = l.id_localidade`         |
| Avaliação de curso | Calendário      | `f.id_calendario = d.id_calendario`         |
| Avaliação de IES   | IES             | `f.id_ies = i.id_ies`                       |
| Avaliação de IES   | Calendário      | `f.id_calendario = d.id_calendario`         |

**[AV-JOIN-001 | REGRA]** Nunca faça join direto entre as duas fatos para agregar conceitos. Uma IES pode ter vários cursos avaliados no mesmo ano, de modo que juntar as fatos pela IES e pelo ano **repetirá** o IGC tantas vezes quantos forem seus cursos. Agregue separadamente em suas respectivas granularidades.

**[AV-JOIN-002 | REGRA]** Não junte diretamente `fact_avaliacao_curso_superior` com `fact_educacao_superior` para somar matrículas ou notas: as chaves e granularidades são diferentes, e uma categoria analítica de curso pode representar mais de um código oficial. Qualquer cruzamento deve passar por correspondência explícita e validada de cursos, anos e oferta.

### Política de consolidação confirmada no Gold

**[AV-ETL-001 | ETL]** `fact_avaliacao_curso_superior.py` ordena as fontes por prioridade **Enade (1) → CPC (2) → IDD (3)**. Para cada `(ano, codigo_ies, codigo_curso)`, escolhe o **primeiro valor não nulo por coluna**. Logo, o resultado da dimensão descritiva (município, grau, modalidade e área) pode depender da fonte prioritária com informação disponível; o mecanismo **não é uma votação nem uma validação metodológica da divergência**.

**[AV-ETL-002 | ETL — ATENÇÃO]** Antes de consolidar, o Gold identifica divergências de município, área, grau e modalidade entre as fontes para a mesma chave e chama `registrar_alerta`. **Esse bloco não aborta a execução se houver conflito.** É necessário inspecionar o CSV de auditoria `audit_gold_avaliacao_curso_descritores_brutos_divergentes.csv` e decidir se as divergências são aceitáveis. Não afirmar que a publicação “corrigiu” todos os conflitos.

**[AV-ETL-003 | ETL]** A correspondência com `dim_curso_superior` prioriza um lookup por `(codigo_ies, codigo_curso)` a partir do **último ano disponível na Silver do Censo Superior**. Se não houver correspondência, tenta localizar uma identidade analítica já existente por descritores da avaliação (área, grau, modalidade); **não cria um novo curso artificial**. Correspondência ausente faz a Gold falhar e gera auditoria. Uma identidade analítica não substitui o código oficial avaliado.

**[AV-ETL-004 | ETL]** O IGC tem uma linha por IES×ano. A fato institucional não faz médias nem recomputa o IGC: carrega as métricas da Silver e mapeia `ano_igc` para `ano`/`id_calendario`. Falha se a IES não estiver na dimensão; valida unicidade final.

**[AV-ETL-005 | ETL]** As Silver tipam identificadores (`strict=False`), limpam texto e validam unicidade. Como as regras de conversão de notas e dos marcadores `SC` envolvem leitura/contratos compartilhados, o destino exato de cada formato textual da fonte deve ser verificado nos XLSX reais ou com testes específicos; **não presumir** que `SC` foi sempre preservado como texto em campos numéricos.

**[AV-ETL-006 | ETL]** Na construção da fato de avaliação de curso, `_parte_avaliacao` retorna `None` quando o arquivo Silver de uma fonte não existe; o processo pode publicar **um subconjunto de Enade/CPC/IDD** se pelo menos uma Silver estiver presente. Ele só falha por ausência quando nenhuma das três existir. Portanto, a cobertura efetiva por indicador e edição precisa ser consultada no banco; a existência da fato não comprova presença de todas as três fontes.

## 3. Conceito Enade

**[AV-ENA-001 | INEP]** O **Conceito Enade** é um indicador de qualidade de cursos de graduação derivado do desempenho de estudantes concluintes no Enade. Nas definições públicas históricas do Inep, seu cálculo pressupõe pelo menos dois concluintes participantes; edições e modalidades recentes devem seguir a nota técnica específica correspondente. O resultado do curso **não equivale a uma nota individual de aluno**.

**[AV-ENA-002 | CONTRATO]** A Gold preserva campos de Formação Geral (FG), Componente Específico (CE), Conceito Contínuo, Conceito Faixa, concluintes inscritos, participantes e, quando disponíveis, concluintes acima de padrão e percentual correspondente.

**[AV-ENA-003 | REGRA]** Use `enade_conceito_faixa` quando a pergunta mencionar o **conceito/nota de 1 a 5**. Use `enade_conceito_continuo` quando pedir explicitamente o valor contínuo. Não substitua uma escala pela outra e não converta uma nota contínua em faixa com cortes inventados.

**[AV-ENA-004 | REGRA]** `enade_concluintes_inscritos_qtd` não é sinônimo de `enade_concluintes_participantes_qtd`. Não equipare participantes do exame a todos os concluintes registrados no Censo da Educação Superior.

**[AV-ENA-005 | PENDENTE]** A semântica exata de `enade_concluintes_acima_padrao_qtd` e `enade_percentual_acima_padrao` pode variar entre formatos recentes; conferir `silver_conceito_enade.py`, os XLSX originais e a nota técnica da edição antes de permitir respostas substantivas sobre esses dois campos.

## 4. IDD — Valor agregado estimado

**[AV-IDD-001 | INEP]** O **IDD** busca estimar o valor agregado pelo processo formativo ao desempenho de concluintes, usando o resultado do Enade e o desempenho anterior no Enem como aproximação do perfil de entrada. Não mede causalmente, por si só, a qualidade isolada da instituição nem o ganho individual de cada aluno.

**[AV-IDD-002 | INEP]** Nas regras públicas do Inep, o cálculo exige pelo menos **dois** concluintes participantes com dados recuperados do Enem, e **20% ou mais** dos concluintes participantes do Enade com esses dados. Os parâmetros de cada edição devem ser conferidos na nota técnica pertinente.

**[AV-IDD-003 | CONTRATO]** Campos centrais: `idd_nota_bruta`, `idd_continuo`, `idd_faixa`, `idd_concluintes_com_enem_qtd`, `idd_proporcao_concluintes_com_enem`, inscritos e participantes.

**[AV-IDD-004 | REGRA]** Quando o campo IDD estiver nulo, indisponível ou “Sem Conceito”, **não** o converta em zero. Não calcule IDD por `nota Enade − nota Enem`; a metodologia oficial não é uma subtração direta de médias exibidas na Gold.

## 5. CPC — Conceito Preliminar de Curso

**[AV-CPC-001 | INEP]** O **CPC** avalia cursos e combina medidas de desempenho dos estudantes, valor agregado do processo formativo e condições de oferta (como organização didático-pedagógica, infraestrutura e corpo docente), seguindo metodologia específica do Inep. O índice não é uma medida simples da nota do Enade.

**[AV-CPC-002 | INEP]** O Inep informa que cursos com menos de dois concluintes participantes ficam **Sem Conceito (SC)** no CPC. O cálculo e a divulgação ocorrem no ano seguinte à realização do Enade, sem alterar o ano de referência da edição.

**[AV-CPC-003 | CONTRATO]** `cpc_continuo` e `cpc_faixa` são os campos finais. A Gold também preserva componentes FG/CE, nota de IDD, organização didático-pedagógica, infraestrutura, oportunidade de ampliação da formação, mestres, doutores e regime de trabalho, com campos brutos e/ou padronizados segundo o arquivo de origem.

**[AV-CPC-004 | REGRA]** **Não recalcular `cpc_continuo`** a partir da soma das colunas de componentes: os pesos, normalizações e regras de elegibilidade pertencem à nota técnica da edição. Use o valor publicado da fonte, armazenado na Gold.

**[AV-CPC-005 | REGRA]** Componentes que aparecem tanto no registro CPC quanto no Enade/IDD são **representações relacionadas do mesmo processo avaliativo**, não medidas independentes que devam ser somadas. Não confunda `cpc_nota_bruta_idd` com `idd_nota_bruta` sem verificação da origem e da edição.

## 6. IGC — Índice Geral de Cursos Avaliados da Instituição

**[AV-IGC-001 | INEP]** O **IGC** avalia a IES. Seu cálculo é anual e considera CPCs de cursos avaliados no último **triênio**, desempenho da pós-graduação stricto sensu informado pela Capes e distribuição de estudantes entre graduação e pós-graduação, conforme regras oficiais de ponderação.

**[AV-IGC-002 | CONTRATO]** A fato `gold.fact_avaliacao_ies` apresenta `igc_continuo`, `igc_faixa`, `igc_cursos_cpc_trienio_qtd`, `igc_alfa_graduacao`, `igc_conceito_medio_graduacao`, `igc_beta_mestrado`, `igc_conceito_medio_mestrado`, `igc_gama_doutorado`, `igc_conceito_medio_doutorado`, `observacao_igc` e `cebas_igc`.

**[AV-IGC-003 | REGRA]** Use `igc_continuo` como valor contínuo e `igc_faixa` como conceito de faixa da instituição. **Não calcule o IGC como média simples do CPC de todos os cursos**, nem recalcule a nota apenas com as colunas auxiliares da fato; os pesos e critérios pertencem ao Inep.

**[AV-IGC-004 | REGRA]** `igc_cursos_cpc_trienio_qtd` é o número de cursos considerados na edição do indicador, **não o total de cursos em atividade na instituição**. Não some a mesma quantidade ao longo de anos para obter um total único de cursos; há sobreposição entre triênios.

**[AV-IGC-005 | REGRA]** Uma evolução anual do IGC compara **edições anuais de um indicador com janela de três anos**, não desempenhos estritamente isolados de cada ano. Alertar sobre a natureza da janela móvel quando a pergunta implicar tendências ano a ano.

## 7. Inventário de métricas e regras de agregação

### 7.1 Fato `gold.fact_avaliacao_curso_superior`

| Família                | Colunas                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | Uso permitido                                                                    |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Identificadores        | `id_ies`, `id_curso_superior`, `id_localidade`, `id_calendario`, `ano`, `codigo_curso_avaliado`, `codigo_area`, `area_avaliacao`, `grau_academico_avaliacao`, `modalidade_ensino_avaliacao`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Filtros, identificação e agrupamentos; não são notas                             |
| Enade — quantidades    | `enade_concluintes_inscritos_qtd`, `enade_concluintes_participantes_qtd`, `enade_concluintes_acima_padrao_qtd`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Contagens, **somente após confirmar ausência de duplicação das chaves oficiais** |
| Enade — notas          | `enade_nota_bruta_fg`, `enade_nota_padronizada_fg`, `enade_nota_bruta_ce`, `enade_nota_padronizada_ce`, `enade_conceito_continuo`, `enade_conceito_faixa`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Indicadores de curso; **não somar**                                              |
| Enade — proporção      | `enade_percentual_acima_padrao`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Percentual de origem; **não somar** nem promediar sem justificativa              |
| IDD — quantidades      | `idd_concluintes_inscritos_qtd`, `idd_concluintes_participantes_qtd`, `idd_concluintes_com_enem_qtd`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Contagens por universo IDD; verificar chave antes de agregar                     |
| IDD — escore/proporção | `idd_proporcao_concluintes_com_enem`, `idd_nota_bruta`, `idd_continuo`, `idd_faixa`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Indicadores não aditivos                                                         |
| CPC — quantidades      | `cpc_concluintes_inscritos_qtd`, `cpc_concluintes_participantes_qtd`, `cpc_concluintes_com_enem_qtd`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Contagens por universo CPC; verificar chave antes de agregar                     |
| CPC — componentes      | `cpc_nota_bruta_fg`, `cpc_nota_padronizada_fg`, `cpc_nota_bruta_ce`, `cpc_nota_padronizada_ce`, `cpc_conceito_enade_continuo`, `cpc_proporcao_concluintes_com_enem`, `cpc_nota_bruta_idd`, `cpc_nota_padronizada_idd`, `cpc_nota_bruta_organizacao_didatico_pedagogica`, `cpc_nota_padronizada_organizacao_didatico_pedagogica`, `cpc_nota_bruta_infraestrutura`, `cpc_nota_padronizada_infraestrutura`, `cpc_nota_bruta_oportunidade_formacao`, `cpc_nota_padronizada_oportunidade_formacao`, `cpc_nota_bruta_mestres`, `cpc_nota_padronizada_mestres`, `cpc_nota_bruta_doutores`, `cpc_nota_padronizada_doutores`, `cpc_nota_bruta_regime_trabalho`, `cpc_nota_padronizada_regime_trabalho` | Não aditivos; não reconstruir índice por soma                                    |
| CPC — resultado        | `cpc_continuo`, `cpc_faixa`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Nota/faixa por curso e edição                                                    |
| Observações            | `observacao_enade`, `observacao_idd`, `observacao_cpc`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Qualificações e ressalvas de origem                                              |

### 7.2 Fato `gold.fact_avaliacao_ies`

| Família     | Colunas                                                                                                                                                        | Uso permitido                                                  |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Chaves      | `id_ies`, `id_calendario`, `ano`                                                                                                                               | Identificação de IES e edição                                  |
| Quantidade  | `igc_cursos_cpc_trienio_qtd`                                                                                                                                   | Quantidade de cursos incluídos no triênio, não total de cursos |
| Componentes | `igc_alfa_graduacao`, `igc_conceito_medio_graduacao`, `igc_beta_mestrado`, `igc_conceito_medio_mestrado`, `igc_gama_doutorado`, `igc_conceito_medio_doutorado` | Componentes publicados; não aditivos                           |
| Resultado   | `igc_continuo`, `igc_faixa`                                                                                                                                    | Nota/faixa por IES e edição                                    |
| Outros      | `observacao_igc`, `cebas_igc`                                                                                                                                  | Ressalvas e cadastro de origem                                 |

### 7.3 Políticas analíticas obrigatórias

**[AV-AGG-001 | REGRA — CRÍTICA]** **Não somar, fazer média, mediana ou ponderação de conceitos** para responder “qual é o Conceito Enade/CPC/IDD/IGC de uma cidade, UF, rede ou grupo de instituições”. O Inep publica esses indicadores por unidade avaliada. Uma estatística descritiva calculada sobre um conjunto só poderá ser apresentada como **estatística do projeto**, com denominador e universo explícitos, nunca como conceito oficial agregado do Inep.

**[AV-AGG-002 | REGRA]** Para perguntas como “quantos cursos receberam CPC faixa 4 em 2023?”, conte **códigos de cursos avaliados distintos na granularidade correta**, com filtros da fonte, não matrículas ou linhas indiscriminadas. Antes de confiar na contagem, validar a chave da fato e a deduplicação real.

**[AV-AGG-003 | REGRA]** Para IGC, conte IES em uma edição com `COUNT(DISTINCT id_ies)` quando pertinente; nunca conte os cursos da fato de avaliação como IES. Para Conceito Enade/CPC/IDD, **o filtro de ano é obrigatório** em consultas comparativas e rankings de uma edição.

**[AV-AGG-004 | REGRA]** Não tratar nulos, registros ausentes e “Sem Conceito (SC)” como zeros, faixas mínimas nem prova de baixa qualidade. Diferenciar: sem registro na base consultada; registro com indicador nulo; registro com observação de fonte; zero numérico efetivamente publicado (quando aplicável).

**[AV-AGG-005 | REGRA]** Comparações intertemporais devem considerar o ciclo avaliativo, possíveis mudanças metodológicas e cobertura parcial de áreas. Evitar rankings globais que misturem cursos de áreas e anos diferentes sem contextualização.

**[AV-AGG-006 | REGRA]** Ao comparar resultados entre públicos e privados ou entre UF/municípios, especifique se a classificação vem de `dim_ies` (cadastro mais recente, conforme documento de educação superior) ou da coluna histórica na Silver. Não afirmar que a classificação atual da dimensão representa necessariamente o ano da avaliação.

**[AV-AGG-007 | REGRA]** Nunca apresentar `cpc_continuo`, `enade_conceito_continuo`, `idd_continuo` ou `igc_continuo` como quantidade de alunos, matrículas, inscritos ou concluintes. Não converter pontuações em porcentagens sem documentação específica da escala.

**[AV-AGG-008 | REGRA]** Quando forem solicitadas notas por curso, além do indicador, recuperar **IES, curso avaliado (código oficial), área de avaliação, modalidade e ano**. A categoria `dim_curso_superior` pode ser usada como apoio, mas não é substituta da identidade oficial da avaliação.

## 8. SQL exemplificativo: consulta somente de leitura

Os exemplos seguintes usam as colunas contratadas, mas dependem da **existência e validade dos registros reais** na Gold. O backend deverá usar parâmetros `psycopg` e whitelist de consultas/identificadores, nunca SQL arbitrário gerado pela LLM.

### 8.1 Conceito Enade de cursos de uma IES em determinada edição

```sql
SELECT
    i.codigo_ies,
    i.nome_ies,
    a.ano,
    a.codigo_curso_avaliado,
    a.area_avaliacao,
    a.modalidade_ensino_avaliacao,
    a.enade_conceito_continuo,
    a.enade_conceito_faixa,
    a.observacao_enade
FROM gold.fact_avaliacao_curso_superior AS a
JOIN gold.dim_ies AS i ON i.id_ies = a.id_ies
WHERE i.codigo_ies = %(codigo_ies)s
  AND a.ano = %(ano)s
  AND a.enade_conceito_faixa IS NOT NULL
ORDER BY a.area_avaliacao, a.codigo_curso_avaliado;
```

### 8.2 Distribuição de cursos por faixa do CPC em uma edição

```sql
SELECT
    a.cpc_faixa,
    COUNT(*) AS registros_avaliados
FROM gold.fact_avaliacao_curso_superior AS a
WHERE a.ano = %(ano)s
  AND a.cpc_faixa IS NOT NULL
GROUP BY a.cpc_faixa
ORDER BY a.cpc_faixa;
```

> **Cuidado:** a consulta acima conta **linhas publicadas na fato**, não necessariamente cursos oficiais distintos. Somente rotular como quantidade de cursos após validação de unicidade por `id_ies`, `ano`, `codigo_curso_avaliado` e demais elementos relevantes. Caso a fato contenha mais de uma linha por código oficial, revisar a métrica.

### 8.3 Evolução do IGC de uma instituição

```sql
SELECT
    i.codigo_ies,
    i.nome_ies,
    a.ano,
    a.igc_continuo,
    a.igc_faixa,
    a.igc_cursos_cpc_trienio_qtd,
    a.observacao_igc
FROM gold.fact_avaliacao_ies AS a
JOIN gold.dim_ies AS i ON i.id_ies = a.id_ies
WHERE i.codigo_ies = %(codigo_ies)s
ORDER BY a.ano;
```

## 9. Regras de interpretação para o chatbot e RAG

**[AV-LLM-001 | REGRA]** Pergunta “qual é o Enade/CPC/IDD **de um curso**?” → identificar indicador, edição, IES e código do curso avaliado. Se vários registros correspondem à descrição livre, solicitar desambiguação ou exibir opções verificadas, sem escolher silenciosamente.

**[AV-LLM-002 | REGRA]** Pergunta “qual é a nota **da faculdade**?” → **não** assumir automaticamente CPC ou IGC. Se a solicitação disser “indicador institucional”, utilizar IGC; caso contrário, esclarecer que há indicadores distintos por curso e por instituição.

**[AV-LLM-003 | REGRA]** Pergunta “qual é o Enade médio da cidade?” → informar que não existe um “Conceito Enade oficial da cidade” nesta modelagem. É possível, após validação, apresentar distribuição de cursos por faixa, com edição, universo e número de unidades avaliadas.

**[AV-LLM-004 | REGRA]** Pergunta sobre curso/IES que não aparece em um ano → distinguir falta de cobertura, ausência de avaliação, ausência de publicação e “Sem Conceito”, conforme dados e observações disponíveis. Não afirmar causa sem evidência.

**[AV-LLM-005 | REGRA]** Pergunta comparando “2020 e 2023” → a configuração não declara indicadores de avaliação de 2020. Não preencher 2020 com valor de 2019 ou 2021; informar indisponibilidade no recorte carregado.

**[AV-LLM-006 | REGRA]** Respostas devem mencionar o **nome exato do indicador, edição/ano, IES, código de curso quando aplicável**, valor/faixa, filtros de área/modalidade e ressalvas de cobertura/metodologia. Não apresentar uma conclusão causal como consequência automática de mudança de conceito.

## 10. Testes recomendados antes da aprovação do documento

| ID          | Teste                                                                               | Critério                                                                  |
| ----------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| AV-TEST-001 | Unicidade da chave `CHAVE_FACT_AVALIACAO_CURSO_SUPERIOR`                            | Nenhuma duplicidade                                                       |
| AV-TEST-002 | Unicidade da chave `(id_ies, ano)` para IGC                                         | Nenhuma duplicidade                                                       |
| AV-TEST-003 | Integridade das FKs com IES, curso, localidade e calendário                         | Sem órfãos                                                                |
| AV-TEST-004 | Cobertura por indicador e ano                                                       | `COUNT(*)` / `COUNT(coluna)` por Enade, CPC, IDD, IGC                     |
| AV-TEST-005 | Faixas publicadas                                                                   | Valores válidos por edição; nulos/SC preservados                          |
| AV-TEST-006 | Reconciliar totais de inscritos/participantes                                       | Conferir por fonte, sem somar ENADE+CPC+IDD                               |
| AV-TEST-007 | Colisões de `id_curso_superior` analítico com múltiplos `codigo_curso_avaliado`     | Identificar e documentar                                                  |
| AV-TEST-008 | Área/modalidade/localidade e EAD                                                    | Validar com arquivos originais e notas da edição                          |
| AV-TEST-009 | IGC em IES que só aparece em avaliações                                             | Identificar classificação/sede possivelmente ausente                      |
| AV-TEST-010 | Checar `ano` da Gold contra `ano_enade`, `ano_cpc`, `ano_idd`, `ano_igc` das Silver | Registrar critérios de harmonização                                       |
| AV-TEST-011 | Verificar 2025 no Conceito Enade                                                    | Confirmar quais áreas realmente foram carregadas                          |
| AV-TEST-012 | Comparar amostras Gold com XLSX Inep                                                | Sem alterações involuntárias de faixas, casas decimais, SC ou observações |

## 11. Pendências para aprovação da versão 1.0.0

1. **[INSPEÇÃO CONCLUÍDA; TESTE DE FONTE PENDENTE]** As quatro Bronze foram inspecionadas e chamam o leitor Excel compartilhado com contratos e abas configurados. Confirmar em arquivos XLSX amostrais e na implementação compartilhada a leitura de `SC`, nulos, abas e layout por edição.
2. **[INSPEÇÃO CONCLUÍDA; RECONCILIAÇÃO PENDENTE]** As quatro Silver foram inspecionadas: validam contratos, tipos e chaves únicas por fonte; CPC corrige códigos municipais via GEO com auditoria. Testar valores e observações “SC”/nulos contra os XLSX de origem e as funções compartilhadas.
3. **[INSPEÇÃO CONCLUÍDA; AUDITORIA PENDENTE]** As duas fatos Gold foram inspecionadas e a estratégia de prioridade Enade→CPC→IDD foi registrada em `AV-ETL-001` a `AV-ETL-004`. É necessário examinar o arquivo de divergências de descritores por curso/ano e o comportamento efetivo de fallback de cursos com amostras reais.
4. **[PARCIALMENTE VALIDADO]** A execução local reportada de `postgres.validate_gold --deep` retornou 46 OK, 5 alertas documentais e 0 erros, incluindo unicidade das fatos, constraints e cobertura de anos. Os 12 testes AV-TEST ainda **não foram integralmente executados**: faltam conferências de `SC`, notas, auditorias, amostras XLSX e metodologias por edição.
5. **[PENDENTE]** Verificar notas técnicas de metodologia específicas dos anos 2018, 2019, 2021, 2022, 2023 e as publicações específicas de 2025. Não reutilizar automaticamente uma fórmula antiga para todas as edições.
6. **[PENDENTE]** Decidir se estatísticas descritivas agregadas de conceitos serão permitidas no chatbot e, caso positivo, documentar denominador, elegibilidade, ponderação e rotulagem **não oficial**. Por padrão, **não produzir agregados numéricos de conceitos**.
