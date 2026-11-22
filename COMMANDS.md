# EI DataBot — Development Guide

This guide covers local setup, data processing, PostgreSQL, RAG, FastAPI, React, Docker, and validation.

Run commands from the repository root using **PowerShell on Windows 11**, with the Python environment activated.

> **Status:** Alpha (`v0.1.1`). Local development only. Authentication and user-level session isolation are not implemented.

## 1. Requirements

- Python 3.13
- Node.js and npm
- Docker and Docker Compose
- PostgreSQL with pgvector
- Gemini API credentials

### Environment Setup

```powershell
python --version

python -m pip install -e ".[etl]"

# Required for linting and automated tests.
python -m pip install --group dev

python -m pip check
```

Create a local `.env` file using `.env.example` as a reference.

Configure PostgreSQL credentials and `LLM_API_KEY`. Keep `.env` out of version control.

Never expose private credentials through frontend variables prefixed with `VITE_`.

### Start PostgreSQL

```powershell
docker compose config --quiet
docker compose up -d postgres
docker compose ps
```

### Initialize a New Database

Run the following commands after starting PostgreSQL.

These commands initialize the RAG and application schemas. They do not create or populate the Gold analytical tables.

```powershell
# Initialize the RAG schema and required extensions.
Get-Content "postgres/rag_schema.sql" -Raw |
    docker compose exec -T postgres sh -c 'exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1'

# Apply RAG migrations.
Get-Content "postgres/rag_migration.sql" -Raw |
    docker compose exec -T postgres sh -c 'exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1'

# Initialize the embedding cache.
Get-Content "postgres/rag_embedding_cache.sql" -Raw |
    docker compose exec -T postgres sh -c 'exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1'

# Initialize chatbot sessions and messages.
Get-Content "postgres/app_schema.sql" -Raw |
    docker compose exec -T postgres sh -c 'exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1'
```

Check `$LASTEXITCODE` after each command and stop if any SQL execution fails.

Next, generate the Gold Parquet files using the ETL commands described below. The Gold publication process creates the analytical tables.

After publishing Gold, synchronize the schema catalog before indexing RAG documents.

**Important:** These initialization commands are intended for a new database. Review schema changes and migrations before running them against existing databases.

## 2. Data Pipeline

The educational pipeline follows:

**Raw → Bronze → Silver → Gold → PostgreSQL**

The root `main.py` orchestrates ETL processing, Gold publication, catalog synchronization, and validation. Source downloads and RAG indexing are optional.

### Preview the Pipeline

```powershell
python .\main.py --help
python .\main.py --plan
```

The default plan does not process data.

Additional options:

| Option           | Purpose                               |
| ---------------- | ------------------------------------- |
| `--download`     | Update source files before ETL        |
| `--deep`         | Run deeper PostgreSQL validation      |
| `--rag`          | Synchronize RAG after data validation |
| `--no-dashboard` | Skip dashboard regeneration           |

Example:

```powershell
python .\main.py --plan --download --deep --rag
```

### Run the Complete Pipeline

```powershell
python .\main.py --run
```

**Warning:** This command can overwrite processed files and replace existing Gold tables. Check source files, database state, and backups before running it.

For deeper validation without rebuilding dashboards:

```powershell
python .\main.py --run --deep --no-dashboard
```

A successful complete run already handles Gold publication, catalog synchronization, and validation. Do not repeat these steps unnecessarily.

## 3. Individual ETL Operations

Use individual commands for debugging, partial processing, or planned maintenance. They are alternatives to the complete pipeline.

### Update Sources

```powershell
python -m etl.educacao.downloader
```

This operation may download files from external services.

### Process Data

```powershell
# All ETL phases
python -m etl.etl --educacao

# Individual phases
python -m etl.etl --educacao --phase bronze
python -m etl.etl --educacao --phase silver
python -m etl.etl --educacao --phase gold
python -m etl.etl --educacao --phase dashboard
```

When processing phases separately, follow their dependencies.

For targeted execution:

```powershell
python -m etl.etl --educacao --only STEP_NAME
python -m etl.etl --educacao --skip STEP_NAME
```

Other supported options include `--skip-bronze` and `--skip-silver`.

### Publish and Validate Gold

```powershell
python -m postgres.sync --dataset educacao
python -m postgres.sync_catalog
python -m postgres.validate_gold
```

For deeper validation:

```powershell
python -m postgres.validate_gold --deep --timeout 180
```

Gold publication can replace existing analytical tables. Catalog synchronization updates metadata without generating RAG embeddings.

## 4. RAG Synchronization

Business rules are stored in `docs/` and indexed through PostgreSQL and pgvector.

The five business documents participate in retrieval. `COMMANDS.md` is an operational guide and is **not indexed**.

### Preview Changes

```powershell
python -m postgres.sync_rag --dry-run
```

This reports pending changes without generating embeddings or modifying the database.

### Synchronize Documents

After reviewing the business documentation:

```powershell
python -m postgres.sync_rag --batch-size 5 --interval 10
```

The process uses document hashes and cached embeddings to avoid unnecessary work.

Documents awaiting approval are not included in normal retrieval. For development-only testing:

```powershell
python -m chatbot.services.rag --query 'Por que EAD não aparece nas matrículas de um município?' --include-drafts --limit 3
```

Synchronizing RAG does not approve business rules or grant additional SQL permissions. Changes to Markdown documentation do not require rebuilding Gold.

## 5. Backend and Frontend

### FastAPI

Start the backend in a terminal with the Python environment activated:

```powershell
python -m uvicorn chatbot.chatbot:app --host 127.0.0.1 --port 8000
```

Check HTTP availability from another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

The `/health` endpoint confirms HTTP availability, not connectivity with Gemini or PostgreSQL.

### React Frontend

In another terminal:

```powershell
npm --prefix .\frontend ci
npm --prefix .\frontend run dev
```

Local addresses:

- **Frontend:** `http://127.0.0.1:8080/`
- **API health:** `http://127.0.0.1:8000/health`

### Test a Conversation

Ask:

> Quantas matrículas da educação básica houve em Volta Redonda/RJ em 2025?

Then, in the same conversation:

> E em 2024?

The second question should preserve the location and indicator.

Also test conversation switching, deletion, and restoration after refreshing the page.

### Test the API Directly

```powershell
$body = @{
    pergunta = "Quantas matrículas da educação básica houve em Volta Redonda/RJ em 2025?"
    session_id = [guid]::NewGuid().ToString()
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/api/chat" `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

The chatbot supports only authorized indicators and operations. A successful HTTP response alone does not confirm the accuracy of analytical results.

## 6. Docker Compose

The current Compose configuration contains three services:

| Service    | Responsibility          |
| ---------- | ----------------------- |
| `postgres` | PostgreSQL and pgvector |
| `chatbot`  | FastAPI backend         |
| `frontend` | React/Vite application  |

There is currently **no Docker service for ETL**.

### Build Application Images

```powershell
docker compose config --quiet
docker compose build chatbot frontend
```

### Start the Application

```powershell
docker compose up -d postgres
docker compose up -d chatbot frontend
docker compose ps
```

Test the API:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Open the frontend at `http://127.0.0.1:8080/`.

### Logs and Shutdown

```powershell
# Review logs
docker compose logs --tail 100 chatbot
docker compose logs --tail 100 frontend

# Stop application services without deleting data
docker compose stop chatbot frontend
```

Starting Docker services does not execute the ETL or rebuild Gold tables.

## 7. Validation & Quality

### Python

```powershell
python -m ruff check chatbot etl dashboards health postgres tests main.py

python -m unittest discover -s tests -p 'test_*.py' -q

python -m pip check

python -m postgres.validate_gold --offline

python -m postgres.sync_rag --dry-run
```

For database validation, when PostgreSQL is available:

```powershell
python -m postgres.validate_gold --deep
```

Some validation warnings concern business documents awaiting approval.

### Frontend

```powershell
npm --prefix .\frontend run check

npm --prefix .\frontend audit --omit=dev

npm --prefix .\frontend audit
```

The `check` script includes TypeScript validation, ESLint, JavaScript tests, and a production build.

Dependency audits should be reviewed before applying upgrades. Avoid using `npm audit fix --force` without checking compatibility.

### Git Checks

```powershell
git status --short
git diff --check
git diff --stat
```

Do not commit `.env`, local databases, backups, logs, or generated datasets.

## 8. Previous Alpha 1 Validation

The following results were recorded on **November 3, 2026**:

| Check                   | Recorded result                               |
| ----------------------- | --------------------------------------------- |
| Educational ETL         | 27/27 steps completed                         |
| PostgreSQL Gold         | 2,702,972 records across 10 tables            |
| Deep Gold validation    | 46 passed, 5 documentation warnings, 0 errors |
| Offline Gold validation | 7 passed, 5 documentation warnings, 0 errors  |
| Python tests            | 56 passed                                     |
| Frontend tests          | 13 passed                                     |
| Docker images           | Backend and frontend built successfully       |
| HTTP availability       | API and frontend returned HTTP 200            |
| PostgreSQL container    | Healthy                                       |

These are **historical validation results**, not a guarantee that subsequent changes have passed the same checks.

Full conversational integration through Docker, security controls, and a dedicated Docker ETL service remain pending.

## 9. Related Documentation

- [README.md](README.md) — project overview, architecture, and limitations.
- [CHANGELOG.md](CHANGELOG.md) — release history.
- [`docs/`](docs/) — business rules, methodologies, and indicator contracts.

Business documentation remains in Portuguese and is managed separately from this operational guide.
