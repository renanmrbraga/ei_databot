-- Cache persistente dos embeddings criados pelo sincronizador RAG.
-- Seguro para reexecucao; nao modifica gold nem descarta documentos/chunks.
-- Execute apos rag_schema.sql e rag_migration.sql.
BEGIN;
CREATE TABLE IF NOT EXISTS rag.embedding_cache (
    content_hash text NOT NULL,
    embedding_model text NOT NULL,
    embedding vector(768) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (content_hash, embedding_model)
);
-- A primeira instalacao recupera os vetores que ja foram indexados.
INSERT INTO rag.embedding_cache (content_hash, embedding_model, embedding)
SELECT DISTINCT ON (content_hash, embedding_model)
    content_hash, embedding_model, embedding
FROM rag.chunks
ORDER BY content_hash, embedding_model, id
ON CONFLICT (content_hash, embedding_model) DO NOTHING;
COMMIT;
