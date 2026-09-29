-- =============================================================================
-- RepoMedic PostgreSQL Initialization
-- Runs once when the postgres container is first created.
-- =============================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Confirm extensions
SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'pgcrypto');
