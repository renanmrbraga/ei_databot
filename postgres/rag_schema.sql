-- EI DataBot: estrutura inicial do schema rag (PostgreSQL 17 + pgvector)
-- Executar separadamente da sincronizacao Gold; nao modifica o schema gold.
BEGIN;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS rag;

-- Fotografias do catalogo real do Gold (atualizadas por introspeccao).
CREATE TABLE IF NOT EXISTS rag.schema_catalog (
    object_name text PRIMARY KEY,
    definition jsonb NOT NULL,
    source_hash text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT schema_catalog_object_name_nonempty CHECK (length(btrim(object_name)) > 0),
    CONSTRAINT schema_catalog_definition_object CHECK (jsonb_typeof(definition) = 'object')
);

-- Documentos versionados na pasta knowledge/ ou docs/.
CREATE TABLE IF NOT EXISTS rag.documents (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_path text NOT NULL UNIQUE,
    title text NOT NULL,
    content_hash text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT documents_metadata_object CHECK (jsonb_typeof(metadata) = 'object')
);

-- Textos pesquisaveis e embeddings. Dimensao associada a gemini-embedding-001.
CREATE TABLE IF NOT EXISTS rag.chunks (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id bigint NOT NULL REFERENCES rag.documents(id) ON DELETE CASCADE,
    position integer NOT NULL CHECK (position >= 0),
    content text NOT NULL,
    content_hash text NOT NULL,
    embedding vector(768) NOT NULL,
    embedding_model text NOT NULL DEFAULT 'gemini-embedding-001',
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, position),
    CONSTRAINT chunks_content_nonempty CHECK (length(btrim(content)) > 0)
);

CREATE INDEX IF NOT EXISTS rag_chunks_document_idx ON rag.chunks (document_id);
-- Para corpus pequeno, busca vetorial exata e suficiente. Avaliar HNSW depois dos benchmarks.
COMMIT;
