# Memora — Lightweight Agent Memory Service

> Secure, persistent memory for AI agents: store memories, retrieve them with hybrid search, compact old memories, and store large tool outputs as pointers.

## Problem

AI agents lose context between sessions. Memora gives them a persistent, searchable memory store with namespace isolation, so multiple agents can share infrastructure without accessing each other's data.

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────┐     ┌──────────────┐
│  Dashboard   │────▶│         FastAPI Backend           │────▶│ PostgreSQL   │
│  (React/TS)  │     │                                  │     │ + pgvector   │
└─────────────┘     │  ┌──────┐ ┌────────┐ ┌────────┐  │     └──────────────┘
                    │  │ Auth │ │ Search │ │Compact │  │
┌─────────────┐     │  └──────┘ └────────┘ └────────┘  │
│ Agent / CLI  │────▶│  ┌──────┐ ┌────────┐ ┌────────┐  │
│ (API key)    │     │  │Memory│ │Pointer │ │ Stats  │  │
└─────────────┘     │  └──────┘ └────────┘ └────────┘  │
                    └──────────────────────────────────┘
```

**Modular monolith** — all features in one FastAPI app, structured as internal modules. No microservices.

### Key Design Choices

- **Hybrid search:** Reciprocal Rank Fusion (k=60) over keyword (tsvector + GIN) and semantic (pgvector) retrieval.
- **Namespace isolation:** Every query scoped by the namespace derived from the API key. No client-supplied namespace overrides.
- **Hard deletion:** Removing a memory deletes the row, embedding, and all derived compaction summaries.
- **Deterministic compaction:** Extractive summarizer (no LLM required). LLM interface exists but is disabled by default.

## Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.12 (for local development)
- Node.js 18+ (for dashboard)

### Quick Start

```bash
# Clone and configure
git clone <repo-url> && cd memora
cp .env.example .env
# Edit .env — set DATABASE_URL, ADMIN_TOKEN, SESSION_SECRET_KEY

# Start everything
docker compose up --build

# Run migrations
docker compose exec backend alembic upgrade head

# Create a namespace and key
docker compose exec backend python scripts/create_namespace.py --name "my-agent"
# Save the printed API key — it is shown only once.
```

### Environment Variables

See [`.env.example`](.env.example) for all variables with descriptions.

### API Endpoints

```
GET    /health                              — health check
POST   /v1/namespaces                       — create namespace (admin)
POST   /v1/namespaces/{id}/keys             — create API key (admin)
POST   /v1/keys/{key_id}/revoke             — revoke key (admin or own namespace)
POST   /v1/session                          — exchange key for session cookie
DELETE /v1/session                          — end session
POST   /v1/memories                         — create memory
GET    /v1/memories                         — list memories
GET    /v1/memories/{id}                    — get memory
PATCH  /v1/memories/{id}                    — update memory
DELETE /v1/memories/{id}                    — delete memory
POST   /v1/memories/search                  — hybrid search
POST   /v1/compaction/dry-run               — preview compaction
POST   /v1/compaction/run                   — run compaction
POST   /v1/pointers                         — create pointer
GET    /v1/pointers/{id}                    — get pointer
DELETE /v1/pointers/{id}                    — delete pointer
GET    /v1/stats                            — namespace stats
```

Full request/response schemas are available at `/docs` (Swagger UI) when the backend is running.

### Example: Store and Search a Memory

```bash
# Store a memory (replace YOUR_API_KEY)
curl -X POST http://localhost:8000/v1/memories \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Database choice",
    "content": "We chose PostgreSQL 16 for its pgvector support and full-text search.",
    "tags": ["architecture", "database"],
    "category": "decision",
    "importance": 0.8
  }'

# Search using different wording
curl -X POST http://localhost:8000/v1/memories/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "which database engine did we pick?"}'
```

## Demo Walkthrough

See the scripted demo scenario in `backend/tests/demo/` (Checkpoint 7) which exercises:
1. Namespace + key creation → 2. Memory storage → 3. Cross-session search → 4. Pointer storage → 5. Compaction → 6. Hard deletion cascade → 7. Cross-namespace denial.

## Limitations

- **Rate limiting is per-instance** (`slowapi` in-memory). Multi-instance deployments need Redis-backed limiting.
- **No Row-Level Security** — isolation is application-enforced and test-verified. See DECISIONS.md.
- **Embedding model is English-centric** — multilingual queries may degrade.
- **No background compaction scheduler** — compaction runs on-demand via API or CLI.
- **Single-node deployment** — no HA, clustering, or replication in MVP.
- **256-token embedding window** — long content is truncated for embedding (full content is stored and keyword-searchable).

## Future Work

- Row-Level Security for defense-in-depth
- HNSW vector index for large namespaces (>10k memories)
- LLM-backed compaction summarizer
- Background compaction scheduler
- Redis-backed rate limiting
- Multi-user accounts and RBAC
- Multilingual embedding model

## Documentation

| File | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | Agent development rules |
| [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) | Checkpoint status, results, task list |
| [DECISIONS.md](DECISIONS.md) | Architecture decisions and rationale |
| [SECURITY.md](SECURITY.md) | Threat model and security controls |
| [.env.example](.env.example) | Environment variable template |
