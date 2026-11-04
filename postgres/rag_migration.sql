-- Complemento incremental ao rag_schema.sql ja instalado.
-- Nao altera gold, nao apaga vetores e pode ser reexecutado.
BEGIN;
ALTER TABLE rag.chunks
    ADD COLUMN IF NOT EXISTS section text NOT NULL DEFAULT '';
ALTER TABLE rag.chunks
    ADD COLUMN IF NOT EXISTS rule_ids text[] NOT NULL DEFAULT '{}'::text[];

CREATE TABLE IF NOT EXISTS rag.document_versions (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id bigint NOT NULL REFERENCES rag.documents(id) ON DELETE CASCADE,
    content_hash text NOT NULL,
    version_label text NOT NULL,
    status text NOT NULL,
    rule_ids text[] NOT NULL DEFAULT '{}'::text[],
    chunk_count integer NOT NULL CHECK (chunk_count >= 0),
    indexed_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, content_hash)
);
COMMIT;
