# Customer Success FTE - Digital Employee

> **Hackathon 5: The CRM Digital FTE Factory**
>
> Build a 24/7 AI-powered customer support agent that handles inquiries across Gmail, WhatsApp, and Web Form channels.

---

## Quick Links

- [Hackathon Specification](../The%20CRM%20Digital%20FTE%20Factory%20Final%20Hackathon%205.md)
- [Project Specification](specs/002-customer-success-fte-spec.md)
- [Discovery Log](specs/001-discovery-log.md)
- [Transition Checklist](specs/003-transition-checklist.md)
- [Database Schema](database/schema.sql)

---

## Project Overview

This project builds a **Customer Success Digital FTE** (Full-Time Equivalent) - an AI employee that:

- Handles customer questions about products 24/7
- Accepts inquiries from **3 channels**: Gmail, WhatsApp, and Web Form
- Triage and escalate complex issues appropriately
- Track all interactions in a PostgreSQL-based ticket management system (CRM)
- Generate daily reports on customer sentiment
- Learn from resolved tickets to improve responses

**Target Cost:** < $1,000/year (vs $75,000/year for human FTE)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-CHANNEL INTAKE                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │  Gmail   │    │ WhatsApp │    │ Web Form │                  │
│  │ Webhook  │    │ Webhook  │    │ Endpoint │                  │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘                  │
│       │               │               │                         │
│       └───────────────┼───────────────┘                         │
│                       ▼                                         │
│              ┌─────────────────┐                                │
│              │  Kafka (Events) │                                │
│              └────────┬────────┘                                │
│                       │                                         │
│                       ▼                                         │
│              ┌─────────────────┐                                │
│              │  Agent Worker   │                                │
│              │ (OpenAI Agents) │                                │
│              └────────┬────────┘                                │
│                       │                                         │
│         ┌─────────────┼─────────────┐                          │
│         ▼             ▼             ▼                           │
│    ┌─────────┐  ┌──────────┐  ┌──────────┐                     │
│    │Postgres │  │  Gmail   │  │  Twilio  │                     │
│    │  (CRM)  │  │   API    │  │   API    │                     │
│    └─────────┘  └──────────┘  └──────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Agent Framework** | OpenAI Agents SDK |
| **API Layer** | FastAPI |
| **Database** | PostgreSQL + pgvector |
| **Event Streaming** | Apache Kafka |
| **Channel Integrations** | Gmail API, Twilio WhatsApp API |
| **Frontend** | React (Web Form) |
| **Deployment** | Kubernetes |
| **Containerization** | Docker |

---

## Project Structure

```
customer-success-fte/
├── context/                    # Incubation phase artifacts
│   ├── 001-company-profile.md
│   ├── 002-escalation-rules.md
│   └── sample-tickets.json
│
├── specs/                      # Specification documents
│   ├── 001-discovery-log.md
│   ├── 002-customer-success-fte-spec.md
│   └── 003-transition-checklist.md
│
├── production/
│   ├── agent/                  # OpenAI Agents SDK implementation
│   ├── channels/               # Gmail, WhatsApp, Web Form handlers
│   ├── workers/                # Kafka message processors
│   ├── api/                    # FastAPI service
│   ├── database/               # PostgreSQL schema and queries
│   ├── tests/                  # Test suite
│   └── k8s/                    # Kubernetes manifests
│
├── web-form/                   # React support form component
│
├── database/
│   └── schema.sql              # PostgreSQL CRM schema
│
└── README.md
```

---

## Development Phases

### Phase 1: Incubation (Hours 1-16)

**Goal:** Explore requirements and build working prototype

- [ ] Set up context files (company profile, sample tickets, escalation rules)
- [ ] Use Claude Code to explore the problem space
- [ ] Build MCP server prototype with 5+ tools
- [ ] Discover edge cases through testing
- [ ] Document findings in `specs/001-discovery-log.md`

### Phase 2: Transition (Hours 15-18)

**Goal:** Prepare for production build

- [ ] Complete `specs/003-transition-checklist.md`
- [ ] Extract working prompts and tool definitions
- [ ] Create transition test suite
- [ ] Map prototype code to production structure

### Phase 3: Specialization (Hours 17-40)

**Goal:** Build production-grade Custom Agent

- [ ] Implement OpenAI Agents SDK agent
- [ ] Build Gmail integration (webhook + send)
- [ ] Build WhatsApp integration via Twilio
- [ ] Build Web Form UI (React component)
- [ ] Set up PostgreSQL database with pgvector
- [ ] Configure Kafka topics and event streaming
- [ ] Create FastAPI service with all endpoints
- [ ] Build Kubernetes deployment manifests
- [ ] Dockerize and deploy

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for web form)
- Docker Desktop
- Kubernetes cluster (local: kind/minikube, or cloud)
- OpenAI API key
- Gmail API credentials
- Twilio account (for WhatsApp)

### Local Development Setup

```bash
# 1. Clone and navigate to project
cd customer-success-fte

# 2. Create Python virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies (after requirements.txt is created)
pip install -r requirements.txt

# 4. Start database with Docker
docker-compose up -d postgres

# 5. Run database migrations
psql -f database/schema.sql

# 6. Start Kafka (requires Docker)
docker-compose up -d kafka

# 7. Set environment variables
export OPENAI_API_KEY=your-key
export POSTGRES_HOST=localhost
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# 8. Run the API server
uvicorn production.api.main:app --reload
```

---

## Supported Channels

| Channel | Identifier | Integration | Response Style |
|---------|------------|-------------|----------------|
| **Email** | Email address | Gmail API + Pub/Sub | Formal, detailed (500 words) |
| **WhatsApp** | Phone number | Twilio WhatsApp API | Conversational, concise (160 chars) |
| **Web Form** | Email address | FastAPI + React | Semi-formal (300 words) |

---

## Agent Tools

| Tool | Purpose |
|------|---------|
| `search_knowledge_base` | Find relevant product documentation |
| `create_ticket` | Log customer interaction (required for all conversations) |
| `get_customer_history` | Get cross-channel conversation history |
| `escalate_to_human` | Hand off to human support |
| `send_response` | Send reply via appropriate channel |

---

## Testing

```bash
# Run unit tests
pytest production/tests/

# Run transition tests
pytest production/tests/test_transition.py

# Run end-to-end tests
pytest production/tests/test_e2e.py
```

---

## Deployment

### Kubernetes Deployment

```bash
# Apply namespace
kubectl apply -f production/k8s/namespace.yaml

# Apply configuration
kubectl apply -f production/k8s/configmap.yaml
kubectl apply -f production/k8s/secrets.yaml

# Deploy application
kubectl apply -f production/k8s/deployment-api.yaml
kubectl apply -f production/k8s/deployment-worker.yaml

# Check status
kubectl get pods -n customer-success-fte
```

---

## Key Metrics

| Metric | Target |
|--------|--------|
| Response time (processing) | < 3 seconds |
| Response time (delivery) | < 30 seconds |
| Accuracy on test set | > 85% |
| Escalation rate | < 20% |
| Cross-channel ID accuracy | > 95% |

---

## Guardrails

The agent must NEVER:
- Discuss pricing (escalate immediately)
- Promise features not in documentation
- Process refunds (escalate to billing)
- Share internal processes or system details
- Respond without using `send_response` tool

---

## License

This project is part of GIAIC Q4 Agentic AI Hackathon 5.

---

## Team

- **Developer:** _Your Name_
- **Hackathon:** Customer Success Digital FTE
- **Start Date:** 2026-03-17
