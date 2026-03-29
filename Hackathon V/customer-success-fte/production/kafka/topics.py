# Customer Success FTE - Kafka Topic Definitions

from enum import Enum
from typing import Dict, List


class TopicNames(str, Enum):
    """Kafka topic names for customer success events."""

    # Inbound events (from channels)
    EMAILS_INBOUND = "customer_success.emails.inbound"
    WHATSAPP_INBOUND = "customer_success.whatsapp.inbound"
    WEB_FORM_SUBMISSIONS = "customer_success.web_form.submissions"

    # Outbound events (responses)
    EMAILS_OUTBOUND = "customer_success.emails.outbound"
    WHATSAPP_OUTBOUND = "customer_success.whatsapp.outbound"

    # Internal events
    TICKETS_CREATED = "customer_success.tickets.created"
    TICKETS_UPDATED = "customer_success.tickets.updated"
    ESCALATIONS = "customer_success.escalations"

    # Analytics
    METRICS = "customer_success.metrics"
    AUDIT_LOG = "customer_success.audit"


# Topic configurations
TOPIC_CONFIGS: Dict[str, Dict] = {
    TopicNames.EMAILS_INBOUND: {
        "partitions": 3,
        "replication_factor": 1,
        "retention_ms": 604800000,  # 7 days
        "config": {
            "cleanup.policy": "delete",
        }
    },
    TopicNames.WHATSAPP_INBOUND: {
        "partitions": 3,
        "replication_factor": 1,
        "retention_ms": 604800000,
        "config": {
            "cleanup.policy": "delete",
        }
    },
    TopicNames.WEB_FORM_SUBMISSIONS: {
        "partitions": 2,
        "replication_factor": 1,
        "retention_ms": 604800000,
        "config": {
            "cleanup.policy": "delete",
        }
    },
    TopicNames.EMAILS_OUTBOUND: {
        "partitions": 2,
        "replication_factor": 1,
        "retention_ms": 2592000000,  # 30 days
        "config": {
            "cleanup.policy": "delete",
        }
    },
    TopicNames.WHATSAPP_OUTBOUND: {
        "partitions": 2,
        "replication_factor": 1,
        "retention_ms": 2592000000,
        "config": {
            "cleanup.policy": "delete",
        }
    },
    TopicNames.TICKETS_CREATED: {
        "partitions": 3,
        "replication_factor": 1,
        "retention_ms": 7776000000,  # 90 days
        "config": {
            "cleanup.policy": "delete",
        }
    },
    TopicNames.TICKETS_UPDATED: {
        "partitions": 3,
        "replication_factor": 1,
        "retention_ms": 7776000000,
        "config": {
            "cleanup.policy": "delete",
        }
    },
    TopicNames.ESCALATIONS: {
        "partitions": 1,
        "replication_factor": 1,
        "retention_ms": 7776000000,
        "config": {
            "cleanup.policy": "delete",
        }
    },
    TopicNames.METRICS: {
        "partitions": 1,
        "replication_factor": 1,
        "retention_ms": 259200000,  # 3 days
        "config": {
            "cleanup.policy": "delete",
            "segment.ms": 3600000,  # 1 hour segments
        }
    },
    TopicNames.AUDIT_LOG: {
        "partitions": 3,
        "replication_factor": 1,
        "retention_ms": 7776000000,
        "config": {
            "cleanup.policy": "delete",
        }
    },
}


def get_all_topics() -> List[str]:
    """Get list of all topic names."""
    return [topic.value for topic in TopicNames]


def get_topic_config(topic_name: str) -> Dict:
    """Get configuration for a specific topic."""
    return TOPIC_CONFIGS.get(topic_name, {
        "partitions": 1,
        "replication_factor": 1,
        "retention_ms": 604800000,
    })
