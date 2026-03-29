# Customer Success FTE - Kafka Producer Helpers
# High-level producer for common events

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid

from .client import KafkaClient, get_kafka_client
from .topics import TopicNames

logger = logging.getLogger(__name__)


class KafkaProducer:
    """
    High-level Kafka producer for customer success events.

    Provides methods for publishing common event types:
    - Channel events (emails, WhatsApp, web forms)
    - Ticket events
    - Escalations
    - Metrics
    """

    def __init__(self, client: Optional[KafkaClient] = None):
        """
        Initialize producer.

        Args:
            client: Optional Kafka client (uses global if not provided)
        """
        self.client = client or get_kafka_client()

    # =============================================================================
    # CHANNEL EVENTS
    # =============================================================================

    async def publish_email_inbound(
        self,
        email_data: Dict[str, Any],
        message_id: Optional[str] = None
    ) -> bool:
        """
        Publish inbound email event.

        Args:
            email_data: Email data from Gmail handler
            message_id: Optional message ID for key

        Returns:
            True if published successfully
        """
        event = {
            "event_type": "email.inbound",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": email_data
        }

        key = message_id or email_data.get("message_id", str(uuid.uuid4()))

        return await self.client.produce(
            topic=TopicNames.EMAILS_INBOUND.value,
            value=event,
            key=key
        )

    async def publish_whatsapp_inbound(
        self,
        message_data: Dict[str, Any],
        from_number: Optional[str] = None
    ) -> bool:
        """
        Publish inbound WhatsApp message event.

        Args:
            message_data: Message data from WhatsApp handler
            from_number: Optional sender number for key

        Returns:
            True if published successfully
        """
        event = {
            "event_type": "whatsapp.inbound",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": message_data
        }

        key = from_number or message_data.get("from", str(uuid.uuid4()))

        return await self.client.produce(
            topic=TopicNames.WHATSAPP_INBOUND.value,
            value=event,
            key=key
        )

    async def publish_web_form_submission(
        self,
        form_data: Dict[str, Any],
        ticket_id: Optional[str] = None
    ) -> bool:
        """
        Publish web form submission event.

        Args:
            form_data: Form submission data
            ticket_id: Optional ticket ID for key

        Returns:
            True if published successfully
        """
        event = {
            "event_type": "web_form.submission",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": form_data
        }

        key = ticket_id or str(uuid.uuid4())

        return await self.client.produce(
            topic=TopicNames.WEB_FORM_SUBMISSIONS.value,
            value=event,
            key=key
        )

    async def publish_email_outbound(
        self,
        email_data: Dict[str, Any],
        ticket_id: Optional[str] = None
    ) -> bool:
        """
        Publish outbound email event.

        Args:
            email_data: Email data
            ticket_id: Optional ticket ID for key

        Returns:
            True if published successfully
        """
        event = {
            "event_type": "email.outbound",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": email_data
        }

        key = ticket_id or str(uuid.uuid4())

        return await self.client.produce(
            topic=TopicNames.EMAILS_OUTBOUND.value,
            value=event,
            key=key
        )

    async def publish_whatsapp_outbound(
        self,
        message_data: Dict[str, Any],
        ticket_id: Optional[str] = None
    ) -> bool:
        """
        Publish outbound WhatsApp message event.

        Args:
            message_data: Message data
            ticket_id: Optional ticket ID for key

        Returns:
            True if published successfully
        """
        event = {
            "event_type": "whatsapp.outbound",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": message_data
        }

        key = ticket_id or str(uuid.uuid4())

        return await self.client.produce(
            topic=TopicNames.WHATSAPP_OUTBOUND.value,
            value=event,
            key=key
        )

    # =============================================================================
    # TICKET EVENTS
    # =============================================================================

    async def publish_ticket_created(
        self,
        ticket_data: Dict[str, Any],
        ticket_id: Optional[str] = None
    ) -> bool:
        """
        Publish ticket created event.

        Args:
            ticket_data: Ticket data
            ticket_id: Optional ticket ID for key

        Returns:
            True if published successfully
        """
        event = {
            "event_type": "ticket.created",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": ticket_data
        }

        key = ticket_id or ticket_data.get("id", str(uuid.uuid4()))

        return await self.client.produce(
            topic=TopicNames.TICKETS_CREATED.value,
            value=event,
            key=key
        )

    async def publish_ticket_updated(
        self,
        ticket_data: Dict[str, Any],
        changes: Dict[str, Any],
        ticket_id: Optional[str] = None
    ) -> bool:
        """
        Publish ticket updated event.

        Args:
            ticket_data: Updated ticket data
            changes: Fields that changed
            ticket_id: Optional ticket ID for key

        Returns:
            True if published successfully
        """
        event = {
            "event_type": "ticket.updated",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "ticket": ticket_data,
                "changes": changes
            }
        }

        key = ticket_id or ticket_data.get("id", str(uuid.uuid4()))

        return await self.client.produce(
            topic=TopicNames.TICKETS_UPDATED.value,
            value=event,
            key=key
        )

    # =============================================================================
    # ESCALATION EVENTS
    # =============================================================================

    async def publish_escalation(
        self,
        escalation_data: Dict[str, Any],
        escalation_id: Optional[str] = None
    ) -> bool:
        """
        Publish escalation event.

        Args:
            escalation_data: Escalation data
            escalation_id: Optional escalation ID for key

        Returns:
            True if published successfully
        """
        event = {
            "event_type": "escalation.created",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": escalation_data
        }

        key = escalation_id or escalation_data.get("id", str(uuid.uuid4()))

        return await self.client.produce(
            topic=TopicNames.ESCALATIONS.value,
            value=event,
            key=key
        )

    # =============================================================================
    # METRICS EVENTS
    # =============================================================================

    async def publish_metric(
        self,
        metric_name: str,
        metric_value: float,
        dimensions: Optional[Dict[str, Any]] = None,
        channel: Optional[str] = None
    ) -> bool:
        """
        Publish metric event.

        Args:
            metric_name: Metric name
            metric_value: Metric value
            dimensions: Optional dimensions
            channel: Optional channel name

        Returns:
            True if published successfully
        """
        event = {
            "event_type": "metric.recorded",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "metric_name": metric_name,
                "metric_value": metric_value,
                "dimensions": dimensions or {},
                "channel": channel
            }
        }

        return await self.client.produce(
            topic=TopicNames.METRICS.value,
            value=event,
            key=metric_name
        )

    async def publish_response_time(
        self,
        channel: str,
        response_time_ms: float,
        ticket_id: Optional[str] = None
    ) -> bool:
        """
        Publish response time metric.

        Args:
            channel: Channel name
            response_time_ms: Response time in milliseconds
            ticket_id: Optional ticket ID

        Returns:
            True if published successfully
        """
        return await self.publish_metric(
            metric_name="response_time_ms",
            metric_value=response_time_ms,
            dimensions={"ticket_id": ticket_id} if ticket_id else {},
            channel=channel
        )

    async def publish_ticket_volume(
        self,
        channel: str,
        count: int
    ) -> bool:
        """
        Publish ticket volume metric.

        Args:
            channel: Channel name
            count: Number of tickets

        Returns:
            True if published successfully
        """
        return await self.publish_metric(
            metric_name="ticket_count",
            metric_value=count,
            channel=channel
        )

    # =============================================================================
    # AUDIT EVENTS
    # =============================================================================

    async def publish_audit(
        self,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish audit log event.

        Args:
            action: Action performed
            user_id: Optional user ID
            resource_type: Optional resource type
            resource_id: Optional resource ID
            details: Optional details

        Returns:
            True if published successfully
        """
        event = {
            "event_type": "audit",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "action": action,
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {}
            }
        }

        return await self.client.produce(
            topic=TopicNames.AUDIT_LOG.value,
            value=event,
            key=action
        )
