# Changelog

Notable changes to this project are documented here.

This project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.1] - 2026-11-22

### Added

- Added a changelog to track project releases.

### Fixed

- Resolved Starlette TestClient deprecation by adding httpx2 to development dependencies.
- Corrected Dependabot's Python dependency directory.
- Resolved frontend development dependency vulnerabilities.
- Approved installation scripts for esbuild and SWC.
- Documented the required database initialization and migration sequence.
- Fixed PostgreSQL row-count validation to support Psycopg dictionary rows.

### Changed

- Upgraded ESLint to version 10 and updated its React and TypeScript plugins.
- Translated the README and operational guide into English.
- Simplified project documentation while preserving technical details.
- Moved `docs/comandos.md` to `COMMANDS.md` in the repository root.
- Standardized documentation and commit conventions in English.
- Standardized version numbering across the project.
- Updated documentation links and project references.

## [0.1.0-alpha.1] - 2026-11-03

### Added

- Educational ETL pipeline using Raw, Bronze, Silver, and Gold layers.
- PostgreSQL Gold with five dimensions and five fact tables.
- Incremental RAG indexing with pgvector and Gemini embeddings.
- FastAPI backend with authorized analytical queries.
- React frontend with conversation history and contextual follow-up questions.
- Educational dashboards generated from Gold data.
- Docker Compose configuration for PostgreSQL, backend, and frontend.
- Data validation and automated testing workflows.

### Changed

- Refactored the project's data processing and application architecture.
- Integrated the chatbot and dashboards with the Gold analytical layer.

### Known Limitations

- Authentication and user-level session isolation are not implemented.
- Only two analytical indicators are enabled in the chatbot.
- Business rules still require review and approval.
- Public deployment and full security validation remain pending.
