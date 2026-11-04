---
id: regras_gerais
area: educacao
categoria: regras_transversais
versao: "0.9.1"
status: revisao_humana_pendente
fonte_verdade_semantica: "docs/"
fonte_verdade_estrutura: "PostgreSQL pg_catalog; espelho em rag.schema_catalog"
ultima_revisao_documental: "2026-11-03"
documentos_relacionados:
  - docs/indicadores.md
  - docs/educacao_superior.md
  - docs/educacao_basica.md
  - docs/avaliacoes.md
---

# Regras gerais — Consultas analíticas e uso do RAG no EI DataBot

> **Status:** primeira versão para revisão humana. Este documento consolida as regras **transversais** dos quatro documentos de domínio e as diretrizes de revisão documental do projeto. Não cria novos indicadores, não aprova regras pendentes e não substitui os contratos específicos de cada fonte. Posteriormente, o proprietário executou `postgres.validate_gold --deep` e informou 46 OK, 5 alertas documentais e 0 erros. Isso confirma **parte** dos critérios estruturais, sem substituir os testes metodológicos, de conteúdo ou de segurança da LLM/RAG.
>
> **Uso previsto:** referência humana para implementar e testar interpretação de perguntas, seleção de consultas SQL, resposta fundamentada e futura recuperação RAG. Os identificadores `RG-*` devem permanecer estáveis entre revisões. As marcações **[CONSOLIDADA]**, **[POLÍTICA PROPOSTA]** e **[PENDENTE]** descrevem o grau de evidência/decisão, não aprovação automática para produção.

## 1. Hierarquia de fontes e governança

**[RG-GOV-001 | CONSOLIDADA]** Os documentos Markdown em `docs/` são a **fonte humana das regras de negócio**. O PostgreSQL (`pg_catalog`, `information_schema`) descreve a estrutura física efetiva; `rag.schema_catalog` registra o catálogo técnico sincronizado. A existência de uma coluna não valida sua definição, finalidade ou fórmula.

**[RG-GOV-002 | CONSOLIDADA]** Mudanças no ETL, na estrutura Gold ou no catálogo técnico **não podem produzir nem aprovar regras de negócio automaticamente**. Criar ou alterar uma regra semântica requer edição de Markdown e revisão humana, com registro de versão e rastreabilidade.

**[RG-GOV-003 | CONSOLIDADA]** `docs/indicadores.md` conecta IDs `CAT-*` a tabelas, colunas e operações; os documentos `educacao_superior.md`, `educacao_basica.md` e `avaliacoes.md` fornecem os significados, restrições e pendências detalhados. O presente arquivo define convenções comuns. Nenhum deles, isoladamente, concede permissão de executar SQL arbitrário.

**[RG-GOV-004 | CONSOLIDADA]** Ao encontrar divergência entre **existência física** e documentação, o backend deve usar o schema publicado para verificar existência e tipo, **sem reinterpretar** o significado do campo. Ao encontrar conflito **semântico** entre documentos, sinalizar revisão humana; não escolher a versão com embedding mais próximo, mais recente ou mais repetida como automaticamente correta.

**[RG-GOV-005 | CONSOLIDADA]** Preservar a origem das afirmações: **[ETL]** (comportamento inspecionado), **[CONTRATO]** (campo/chave/arquivo previsto), **[INEP]** (metodologia de fonte oficial), **[REGRA]** (restrição analítica definida pelo projeto) e **[PENDENTE]** (não verificado). Um contrato físico ou a presença de um arquivo não comprovam cobertura ou metodologia efetiva.

**[RG-GOV-006 | POLÍTICA PROPOSTA]** Para o uso em produção, recuperar e aplicar como regras operacionais somente versões **aprovadas**. Documentos em revisão podem permanecer armazenados e ser usados em ambiente de desenvolvimento, com identificação explícita de rascunho; conteúdos marcados `[PENDENTE]` não podem se converter em fatos apresentados ao usuário. A representação desse estado em `rag.documents` ainda será implementada.

## 2. Vocabulário e unidade de análise

| Termo                        | Significado neste projeto                                                  | Cuidado obrigatório                                                              |
| ---------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **Matrícula**                | Contagem de matrículas/vínculos reportados na fonte e no recorte da fato   | Não equivale automaticamente a pessoas únicas ou CPFs distintos                  |
| **Ingressante / concluinte** | Contagem associada a ingresso ou conclusão na referência do Censo Superior | Não confundir com inscritos em seleção, participantes do Enade ou matrículas     |
| **Escola**                   | Estabelecimento identificado em `dim_escola`                               | Contagem de cadastro não é contagem de escolas com matrícula no ano              |
| **IES**                      | Instituição identificada em `dim_ies`                                      | Cadastro institucional não equivale a IES com matrículas ou IGC publicado no ano |
| **Curso analítico**          | Classificação consolidada de `dim_curso_superior`                          | Não equivale necessariamente ao código oficial e-MEC nem a uma oferta/campus     |
| **Curso avaliado**           | Unidade que inclui `codigo_curso_avaliado` na fato de avaliação            | Não substituir pela identidade analítica de curso                                |
| **Ano censitário**           | Ano de referência da observação de educação                                | Não equivale à data de processamento ou de publicação do resultado               |
| **Edição de avaliação**      | Ano de referência de Enade/CPC/IDD/IGC                                     | Pode diferir do ano de divulgação; coberturas e ciclos variam                    |
| **Sem Conceito (SC)**        | Situação específica em indicadores de avaliação                            | Não equivale a zero nem a nota baixa                                             |

**[RG-UNI-001 | CONSOLIDADA]** Toda resposta quantitativa deve identificar a unidade: vínculos de matrícula, instituições distintas, escolas distintas, cursos avaliados, vagas, inscrições, notas, proporções ou outra unidade explicitamente catalogada. Não mudar de unidade por conveniência da interpretação da LLM.

**[RG-UNI-002 | CONSOLIDADA]** Uma medida armazenada como total de vínculos não deve ser apresentada como total de **alunos únicos** sem dados individualizados e uma regra aprovada de deduplicação, ausentes nas fatos agregadas documentadas.

## 3. Seleção de fatos, granularidade e relacionamentos

| Fato                                 | Grão documentado                                          | Consulta principal                                              |
| ------------------------------------ | --------------------------------------------------------- | --------------------------------------------------------------- |
| `gold.fact_educacao_basica`          | Escola × ano                                              | Contagens de matrículas por escola, etapa ou recorte disponível |
| `gold.fact_educacao_superior`        | IES × curso analítico × localidade analítica × ano        | Contagens de matrículas, vagas, ingressos e conclusões          |
| `gold.fact_educacao_superior_turno`  | IES × curso analítico × localidade × ano × turno          | Seis medidas por turno **presencial**                           |
| `gold.fact_avaliacao_curso_superior` | IES × curso avaliado × curso analítico × localidade × ano | Conceito Enade, IDD, CPC e componentes                          |
| `gold.fact_avaliacao_ies`            | IES × ano                                                 | IGC e componentes por instituição                               |

**[RG-GRA-001 | CONSOLIDADA]** Antes de calcular, selecionar **uma fato principal** e confirmar que ela contém a unidade, o indicador e a granularidade solicitados. A mera presença de dimensões em comum não autoriza juntar fatos diretamente.

**[RG-GRA-002 | CONSOLIDADA]** Joins de uma fato com suas dimensões devem utilizar as chaves documentadas e preservar cardinalidade 1:N (uma linha de dimensão para várias da fato). Validar a unicidade real das chaves dimensionais; caso contrário, a agregação pode duplicar medidas.

**[RG-GRA-003 | CONSOLIDADA]** Para comparar medidas de fatos diferentes, consultar/agregar cada fato **separadamente**, alinhando período, unidade, localidade e filtros. Se a compatibilidade não estiver comprovada, não produzir um indicador combinado.

**[RG-GRA-004 | CONSOLIDADA]** `fact_educacao_superior` e `fact_educacao_superior_turno` contêm universos relacionados: **não** somar seus valores para criar um total. A fato por turno tem somente `DIURNO` e `NOTURNO` e é exclusivamente presencial. Não presumir conciliação exata entre soma de turnos e fato geral sem teste específico.

**[RG-GRA-005 | CONSOLIDADA]** As notas CPC/Enade/IDD pertencem a cursos avaliados; o IGC pertence à IES. Não fazer join direto entre as duas fatos avaliativas para somar ou tirar médias, pois o IGC pode ser multiplicado pelo número de cursos.

**[RG-GRA-006 | CONSOLIDADA]** Contagem de entidades **com ocorrência** em um ano deve partir da fato correspondente, normalmente com `COUNT(DISTINCT chave)` e condição positiva da métrica apropriada. Contar linhas em `dim_ies` ou `dim_escola` responde a uma questão cadastral diferente.

## 4. Tipos de indicadores e agregações

| Tipo de operação      | Condição de uso                                                         | Condição de bloqueio                                                               |
| --------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `SOMA_ANUAL`          | Contagem aditiva na mesma fato, ano e recorte compatível                | Notas, conceitos, proporções ou mistura de grãos                                   |
| `SERIE_ANUAL`         | Uma medida por ano efetivamente observado                               | Completar anos ausentes com zero ou interpolação                                   |
| `VARIACAO_ABSOLUTA`   | Valor final − inicial, mesma métrica e universo                         | Extremos ausentes ou não comparáveis                                               |
| `VARIACAO_PERCENTUAL` | `(final / inicial − 1) × 100`                                           | Inicial nulo ou igual a zero; mudança de definição não avaliada                    |
| `RAZAO_AGREGADA`      | Razão dos **totais** de numerador e denominador, no mesmo recorte       | Denominador nulo/zero, universos distintos, atribuição indevida de caráter oficial |
| `CONTAGEM_DISTINTA`   | Identidade e filtros de ocorrência validados                            | Contagem indistinta de linhas de dimensão ou duplicidades de fato                  |
| `VALOR_UNIDADE`       | Nota/conceito de uma unidade avaliada e edição                          | Somar ou transformar nota de curso/IES em nota oficial territorial                 |
| `DISTRIBUICAO`        | Contagem de unidades por faixa/edição com chave validada                | Média não autorizada, mistura de edições ou duplicidade                            |
| `NAO_AUTORIZADA`      | Indicador desconhecido, filtros inviáveis ou granularidade insuficiente | Nunca responder por aproximação inventada                                          |

**[RG-AGG-001 | CONSOLIDADA]** Preferir a coluna de **total já materializada** em cada domínio. Não reconstruir matrículas totais somando famílias sobrepostas (etapas, educação especial, sexo, cor/raça, financiamento, forma de ingresso etc.). Recortes independentes não representam necessariamente partições disjuntas.

**[RG-AGG-002 | CONSOLIDADA]** Somar estoques de matrícula de anos distintos **não** produz estudantes únicos em todo o período. Retornar série anual ou comparação dos extremos, com cada período identificado.

**[RG-AGG-003 | CONSOLIDADA]** Percentuais derivados pelo projeto devem ser calculados a partir de numerador e denominador **agregados com os mesmos filtros**, com denominador positivo. Não tirar a média simples de taxas de escolas/cursos para representar a taxa do conjunto, salvo definição explícita e aprovada.

**[RG-AGG-004 | CONSOLIDADA]** Não somar, ponderar ou calcular automaticamente uma “nota oficial” municipal/estadual a partir de Conceito Enade, CPC, IDD ou IGC. Os índices e componentes não são medidas aditivas. Estatísticas descritivas sobre notas exigem autorização, unidade, universo e rotulagem **não oficial** explícitos.

**[RG-AGG-005 | CONSOLIDADA]** Não recalcular CPC, IGC, IDD ou faixas de conceito com fórmulas presumidas. Utilizar os valores publicados e materializados, respeitando as regras e notas técnicas da edição.

**[RG-AGG-006 | CONSOLIDADA]** `rematriculados` no Censo Superior é **medida derivada do ETL**, calculada por linha como `max(matriculados_linha − ingressantes_linha, 0)` antes da agregação. Utilizar o campo Gold materializado; não o substituir pela subtração entre totais agregados.

**[RG-AGG-007 | PENDENTE]** Padrão de arredondamento e casas decimais na apresentação não foi aprovado nos documentos fornecidos. A aplicação deverá preservar a precisão do cálculo e adotar uma convenção de exibição após revisão humana; não arredondar valores intermediários silenciosamente.

## 5. Tempo, cobertura e comparação histórica

| Conjunto                         | Período **configurado** no ETL     | Cuidado                                                    |
| -------------------------------- | ---------------------------------- | ---------------------------------------------------------- |
| Censo da Educação Superior       | 2018–2024                          | Consultar anos efetivamente presentes na fato              |
| Censo Escolar da Educação Básica | 2018–2025                          | Variáveis e formatos podem diferir entre edições           |
| Conceito Enade                   | 2018, 2019, 2021, 2022, 2023, 2025 | 2025 pode ter cobertura parcial de áreas                   |
| CPC, IDD e IGC                   | 2018, 2019, 2021, 2022, 2023       | Não tratar anos configurados como sequência anual contínua |

**[RG-TEM-001 | CONSOLIDADA]** Diferenciar **ano configurado**, **ano presente em `dim_calendario`** e **ano com registros válidos da métrica na fato**. O calendário reúne anos de diferentes fontes e não garante cobertura de um indicador.

**[RG-TEM-002 | CONSOLIDADA]** Antes de executar comparação temporal, verificar disponibilidade do indicador nos anos solicitados e a compatibilidade metodológica das edições. Não imputar 2020 a Enade/CPC/IDD/IGC caso a configuração não contenha essa referência; também não presumir que a edição 2025 do Enade cubra todos os cursos.

**[RG-TEM-003 | CONSOLIDADA]** Ausência de registros para um ano não equivale a zero. Não interpolar, extrapolar ou projetar valores como se fossem observações do Gold. Previsões, se algum dia oferecidas, precisarão de procedimento e rotulagem próprios, fora do MVP atual.

**[RG-TEM-004 | CONSOLIDADA]** Para comparações entre dois anos, indicar o valor inicial, o final, a variação absoluta e, quando calculável, a percentual. Não chamar essa variação de **taxa anualizada** nem inferir causalidade do crescimento/queda.

**[RG-TEM-005 | CONSOLIDADA]** Resultados Enade/CPC/IDD/IGC devem ser atribuídos ao **ano de referência/edição**, que pode ser distinto da data de divulgação. O IGC incorpora uma janela de avaliação de três anos; comparar edições não equivale a comparar anos independentes.

## 6. Geografia, modalidade e dimensões históricas

**[RG-GEO-001 | CONSOLIDADA — CRÍTICA]** Na fato geral de educação superior, os cursos EAD são vinculados à localidade sentinela `codigo_municipio = -1` (`municipio = 'EAD'`, `uf = 'EAD'`). A sentinela **não** representa município, sede ou residência de estudante. Portanto, recortes por município da oferta na Gold **não incluem EAD municipal**.

**[RG-GEO-002 | CONSOLIDADA]** Em perguntas sobre matrículas superiores “em município X”, informar claramente que a consulta municipal disponível representa **oferta presencial localizada no município**. Não distribuir EAD entre municípios usando sede da IES, distância geográfica ou valores imputados. A política de responder com ressalva ou solicitar esclarecimento permanece pendente de aprovação em `docs/educacao_superior.md`.

**[RG-GEO-003 | CONSOLIDADA]** Para educação básica, o município se refere à **localização da escola** segundo a modelagem Gold; não à residência dos alunos. Para educação superior, distinguir município da oferta presencial (`dim_localidade`) de município da sede institucional (`dim_ies`). Para IGC, a fato institucional não contém `id_localidade`.

**[RG-GEO-004 | CONSOLIDADA]** Preferir `codigo_municipio` (IBGE) como identificador quando disponível; caso contrário, validar **município + UF** para evitar homônimos. Nunca confundir nome de município com unidade administrativa de mesma grafia em outra UF.

**[RG-GEO-005 | CONSOLIDADA]** `dim_ies` mantém o **cadastro mais recente** por código de IES, não histórico SCD2. Nomes, categoria administrativa, organização e sede usados em recortes históricos podem refletir atributos atuais. A política temporal de `dim_escola` **ainda não foi verificada** nos seus módulos específicos.

**[RG-GEO-006 | CONSOLIDADA]** `distancia_referencia_km` da dimensão localidade é uma estimativa derivada da referência geográfica adotada pelo projeto; para o sentinela EAD, o valor `3600` é convencional, **não distância real**. Excluir esse sentinela de cálculos de proximidade, médias e rankings espaciais.

**[RG-GEO-007 | PENDENTE]** Não transportar automaticamente a regra geográfica da **fato censitária** para a `fact_avaliacao_curso_superior`: a atribuição territorial das avaliações depende de inspeção de seus transformadores e arquivos de origem.

## 7. Nulos, zeros, ausência de linha e Sem Conceito

| Estado                | Significado de resposta                                   | Ação proibida                                              |
| --------------------- | --------------------------------------------------------- | ---------------------------------------------------------- |
| **Nenhuma linha**     | Recorte não encontrado na base consultada                 | Dizer que o valor observado foi zero                       |
| **`NULL`**            | Indicador sem valor informado/materializado               | Substituir por zero sem regra do ETL comprovada            |
| **Zero numérico**     | Valor zero presente no Gold; interpretação depende do ETL | Afirmar que a fonte original necessariamente declarou zero |
| **Sem Conceito (SC)** | Situação de avaliação conforme origem/edição              | Interpretar como conceito 0 ou reprovação                  |
| **Ano sem cobertura** | Não há edição/observação disponível                       | Completar, interpolar ou usar edição vizinha               |

**[RG-DAD-001 | CONSOLIDADA]** Em educação superior, o ETL faz preenchimento de nulos com zero em certas agregações de métricas das fatos censitárias. Isso pode apagar a distinção entre nulo original e zero na Gold. A resposta deve evitar tratar todo zero como declaração original explícita da fonte.

**[RG-DAD-002 | CONSOLIDADA]** Na educação básica, o contrato permite métricas nulas. Antes de somar, avaliar **cobertura** por ano, inclusive `COUNT(campo)`. `SUM()` ignora nulos e pode produzir um subtotal sem que todas as escolas tenham informado o indicador.

**[RG-DAD-003 | CONSOLIDADA]** Em avaliação, conceitos nulos, ausentes e `SC` não significam baixo desempenho. Quando uma consulta não encontra nota, diferenciar falta de registro, edição não disponível e ausência de conceito **apenas quando os dados realmente permitirem**.

**[RG-DAD-004 | CONSOLIDADA]** O resultado SQL `0` calculado para `COUNT(*)` sobre conjunto vazio é uma **contagem de registros encontrados**, não prova automática de ocorrência zero do fenômeno educacional. Separar indicadores de qualidade/cobertura da métrica solicitada.

## 8. Contrato de comportamento da LLM e das respostas

**[RG-LLM-001 | CONSOLIDADA]** A LLM interpreta a pergunta; o backend resolve o identificador `CAT-*` em um catálogo permitido, valida dimensões, valores e períodos, escolhe um **template SQL parametrizado** e realiza os cálculos. A LLM não escolhe livremente tabelas/colunas executáveis e **não gera SQL arbitrário para execução**.

**[RG-LLM-002 | CONSOLIDADA]** O RAG recupera contexto documental relevante, identificando origem, ID da regra e status. A recuperação semântica **não altera** direitos de consulta, existência de colunas, fórmulas aprovadas ou veracidade dos resultados SQL.

**[RG-LLM-003 | CONSOLIDADA]** A chamada responsável pela redação final pode explicar e contextualizar **somente** os valores efetivamente retornados pelo SQL e as regras/documentos aplicáveis. Não completar lacunas com números plausíveis, estatísticas externas não consultadas, causas supostas ou inferências sobre estudantes individuais.

**[RG-LLM-004 | CONSOLIDADA]** Quando a pergunta for ambígua e a escolha afetar seu significado — p.ex. curso analítico versus código e-MEC, conceito de curso versus IGC institucional, cidade da sede versus local de oferta — esclarecer a unidade/recorte; não escolher silenciosamente uma interpretação incompatível com as regras.

**[RG-LLM-005 | CONSOLIDADA]** Quando o modelo não fornecer a métrica, interseção ou granularidade pedida — p.ex. meninas indígenas por etapa, residentes EAD por município ou taxa de abandono não materializada — responder explicitamente à limitação, sem fabricar proxy ou resultado numérico.

**[RG-LLM-006 | POLÍTICA PROPOSTA]** Estrutura mínima de resposta analítica em produção: (a) resultado e unidade; (b) fonte e ano/edição; (c) filtros/granularidade; (d) ressalva metodológica importante; (e) referências rastreáveis aos IDs de indicadores/regras utilizados, quando houver. O formato exato de exibição será definido na integração frontend/API.

**[RG-LLM-007 | CONSOLIDADA]** O histórico da conversa pode esclarecer referências contextuais como “no mesmo município” ou “e em 2023?”, **sem suplantar** os parâmetros explícitos da pergunta atual, a disponibilidade do banco ou as regras aprovadas. Uma resposta anterior incorreta não se torna fonte de verdade.

**[RG-LLM-008 | CONSOLIDADA]** Resultado inexistente, erro na API Gemini, documentação em revisão ou indisponibilidade do banco são condições distintas. Tratar falhas operacionalmente como erros/limitações; não mascarar falhas com uma resposta inventada.

## 9. Segurança, privacidade e SQL

**[RG-SEG-001 | CONSOLIDADA]** Consultas analíticas e recuperação do RAG em tempo de atendimento devem usar credenciais com **permissão de leitura** em `gold` e nos objetos de recuperação de `rag`. Ingestão e atualização do catálogo terão permissões separadas, apropriadas a seus processos.

**[RG-SEG-002 | CONSOLIDADA]** Usar SQL previamente definido e filtros por **parâmetros** (`psycopg`). Identificadores de tabela e coluna são resolvidos de listas autorizadas pelo backend — não interpolados a partir do texto livre do usuário ou de trechos RAG.

**[RG-SEG-003 | CONSOLIDADA]** Validar limites de período, ordenação, tamanho dos resultados e presença do identificador do indicador antes de executar consultas. Nunca executar comandos de alteração (`INSERT`, `UPDATE`, `DELETE`, `DDL`) como resposta a uma pergunta analítica.

**[RG-SEG-004 | CONSOLIDADA]** Não registrar chaves de API, senhas, prompts completos contendo dados sensíveis ou parâmetros de conexão em logs operacionais. O histórico de conversa em schema `app` será tratado separadamente dos dados analíticos e do RAG, com autorização de escrita específica.

**[RG-SEG-005 | POLÍTICA PROPOSTA]** Antes de expor o serviço a empresas ou usuários externos, validar isolamento de sessões, limites de uso, controle de acesso, retenção do histórico e tratamento de conteúdo não confiável nos documentos recuperados. Nenhum desses controles é considerado implementado por este Markdown.

## 10. Regras para futura ingestão vetorial e sincronização

**[RG-RAG-001 | CONSOLIDADA]** A origem dos documentos é `docs/*.md`; a ingestão deverá conservar **caminho, ID, versão, status, hash e identificadores das regras**. O banco vetorial é índice de recuperação; não substitui o arquivo Markdown versionado.

**[RG-RAG-002 | CONSOLIDADA]** Comparar hash do documento e, quando aplicável, dos fragmentos; atualizar embeddings **somente do conteúdo alterado**. Evitar recomputação desnecessária em execução repetida. Persistir o nome e a dimensão do modelo de embeddings para impedir mistura de vetores incompatíveis.

**[RG-RAG-003 | CONSOLIDADA]** Ao alterar ou remover uma regra, conservar seu identificador para auditoria e impedir recuperação de versões obsoletas como vigentes. Não reutilizar IDs para significados diferentes.

**[RG-RAG-004 | CONSOLIDADA]** Validar referências explícitas a tabelas/colunas contra `rag.schema_catalog` atualizado e, quando necessário, `pg_catalog`. Uma referência inexistente ou incompatível gera **alerta de inconsistência**, não correção automática pela LLM. Referências genéricas em prosa exigirão critérios de extração que evitem falsos positivos.

**[RG-RAG-005 | CONSOLIDADA]** A futura atualização será acoplada **após** a publicação Gold bem-sucedida: sincronizar catálogo técnico, verificar compatibilidade documental e atualizar índice vetorial. Falha na API de embeddings **não desfaz** a publicação dos dados Gold; deve ser registrada para retentativa independente.

**[RG-RAG-006 | CONSOLIDADA]** A ingestão não deve conferir aprovação semântica. Um documento em revisão continua **em revisão** mesmo que tenha embedding atualizado. Aplicar filtro de status para não apresentar regras `[PENDENTE]` como aprovadas.

**[RG-RAG-007 | POLÍTICA PROPOSTA]** Para preservar contexto de cada regra, dividir documentos por títulos e IDs estáveis, sem juntar regras de domínios diferentes no mesmo fragmento. Registrar trilha que permita informar **qual arquivo e regra** fundamentaram a resposta. A estratégia exata de chunking será validada ao implementar `postgres/sync_rag.py`.

## 11. Testes mínimos de integração e consistência

Os itens seguintes são **critérios propostos de validação**, não resultados executados.

| ID            | Validação                               | Resultado esperado                                                     |
| ------------- | --------------------------------------- | ---------------------------------------------------------------------- |
| `RG-TEST-001` | Catálogo técnico sincronizado após Gold | Tabelas e colunas da publicação refletidas em `rag.schema_catalog`     |
| `RG-TEST-002` | Chaves de dimensão e grãos de fato      | Sem multiplicação por join nem duplicidade não prevista                |
| `RG-TEST-003` | Indicadores `CAT-*` versus schema       | Referências inexistentes sinalizadas e bloqueadas para consulta        |
| `RG-TEST-004` | Cobertura temporal efetiva              | Anos de cada fato e métrica verificados; ausências não preenchidas     |
| `RG-TEST-005` | Recorte municipal de educação superior  | EAD sentinela não atribuída a municípios reais                         |
| `RG-TEST-006` | Avaliações                              | Conceitos não somados, `SC`/nulos tratados separadamente               |
| `RG-TEST-007` | Atualização incremental de documentação | Segunda execução sem mudança: nenhum re-embedding necessário           |
| `RG-TEST-008` | Alteração/remoção de documento          | Versão anterior não recuperável como regra vigente                     |
| `RG-TEST-009` | Falha de embeddings                     | Gold preservado; atualização RAG sinalizada como incompleta            |
| `RG-TEST-010` | Pergunta fora da granularidade          | Resposta de limitação sem SQL improvisado ou valores inventados        |
| `RG-TEST-011` | Prompt/documento adversarial            | Texto recuperado não consegue modificar política de SQL nem permissões |
| `RG-TEST-012` | Rastreabilidade da resposta             | IDs de indicador e regra usados ficam identificáveis                   |

### SQL de diagnóstico — cobertura anual de uma métrica

Exemplo limitado à fato de educação básica, para distinguir anos com linhas daqueles com valor informado. **Não comprova, isoladamente, qualidade ou correção metodológica.**

```sql
SELECT
    ano,
    COUNT(*) AS linhas_escola_ano,
    COUNT(matriculas_educacao_basica) AS linhas_com_metrica_informada,
    SUM(matriculas_educacao_basica)::bigint AS matriculas
FROM gold.fact_educacao_basica
GROUP BY ano
ORDER BY ano;
```

### SQL de diagnóstico — objetos do catálogo técnico

```sql
SELECT
    object_name,
    jsonb_array_length(definition -> 'columns') AS colunas
FROM rag.schema_catalog
WHERE object_name LIKE 'gold.%'
ORDER BY object_name;
```

Essas consultas são destinadas a diagnóstico. Resultados reais, integridade referencial e cobertura por edição precisam ser executados e registrados no ambiente do projeto antes da aprovação.

## 12. Pendências para aprovação da versão 1.0.0

**[RG-PEN-001 | PARCIALMENTE RESOLVIDA]** Módulos específicos de educação básica e avaliações foram inspecionados e as respectivas regras operacionais adicionadas aos documentos de domínio. Confirmar valores em fontes oficiais e revisar auditorias de divergência, especialmente em Enade/CPC/IDD.

**[RG-PEN-002 | PARCIALMENTE RESOLVIDA]** O proprietário reportou validação profunda com 46 OK, 5 alertas documentais e 0 erros (unicidade, constraints, cobertura, EAD e turnos). Não houve comprovação de execução de todos os testes de reconciliação de valores ou verificação metodológica por edição.

**[RG-PEN-003]** Definir a política conversacional aprovada para perguntas municipais de educação superior sem modalidade explícita (responder presencial com ressalva ou pedir esclarecimento).

**[RG-PEN-004]** Aprovar, caso desejado, formato de resposta e arredondamento, operações derivadas permitidas e critérios para estatísticas descritivas não oficiais sobre conceitos de avaliação.

**[RG-PEN-005]** Definir e implementar status/versionamento e filtro de aprovação no índice vetorial; testar alteração, descontinuação e revogação de documentos.

**[RG-PEN-006]** Aprovar a lista efetiva de indicadores liberados para o MVP, distinta do inventário físico de 158 campos numéricos.

**[RG-PEN-007]** Revisar com o responsável do projeto os documentos `docs/*.md` antes de alterar os respectivos status para `aprovado`. Até então, este arquivo não constitui liberação para produção.
