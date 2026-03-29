# Customer Success FTE Specification

**Version:** 1.0.0
**Created:** 2026-03-17
**Status:** Initial specification - To be refined during Incubation

---

## 1. Purpose

Build a 24/7 AI-powered Customer Success agent (Digital FTE) that handles routine customer support queries across multiple communication channels with speed, accuracy, and consistency.

**Business Goal:** Replace a $75,000/year human FTE with a < $1,000/year AI system that works 24/7 without breaks, sick days, or vacations.

---

## 2. Scope

### 2.1 In Scope

| Functionality | Description |
|---------------|-------------|
| Product feature questions | Answer questions about what the product does |
| How-to guidance | Help customers use the product |
| Bug report intake | Collect bug information and create tickets |
| Feedback collection | Gather and categorize customer feedback |
| Cross-channel continuity | Maintain context when customers switch channels |

### 2.2 Out of Scope (Must Escalate)

| Topic | Reason | Action |
|-------|--------|--------|
| Pricing inquiries | Requires sales team | Escalate with reason "pricing_inquiry" |
| Refund requests | Requires billing team | Escalate with reason "refund_request" |
| Legal/compliance questions | Requires legal team | Escalate with reason "legal_inquiry" |
| Angry customers (sentiment < 0.3) | Requires human empathy | Escalate with reason "negative_sentiment" |
| Feature requests not in docs | Requires product team | Escalate with reason "feature_request" |

---

## 3. Supported Channels

| Channel | Identifier | Response Style | Max Length | Integration |
|---------|------------|----------------|------------|-------------|
| **Email (Gmail)** | Email address | Formal, detailed | 500 words | Gmail API + Pub/Sub |
| **WhatsApp** | Phone number | Conversational, concise | 160 chars (preferred), 1600 (max) | Twilio WhatsApp API |
| **Web Form** | Email address | Semi-formal | 300 words | FastAPI + React |

---

## 4. Architecture Overview

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

## 5. Data Model (PostgreSQL CRM)

### 5.1 Core Tables

```sql
-- Customers (unified across channels)
customers (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    name VARCHAR(255),
    created_at TIMESTAMP,
    metadata JSONB
)

-- Customer identifiers (for cross-channel matching)
customer_identifiers (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    identifier_type VARCHAR(50),  -- 'email', 'phone', 'whatsapp'
    identifier_value VARCHAR(255),
    verified BOOLEAN,
    created_at TIMESTAMP,
    UNIQUE(identifier_type, identifier_value)
)

-- Conversations
conversations (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    initial_channel VARCHAR(50),
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    status VARCHAR(50),
    sentiment_score DECIMAL(3,2),
    resolution_type VARCHAR(50),
    escalated_to VARCHAR(255),
    metadata JSONB
)

-- Messages (with channel tracking)
messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    channel VARCHAR(50),
    direction VARCHAR(20),  -- 'inbound', 'outbound'
    role VARCHAR(20),       -- 'customer', 'agent', 'system'
    content TEXT,
    created_at TIMESTAMP,
    tokens_used INTEGER,
    latency_ms INTEGER,
    tool_calls JSONB,
    channel_message_id VARCHAR(255),
    delivery_status VARCHAR(50)
)

-- Tickets
tickets (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    customer_id UUID REFERENCES customers(id),
    source_channel VARCHAR(50),
    category VARCHAR(100),
    priority VARCHAR(20),
    status VARCHAR(50),
    created_at TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_notes TEXT
)

-- Knowledge base
knowledge_base (
    id UUID PRIMARY KEY,
    title VARCHAR(500),
    content TEXT,
    category VARCHAR(100),
    embedding VECTOR(1536),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

---

## 6. Agent Tools

| Tool | Purpose | Input Schema | Constraints |
|------|---------|--------------|-------------|
| `search_knowledge_base` | Find relevant product documentation | query: str, max_results: int (default 5) | Max 5 results returned |
| `create_ticket` | Log customer interaction | customer_id, issue, priority, category, channel | Required for ALL conversations |
| `get_customer_history` | Get cross-channel conversation history | customer_id: str | Returns last 20 messages |
| `escalate_to_human` | Hand off to human support | ticket_id, reason, urgency | Includes full context |
| `send_response` | Send reply via appropriate channel | ticket_id, message, channel | Channel-aware formatting |

---

## 7. Required Workflow

**The agent MUST follow this order for every customer interaction:**

```
1. CREATE TICKET → Log the interaction (include channel!)
       │
       ▼
2. GET CUSTOMER HISTORY → Check for prior context (all channels)
       │
       ▼
3. SEARCH KNOWLEDGE BASE → If product questions arise
       │
       ▼
4. SEND RESPONSE → Reply via channel (NEVER respond without this)
```

---

## 8. Hard Constraints (Guardrails)

| Constraint | Enforcement |
|------------|-------------|
| NEVER discuss pricing | Immediate escalation |
| NEVER promise features not in docs | KB-only responses |
| NEVER process refunds | Escalate to billing |
| NEVER share internal processes | Guardrail in system prompt |
| ALWAYS create ticket before responding | Tool call order validation |
| ALWAYS check sentiment before closing | Sentiment analysis tool |
| ALWAYS use channel-appropriate tone | Formatter middleware |
| NEVER respond without send_response tool | Tool call validation |

---

## 9. Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Processing time | < 3 seconds | Agent execution time |
| Delivery time | < 30 seconds | End-to-end latency |
| Accuracy | > 85% | Test set evaluation |
| Escalation rate | < 20% | Tickets escalated / Total |
| Cross-channel ID accuracy | > 95% | Customer resolution rate |

---

## 10. Kafka Topics

| Topic | Purpose | Producer | Consumer |
|-------|---------|----------|----------|
| `fte.tickets.incoming` | Unified ticket intake | Channel handlers | Message processor |
| `fte.channels.email.inbound` | Email-specific inbound | Gmail handler | - |
| `fte.channels.whatsapp.inbound` | WhatsApp-specific inbound | Twilio handler | - |
| `fte.channels.email.outbound` | Email responses | Message processor | Gmail handler |
| `fte.channels.whatsapp.outbound` | WhatsApp responses | Message processor | Twilio handler |
| `fte.escalations` | Human escalations | Agent | Human agents |
| `fte.metrics` | Performance metrics | Message processor | Metrics dashboard |
| `fte.dlq` | Failed messages (dead letter) | Error handler | Manual review |

---

## 11. API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/webhooks/gmail` | POST | Gmail push notifications |
| `/webhooks/whatsapp` | POST | Twilio WhatsApp webhook |
| `/webhooks/whatsapp/status` | POST | WhatsApp delivery status |
| `/support/submit` | POST | Web form submission |
| `/support/ticket/{ticket_id}` | GET | Ticket status lookup |
| `/conversations/{conversation_id}` | GET | Conversation history |
| `/customers/lookup` | GET | Customer by email/phone |
| `/metrics/channels` | GET | Channel performance metrics |

---

## 12. Test Requirements

### 12.1 Transition Tests (Required)

| Test ID | Test Case | Expected |
|---------|-----------|----------|
| TC-001 | Empty message handling | Returns helpful prompt |
| TC-002 | Pricing inquiry | Escalates with reason "pricing_inquiry" |
| TC-003 | Angry customer | Shows empathy OR escalates |
| TC-004 | Cross-channel follow-up | Links to existing conversation |
| TC-005 | Unknown product question | Searches KB twice, then escalates |
| TC-006 | Email response length | Includes greeting + signature |
| TC-007 | WhatsApp response length | Under 500 characters |
| TC-008 | Tool call order | create_ticket first, send_response last |

### 12.2 Integration Tests

- Gmail webhook processing
- WhatsApp webhook processing
- Web form submission
- Kafka message publishing
- PostgreSQL persistence

### 12.3 End-to-End Tests

- Full conversation flow per channel
- Cross-channel conversation continuity
- Escalation workflow
- Metrics collection

---

## 13. Deployment Requirements

### 13.1 Kubernetes Resources

| Component | Replicas | Memory | CPU |
|-----------|----------|--------|-----|
| API Pods | 3 | 512Mi - 1Gi | 250m - 500m |
| Worker Pods | 3 (auto-scale) | 512Mi - 1Gi | 250m - 500m |

### 13.2 Environment Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `OPENAI_API_KEY` | Secret | OpenAI API access |
| `POSTGRES_HOST` | ConfigMap | Database connection |
| `POSTGRES_PASSWORD` | Secret | Database auth |
| `KAFKA_BOOTSTRAP_SERVERS` | ConfigMap | Kafka connection |
| `GMAIL_CREDENTIALS` | Secret | Gmail API OAuth |
| `TWILIO_ACCOUNT_SID` | Secret | Twilio auth |
| `TWILIO_AUTH_TOKEN` | Secret | Twilio auth |
| `TWILIO_WHATSAPP_NUMBER` | Secret | Twilio WhatsApp sender |

---

## 14. Deliverables Checklist

### Incubation Phase (Hours 1-16)
- [x] Working prototype handling basic queries
- [x] Discovery log documenting requirements
- [x] MCP server with 5+ tools
- [x] Agent skills defined
- [x] Edge cases documented (min 10)
- [x] Escalation rules finalized
- [x] Channel-specific response templates
- [x] Performance baseline measured

### Transition Phase (Hours 15-18)
- [x] Transition checklist completed
- [x] Prompts extracted to `prompts.py`
- [x] MCP tools converted to @function_tool
- [x] Pydantic input validation for all tools
- [x] Error handling for all tools
- [x] Transition test suite created
- [x] All transition tests passing

### Specialization Phase (Hours 17-40)
- [x] PostgreSQL schema deployed
- [x] Kafka topics created
- [x] OpenAI Agents SDK implementation
- [x] Gmail integration working
- [x] WhatsApp integration working
- [x] Web form handler complete
- [x] FastAPI service running
- [x] Kubernetes deployment manifests
- [x] Docker container built and tested
- [x] End-to-end tests passing (35/35 tests passing)

---

## 15. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-17 | Initial | Initial specification from hackathon doc |
| | | | |

---

## Appendix A: Sample Customer Inquiries

*To be populated with actual sample tickets during Incubation*
