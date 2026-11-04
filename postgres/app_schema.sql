-- Histórico do chatbot. Aplicar uma vez, manualmente, via psql.
-- Não altera os schemas gold ou rag e não é executado no startup da API.
BEGIN;

CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.sessions (
    id uuid PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.messages (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES app.sessions (id) ON DELETE CASCADE,
    role text NOT NULL CHECK (role IN ('user', 'assistant')),
    content jsonb NOT NULL CHECK (
        jsonb_typeof(content) = 'object'
        AND jsonb_typeof(content -> 'text') = 'string'
    ),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS app_messages_session_id_id_idx
    ON app.messages (session_id, id DESC);

COMMIT;
