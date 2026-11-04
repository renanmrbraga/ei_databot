---
id: indicadores
area: educacao
categoria: catalogo_de_indicadores
versao: "0.9.1"
status: revisao_humana_pendente
fonte_verdade_semantica: docs/
fonte_metadados_tecnicos: rag.schema_catalog
ultima_revisao_documental: "2026-11-03"
---

# Catálogo consolidado de indicadores — EI DataBot

> **Status:** rascunho técnico para revisão humana. Este catálogo organiza os indicadores **já previstos no contrato de dados do ETL**, mas não concede aprovação automática a todos eles para o chatbot. A publicação em produção depende dos documentos de domínio, da verificação do esquema efetivamente carregado e dos testes de qualidade. Valores, cobertura efetiva e resultados do banco **não** foram recalculados nesta redação.
>
> **Governança:** as diretrizes de revisão e rastreabilidade documental estão consolidadas em `docs/regras_gerais.md`. Alterações de código ou de schema podem atualizar metadados técnicos, **nunca** aprovar novas regras; alterações neste arquivo exigem revisão humana. Na ingestão vetorial, preservar IDs, versão e hash de conteúdo, indexar apenas textos alterados e sinalizar referências de colunas ausentes em `rag.schema_catalog`.

## 1. Objetivo, fontes de evidência e limites

Este documento é um **índice semântico consolidado**, não uma cópia de todo o dicionário do Inep, nem um mecanismo de SQL livre. Ele liga um pedido do usuário a uma **coluna existente, uma tabela fato, uma granularidade e uma política de agregação**. Em caso de divergência, o metadado físico vem do PostgreSQL e a interpretação vem das regras humanas revisadas.

| Origem                                   | Contribuição                                                    | Nível de comprovação                                                    |
| ---------------------------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `etl/educacao/schema.py` (ZIP fornecido) | Colunas, tipos, contratos e chaves das fatos                    | **CONTRATO**, não garantia de disponibilidade por ano                   |
| `docs/educacao_superior.md`              | Regras derivadas dos módulos de educação superior analisados    | **ETL/REGRA**, com pendências indicadas no próprio documento            |
| `docs/educacao_basica.md`                | Definições e famílias das 54 métricas censitárias               | **CONTRATO/REGRA**; transformadores específicos ainda não inspecionados |
| `docs/avaliacoes.md`                     | Enade, IDD, CPC, IGC e restrições de agregação                  | **CONTRATO/REGRA**; transformação das avaliações ainda não inspecionada |
| `rag.schema_catalog`                     | Reflexo do schema físico `gold` após sincronização              | **TÉCNICO**; não valida metodologia nem preenchimento                   |
| `docs/regras_gerais.md`                  | Diretrizes transversais de revisão, rastreabilidade e consultas | **REGRAS** em revisão humana                                            |

### 1.1 Inventário quantitativo dos contratos

| Fato Gold                            | Grão lógico                                                       | Campos de métrica numéricos |
| ------------------------------------ | ----------------------------------------------------------------- | --------------------------: |
| `gold.fact_educacao_superior`        | IES × curso analítico × localidade × ano                          |                          47 |
| `gold.fact_educacao_superior_turno`  | IES × curso analítico × localidade × ano × turno                  |                           6 |
| `gold.fact_educacao_basica`          | escola × ano                                                      |                          54 |
| `gold.fact_avaliacao_curso_superior` | IES × curso avaliado × classificação analítica × localidade × ano |                          42 |
| `gold.fact_avaliacao_ies`            | IES × ano                                                         |                           9 |

**Total: 158 campos numéricos catalogados em cinco fatos.** É a soma de _campos por fato_, não 158 conceitos únicos: por exemplo, `matriculados` aparece na fato geral e na fato por turno com granularidades diferentes. Além dessas métricas, existem chaves, atributos e observações textuais que não são métricas aditivas.

### 1.2 Abrangência temporal contratada (não cobertura comprovada)

| Domínio                         | Referências configuradas no ETL    | Condição de uso                                                         |
| ------------------------------- | ---------------------------------- | ----------------------------------------------------------------------- |
| Educação superior (Censo)       | 2018–2024                          | Confirmar anos e filtros presentes na fato                              |
| Educação básica (Censo Escolar) | 2018–2025                          | Confirmar cobertura e compatibilidade histórica por variável            |
| Conceito Enade                  | 2018, 2019, 2021, 2022, 2023, 2025 | 2025 não implica todas as áreas; 2020 não é edição no contrato          |
| CPC, IDD e IGC                  | 2018, 2019, 2021, 2022, 2023       | Não interpolar anos ausentes nem assumir cobertura de todas as unidades |

## 2. Contrato de interpretação e operações

| Operação semântica    | Definição e proteção                                                                                                                                                            |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SOMA_ANUAL`          | `SUM(coluna)` por ano e filtros, **somente** para contagens aditivas no grão da fato; não somar séries de estoque para afirmar alunos únicos plurianuais                        |
| `SOMA_CONDICIONAL`    | Soma de quantidades por unidade avaliada, **apenas** após provar unicidade no ano/edição e que o universo/medida permitem agregação; não aplicada a notas, proporções ou faixas |
| `SERIE_ANUAL`         | Devolver uma observação por `ano`, sem completar ausências por zero/interpolação                                                                                                |
| `VARIACAO_ABSOLUTA`   | `valor_final - valor_inicial`, quando ambos presentes e comparáveis                                                                                                             |
| `VARIACAO_PERCENTUAL` | `(valor_final / valor_inicial - 1) * 100`, apenas se `valor_inicial` diferente de zero e não nulo                                                                               |
| `RAZAO_AGREGADA`      | `SUM(numerador) / NULLIF(SUM(denominador), 0)` no **mesmo recorte**; não média simples de percentuais; indicar quando for cálculo do projeto                                    |
| `CONTAGEM_DISTINTA`   | `COUNT(DISTINCT chave)` no universo correto, por exemplo IES com matrículas positivas **na fato do ano**; não contar linhas da dimensão como atividade anual                    |
| `VALOR_UNIDADE`       | Recuperar conceito/nota/faixa de **uma** unidade avaliada e edição; não somar nem calcular média como indicador oficial                                                         |
| `DISTRIBUICAO`        | Contar unidades avaliadas por faixa/ano, conservando nulos e sem conceito separados; verificar unicidade antes de contar                                                        |
| `NAO_AUTORIZADA`      | Desconhecido, combinação incompatível, granularidade insuficiente, cálculo causal ou indicador não presente; esclarecer limitação                                               |

**[CAT-REG-001]** Métricas de contagem educacional representam registros/vínculos no universo da fonte, não necessariamente **pessoas únicas**. Edições diferentes não podem ser somadas como coorte de alunos únicos.

**[CAT-REG-002]** `NULL`, ausência de linha, observação “Sem Conceito” e valor 0 são estados distintos. Em educação superior, alguns nulos de origem podem ter sido normalizados para zero pelo ETL; em educação básica e avaliações não pressupor o mesmo tratamento antes de verificar transformadores.

**[CAT-REG-003]** Não somar métricas de famílias sobrepostas: etapas e educação especial; sexo e cor/raça; financiamento Fies e Prouni; formas de ingresso; fato geral e fato por turno. Para total, preferir a coluna total materializada.

**[CAT-REG-004]** A dimensão IES usa o cadastro mais recente e pode descrever historicamente uma classificação **atual**. Em educação básica, `dim_escola` mantém os atributos do **ano mais recente por escola** (confirmado no ETL), não históricos por ano. Não afirmar atributos históricos sem dimensão temporal adequada.

**[CAT-REG-005]** A localização geográfica da **fato geral de educação superior** atribui EAD à sentinela (`codigo_municipio = -1`): consultas municipais com `dim_localidade` não incluem EAD daquele município. A localidade de uma escola é a da unidade escolar; a de uma IES pode ser sede, oferta ou avaliação conforme tabela e join. Não confundir com residência do aluno.

**[CAT-REG-006]** Cada consulta usa **uma fato principal**; cruzamentos entre fatos exigem agregação isolada e alinhamento explícito de chaves/grãos. Nunca fazer join direto entre fatos e então somar medidas.

**[CAT-REG-007]** O Gemini identifica intenção, mas o backend seleciona apenas indicadores, filtros e templates SQL previamente **autorizados**. O RAG não concede a um documento permissão de executar SQL livre.

## 3. Catálogo — Educação superior (Censo)

**Fonte física:** `gold.fact_educacao_superior` (47 campos; 52 colunas incluindo chaves). **Operação padrão:** `SOMA_ANUAL`, em um ano e filtros compatíveis, com ressalva de que a contagem é de vínculos/eventos. **Documento:** `docs/educacao_superior.md`.

### 3.1 Inventário de campos

| ID estável   | Coluna Gold                         | Tipo    | Família / tratamento                                                                                                                                   |
| ------------ | ----------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CAT-ES-001` | `vagas_total`                       | `Int32` | **Principal** · Vagas · `SOMA_ANUAL`                                                                                                                   |
| `CAT-ES-002` | `vagas_novas`                       | `Int32` | Vagas · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                                                  |
| `CAT-ES-003` | `vagas_processo_seletivo`           | `Int32` | Vagas · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                                                  |
| `CAT-ES-004` | `vagas_remanescentes`               | `Int32` | Vagas · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                                                  |
| `CAT-ES-005` | `vagas_programa_especial`           | `Int32` | Vagas · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                                                  |
| `CAT-ES-006` | `inscritos_total`                   | `Int32` | **Principal** · Inscrições/candidaturas · `SOMA_ANUAL`                                                                                                 |
| `CAT-ES-007` | `inscritos_vagas_novas`             | `Int32` | Inscrições/candidaturas · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                                |
| `CAT-ES-008` | `inscritos_processo_seletivo`       | `Int32` | Inscrições/candidaturas · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                                |
| `CAT-ES-009` | `inscritos_vagas_remanescentes`     | `Int32` | Inscrições/candidaturas · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                                |
| `CAT-ES-010` | `inscritos_programa_especial`       | `Int32` | Inscrições/candidaturas · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                                |
| `CAT-ES-011` | `ingressantes`                      | `Int32` | **Principal** · Ingressos / formas de seleção · `SOMA_ANUAL`                                                                                           |
| `CAT-ES-012` | `ingressantes_vagas_novas`          | `Int32` | Ingressos / formas de seleção · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                          |
| `CAT-ES-013` | `ingressantes_vestibular`           | `Int32` | Ingressos / formas de seleção · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                          |
| `CAT-ES-014` | `ingressantes_enem`                 | `Int32` | Ingressos / formas de seleção · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                          |
| `CAT-ES-015` | `ingressantes_avaliacao_seriada`    | `Int32` | Ingressos / formas de seleção · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                          |
| `CAT-ES-016` | `ingressantes_selecao_simplificada` | `Int32` | Ingressos / formas de seleção · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                          |
| `CAT-ES-017` | `ingressantes_egressos`             | `Int32` | Ingressos / formas de seleção · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                          |
| `CAT-ES-018` | `ingressantes_outro_tipo_selecao`   | `Int32` | Ingressos / formas de seleção · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                          |
| `CAT-ES-019` | `ingressantes_processo_seletivo`    | `Int32` | Ingressos / formas de seleção · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                          |
| `CAT-ES-020` | `ingressantes_vagas_remanescentes`  | `Int32` | Ingressos / formas de seleção · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                          |
| `CAT-ES-021` | `ingressantes_programa_especial`    | `Int32` | Ingressos / formas de seleção · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                          |
| `CAT-ES-022` | `ingressantes_outra_forma`          | `Int32` | Ingressos / formas de seleção · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                          |
| `CAT-ES-023` | `matriculados`                      | `Int32` | **Principal** · Matrículas, rematrículas e conclusões · `SOMA_ANUAL`                                                                                   |
| `CAT-ES-024` | `rematriculados`                    | `Int32` | Matrícula derivada pelo ETL (`max(matriculados_linha − ingressantes_linha, 0)`); `SOMA_ANUAL` do campo **já materializado**, não reconstruir de totais |
| `CAT-ES-025` | `concluintes`                       | `Int32` | **Principal** · Matrículas, rematrículas e conclusões · `SOMA_ANUAL`                                                                                   |
| `CAT-ES-026` | `ingressantes_fies`                 | `Int32` | Fies/Prouni por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                      |
| `CAT-ES-027` | `ingressantes_prouni_integral`      | `Int32` | Fies/Prouni por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                      |
| `CAT-ES-028` | `ingressantes_prouni_parcial`       | `Int32` | Fies/Prouni por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                      |
| `CAT-ES-029` | `matriculados_fies`                 | `Int32` | Fies/Prouni por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                      |
| `CAT-ES-030` | `matriculados_prouni_integral`      | `Int32` | Fies/Prouni por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                      |
| `CAT-ES-031` | `matriculados_prouni_parcial`       | `Int32` | Fies/Prouni por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                      |
| `CAT-ES-032` | `concluintes_fies`                  | `Int32` | Fies/Prouni por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                      |
| `CAT-ES-033` | `concluintes_prouni_integral`       | `Int32` | Fies/Prouni por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                      |
| `CAT-ES-034` | `concluintes_prouni_parcial`        | `Int32` | Fies/Prouni por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                      |
| `CAT-ES-035` | `trancados`                         | `Int32` | Situações acadêmicas · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                                   |
| `CAT-ES-036` | `desvinculados`                     | `Int32` | Situações acadêmicas · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                                   |
| `CAT-ES-037` | `transferidos`                      | `Int32` | Situações acadêmicas · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                                   |
| `CAT-ES-038` | `falecidos`                         | `Int32` | Situações acadêmicas · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                                   |
| `CAT-ES-039` | `ingressantes_escola_publica`       | `Int32` | Origem escolar por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                   |
| `CAT-ES-040` | `ingressantes_escola_privada`       | `Int32` | Origem escolar por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                   |
| `CAT-ES-041` | `ingressantes_escola_nao_informada` | `Int32` | Origem escolar por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                   |
| `CAT-ES-042` | `matriculados_escola_publica`       | `Int32` | Origem escolar por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                   |
| `CAT-ES-043` | `matriculados_escola_privada`       | `Int32` | Origem escolar por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                   |
| `CAT-ES-044` | `matriculados_escola_nao_informada` | `Int32` | Origem escolar por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                   |
| `CAT-ES-045` | `concluintes_escola_publica`        | `Int32` | Origem escolar por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                   |
| `CAT-ES-046` | `concluintes_escola_privada`        | `Int32` | Origem escolar por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                   |
| `CAT-ES-047` | `concluintes_escola_nao_informada`  | `Int32` | Origem escolar por estágio acadêmico · `SOMA_ANUAL` (não somar com outras famílias para criar total)                                                   |

**[CAT-ES-REG-001]** `matriculados`, `ingressantes`, `concluintes`, `vagas_total` e `inscritos_total` são medidas diferentes. A coluna `rematriculados` é definição operacional do **projeto**, não indicador oficial reproduzido diretamente do Inep.

**[CAT-ES-REG-002]** O mesmo `id_curso_superior` pode agrupar diferentes códigos técnicos de curso. Contar `DISTINCT id_curso_superior` **não** equivale a contar ofertas ou códigos e-MEC oficiais. `dim_ies` não é um cadastro histórico por ano.

### 3.2 Inventário — recortes por turno

**Fonte física:** `gold.fact_educacao_superior_turno`. Recorte **somente presencial** e turnos `DIURNO`/`NOTURNO`. Embora haja seis nomes iguais aos da fato geral, são **medidas de outra granularidade**, não novas categorias somáveis à fato principal.

| ID estável    | Coluna Gold       | Tipo    | Família / tratamento                                                                             |
| ------------- | ----------------- | ------- | ------------------------------------------------------------------------------------------------ |
| `CAT-EST-001` | `vagas_total`     | `Int32` | Turno presencial · `SOMA_ANUAL` **dentro desta fato**; não combinar diretamente com a fato geral |
| `CAT-EST-002` | `inscritos_total` | `Int32` | Turno presencial · `SOMA_ANUAL` **dentro desta fato**; não combinar diretamente com a fato geral |
| `CAT-EST-003` | `ingressantes`    | `Int32` | Turno presencial · `SOMA_ANUAL` **dentro desta fato**; não combinar diretamente com a fato geral |
| `CAT-EST-004` | `matriculados`    | `Int32` | Turno presencial · `SOMA_ANUAL` **dentro desta fato**; não combinar diretamente com a fato geral |
| `CAT-EST-005` | `rematriculados`  | `Int32` | Turno presencial · `SOMA_ANUAL` **dentro desta fato**; não combinar diretamente com a fato geral |
| `CAT-EST-006` | `concluintes`     | `Int32` | Turno presencial · `SOMA_ANUAL` **dentro desta fato**; não combinar diretamente com a fato geral |

**[CAT-EST-REG-001]** O ETL reconcilia a soma de campos de turno de origem na Silver; isso **não garante** igualdade entre o total da fato de turnos e o total geral de todos os cursos. Não impor a igualdade sem teste específico.

## 4. Catálogo — Educação básica (Censo Escolar)

**Fonte física:** `gold.fact_educacao_basica` (54 campos de matrícula; 58 colunas incluindo chaves). **Grão:** escola × ano. **Documento:** `docs/educacao_basica.md`. As 54 métricas são **recortes parcialmente sobrepostos**, não uma lista de partes disjuntas. As transformações específicas de educação básica foram inspecionadas: Bronze valida escola×ano e preserva escolas de 2025 sem matrícula, Silver mantém nulos e valida campos, Gold mantém uma linha por escola×ano sem somar etapas. Persistem as pendências de comparabilidade metodológica entre edições.

### 4.1 Inventário de campos

| ID estável   | Coluna Gold                                           | Tipo    | Família / tratamento                                                                                            |
| ------------ | ----------------------------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------- |
| `CAT-EB-001` | `matriculas_educacao_basica`                          | `Int32` | **Principal** · `SOMA_ANUAL` do total informado; não reconstituir somando etapas                                |
| `CAT-EB-002` | `matriculas_educacao_infantil`                        | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-003` | `matriculas_creche`                                   | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-004` | `matriculas_pre_escola`                               | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-005` | `matriculas_ensino_fundamental`                       | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-006` | `matriculas_fundamental_anos_iniciais`                | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-007` | `matriculas_fundamental_anos_finais`                  | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-008` | `matriculas_ensino_medio`                             | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-009` | `matriculas_educacao_profissional`                    | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-010` | `matriculas_educacao_profissional_tecnica`            | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-011` | `matriculas_eja`                                      | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-012` | `matriculas_eja_fundamental`                          | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-013` | `matriculas_eja_ensino_medio`                         | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-014` | `matriculas_educacao_especial`                        | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-015` | `matriculas_educacao_especial_classe_comum`           | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-016` | `matriculas_educacao_especial_classe_exclusiva`       | `Int32` | Total, etapa ou modalidade · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis            |
| `CAT-EB-017` | `matriculas_fundamental_ano_1`                        | `Int32` | Ano do ensino fundamental · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis             |
| `CAT-EB-018` | `matriculas_fundamental_ano_2`                        | `Int32` | Ano do ensino fundamental · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis             |
| `CAT-EB-019` | `matriculas_fundamental_ano_3`                        | `Int32` | Ano do ensino fundamental · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis             |
| `CAT-EB-020` | `matriculas_fundamental_ano_4`                        | `Int32` | Ano do ensino fundamental · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis             |
| `CAT-EB-021` | `matriculas_fundamental_ano_5`                        | `Int32` | Ano do ensino fundamental · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis             |
| `CAT-EB-022` | `matriculas_fundamental_ano_6`                        | `Int32` | Ano do ensino fundamental · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis             |
| `CAT-EB-023` | `matriculas_fundamental_ano_7`                        | `Int32` | Ano do ensino fundamental · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis             |
| `CAT-EB-024` | `matriculas_fundamental_ano_8`                        | `Int32` | Ano do ensino fundamental · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis             |
| `CAT-EB-025` | `matriculas_fundamental_ano_9`                        | `Int32` | Ano do ensino fundamental · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis             |
| `CAT-EB-026` | `matriculas_ensino_medio_1`                           | `Int32` | Série do ensino médio · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                 |
| `CAT-EB-027` | `matriculas_ensino_medio_2`                           | `Int32` | Série do ensino médio · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                 |
| `CAT-EB-028` | `matriculas_ensino_medio_3`                           | `Int32` | Série do ensino médio · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                 |
| `CAT-EB-029` | `matriculas_ensino_medio_4`                           | `Int32` | Série do ensino médio · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                 |
| `CAT-EB-030` | `matriculas_ensino_medio_nao_seriado`                 | `Int32` | Série do ensino médio · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                 |
| `CAT-EB-031` | `matriculas_educacao_basica_feminino`                 | `Int32` | Sexo · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                                  |
| `CAT-EB-032` | `matriculas_educacao_basica_masculino`                | `Int32` | Sexo · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                                  |
| `CAT-EB-033` | `matriculas_educacao_basica_cor_nao_declarada`        | `Int32` | Cor/raça · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                              |
| `CAT-EB-034` | `matriculas_educacao_basica_cor_branca`               | `Int32` | Cor/raça · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                              |
| `CAT-EB-035` | `matriculas_educacao_basica_cor_preta`                | `Int32` | Cor/raça · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                              |
| `CAT-EB-036` | `matriculas_educacao_basica_cor_parda`                | `Int32` | Cor/raça · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                              |
| `CAT-EB-037` | `matriculas_educacao_basica_cor_amarela`              | `Int32` | Cor/raça · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                              |
| `CAT-EB-038` | `matriculas_educacao_basica_cor_indigena`             | `Int32` | Cor/raça · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                              |
| `CAT-EB-039` | `matriculas_educacao_basica_idade_0_3`                | `Int32` | Faixa etária · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                          |
| `CAT-EB-040` | `matriculas_educacao_basica_idade_4_5`                | `Int32` | Faixa etária · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                          |
| `CAT-EB-041` | `matriculas_educacao_basica_idade_6_10`               | `Int32` | Faixa etária · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                          |
| `CAT-EB-042` | `matriculas_educacao_basica_idade_11_14`              | `Int32` | Faixa etária · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                          |
| `CAT-EB-043` | `matriculas_educacao_basica_idade_15_17`              | `Int32` | Faixa etária · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                          |
| `CAT-EB-044` | `matriculas_educacao_basica_idade_18_mais`            | `Int32` | Faixa etária · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                          |
| `CAT-EB-045` | `matriculas_educacao_basica_diurno`                   | `Int32` | Turno/EAD · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                             |
| `CAT-EB-046` | `matriculas_educacao_basica_noturno`                  | `Int32` | Turno/EAD · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                             |
| `CAT-EB-047` | `matriculas_educacao_basica_ead`                      | `Int32` | Turno/EAD · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis                             |
| `CAT-EB-048` | `matriculas_educacao_infantil_tempo_integral`         | `Int32` | Tempo integral (subconjunto da etapa) · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis |
| `CAT-EB-049` | `matriculas_creche_tempo_integral`                    | `Int32` | Tempo integral (subconjunto da etapa) · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis |
| `CAT-EB-050` | `matriculas_pre_escola_tempo_integral`                | `Int32` | Tempo integral (subconjunto da etapa) · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis |
| `CAT-EB-051` | `matriculas_ensino_fundamental_tempo_integral`        | `Int32` | Tempo integral (subconjunto da etapa) · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis |
| `CAT-EB-052` | `matriculas_fundamental_anos_iniciais_tempo_integral` | `Int32` | Tempo integral (subconjunto da etapa) · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis |
| `CAT-EB-053` | `matriculas_fundamental_anos_finais_tempo_integral`   | `Int32` | Tempo integral (subconjunto da etapa) · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis |
| `CAT-EB-054` | `matriculas_ensino_medio_tempo_integral`              | `Int32` | Tempo integral (subconjunto da etapa) · `SOMA_ANUAL` por escola/ano; cruzamentos entre famílias não disponíveis |

**[CAT-EB-REG-001]** Não reconstruir `matriculas_educacao_basica` pela soma das etapas/modalidades. Educação especial, EJA, profissional e demais famílias podem se sobrepor; a interpretação de cada edição exige o dicionário da fonte.

**[CAT-EB-REG-002]** Interseções como “meninas indígenas do ensino médio” **não** estão materializadas; colunas agregadas independentes de sexo, cor/raça e etapa não permitem calcular esse cruzamento.

**[CAT-EB-REG-003]** Exemplos de razão **calculada pelo projeto**, ainda sujeitos a validação de comparabilidade da fonte: `matriculas_ensino_medio_tempo_integral / matriculas_ensino_medio`, com ambos agregados no mesmo ano e recorte, e denominador positivo. Não chamar de taxa oficial do Inep sem comprovar metodologia da edição.

**[CAT-EB-REG-004]** A fato não publica, neste contrato, taxas de aprovação, reprovação, abandono, Ideb, proficiência ou distorção idade-série. Uma tabela de detalhe aparece no `schema.py`, mas não integra as dez tabelas Gold publicadas e **não** é fonte disponível para respostas.

## 5. Catálogo — Avaliações de cursos (Conceito Enade, IDD, CPC)

**Fonte física:** `gold.fact_avaliacao_curso_superior`. **Grão contratado:** IES × curso oficial avaliado × curso analítico × localidade × ano. **Chave distintiva:** `codigo_curso_avaliado` integra a chave; `id_curso_superior` isolado não representa um curso avaliado oficial. **Documento:** `docs/avaliacoes.md`.

### 5.1 Inventário numérico

| ID estável    | Coluna Gold                                            | Tipo      | Família / tratamento                                                                                 |
| ------------- | ------------------------------------------------------ | --------- | ---------------------------------------------------------------------------------------------------- |
| `CAT-AVC-001` | `enade_concluintes_inscritos_qtd`                      | `Int64`   | Conceito Enade · contagem; `SOMA_CONDICIONAL` apenas com cursos/edição distintos e universo validado |
| `CAT-AVC-002` | `enade_concluintes_participantes_qtd`                  | `Int64`   | Conceito Enade · contagem; `SOMA_CONDICIONAL` apenas com cursos/edição distintos e universo validado |
| `CAT-AVC-003` | `enade_nota_bruta_fg`                                  | `Float64` | Conceito Enade · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                  |
| `CAT-AVC-004` | `enade_nota_padronizada_fg`                            | `Float64` | Conceito Enade · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                  |
| `CAT-AVC-005` | `enade_nota_bruta_ce`                                  | `Float64` | Conceito Enade · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                  |
| `CAT-AVC-006` | `enade_nota_padronizada_ce`                            | `Float64` | Conceito Enade · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                  |
| `CAT-AVC-007` | `enade_conceito_continuo`                              | `Float64` | Conceito Enade · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                  |
| `CAT-AVC-008` | `enade_conceito_faixa`                                 | `Int32`   | Conceito Enade · **não aditivo**; `VALOR_UNIDADE` ou `DISTRIBUICAO`                                  |
| `CAT-AVC-009` | `enade_concluintes_acima_padrao_qtd`                   | `Int64`   | Conceito Enade · contagem; `SOMA_CONDICIONAL` apenas com cursos/edição distintos e universo validado |
| `CAT-AVC-010` | `enade_percentual_acima_padrao`                        | `Float64` | Conceito Enade · **não aditivo**; indicador publicado por unidade, não somar nem fazer média simples |
| `CAT-AVC-011` | `idd_concluintes_inscritos_qtd`                        | `Int64`   | IDD · contagem; `SOMA_CONDICIONAL` apenas com cursos/edição distintos e universo validado            |
| `CAT-AVC-012` | `idd_concluintes_participantes_qtd`                    | `Int64`   | IDD · contagem; `SOMA_CONDICIONAL` apenas com cursos/edição distintos e universo validado            |
| `CAT-AVC-013` | `idd_concluintes_com_enem_qtd`                         | `Int64`   | IDD · contagem; `SOMA_CONDICIONAL` apenas com cursos/edição distintos e universo validado            |
| `CAT-AVC-014` | `idd_proporcao_concluintes_com_enem`                   | `Float64` | IDD · **não aditivo**; indicador publicado por unidade, não somar nem fazer média simples            |
| `CAT-AVC-015` | `idd_nota_bruta`                                       | `Float64` | IDD · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-016` | `idd_continuo`                                         | `Float64` | IDD · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-017` | `idd_faixa`                                            | `Int32`   | IDD · **não aditivo**; `VALOR_UNIDADE` ou `DISTRIBUICAO`                                             |
| `CAT-AVC-018` | `cpc_concluintes_inscritos_qtd`                        | `Int64`   | CPC · contagem; `SOMA_CONDICIONAL` apenas com cursos/edição distintos e universo validado            |
| `CAT-AVC-019` | `cpc_concluintes_participantes_qtd`                    | `Int64`   | CPC · contagem; `SOMA_CONDICIONAL` apenas com cursos/edição distintos e universo validado            |
| `CAT-AVC-020` | `cpc_nota_bruta_fg`                                    | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-021` | `cpc_nota_padronizada_fg`                              | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-022` | `cpc_nota_bruta_ce`                                    | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-023` | `cpc_nota_padronizada_ce`                              | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-024` | `cpc_conceito_enade_continuo`                          | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-025` | `cpc_concluintes_com_enem_qtd`                         | `Int64`   | CPC · contagem; `SOMA_CONDICIONAL` apenas com cursos/edição distintos e universo validado            |
| `CAT-AVC-026` | `cpc_proporcao_concluintes_com_enem`                   | `Float64` | CPC · **não aditivo**; indicador publicado por unidade, não somar nem fazer média simples            |
| `CAT-AVC-027` | `cpc_nota_bruta_idd`                                   | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-028` | `cpc_nota_padronizada_idd`                             | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-029` | `cpc_nota_bruta_organizacao_didatico_pedagogica`       | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-030` | `cpc_nota_padronizada_organizacao_didatico_pedagogica` | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-031` | `cpc_nota_bruta_infraestrutura`                        | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-032` | `cpc_nota_padronizada_infraestrutura`                  | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-033` | `cpc_nota_bruta_oportunidade_formacao`                 | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-034` | `cpc_nota_padronizada_oportunidade_formacao`           | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-035` | `cpc_nota_bruta_mestres`                               | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-036` | `cpc_nota_padronizada_mestres`                         | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-037` | `cpc_nota_bruta_doutores`                              | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-038` | `cpc_nota_padronizada_doutores`                        | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-039` | `cpc_nota_bruta_regime_trabalho`                       | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-040` | `cpc_nota_padronizada_regime_trabalho`                 | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-041` | `cpc_continuo`                                         | `Float64` | CPC · **não aditivo** (nota/componente); `VALOR_UNIDADE`                                             |
| `CAT-AVC-042` | `cpc_faixa`                                            | `Int32`   | CPC · **não aditivo**; `VALOR_UNIDADE` ou `DISTRIBUICAO`                                             |

**[CAT-AVC-REG-001]** O Conceito Enade, IDD e CPC podem aparecer em escala contínua e em faixa. Faixas são classificações da edição; **não** converter de contínuo para faixa por regras inventadas ou calcular um “conceito oficial médio municipal”.

**[CAT-AVC-REG-002]** `*_inscritos_qtd`, `*_participantes_qtd` e `*_com_enem_qtd` representam universos diferentes. Somar quantidades só após validar unicidade por curso/edição e ausência de duplicidade entre fontes; **não** apresentar o total como número de estudantes únicos em todo o sistema.

**[CAT-AVC-REG-003]** Os componentes de CPC e notas padronizadas não devem ser recombinados para tentar reproduzir a fórmula oficial sem documentação e pesos específicos da edição.

## 6. Catálogo — Avaliação institucional (IGC)

**Fonte física:** `gold.fact_avaliacao_ies`. **Grão contratado:** IES × ano. A dimensão IES oferece sede e cadastro mais recente; não existe localidade do curso na fato IGC. **Documento:** `docs/avaliacoes.md`.

### 6.1 Inventário numérico

| ID estável    | Coluna Gold                    | Tipo      | Família / tratamento                                                                                                                        |
| ------------- | ------------------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `CAT-AVI-001` | `igc_cursos_cpc_trienio_qtd`   | `Int32`   | Quantidade de cursos no cálculo do triênio; `SOMA_CONDICIONAL` somente para IES distintas no mesmo ano, não contagem de ofertas censitárias |
| `CAT-AVI-002` | `igc_alfa_graduacao`           | `Float64` | Componente do cálculo IGC · **não aditivo**; `VALOR_UNIDADE`                                                                                |
| `CAT-AVI-003` | `igc_conceito_medio_graduacao` | `Float64` | Componente do cálculo IGC · **não aditivo**; `VALOR_UNIDADE`                                                                                |
| `CAT-AVI-004` | `igc_beta_mestrado`            | `Float64` | Componente do cálculo IGC · **não aditivo**; `VALOR_UNIDADE`                                                                                |
| `CAT-AVI-005` | `igc_conceito_medio_mestrado`  | `Float64` | Componente do cálculo IGC · **não aditivo**; `VALOR_UNIDADE`                                                                                |
| `CAT-AVI-006` | `igc_gama_doutorado`           | `Float64` | Componente do cálculo IGC · **não aditivo**; `VALOR_UNIDADE`                                                                                |
| `CAT-AVI-007` | `igc_conceito_medio_doutorado` | `Float64` | Componente do cálculo IGC · **não aditivo**; `VALOR_UNIDADE`                                                                                |
| `CAT-AVI-008` | `igc_continuo`                 | `Float64` | IGC contínuo · **não aditivo**; `VALOR_UNIDADE`                                                                                             |
| `CAT-AVI-009` | `igc_faixa`                    | `Int32`   | IGC em faixa · **não aditivo**; `VALOR_UNIDADE` ou `DISTRIBUICAO`                                                                           |

**[CAT-AVI-REG-001]** O IGC é institucional e refere-se à **IES**, não a todos os cursos, alunos, campi ou municípios individualmente. O campo de quantidade de cursos do triênio não equivale ao catálogo completo de cursos da IES.

**[CAT-AVI-REG-002]** É válida uma contagem de IES com IGC faixa 4 em uma edição (`COUNT(DISTINCT id_ies)` na fato e filtro de faixa), mas **não** calcular uma “nota oficial da cidade” a partir da média dos IGCs.

## 7. Indicadores calculados no backend (não colunas Gold)

As fórmulas abaixo são **operações derivadas do projeto**, não medidas originais nem indicadores oficiais do Inep. A autorização de uso depende da revisão humana deste catálogo e das regras por domínio.

| ID            | Resultado                                               | Expressão conceitual                                                                    | Pré-condições                                                                   |
| ------------- | ------------------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `CAT-DER-001` | Variação absoluta                                       | `final - inicial`                                                                       | Mesma métrica, recorte e critérios; dois anos com dados                         |
| `CAT-DER-002` | Variação percentual                                     | `(final / inicial - 1) * 100`                                                           | Denominador inicial positivo/não nulo; sem interpolação                         |
| `CAT-DER-003` | Razão ingressantes/vagas                                | `SUM(ingressantes) / NULLIF(SUM(vagas_total), 0)`                                       | Mesma fato geral/ano/filtros; **não** intitular “taxa oficial de ocupação”      |
| `CAT-DER-004` | Parcela de matrículas em tempo integral no ensino médio | `SUM(matriculas_ensino_medio_tempo_integral) / NULLIF(SUM(matriculas_ensino_medio), 0)` | Mesma fato básica/ano/filtros; verificar comparabilidade e significado da fonte |
| `CAT-DER-005` | IES com matrículas positivas                            | `COUNT(DISTINCT id_ies)` filtrando `matriculados > 0`                                   | Fato superior; um ano e universo de oferta declarados                           |
| `CAT-DER-006` | Escolas com matrículas positivas                        | `COUNT(DISTINCT id_escola)` filtrando `matriculas_educacao_basica > 0`                  | Fato básica; não equivale a escolas ativas no cadastro                          |
| `CAT-DER-007` | Distribuição de cursos por faixa de CPC                 | Contagem de cursos avaliados distintos por `cpc_faixa` e edição                         | Confirmar chave única e cobertura da edição; não é média de CPC                 |
| `CAT-DER-008` | Distribuição de IES por faixa de IGC                    | `COUNT(DISTINCT id_ies)` por `igc_faixa` em um ano                                      | Fato IGC e edição explícita                                                     |

## 8. Seleção de indicador pela aplicação

A extração pela LLM deve retornar **intenção**, não SQL, nome de coluna arbitrário ou valor numérico. O backend resolve o ID do indicador no registro autorizado, verifica as dimensões e executa template SQL parametrizado, por exemplo:

```json
{
  "indicador_id": "CAT-ES-023",
  "operacao": "SERIE_ANUAL",
  "municipio": "Volta Redonda",
  "uf": "RJ",
  "ano_inicial": 2020,
  "ano_final": 2023,
  "modalidade": "PRESENCIAL"
}
```

> A seleção exemplifica a **representação desejada**, não uma API já implementada. Ela não deve autorizar uma consulta antes da revisão do catálogo. O exemplo usa `CAT-ES-023`, correspondente à coluna `matriculados` segundo a ordem contratual de `schema.py`. A série municipal é **presencial** porque a fato geral consolida EAD na sentinela geográfica.

**[CAT-SEL-001]** Se a pergunta for “matrículas em Volta Redonda” sem modalidade, o backend não poderá responder como se abrangisse residentes e EAD. Deve esclarecer o escopo presencial ou solicitar precisão, conforme política aprovada em `docs/educacao_superior.md`.

**[CAT-SEL-002]** Se o indicador ou o filtro não existir na fato ou exceder sua granularidade (por exemplo, meninas indígenas por escola, EAD por município de residência, taxa de abandono), responder sobre a indisponibilidade em vez de inventar aproximação.

**[CAT-SEL-003]** Em perguntas com termos genéricos como “quantos cursos”, “taxa de matrículas”, “nota média” e “instituições por cidade”, classificar o universo e a unidade de medida antes de executar SQL. Diferenciar curso analítico, código avaliado, IES, escola, matrícula e estudante único.

## 9. Validações obrigatórias para aprovação e ingestão

Parte das verificações foi executada **posteriormente** no ambiente local via `postgres.validate_gold --deep` (46 OK, 5 alertas de revisão, 0 erros, conforme saída fornecida); testes de valores contra fontes Inep permanecem pendentes.

| Verificação             | Condição de aprovação                                                                                                    |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Colunas existentes      | Cada `gold.tabela.coluna` referenciada existe em `rag.schema_catalog` e em `pg_catalog` após a última carga bem-sucedida |
| Tipos esperados         | Quantidades inteiras, scores contínuos e faixas conforme contrato, com divergências sinalizadas                          |
| Unicidade por grão      | Chaves de fatos verificadas; sem duplicidade inesperada em avaliação por código de curso                                 |
| Cobertura temporal      | Anos de fato comparados com configuração, distinguindo ano previsto de ano carregado                                     |
| Integridade dimensional | Nenhuma FK lógica órfã após sincronização                                                                                |
| Agregabilidade          | Testes por indicador e por família; recortes sobrepostos não somados                                                     |
| Nulos e ausência        | Políticas diferentes para null, sem registro, zero e sem conceito                                                        |
| Rastreabilidade         | ID estável, documento de origem, caminho da regra e versão do Markdown preservados                                       |
| Aprovação humana        | Somente regras revisadas passam de `revisao_humana_pendente` para estado aprovado                                        |

### 9.1 Conferência física mínima

Esta consulta é apenas diagnóstica: confirma a presença dos cinco objetos no catálogo, **não** garante que as 158 colunas nem seus valores foram validados.

```sql
SELECT object_name, jsonb_array_length(definition->'columns') AS colunas
FROM rag.schema_catalog
WHERE object_name IN (
    'gold.fact_educacao_superior',
    'gold.fact_educacao_superior_turno',
    'gold.fact_educacao_basica',
    'gold.fact_avaliacao_curso_superior',
    'gold.fact_avaliacao_ies'
)
ORDER BY object_name;
```

### 9.2 Política de alteração e indexação

1. **Código/schema mudou:** atualizar o catálogo técnico `rag.schema_catalog` após publicar o Gold; comparar colunas usadas pelas regras e emitir incompatibilidades; **não** alterar regras humanas automaticamente.
2. **Regra de negócio mudou:** editar o Markdown em `docs/`, revisá-lo e atualizar versão/status antes de disponibilizá-lo ao RAG.
3. **Ingestão:** calcular hash por documento (e preferencialmente por fragmento), preservar IDs e origem, re-embedar apenas conteúdo alterado e marcar versões obsoletas para não recuperar regras revogadas.
4. **Inconsistência:** documento que referencia coluna inexistente, grão incompatível ou mudança metodológica não resolvida deve gerar alerta; jamais ser corrigido/aceito por decisão autônoma da LLM.
5. **Histórico de alterações:** IDs `CAT-*` devem permanecer estáveis entre revisões para rastrear respostas. Se uma métrica for removida, deprecar o ID em vez de reutilizá-lo para outro significado.

## 10. Pendências para aprovação da versão 1.0.0

- **[CAT-PEN-001 | PARCIALMENTE RESOLVIDA]** Os módulos Bronze/Silver/Gold de educação básica foram inspecionados: a Gold preserva o grão escola×ano, métricas nulas e atributos mais recentes em `dim_escola`. A validação de comparabilidade e nulos por edição ainda exige amostras da fonte.
- **[CAT-PEN-002 | PARCIALMENTE RESOLVIDA]** Módulos de avaliação inspecionados: Silver valida unicidade por fonte; Gold escolhe primeiro não nulo por coluna com prioridade Enade→CPC→IDD e audita descritores divergentes. Faltam amostras XLSX, avaliação do arquivo de conflitos e validação de `SC`/notas.
- **[CAT-PEN-003 | PARCIALMENTE RESOLVIDA]** Execução local reportada de `postgres.validate_gold --deep` (46 OK/5 alertas/0 erros) confirmou chaves únicas, constraints, cobertura, localidade sentinela de 52.264 registros EAD sem desvios e ausência de turnos não presenciais. Reconciliação quantitativa por indicador e edição continua pendente.
- **[CAT-PEN-004]** Validar definições por edição diretamente nos dicionários de dados/notas técnicas do Inep antes de chamar taxas e agregados calculados pelo projeto de “oficiais”.
- **[CAT-PEN-005]** Definir com revisão humana quais indicadores entram no MVP e quais ficam apenas documentados, mesmo que a coluna exista.
- **[CAT-PEN-006]** Confirmar por revisão humana que as diretrizes documentais de `docs/regras_gerais.md` estejam coerentes com os demais documentos, sem aprová-las automaticamente.
