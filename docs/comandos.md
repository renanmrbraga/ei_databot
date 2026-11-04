# Comandos — EI DataBot

Guia operacional **geral do projeto** para desenvolvimento local no Windows 11 com PowerShell. Reúne ETL Educacional, PostgreSQL, catálogo, RAG, chatbot FastAPI, frontend React/Vite, Docker e testes. Execute os exemplos na raiz do repositório `D:\Projetos\ei_databot`, com o ambiente Python ativado.

> **Estado em 03/11/2026:** execução integral do ETL educacional concluída com **27/27 etapas**, com **2.702.972 registros publicados em 10 tabelas Gold**. A validação profunda do PostgreSQL apresentou **46 verificações aprovadas, 5 alertas documentais e nenhum erro**. Foram aprovados **56 testes Python**, **13 testes do frontend**, Ruff e build Vite. As imagens Docker da API e do frontend foram reconstruídas com sucesso; os dois serviços responderam HTTP 200, e o PostgreSQL apresentou estado `healthy`. A integração conversacional completa e a segurança de acesso público ainda exigem validações específicas.
> **Escopo do `main.py`:** o comando da raiz coordena a **carga de dados**, não o ciclo de vida do chatbot e do frontend. Não existe ainda um serviço Docker para o ETL. Este documento diferencia procedimentos existentes de validações ainda pendentes. É um guia operacional e **não é indexado no RAG**.

## 1. Arquitetura operacional e ordem

| Responsável            | Entrada                                      | Objetivo                                                                                  |
| ---------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Orquestrador de dados  | `python .\main.py`                           | Planejar ou executar ETL → publicação Gold → catálogo → validação; download/RAG opcionais |
| Orquestrador de etapas | `python -m etl.etl --educacao`               | Executar Bronze → Silver → Gold → Dashboard, na ordem de `etl.educacao.config.STEPS`      |
| Downloader             | `python -m etl.educacao.downloader`          | Atualizar arquivos-fonte; opcional                                                        |
| Publicador             | `python -m postgres.sync --dataset educacao` | Publicar os dez Parquets Gold no PostgreSQL                                               |
| Catálogo               | `python -m postgres.sync_catalog`            | Atualizar metadados técnicos do Gold                                                      |
| Validador              | `python -m postgres.validate_gold`           | Verificar o Gold publicado                                                                |
| RAG                    | `python -m postgres.sync_rag`                | Indexar documentos de regras incrementalmente                                             |
| API conversacional     | `python -m uvicorn chatbot.chatbot:app ...`  | Iniciar FastAPI; **não executa ETL**                                                      |
| Frontend               | `npm --prefix .\frontend run dev`            | Iniciar Vite; **não executa ETL**                                                         |
| Stack Docker           | `docker compose ...`                         | Executar PostgreSQL, chatbot e frontend em contêineres                                    |

O pipeline **Educacional** é o único pipeline ativo. O identificador usado na CLI e em `postgres.sync` é `educacao`; o armazenamento local fica em `data/educacao/`. Dashboard e chatbot compartilham os dados da carga, mas o chatbot consulta as tabelas `gold` no PostgreSQL, não os gráficos do dashboard.

## 2. Preparação segura

```powershell
Set-Location D:\Projetos\ei_databot
python --version
python -m pip check
docker compose config --quiet
docker compose ps
```

As variáveis de desenvolvimento ficam em **`.env` na raiz**. O backend utiliza as configurações do PostgreSQL e da API Gemini; o frontend deve receber apenas `API_PROXY_TARGET` (variável do servidor Vite, não uma credencial). Não crie `frontend/.env` com segredos nem use `VITE_` para chaves privadas.

Inicie o banco se necessário:

```powershell
docker compose up -d postgres
docker compose ps
```

**Não execute `docker compose down -v`**: essa opção remove volumes e pode apagar o PostgreSQL persistido. Não reaplique scripts de criação de schema em um banco já populado sem revisar seu conteúdo.

### Verificar os dados existentes sem processar

```powershell
Get-ChildItem .\data -Directory | Select-Object Name
Get-ChildItem .\data\educacao -Directory | Select-Object Name
Get-ChildItem .\data\educacao\gold -Filter '*.parquet' -File | Select-Object Name, Length
python -m postgres.validate_gold --offline
```

O diretório `data/raw` também existe no ambiente observado; os caminhos efetivos de Raw são definidos em `etl/core/config.py` e `etl/educacao/config.py`, e não devem ser inferidos apenas pelo nome da pasta.

## 3. Validação A — orquestrador geral da raiz (`main.py`)

### 3.1 Conferir os comandos aceitos

```powershell
python .\main.py --help
python .\main.py --plan
python .\main.py --plan --download --deep --rag
python .\main.py --plan --no-dashboard
```

A pré-visualização é **somente leitura**. O plano padrão confirmado inclui:

1. ETL Educacional — Bronze, Silver, Gold e dashboard quando habilitado.
2. Publicação dos Parquets Gold no PostgreSQL.
3. Sincronização do catálogo técnico.
4. Validação do Gold publicado.

`--download` acrescenta a atualização de fontes **antes** do ETL; `--deep` aprofunda a validação; `--rag` acrescenta a sincronização documental **depois** da validação; `--no-dashboard` evita regenerar o dashboard.

### 3.2 Execução real, após conferência dos dados e backup

```powershell
python .\main.py --run
```

Outras combinações, quando justificadas:

```powershell
# Reprocessar dados e validar profundamente, sem baixar fontes.
python .\main.py --run --deep

# Evitar regenerar o dashboard.
python .\main.py --run --no-dashboard

# Atualizar fontes antes do processamento (acessa serviços externos).
python .\main.py --run --download --deep

# Sincronizar RAG somente DEPOIS de revisar e aprovar as mudanças dos Markdown.
python .\main.py --run --deep --rag
```

**Atenção:** `--run` sobrescreve saídas de ETL e pode republicar o schema `gold`. A execução deve parar quando algum subprocesso falhar. Registre o resultado de cada etapa para a validação Alpha 1. A execução integral do pipeline foi validada durante a refatoração, com 27 etapas concluídas. Uma nova execução só deve ocorrer quando houver necessidade de reprocessar os dados, preferencialmente após conferir os arquivos de entrada e os backups.

## 4. Validação B — comandos individuais de dados

Use esta sequência **em alternativa** à execução integral via `main.py`. Rodar ambos imediatamente em sequência significa repetir as cargas e a publicação; faça isso apenas em um teste de regressão planejado, com backups e comparação dos resultados.

### 4.1 Fontes (opcional)

```powershell
python -m etl.educacao.downloader
```

Pode acessar a rede e baixar arquivos. Confirme se está executando a função de entrada do módulo antes de confiar em um retorno sem mensagens.

### 4.2 ETL de arquivos

```powershell
python -m etl.etl --help
python -m etl.etl --educacao
```

Para validar cada camada separadamente, na ordem correta (dependem dos arquivos produzidos pela anterior):

```powershell
python -m etl.etl --educacao --phase bronze
python -m etl.etl --educacao --phase silver
python -m etl.etl --educacao --phase gold
python -m etl.etl --educacao --phase dashboard
```

**Escolha uma das abordagens:** comando integral ou quatro fases. Não é necessário executar os cinco comandos para um único processamento. Para listar as etapas reais, sem executá-las:

```powershell
@'
import importlib
from etl.core.config import PIPELINES
cfg = importlib.import_module(PIPELINES['educacao'])
for i, (nome, modulo, camada) in enumerate(cfg.STEPS, 1):
    print(f'{i:02d} | {camada:10} | {nome} | {modulo}')
'@ | python -
```

A configuração observada contém oito etapas Bronze, oito Silver, cinco dimensões Gold, cinco fatos Gold e um dashboard. Para diagnóstico pontual:

```powershell
python -m etl.etl --educacao --only NOME_DA_ETAPA
python -m etl.etl --educacao --skip NOME_DA_ETAPA
python -m etl.etl --educacao --skip-bronze
python -m etl.etl --educacao --skip-silver
```

`--skip-silver` também pula Bronze; `--phase` e `--only` são mutuamente exclusivos. Ao executar fases parciais, confirme que as dependências anteriores existem.

### 4.3 Publicação, catálogo e validação

Execute **depois do Gold local**:

```powershell
python -m postgres.sync --dataset educacao
python -m postgres.sync_catalog
python -m postgres.validate_gold
```

Validação profunda quando necessário:

```powershell
python -m postgres.validate_gold --deep --timeout 180
```

A publicação Gold é transacional e pode substituir as tabelas existentes. A sincronização do catálogo registra metadados e não gera embeddings. O `--offline` não verifica o conteúdo efetivamente publicado.

### 4.4 RAG (independente do ETL)

```powershell
python -m postgres.sync_rag --dry-run
```

Se os documentos tiverem sido revisados e a sincronização for desejada:

```powershell
python -m postgres.sync_rag --batch-size 5 --interval 10
```

Teste de busca em regras ainda não aprovadas (somente desenvolvimento):

```powershell
python -m chatbot.services.rag --query 'Por que EAD não aparece nas matrículas de um município?' --include-drafts --limit 3
```

Em 03/11/2026, o dry-run reportou **4 embeddings pendentes**; o número pode mudar. Editar Markdown não exige reprocessar Gold.

## 5. Validação B — chatbot e frontend, individualmente

Estas aplicações são **serviços**, não etapas de carga do `main.py`.

Em um terminal, com o PostgreSQL em execução:

```powershell
python -m uvicorn chatbot.chatbot:app --host 127.0.0.1 --port 8000
```

Em outro terminal:

```powershell
npm --prefix .\frontend ci
npm --prefix .\frontend run check
npm --prefix .\frontend run dev
```

URLs locais: API `http://127.0.0.1:8000/health`; interface `http://127.0.0.1:8080/`.

Valide a saúde HTTP sem acionar Gemini:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Depois, na interface, teste uma pergunta analítica, a continuação contextual, a alternância entre sessões, a exclusão e a restauração após `F5`. Uma resposta HTTP 200 isolada não substitui os testes do SQL Gold, RAG e histórico.

## 6. Validação C — Docker Compose

O Compose atualizado possui **três serviços**: `postgres`, `chatbot` e `frontend`. **Ainda não há serviço `etl`**, portanto o Docker não reproduz a carga inteira do `main.py` até que um serviço específico de ETL seja implementado e testado. Não confunda iniciar a aplicação com reconstruir o Gold.

### 6.1 Conferir e construir, sem iniciar os serviços de aplicação

```powershell
docker compose config --quiet
docker compose build chatbot frontend
```

Os Dockerfiles chatbot/Dockerfile e frontend/Dockerfile foram validados por meio de docker compose build chatbot frontend. As imagens foram reconstruídas com sucesso e os serviços responderam HTTP 200 nos endpoints /health da API e / do frontend. O PostgreSQL permaneceu saudável. Esses testes confirmam a construção e a disponibilidade HTTP, mas não substituem os testes funcionais do chatbot com Gemini, RAG e consultas Gold. Se falhar, revise `chatbot/Dockerfile`, `frontend/Dockerfile`, os arquivos copiados no contexto de build e `pyproject.toml`, antes de atualizar os comandos do guia.

### 6.2 Subir a stack local

```powershell
docker compose up -d postgres
docker compose up -d chatbot frontend
docker compose ps
```

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Acesse `http://127.0.0.1:8080/` e repita o teste do chatbot, incluindo recuperação e exclusão das conversas. Confira os logs em caso de falha:

```powershell
docker compose logs --tail 100 chatbot
docker compose logs --tail 100 frontend
```

Parar a aplicação sem apagar dados:

```powershell
docker compose stop chatbot frontend
```

### 6.3 ETL no Docker — pendente

Não há comando oficial de ETL em Docker nesta versão do Compose. A próxima evolução é um serviço `etl` dedicado, com montagem explícita das pastas de dados e configurações, dependência saudável de PostgreSQL e execução manual (sem processamento automático ao iniciar o chatbot). **Não use um comando `docker compose run etl` enquanto o serviço não existir e não tiver sido testado.**

## 7. Testes automatizados e auditorias

```powershell
python -m ruff check chatbot etl dashboards health postgres tests main.py
python -m unittest discover -s tests -p 'test_*.py' -q
python -m pip check
npm --prefix .\frontend run check
npm --prefix .\frontend audit --omit=dev
```

Resultados informados: 56 testes Python aprovados, Ruff sem erros, 13 testes frontend aprovados, build Vite aprovado, `pip check` sem conflitos e `npm audit --omit=dev` sem vulnerabilidades. O alerta do Starlette/TestClient ainda precisa de revisão. `npm audit --omit=dev` não avalia as dependências de desenvolvimento.

Antes do commit, inspecione também as diferenças staged e não staged, os caminhos antigos e possíveis credenciais; não adicione backups, ZIPs, logs, bases locais ou arquivos `.env` ao Git.

## 8. Matriz de aceite da Alpha 1

| Percurso                           | Evidência necessária                                  | Estado atual                                                                          |
| ---------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `main.py --plan`                   | Plano coerente sem modificações                       | Confirmado                                                                            |
| `main.py --run`                    | ETL → publicação → catálogo → validação               | Confirmado: 27/27 etapas e 2.702.972 registros Gold                                   |
| `etl.etl` individual               | Camadas e dashboard gerados sem erro                  | Validado pelo orquestrador; execução isolada não repetida                             |
| `postgres.sync` individual         | Dez tabelas publicadas e conferidas                   | Publicação validada pelo orquestrador; execução isolada não repetida após refatoração |
| `postgres.validate_gold --offline` | Validação dos arquivos locais sem erros               | Confirmado: 7 OK, 5 alertas documentais, 0 erros                                      |
| `postgres.validate_gold --deep`    | Integridade e relacionamentos do PostgreSQL Gold      | Confirmado: 46 OK, 5 alertas documentais, 0 erros                                     |
| Chatbot local                      | Consulta real, histórico e exclusão                   | Validado anteriormente; repetir testes de integração após as alterações recentes      |
| Frontend local                     | Testes, build e integração                            | 13 testes aprovados, TypeScript, ESLint e build Vite aprovados                        |
| Docker Compose                     | Build e disponibilidade HTTP dos serviços             | Build aprovado; API HTTP 200, frontend HTTP 200 e PostgreSQL healthy                  |
| Integração Docker                  | Consulta real via frontend, Gemini, RAG e PostgreSQL  | Pendente de validação funcional completa                                              |
| ETL em Docker                      | Serviço dedicado, entrada/saída e publicação testadas | Não implementado                                                                      |
| RAG                                | Dry-run e sincronização após revisão dos `.md`        | Último dry-run com 4 embeddings pendentes; sincronização final não confirmada         |

**Regra de documentação:** só marque como validado aquilo que foi efetivamente executado. O README principal deve apresentar a aplicação e apontar para este arquivo, evitando duplicar a execução.
