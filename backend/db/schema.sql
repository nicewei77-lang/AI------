CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);


CREATE TABLE IF NOT EXISTS tags (
    id BIGSERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL
);


CREATE TABLE IF NOT EXISTS posts (
    id BIGSERIAL PRIMARY KEY,
    author_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    post_type TEXT NOT NULL DEFAULT 'project',
    service_url TEXT,
    github_url TEXT,
    one_liner TEXT,
    target_user TEXT,
    tech_stack TEXT[] NOT NULL DEFAULT '{}'::TEXT[],
    analysis_status TEXT NOT NULL DEFAULT 'not_started',
    ai_summary TEXT,
    score INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT posts_post_type_check CHECK (post_type IN ('project', 'idea')),
    CONSTRAINT posts_analysis_status_check CHECK (
        analysis_status IN ('not_started', 'running', 'completed', 'failed', 'need_more_info')
    )
);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'posts' AND column_name = 'excuse_text'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'posts' AND column_name = 'body'
    ) THEN
        ALTER TABLE posts RENAME COLUMN excuse_text TO body;
    END IF;
END $$;

ALTER TABLE posts
    DROP COLUMN IF EXISTS verdict,
    DROP COLUMN IF EXISTS credibility,
    DROP COLUMN IF EXISTS context;

ALTER TABLE posts
    ADD COLUMN IF NOT EXISTS body TEXT,
    ADD COLUMN IF NOT EXISTS post_type TEXT NOT NULL DEFAULT 'project',
    ADD COLUMN IF NOT EXISTS service_url TEXT,
    ADD COLUMN IF NOT EXISTS github_url TEXT,
    ADD COLUMN IF NOT EXISTS one_liner TEXT,
    ADD COLUMN IF NOT EXISTS target_user TEXT,
    ADD COLUMN IF NOT EXISTS tech_stack TEXT[] NOT NULL DEFAULT '{}'::TEXT[],
    ADD COLUMN IF NOT EXISTS analysis_status TEXT NOT NULL DEFAULT 'not_started',
    ADD COLUMN IF NOT EXISTS ai_summary TEXT;

UPDATE posts SET body = '' WHERE body IS NULL;
ALTER TABLE posts ALTER COLUMN body SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'posts_post_type_check'
    ) THEN
        ALTER TABLE posts ADD CONSTRAINT posts_post_type_check
            CHECK (post_type IN ('project', 'idea'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'posts_analysis_status_check'
    ) THEN
        ALTER TABLE posts ADD CONSTRAINT posts_analysis_status_check
            CHECK (analysis_status IN ('not_started', 'running', 'completed', 'failed', 'need_more_info'));
    END IF;
END $$;


CREATE TABLE IF NOT EXISTS comments (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);


CREATE TABLE IF NOT EXISTS post_tags (
    post_id BIGINT REFERENCES posts(id) ON DELETE CASCADE,
    tag_id BIGINT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);


CREATE TABLE IF NOT EXISTS votes (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_type TEXT NOT NULL,
    target_id BIGINT NOT NULL,
    value SMALLINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, target_type, target_id)
);


CREATE TABLE IF NOT EXISTS ai_reports (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT REFERENCES posts(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('completed', 'need_more_info', 'failed', 'refused')),
    report_type TEXT DEFAULT 'full_analysis',
    model TEXT,
    reasoning_effort TEXT,
    response_id TEXT,
    trace_id TEXT,
    usage JSONB,
    input_snapshot JSONB,
    report JSONB,
    error JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mcp_evidences (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT REFERENCES posts(id) ON DELETE CASCADE,
    report_id BIGINT REFERENCES ai_reports(id) ON DELETE SET NULL,
    tool_name TEXT NOT NULL,
    arguments JSONB,
    result JSONB,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS embeddings (
    id BIGSERIAL PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id BIGINT NOT NULL,
    embedding vector(1536),
    embedding_model TEXT NOT NULL DEFAULT 'text-embedding-3-small',
    dimensions INT NOT NULL DEFAULT 1536,
    content_text TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT embeddings_source_type_check CHECK (source_type IN ('post', 'ai_report', 'comment', 'template')),
    CONSTRAINT embeddings_dimensions_check CHECK (dimensions = 1536)
);

CREATE INDEX IF NOT EXISTS ai_reports_post_id_idx ON ai_reports (post_id);
CREATE INDEX IF NOT EXISTS mcp_evidences_post_id_idx ON mcp_evidences (post_id);
CREATE INDEX IF NOT EXISTS mcp_evidences_report_id_idx ON mcp_evidences (report_id);
CREATE INDEX IF NOT EXISTS embeddings_source_idx ON embeddings (source_type, source_id);
CREATE INDEX IF NOT EXISTS embeddings_vec_idx ON embeddings USING ivfflat (embedding vector_cosine_ops);
