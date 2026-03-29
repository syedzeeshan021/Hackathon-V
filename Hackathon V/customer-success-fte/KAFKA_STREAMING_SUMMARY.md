# Kafka Event Streaming Summary - Customer Success FTE

**Status:** ✅ Complete
**Date:** 2026-03-28
**Topics:** 10 topics across 4 categories

---

## Overview

This document describes the Kafka event streaming implementation for the Customer Success FTE. Kafka is used for:

- **Event-driven architecture** - Decouple channels from processing
- **Audit logging** - Track all customer interactions
- **Metrics collection** - Real-time performance monitoring
- **Escalation notifications** - Real-time alerts for human agents

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Kafka Cluster                                    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                         TOPICS                                   │    │
│  │                                                                  │    │
│  │  Inbound Events:           Outbound Events:                      │    │
│  │  - emails.inbound          - emails.outbound                     │    │
│  │  - whatsapp.inbound        - whatsapp.outbound                   │    │
│  │  - web_form.submissions                                          │    │
│  │                                                                  │    │
│  │  Internal Events:          Analytics:                            │    │
│  │  - tickets.created         - metrics                             │    │
│  │  - tickets.updated         - audit                               │    │
│  │  - escalations                                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Channels      │  │   Workers       │  │   Analytics     │
│   (Producers)   │  │   (Consumers)   │  │   (Consumers)   │
│                 │  │                 │  │                 │
│ - Gmail         │  │ - Email proc    │  │ - Metrics       │
│ - WhatsApp      │  │ - WhatsApp proc │  │ - Dashboards    │
│ - Web Form      │  │ - Web form proc │  │ - Alerts        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Topic Definitions

### Inbound Events (3 topics)

| Topic | Partitions | Retention | Purpose |
|-------|------------|-----------|---------|
| `customer_success.emails.inbound` | 3 | 7 days | Incoming emails from Gmail |
| `customer_success.whatsapp.inbound` | 3 | 7 days | Incoming WhatsApp messages |
| `customer_success.web_form.submissions` | 2 | 7 days | Web form submissions |

### Outbound Events (2 topics)

| Topic | Partitions | Retention | Purpose |
|-------|------------|-----------|---------|
| `customer_success.emails.outbound` | 2 | 30 days | Sent email responses |
| `customer_success.whatsapp.outbound` | 2 | 30 days | Sent WhatsApp messages |

### Internal Events (3 topics)

| Topic | Partitions | Retention | Purpose |
|-------|------------|-----------|---------|
| `customer_success.tickets.created` | 3 | 90 days | New ticket events |
| `customer_success.tickets.updated` | 3 | 90 days | Ticket updates |
| `customer_success.escalations` | 1 | 90 days | Escalation events |

### Analytics (2 topics)

| Topic | Partitions | Retention | Purpose |
|-------|------------|-----------|---------|
| `customer_success.metrics` | 1 | 3 days | Performance metrics |
| `customer_success.audit` | 3 | 90 days | Audit log events |

---

## Files Created

| File | Purpose | Size |
|------|---------|------|
| `production/kafka/__init__.py` | Package exports | 15 lines |
| `production/kafka/topics.py` | Topic definitions | 120 lines |
| `production/kafka/client.py` | Kafka client | 250 lines |
| `production/kafka/producer.py` | High-level producer | 300 lines |
| `production/kafka/consumer.py` | High-level consumer | 300 lines |
| `production/workers/__init__.py` | Workers package | 2 lines |
| `production/workers/message_processor.py` | Worker entry point | 100 lines |

**Total:** 7 files, ~1087 lines of code

---

## Kafka Client

### Connection Management

```python
from production.kafka import KafkaClient

# Create client
client = KafkaClient(bootstrap_servers="localhost:9092")

# Connect
await client.connect()

# Check health
health = await client.health_check()
# {"status": "healthy", "connected": True, ...}

# Disconnect
await client.disconnect()
```

### Topic Management

```python
# Ensure all topics exist
results = await client.ensure_topics()
# {"customer_success.emails.inbound": True, ...}
```

---

## Producer Usage

### Publish Channel Events

```python
from production.kafka import KafkaProducer

producer = KafkaProducer()

# Inbound email
await producer.publish_email_inbound(
    email_data={"from": "user@example.com", "subject": "Help"},
    message_id="msg-123"
)

# Inbound WhatsApp
await producer.publish_whatsapp_inbound(
    message_data={"from": "whatsapp:+1234567890", "body": "Help"},
    from_number="+1234567890"
)

# Web form submission
await producer.publish_web_form_submission(
    form_data={"email": "user@example.com", "message": "Help"},
    ticket_id="tkt-001"
)
```

### Publish Ticket Events

```python
# Ticket created
await producer.publish_ticket_created(
    ticket_data={"id": "tkt-001", "status": "open"},
    ticket_id="tkt-001"
)

# Ticket updated
await producer.publish_ticket_updated(
    ticket_data={"id": "tkt-001", "status": "resolved"},
    changes={"status": {"old": "open", "new": "resolved"}},
    ticket_id="tkt-001"
)
```

### Publish Escalations

```python
await producer.publish_escalation(
    escalation_data={
        "id": "esc-001",
        "ticket_id": "tkt-001",
        "reason": "negative_sentiment"
    },
    escalation_id="esc-001"
)
```

### Publish Metrics

```python
# Response time
await producer.publish_response_time(
    channel="email",
    response_time_ms=1250,
    ticket_id="tkt-001"
)

# Ticket volume
await producer.publish_ticket_volume(
    channel="whatsapp",
    count=50
)
```

### Publish Audit Logs

```python
await producer.publish_audit(
    action="ticket.created",
    user_id="system",
    resource_type="ticket",
    resource_id="tkt-001",
    details={"channel": "email"}
)
```

---

## Consumer Usage

### Create Consumer with Handlers

```python
from production.kafka import KafkaConsumer

consumer = KafkaConsumer(group_id="my-worker")

# Register handlers
consumer.register_handler(
    "email.inbound",
    handle_email_inbound
)
consumer.register_handler(
    "escalation.created",
    handle_escalation
)

# Start consuming
await consumer.start(topics=[
    "customer_success.emails.inbound",
    "customer_success.escalations"
])
```

### Handler Function

```python
async def handle_email_inbound(event: Dict[str, Any]) -> None:
    """Process inbound email event."""
    email_data = event["data"]
    event_id = event["event_id"]
    timestamp = event["timestamp"]

    # Process email
    logger.info(f"Processing email {event_id} from {email_data['from']}")

    # ... your processing logic ...
```

### Graceful Shutdown

```python
# Stop consuming
await consumer.stop()
```

---

## Message Processor Worker

### Running the Worker

```bash
# Direct execution
python production/workers/message_processor.py

# With logging
LOG_LEVEL=DEBUG python production/workers/message_processor.py
```

### Docker Compose

```yaml
services:
  worker:
    build:
      context: .
      dockerfile: production/Dockerfile
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:29092
      - DB_HOST=postgres
    command: python production/workers/message_processor.py
```

### Registered Handlers

The worker registers handlers for:

| Event Type | Handler | Action |
|------------|---------|--------|
| `email.inbound` | `_handle_email_inbound` | Process inbound email |
| `whatsapp.inbound` | `_handle_whatsapp_inbound` | Process WhatsApp message |
| `web_form.submission` | `_handle_web_form_submission` | Process form submission |
| `escalation.created` | `_handle_escalation` | Send escalation alert |

---

## Event Schema

All events follow a consistent schema:

```json
{
  "event_type": "email.inbound",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-03-28T10:30:00Z",
  "data": {
    // Event-specific payload
  }
}
```

### Event Types

| Event Type | Data Fields |
|------------|-------------|
| `email.inbound` | from, to, subject, body, message_id, thread_id |
| `whatsapp.inbound` | from, to, body, message_sid, num_media |
| `web_form.submission` | email, name, subject, message, category |
| `ticket.created` | id, customer_id, status, priority, channel |
| `ticket.updated` | id, status, changes |
| `escalation.created` | id, ticket_id, reason, urgency |
| `metric.recorded` | metric_name, metric_value, dimensions |
| `audit` | action, user_id, resource_type, resource_id |

---

## Configuration

### Environment Variables

```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=customer_success

# Consumer
KAFKA_CONSUMER_GROUP=customer-success-worker
KAFKA_AUTO_COMMIT=true
KAFKA_AUTO_OFFSET_RESET=latest
```

### Docker Compose

```yaml
services:
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
```

---

## Health Check

```python
from production.kafka import get_kafka_client

client = get_kafka_client()
health = await client.health_check()

# Response:
{
  "status": "healthy",
  "connected": True,
  "bootstrap_servers": "localhost:9092",
  "topic_count": 10,
  "producer_active": True
}
```

---

## Integration with Channels

### Gmail Handler

```python
# In gmail_handler.py
from production.kafka import KafkaProducer

class GmailHandler:
    def __init__(self, kafka_producer=None):
        self.producer = kafka_producer or KafkaProducer()

    async def process_inbound_email(self, email_data):
        # Process email...

        # Publish event
        await self.producer.publish_email_inbound(email_data)
```

### WhatsApp Handler

```python
# In whatsapp_handler.py
from production.kafka import KafkaProducer

class WhatsAppHandler:
    def __init__(self, kafka_producer=None):
        self.producer = kafka_producer or KafkaProducer()

    async def process_inbound_message(self, message_data):
        # Process message...

        # Publish event
        await self.producer.publish_whatsapp_inbound(message_data)
```

---

## Monitoring

### Metrics to Track

| Metric | Topic | Purpose |
|--------|-------|---------|
| Message throughput | metrics | Messages per second |
| Consumer lag | - | Backlog detection |
| Error rate | audit | Failed processing |
| Response time | metrics | SLA monitoring |

### Alerting

```python
# Publish escalation alert
await producer.publish_escalation({
    "id": "esc-001",
    "reason": "high_volume",
    "details": {"count": 100, "threshold": 50}
})
```

---

## Testing

### Unit Tests

```python
# Test producer
async def test_publish_email():
    producer = KafkaProducer()
    result = await producer.publish_email_inbound(
        {"from": "test@example.com"}
    )
    assert result == True
```

### Integration Tests

```python
# Test end-to-end
async def test_event_flow():
    # Publish event
    await producer.publish_email_inbound(test_data)

    # Verify consumer receives it
    event = await consumer.get_next()
    assert event["data"]["from"] == "test@example.com"
```

---

## Next Steps

1. **Schema Registry** - Add Avro schema validation
2. **Dead Letter Queue** - Handle failed messages
3. **Stream Processing** - Real-time aggregations with Kafka Streams
4. **Monitoring Dashboard** - Grafana integration for metrics

---

## Summary

Kafka event streaming is complete with:

- **10 topics** across 4 categories
- **Producer** with 10+ publish methods
- **Consumer** with handler registration
- **Worker** for background processing
- **Health checks** and monitoring

**Files:** 7 files, ~1087 lines of code
