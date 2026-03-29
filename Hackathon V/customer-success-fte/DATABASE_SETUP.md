# Database Setup Guide - Customer Success FTE

**Status:** ✅ Complete
**Database:** PostgreSQL 16 + pgvector
**Date:** 2026-03-28

---

## Overview

This document describes the database setup for the Customer Success FTE project. The database serves as the primary data store for:

- Customer profiles (unified across Gmail, WhatsApp, Web Form)
- Conversations and message history
- Support tickets and lifecycle
- Knowledge base with vector embeddings
- Escalations to human support
- Performance metrics

---

## Quick Start

### Start Database with Docker

```bash
# Start PostgreSQL + pgvector
docker-compose up -d postgres

# Wait for health check
docker-compose ps

# View logs
docker-compose logs -f postgres
```

### Connect to Database

```bash
# Using psql
docker exec -it customer-success-db psql -U postgres -d customer_success

# Or using connection string
postgresql://postgres:postgres@localhost:5432/customer_success
```

### Verify pgvector Extension

```sql
-- Check extension is installed
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Test vector type
SELECT '[1.0, 2.0, 3.0]'::vector;
```

---

## Database Schema

### Core Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `customers` | Unified customer profiles | id, email, phone, name |
| `customer_identifiers` | Cross-channel ID mapping | identifier_type, identifier_value |
| `conversations` | Conversation threads | id, customer_id, initial_channel, status |
| `messages` | All messages with channel metadata | conversation_id, channel, role, content |
| `tickets` | Support tickets | customer_id, source_channel, priority, status |
| `knowledge_base` | Product docs with vectors | title, content, embedding (1536) |
| `escalations` | Human escalations | ticket_id, reason_code, urgency |
| `channel_configs` | Channel configuration | channel, enabled, config (JSONB) |
| `agent_metrics` | Performance metrics | metric_name, metric_value, dimensions |

### Vector Search

The `knowledge_base` table uses pgvector for semantic search:

```sql
-- Find similar documents by embedding
SELECT title, content,
       1 - (embedding <=> '[...]'::vector) as similarity
FROM knowledge_base
WHERE 1 - (embedding <=> '[...]'::vector) > 0.7
ORDER BY similarity DESC
LIMIT 5;
```

---

## Repository Layer

Python repositories provide async database operations:

### CustomerRepository

```python
from production.db import CustomerRepository

# Create or get customer by email/phone
customer = await CustomerRepository.create_or_get_customer(
    email="user@example.com"
)

# Get by identifier
customer = await CustomerRepository.get_customer_by_identifier(
    "email", "user@example.com"
)
```

### TicketRepository

```python
from production.db import TicketRepository

# Create ticket
ticket = await TicketRepository.create_ticket(
    customer_id=customer["id"],
    source_channel="email",
    issue="Cannot login",
    priority="high"
)

# Update status
await TicketRepository.update_ticket_status(
    ticket_id, "resolved", "Password reset successfully"
)
```

### KnowledgeBaseRepository

```python
from production.db import KnowledgeBaseRepository

# Semantic search with embedding
results = await KnowledgeBaseRepository.search_by_embedding(
    query_embedding=embedding,
    limit=5,
    threshold=0.7
)

# Hybrid search (keyword + vector)
results = await KnowledgeBaseRepository.search_hybrid(
    query_text="password reset",
    query_embedding=embedding,
    limit=5
)
```

### ConversationRepository

```python
from production.db import ConversationRepository

# Create conversation
conv = await ConversationRepository.create_conversation(
    customer_id=customer["id"],
    initial_channel="whatsapp"
)

# Add message
await ConversationRepository.add_message(
    conversation_id=conv["id"],
    channel="whatsapp",
    direction="inbound",
    role="customer",
    content="Help me!"
)
```

### EscalationRepository

```python
from production.db import EscalationRepository

# Create escalation
escalation = await EscalationRepository.create_escalation(
    ticket_id=ticket["id"],
    reason_code="pricing_inquiry",
    urgency="high"
)

# Get pending escalations (priority ordered)
pending = await EscalationRepository.get_pending_escalations(
    urgency="critical"
)
```

---

## Connection Pool

```python
from production.db import init_pool, close_pool, get_connection

# Initialize at startup
await init_pool()

# Use connection
async with get_connection() as conn:
    rows = await conn.fetch("SELECT * FROM customers")

# Close at shutdown
await close_pool()
```

### Pool Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `db_min_connections` | 5 | Minimum pool size |
| `db_max_connections` | 20 | Maximum pool size |
| `db_command_timeout` | 60 | Query timeout (seconds) |
| `db_max_inactive_lifetime` | 300 | Idle connection lifetime |

---

## Seed Data

The `database/seed.sql` file populates:

### Knowledge Base (15 entries)

| Category | Entries |
|----------|---------|
| authentication | 4 (Password Reset, API Keys, OAuth2, 2FA) |
| api_reference | 3 (Rate Limits, Status, Error Handling) |
| webhooks | 2 (Setup, Signature Verification) |
| troubleshooting | 4 (401, 403, 404, 429) |
| getting_started | 2 (Quick Start, SDK Installation) |

### Sample Customers

```sql
SELECT * FROM customers;
-- test@example.com
-- john.doe@company.com
-- jane.smith@startup.io
```

### Escalation Assignees

```sql
SELECT * FROM escalation_assignees;
-- Support Team, Senior Support, Sales, Billing, Legal
```

---

## Indexes

### Performance Indexes

| Table | Index | Purpose |
|-------|-------|---------|
| customers | idx_customers_email, idx_customers_phone | Fast lookup |
| conversations | idx_conversations_customer, idx_conversations_status | Filter queries |
| messages | idx_messages_conversation, idx_messages_created_at | Message retrieval |
| tickets | idx_tickets_customer, idx_tickets_status | Ticket queries |
| knowledge_base | idx_knowledge_embedding | Vector similarity (IVFFlat) |

### Vector Index

```sql
-- IVFFlat index for cosine similarity
CREATE INDEX idx_knowledge_embedding
ON knowledge_base
USING ivfflat (embedding vector_cosine_ops);
```

---

## Views

### active_conversations

Currently active conversations with message counts:

```sql
SELECT * FROM active_conversations;
```

### ticket_summary_24h

Ticket statistics for the last 24 hours:

```sql
SELECT * FROM ticket_summary_24h;
```

### customer_history

Unified customer conversation history:

```sql
SELECT * FROM customer_history WHERE customer_id = '...';
```

---

## Health Check

```python
from production.db import health_check

status = await health_check()
# {
#   "status": "healthy",
#   "database": "connected",
#   "pgvector_enabled": True,
#   "pool_stats": {"size": 10, "free": 8}
# }
```

---

## Docker Compose Services

| Service | Container Name | Port | Purpose |
|---------|----------------|------|---------|
| postgres | customer-success-db | 5432 | PostgreSQL + pgvector |
| zookeeper | customer-success-zookeeper | 2181 | Kafka coordination |
| kafka | customer-success-kafka | 9092 | Event streaming |
| kafka-ui | customer-success-kafka-ui | 8090 | Kafka web UI |
| api | customer-success-api | 8000 | FastAPI application |
| worker | customer-success-worker | - | Message processor |

---

## Environment Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=customer_success
DB_USER=postgres
DB_PASSWORD=postgres

# Connection pool
DB_MIN_CONNECTIONS=5
DB_MAX_CONNECTIONS=20
```

---

## Testing

### Run Tests

```bash
# Unit tests (use in-memory fallback)
pytest production/tests/test_agent.py -v

# Database connection test
python -c "from production.db import health_check; import asyncio; print(asyncio.run(health_check()))"
```

### In-Memory Fallback

Tests use in-memory storage when database is unavailable:

```python
# Tools automatically use DB if available, fallback to in-memory
from production.agent.tools import create_ticket_raw

# Works without database connection
result = await create_ticket_raw(input_data)
```

---

## Next Steps

1. **Start the database:**
   ```bash
   docker-compose up -d postgres
   ```

2. **Verify schema was applied:**
   ```bash
   docker exec -it customer-success-db psql -U postgres -d customer_success -c "\dt"
   ```

3. **Check seed data:**
   ```bash
   docker exec -it customer-success-db psql -U postgres -d customer_success -c "SELECT COUNT(*) FROM knowledge_base;"
   ```

4. **Start the API:**
   ```bash
   docker-compose up -d api
   ```

---

## Troubleshooting

### pgvector Not Found

```sql
-- Install extension manually
CREATE EXTENSION IF NOT EXISTS vector;
```

### Connection Refused

```bash
# Check if postgres is running
docker-compose ps postgres

# View logs
docker-compose logs postgres
```

### Pool Exhausted

Increase max connections in `.env`:
```
DB_MAX_CONNECTIONS=50
```

---

## Files Created

| File | Purpose |
|------|---------|
| `database/schema.sql` | PostgreSQL schema with pgvector |
| `database/seed.sql` | Initial data (knowledge base, customers) |
| `docker-compose.yml` | Docker services (updated) |
| `production/db/database.py` | Connection pool management |
| `production/db/customers.py` | Customer repository |
| `production/db/tickets.py` | Ticket repository |
| `production/db/conversations.py` | Conversation repository |
| `production/db/knowledge_base.py` | Knowledge base with vector search |
| `production/db/escalations.py` | Escalation repository |
| `production/core/config.py` | Configuration management |
| `.env.example` | Environment variable template |

---

## Database URL

```
postgresql://postgres:postgres@localhost:5432/customer_success
```

For async operations:
```
postgresql+asyncpg://postgres:postgres@localhost:5432/customer_success
```
