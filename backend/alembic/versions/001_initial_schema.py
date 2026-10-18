"""Initial Memora schema.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-10-18
"""

from alembic import op

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("""
        CREATE TABLE namespaces (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE api_keys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            namespace_id UUID NOT NULL REFERENCES namespaces(id) ON DELETE CASCADE,
            key_hash VARCHAR(64) NOT NULL UNIQUE,
            key_prefix VARCHAR(10) NOT NULL,
            is_revoked BOOLEAN NOT NULL DEFAULT false,
            expires_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_used_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX idx_api_keys_namespace ON api_keys(namespace_id)")
    op.execute("CREATE INDEX idx_api_keys_hash ON api_keys(key_hash)")
    op.execute("""
        CREATE TABLE memories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            namespace_id UUID NOT NULL REFERENCES namespaces(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            content VARCHAR(2000) NOT NULL,
            tags VARCHAR(50)[] DEFAULT '{}',
            category VARCHAR(100),
            importance FLOAT NOT NULL DEFAULT 0.5 CHECK (importance >= 0.0 AND importance <= 1.0),
            metadata JSONB DEFAULT '{}',
            source VARCHAR(500),
            embedding vector(384),
            search_vector tsvector,
            is_summary BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX idx_memories_namespace_created ON memories(namespace_id, created_at)")
    op.execute("CREATE INDEX idx_memories_tags ON memories USING GIN(tags)")
    op.execute("CREATE INDEX idx_memories_search_vector ON memories USING GIN(search_vector)")
    op.execute("CREATE INDEX idx_memories_namespace_category ON memories(namespace_id, category)")
    op.execute("""
        CREATE TABLE compaction_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            namespace_id UUID NOT NULL REFERENCES namespaces(id) ON DELETE CASCADE,
            group_hash VARCHAR(64) NOT NULL,
            summary_memory_id UUID REFERENCES memories(id) ON DELETE SET NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'completed',
            source_count INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,
            error TEXT,
            CONSTRAINT uq_compaction_group_hash UNIQUE (namespace_id, group_hash)
        )
    """)
    op.execute("CREATE INDEX idx_compaction_runs_namespace ON compaction_runs(namespace_id)")
    op.execute("""
        CREATE TABLE compaction_sources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            summary_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
            source_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
            CONSTRAINT uq_compaction_source UNIQUE (summary_memory_id, source_memory_id)
        )
    """)
    op.execute("CREATE INDEX idx_compaction_sources_summary ON compaction_sources(summary_memory_id)")
    op.execute("CREATE INDEX idx_compaction_sources_source ON compaction_sources(source_memory_id)")
    op.execute("""
        CREATE TABLE memory_pointers (
            id VARCHAR(30) PRIMARY KEY,
            namespace_id UUID NOT NULL REFERENCES namespaces(id) ON DELETE CASCADE,
            content BYTEA NOT NULL,
            content_type VARCHAR(100) NOT NULL DEFAULT 'application/octet-stream',
            content_size INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ NOT NULL
        )
    """)
    op.execute("CREATE INDEX idx_pointers_namespace ON memory_pointers(namespace_id)")
    op.execute("CREATE INDEX idx_pointers_expires ON memory_pointers(expires_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS memory_pointers")
    op.execute("DROP TABLE IF EXISTS compaction_sources")
    op.execute("DROP TABLE IF EXISTS compaction_runs")
    op.execute("DROP TABLE IF EXISTS memories")
    op.execute("DROP TABLE IF EXISTS api_keys")
    op.execute("DROP TABLE IF EXISTS namespaces")
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
