# Customer Success FTE - Project Context

**Project:** Customer Success Digital FTE (Hackathon 5)
**Goal:** Build a 24/7 AI customer support agent across Gmail, WhatsApp, and Web Form

---

## Quick Start

```bash
# Navigate to project
cd customer-success-fte

# View specifications
cat specs/002-customer-success-fte-spec.md

# View database schema
cat database/schema.sql

# View sample tickets
cat context/003-sample-tickets.json
```

---

## Project Structure

```
customer-success-fte/
├── context/              # Company info, escalation rules, sample tickets
├── specs/                # Specifications and checklists
├── production/           # Production code (to be built)
├── database/             # PostgreSQL schema
└── web-form/             # React support form
```

---

## Key Requirements

### Channels
1. **Gmail** - Gmail API + Pub/Sub webhook
2. **WhatsApp** - Twilio WhatsApp API webhook
3. **Web Form** - FastAPI endpoint + React UI

### Agent Tools (OpenAI Agents SDK)
- `search_knowledge_base` - Find product docs
- `create_ticket` - Log all interactions (REQUIRED)
- `get_customer_history` - Cross-channel context
- `escalate_to_human` - Hand off complex issues
- `send_response` - Channel-aware response delivery

### Hard Constraints
- NEVER discuss pricing → escalate
- NEVER process refunds → escalate
- ALWAYS create ticket before responding
- ALWAYS use send_response tool

---

## Development Approach

### Phase 1: Incubation (Hours 1-16)
Use Claude Code to explore and prototype:
1. Analyze sample tickets in `context/003-sample-tickets.json`
2. Build MCP server prototype
3. Discover edge cases
4. Document findings in `specs/001-discovery-log.md`

### Phase 2: Transition (Hours 15-18)
Prepare for production:
1. Complete `specs/003-transition-checklist.md`
2. Extract working prompts
3. Create transition tests

### Phase 3: Specialization (Hours 17-40)
Build production system:
1. OpenAI Agents SDK implementation
2. PostgreSQL + pgvector setup
3. Kafka event streaming
4. Channel integrations
5. Kubernetes deployment

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `specs/002-customer-success-fte-spec.md` | Full specification |
| `specs/001-discovery-log.md` | Incubation findings |
| `specs/003-transition-checklist.md` | Transition checklist |
| `context/001-company-profile.md` | Company context |
| `context/002-escalation-rules.md` | When to escalate |
| `context/004-brand-voice.md` | Communication style |
| `database/schema.sql` | PostgreSQL CRM schema |

---

## Tech Stack

- **Agent:** OpenAI Agents SDK
- **API:** FastAPI
- **Database:** PostgreSQL + pgvector
- **Events:** Kafka
- **Frontend:** React (web form)
- **Deploy:** Kubernetes + Docker

---

## Commands

```bash
# Run tests
pytest production/tests/

# Start local dev
docker-compose up -d
uvicorn production.api.main:app --reload

# Deploy to K8s
kubectl apply -f production/k8s/
```

---

## Notes

- This is a **specification-driven** project
- Update specs/ documents during Incubation
- All edge cases must have test cases
- Follow the transition checklist before building production
