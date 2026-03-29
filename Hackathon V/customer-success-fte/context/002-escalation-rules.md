# Escalation Rules

**Version:** 1.0
**Created:** 2026-03-17
**Status:** Initial - To be refined during Incubation

---

## Overview

This document defines when and how the Customer Success FTE should escalate conversations to human agents.

---

## Automatic Escalation Triggers

### Critical (Always Escalate Immediately)

| Trigger | Keywords/Patterns | Reason Code | Action |
|---------|------------------|-------------|--------|
| Legal threats | "lawyer", "attorney", "sue", "lawsuit", "legal action" | `legal_threat` | Escalate + notify legal team |
| Pricing inquiries | "how much", "pricing", "cost", "price", "enterprise plan" | `pricing_inquiry` | Escalate to sales |
| Refund requests | "refund", "money back", "cancel subscription" | `refund_request` | Escalate to billing |
| Competitor questions | "competitor name", "better than", "switch from" | `competitor_inquiry` | Escalate to sales |

### High Priority (Escalate After Attempting to Help)

| Trigger | Condition | Reason Code | Action |
|---------|-----------|-------------|--------|
| Negative sentiment | Sentiment score < 0.3 | `negative_sentiment` | Show empathy, then escalate |
| Human request | "human", "agent", "representative", "real person" | `human_request` | Escalate immediately |
| Repeated failures | Same question asked 3+ times | `unresolved_issue` | Escalate with conversation history |
| VIP customer | Customer metadata indicates VIP | `vip_request` | Priority escalation |

### Medium Priority (Escalate If Cannot Resolve)

| Trigger | Condition | Reason Code | Action |
|---------|-----------|-------------|--------|
| Unknown topic | KB search returns 0 results twice | `unknown_topic` | Escalate with search queries |
| Feature request | "can you add", "I wish", "feature request" | `feature_request` | Escalate to product team |
| Bug report | "bug", "broken", "not working", "error" | `bug_report` | Create detailed ticket, escalate |
| Integration help | Complex integration questions | `integration_help` | Escalate to engineering |

---

## Escalation Process

### Step 1: Identify Escalation Need

```python
def should_escalate(conversation_context) -> tuple[bool, str]:
    # Check for critical triggers first
    if contains_legal_keywords(conversation_context):
        return True, "legal_threat"

    if contains_pricing_keywords(conversation_context):
        return True, "pricing_inquiry"

    # Check sentiment
    if sentiment_score < 0.3:
        return True, "negative_sentiment"

    # Check for explicit human request
    if customer_requests_human(conversation_context):
        return True, "human_request"

    return False, ""
```

### Step 2: Call Escalation Tool

```python
await escalate_to_human({
    "ticket_id": ticket_id,
    "reason": reason_code,
    "urgency": "high" if critical_trigger else "normal",
    "context": {
        "customer_id": customer_id,
        "conversation_summary": summary,
        "attempts_made": attempts,
        "customer_sentiment": sentiment_score
    }
})
```

### Step 3: Update Ticket Status

```sql
UPDATE tickets
SET status = 'escalated',
    resolution_notes = 'Escalated: {reason}. Customer sentiment: {sentiment}. Attempts: {attempts}'
WHERE id = {ticket_id};
```

### Step 4: Send Customer Response

**For Critical Escalations:**
```
"I understand this is important, and I want to make sure you get the best help possible.
I'm connecting you with a specialist who can assist you further. They'll review your
conversation history and follow up shortly.

Reference: {ticket_id}"
```

**For High Priority Escalations:**
```
"Thanks for your patience. I'm going to have a team member follow up on this to make
sure you get the help you need. They'll be in touch soon!

Reference: {ticket_id}"
```

---

## Escalation Routing

| Reason Code | Route To | SLA | Notification |
|-------------|----------|-----|--------------|
| `legal_threat` | Legal Team | Immediate | Slack + Email + PagerDuty |
| `pricing_inquiry` | Sales Team | 2 hours | Email + Slack |
| `refund_request` | Billing Team | 24 hours | Email |
| `negative_sentiment` | Support Lead | 1 hour | Slack |
| `human_request` | Next Available Agent | 30 minutes | Slack |
| `bug_report` | Engineering | 4 hours | Email + Jira |
| `feature_request` | Product Team | Weekly review | Email |
| `unknown_topic` | Support Lead | 1 hour | Slack |

---

## Kafka Escalation Event Schema

```json
{
  "event_type": "escalation",
  "timestamp": "2026-03-17T10:30:00Z",
  "ticket_id": "uuid",
  "conversation_id": "uuid",
  "customer_id": "uuid",
  "reason_code": "pricing_inquiry",
  "urgency": "high",
  "context": {
    "channel": "email",
    "customer_email": "customer@example.com",
    "sentiment_score": 0.45,
    "message_count": 3,
    "duration_seconds": 45,
    "attempts_made": 1,
    "search_queries": ["pricing", "enterprise"],
    "tools_called": ["create_ticket", "search_knowledge_base"]
  },
  "conversation_summary": "Customer asked about Enterprise plan pricing",
  "requires_response": true,
  "suggested_action": "Sales team to provide custom quote"
}
```

---

## Do NOT Escalate

The agent should handle these WITHOUT escalation:

| Topic | Action |
|-------|--------|
| Password resets | Guide through reset flow |
| API authentication | Provide documentation |
| Rate limit questions | Explain limits from docs |
| How-to questions | Search KB and guide |
| Account settings | Provide step-by-step instructions |
| General product questions | Answer from KB |

---

## Metrics to Track

| Metric | Target | Purpose |
|--------|--------|---------|
| Overall escalation rate | < 20% | Measure agent effectiveness |
| Escalation by channel | Track per channel | Identify channel-specific issues |
| Time to escalate | < 30 seconds | Ensure quick handoffs |
| Re-escalation rate | < 5% | Measure escalation quality |
| Customer satisfaction post-escalation | > 4.0/5.0 | Measure handoff quality |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-17 | Initial specification from hackathon doc |
