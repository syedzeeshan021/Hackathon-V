# Discovery Log - Customer Success FTE

**Created:** 2026-03-17
**Status:** Initial draft - To be updated during Incubation phase

---

## Purpose

This document captures all requirements, patterns, and edge cases discovered during the Incubation phase (Hours 1-16) of building the Customer Success Digital FTE.

---

## Discovered Requirements

### Functional Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| FR-001 | Agent must accept tickets from Gmail, WhatsApp, and Web Form | Critical | Hackathon spec |
| FR-002 | Agent must create a ticket before responding to any customer | Critical | Hackathon spec |
| FR-003 | Agent must track customer conversations across all channels | Critical | Hackathon spec |
| FR-004 | Agent must adapt response style per channel | High | Hackathon spec |
| FR-005 | Agent must escalate pricing inquiries immediately | Critical | Hackathon spec |
| FR-006 | Agent must escalate refund requests | Critical | Hackathon spec |
| FR-007 | Agent must track sentiment for each conversation | High | Hackathon spec |
| FR-008 | Agent must provide conversation continuity across channels | High | Hackathon spec |
| FR-009 | Web support form must be a complete, embeddable UI | Critical | Hackathon spec |
| FR-010 | Agent must generate daily reports on customer sentiment | Medium | Hackathon spec |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-001 | Response time (processing) | < 3 seconds |
| NFR-002 | Response time (delivery) | < 30 seconds |
| NFR-003 | Accuracy on test set | > 85% |
| NFR-004 | Escalation rate | < 20% |
| NFR-005 | Cross-channel identification accuracy | > 95% |
| NFR-006 | System availability | 24/7 |
| NFR-007 | Infrastructure cost | < $1,000/year |

---

## Channel Specifications

### Email (Gmail)
- **Identifier:** Email address
- **Response Style:** Formal, detailed
- **Max Length:** 500 words
- **Required Elements:** Greeting, signature, ticket reference
- **Integration:** Gmail API + Pub/Sub webhook

### WhatsApp
- **Identifier:** Phone number
- **Response Style:** Conversational, concise
- **Max Length:** 160 chars preferred, 1600 max
- **Required Elements:** Quick resolution, offer for more help
- **Integration:** Twilio WhatsApp API webhook

### Web Form
- **Identifier:** Email address
- **Response Style:** Semi-formal
- **Max Length:** 300 words
- **Required Elements:** Thank you message, ticket ID, expected response time
- **Integration:** FastAPI endpoint + React component

---

## Edge Cases Discovered

**Validated:** 2026-03-17 via MCP Server Tests

| # | Edge Case | Handling Strategy | Test Case | Status |
|---|-----------|------------------|-----------|--------|
| 1 | Empty message | Return helpful prompt asking for details | TC-006 | [OK] Validated |
| 2 | Pricing inquiry | Immediate escalation with reason "pricing_inquiry" | TC-002 | [OK] Validated |
| 3 | Angry customer (sentiment < 0.3) | Empathy + escalation with "negative_sentiment" | TC-003 | [OK] Validated |
| 4 | Cross-channel follow-up | Link to existing conversation by customer_id | TC-005 | [OK] Validated |
| 5 | Unknown product question | Return "not found" message, suggest escalation | TC-004 | [OK] Validated |
| 6 | Explicit human request | Direct escalation with "human_request" | TC-007 | [OK] Validated |
| 7 | No KB results | Graceful message with escalation option | TC-004 | [OK] Validated |

### Additional Edge Cases to Test

| # | Edge Case | Priority | Notes |
|---|-----------|----------|-------|
| 8 | Very long customer message | Medium | Truncate for WhatsApp |
| 9 | Special characters in message | Medium | Ensure proper encoding |
| 10 | Duplicate ticket creation | High | Check existing tickets first |
| 11 | Customer with multiple identifiers | High | Merge by email/phone |
| 12 | Sentiment boundary cases | Medium | Score exactly 0.3 |

---

## Escalation Rules

*To be finalized during Incubation*

### Automatic Escalation Triggers
1. Customer mentions: "lawyer", "legal", "sue", "attorney"
2. Pricing or refund requests
3. Sentiment score < 0.3
4. Customer explicitly requests human help
5. WhatsApp: customer sends "human", "agent", "representative"
6. Cannot find relevant information after 2 KB searches

### Escalation Process
1. Call `escalate_to_human` tool with reason
2. Update ticket status to "escalated"
3. Publish to Kafka escalations topic
4. Send apologetic response to customer

---

## Response Patterns

*To be refined during Incubation*

### Email Template Structure
```
Dear [Customer],

Thank you for reaching out to TechCorp Support.

[Detailed response to question]

If you have any further questions, please don't hesitate to reply.

Best regards,
TechCorp AI Support Team
---
Ticket Reference: {ticket_id}
```

### WhatsApp Template Structure
```
[Concise answer under 300 chars]

📱 Reply for more help or type 'human' for live support.
```

### Web Form Template Structure
```
[Helpful response]

---
Need more help? Reply to this message or visit our support portal.
```

---

## Performance Baseline

**Measured:** 2026-03-17 (MCP Server Prototype Tests)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Avg response time | < 3s | < 0.1s (in-memory) | [OK] |
| Accuracy | > 85% | 100% (7/7 tests) | [OK] |
| Escalation rate | < 20% | ~40% (test scenarios biased) | N/A |
| Sentiment detection | > 90% | Working (keyword-based) | [OK] |
| Cross-channel ID | > 95% | 100% (tested) | [OK] |
| Tool success rate | > 95% | 100% (6/6 tools) | [OK] |

### Test Coverage

| Tool | Calls Made | Success |
|------|------------|---------|
| search_knowledge_base | 3 | 100% |
| create_ticket | 8 | 100% |
| get_customer_history | 2 | 100% |
| escalate_to_human | 4 | 100% |
| send_response | 7 | 100% |
| analyze_sentiment | 2 | 100% |

---

## Open Questions

*Questions to clarify during development*

1. What product documentation will the agent answer from?
2. What are the specific Gmail API credentials setup steps?
3. What Twilio WhatsApp number will be used for testing?
4. Where should the web form be embedded (which website)?

---

## Discovery Log - Key Findings

### What Worked Well

1. **Tool-based architecture** - All 6 tools function correctly
2. **In-memory prototype** - Fast iteration during development
3. **Keyword sentiment analysis** - Simple but effective for testing
4. **Channel-aware formatting** - Response lengths appropriate per channel
5. **Cross-channel ID tracking** - Customer history links correctly

### What Needs Improvement

1. **Knowledge base search** - Keyword matching is limited; need semantic search (pgvector)
2. **Sentiment analysis** - Need ML-based analysis for production
3. **Persistence** - In-memory storage must be replaced with PostgreSQL
4. **Error handling** - Need try/catch for external API calls
5. **KB coverage** - Need more product documentation entries

### Migration to Production

| Component | Current | Production |
|-----------|---------|------------|
| Storage | In-memory lists | PostgreSQL + pgvector |
| Search | Keyword matching | Vector similarity (cosine) |
| Sentiment | Keyword counting | ML API or fine-tuned model |
| Tools | Async functions | @function_tool decorators |
| Server | MCP SDK | OpenAI Agents SDK |
| Channel Integration | Simulated | Gmail API, Twilio API |

---

## Notes

- This document should be updated continuously during the Incubation phase
- All discovered edge cases must have corresponding test cases in `production/tests/test_transition.py`
- Response patterns should be validated against sample tickets
- **Test results documented in:** `specs/test-results.md`
