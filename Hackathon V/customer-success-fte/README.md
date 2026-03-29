# Customer Success FTE - AI-Powered Multi-Channel Support Agent

[![Tests](https://img.shields.io/badge/tests-35%20passing-green.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

A production-ready, 24/7 AI customer support agent that handles routine queries across **Gmail**, **WhatsApp**, and **Web Form** channels with automatic ticket creation, cross-channel context awareness, and intelligent escalation.

**Goal:** Replace a $75,000/year human FTE with a < $1,000/year AI system

---

## Features

- **Multi-Channel Support:** Gmail API, Twilio WhatsApp, Web Form
- **Cross-Channel Context:** Unified customer profiles across all channels
- **Semantic Search:** pgvector-powered knowledge base retrieval
- **Event Streaming:** Kafka for escalations and analytics
- **Auto-Scaling:** Kubernetes HPA for demand-based scaling
- **Production Monitoring:** Prometheus alerts for error rate, latency, Kafka lag

---

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/syedzeeshan021/Hackathon-V.git
cd Hackathon-V/customer-success-fte

# Copy environment template
cp .env.example .env

# Edit .env with your OpenAI API key
# OPENAI_API_KEY=sk-...
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL and Kafka
docker-compose up -d postgres kafka

# Wait for services
docker-compose ps
```

### 3. Run Tests

```bash
pip install -r production/requirements.txt
pytest production/tests/ -v
```

### 4. Start Application

```bash
# Full stack (API + Worker)
docker-compose --profile full up -d

# Or run API locally
uvicorn production.api.main:app --reload

# Test health endpoint
curl http://localhost:8000/health
```

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

## Project Structure

```
customer-success-fte/
├── production/
│   ├── agent/                    # OpenAI Agents SDK
│   │   ├── customer_success_agent.py
│   │   ├── tools.py              # 6 tools: search, ticket, history, escalate, respond
│   │   ├── prompts.py
│   │   └── formatters.py
│   ├── db/                       # PostgreSQL + pgvector
│   │   ├── database.py           # Connection pooling
│   │   ├── customers.py
│   │   ├── tickets.py
│   │   ├── conversations.py
│   │   ├── knowledge_base.py     # Vector search
│   │   └── escalations.py
│   ├── channels/                 # Channel handlers
│   │   ├── gmail_handler.py      # Gmail API + Pub/Sub
│   │   ├── whatsapp_handler.py   # Twilio WhatsApp
│   │   └── web_form_handler.py   # FastAPI endpoints
│   ├── kafka/                    # Event streaming
│   │   ├── topics.py             # 10 topic definitions
│   │   ├── client.py
│   │   ├── producer.py
│   │   └── consumer.py
│   ├── api/
│   │   └── main.py               # FastAPI service (7 endpoints)
│   ├── workers/
│   │   └── message_processor.py  # Kafka consumer worker
│   ├── core/
│   │   └── config.py             # Pydantic settings
│   ├── tests/
│   │   └── test_agent.py         # 35 unit tests
│   ├── k8s/                      # Kubernetes manifests
│   │   ├── api-deployment.yaml   # HPA 3-10 pods
│   │   ├── worker-deployment.yaml # HPA 2-8 pods
│   │   ├── ingress.yaml          # SSL, rate limiting
│   │   └── monitoring.yaml       # Prometheus alerts
│   ├── Dockerfile
│   └── requirements.txt
├── database/
│   ├── schema.sql                # PostgreSQL + pgvector
│   └── seed.sql                  # 15 KB entries
├── specs/                        # Specifications
├── context/                      # Company profile, escalation rules
├── docker-compose.yml
├── .env.example
└── DEPLOYMENT_GUIDE.md
```

---

## Agent Tools

| Tool | Purpose |
|------|---------|
| `search_knowledge_base` | Find relevant product documentation using semantic search |
| `create_ticket` | Log ALL customer interactions (required before responding) |
| `get_customer_history` | Get cross-channel conversation history |
| `escalate_to_human` | Hand off complex issues (pricing, refunds, angry customers) |
| `send_response` | Send channel-aware responses (email/WhatsApp/web form) |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with DB + Kafka status |
| `/webhooks/gmail` | POST | Gmail webhook handler |
| `/webhooks/whatsapp` | POST | WhatsApp webhook handler |
| `/webhooks/web-form` | POST | Web form submission |
| `/tickets/{id}/status` | GET | Ticket status lookup |
| `/chat/instant` | POST | Instant chat support |

---

## Kafka Topics

| Category | Topics |
|----------|--------|
| Inbound | `emails.inbound`, `whatsapp.inbound`, `web_form.submissions` |
| Tickets | `tickets.created`, `tickets.updated` |
| System | `escalations`, `metrics` |

---

## Kubernetes Deployment

### Quick Deploy

```bash
# Build image
docker build -f production/Dockerfile -t customer-success-fte:v1.0.0 .

# Deploy to K8s
./production/k8s/deploy.sh

# Check status
kubectl get pods -n customer-success
kubectl logs -f deployment/customer-success-api -n customer-success
```

### Resources

| Component | Replicas | Memory | CPU |
|-----------|----------|--------|-----|
| API | 3 (HPA 3-10) | 512Mi-1Gi | 250m-1000m |
| Worker | 2 (HPA 2-8) | 512Mi-1Gi | 250m-500m |

### Monitoring Alerts

- High error rate (>5%)
- High latency (P95 >2s)
- Pod not ready (5m)
- Kafka consumer lag (>1000)
- DB pool exhausted (<2 connections)

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `DB_PASSWORD` | Yes | PostgreSQL password |
| `KAFKA_BOOTSTRAP_SERVERS` | Yes | Kafka brokers |
| `TWILIO_ACCOUNT_SID` | For WhatsApp | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | For WhatsApp | Twilio auth token |

See `.env.example` for full list.

---

## Testing

```bash
# Run all tests
pytest production/tests/ -v

# Run with coverage
pytest production/tests/ -v --cov=production --cov-report=html

# Test results: 35/35 passing (100%)
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Complete deployment instructions |
| [DATABASE_SETUP.md](DATABASE_SETUP.md) | PostgreSQL + pgvector setup |
| [CHANNEL_INTEGRATIONS_SUMMARY.md](CHANNEL_INTEGRATIONS_SUMMARY.md) | Gmail, WhatsApp, Web Form details |
| [KAFKA_STREAMING_SUMMARY.md](KAFKA_STREAMING_SUMMARY.md) | Event streaming architecture |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Project overview |
| [QUICKSTART.md](QUICKSTART.md) | Quick start guide |

---

## Tech Stack

- **Agent Framework:** OpenAI Agents SDK
- **API:** FastAPI + Uvicorn
- **Database:** PostgreSQL 16 + pgvector
- **Events:** Apache Kafka + aiokafka
- **Channels:** Gmail API, Twilio WhatsApp
- **Deploy:** Docker + Kubernetes
- **Monitoring:** Prometheus + ServiceMonitor

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Processing time | < 3 seconds |
| Delivery time | < 30 seconds |
| Accuracy | > 85% |
| Escalation rate | < 20% |
| Cross-channel ID | > 95% |

---

## License

MIT License - Internal project for educational purposes.

---

## Hackathon

**GIAIC Q4 Agentic AI - Hackathon V**

This project demonstrates a complete production-ready AI customer support agent built with the OpenAI Agents SDK, featuring multi-channel support, event streaming, and Kubernetes deployment.
