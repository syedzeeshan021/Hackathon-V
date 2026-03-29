# Customer Success FTE - Kafka Consumer Helpers
# High-level consumer for processing events

import logging
from typing import Dict, Any, Optional, Callable, Awaitable, List
from datetime import datetime, timezone
import asyncio
import json

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import ConsumerStoppedError

from .client import KafkaClient, get_kafka_client
from .topics import TopicNames

logger = logging.getLogger(__name__)

# Type alias for message handlers
MessageHandler = Callable[[Dict[str, Any]], Awaitable[None]]


class KafkaConsumer:
    """
    High-level Kafka consumer for processing events.

    Provides:
    - Subscription to multiple topics
    - Message handler registration
    - Error handling and retry logic
    - Graceful shutdown
    """

    def __init__(
        self,
        client: Optional[KafkaClient] = None,
        group_id: Optional[str] = None,
        auto_commit: bool = True
    ):
        """
        Initialize consumer.

        Args:
            client: Optional Kafka client (uses global if not provided)
            group_id: Consumer group ID (auto-generated if not provided)
            auto_commit: Enable auto commit
        """
        self.client = client or get_kafka_client()
        self.group_id = group_id or f"customer-success-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.auto_commit = auto_commit

        self._handlers: Dict[str, List[MessageHandler]] = {}
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None

    # =============================================================================
    # HANDLER REGISTRATION
    # =============================================================================

    def register_handler(
        self,
        event_type: str,
        handler: MessageHandler
    ) -> None:
        """
        Register a handler for an event type.

        Args:
            event_type: Event type to handle
            handler: Async handler function
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")

    def unregister_handler(
        self,
        event_type: str,
        handler: MessageHandler
    ) -> None:
        """
        Unregister a handler for an event type.

        Args:
            event_type: Event type
            handler: Handler to remove
        """
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    # =============================================================================
    # START/STOP
    # =============================================================================

    async def start(
        self,
        topics: Optional[List[str]] = None
    ) -> None:
        """
        Start consuming messages.

        Args:
            topics: List of topics to subscribe to (defaults to all inbound topics)
        """
        if self._running:
            logger.warning("Consumer already running")
            return

        # Default topics
        if topics is None:
            topics = [
                TopicNames.EMAILS_INBOUND.value,
                TopicNames.WHATSAPP_INBOUND.value,
                TopicNames.WEB_FORM_SUBMISSIONS.value,
            ]

        # Create consumer
        self._consumer = self.client.create_consumer(
            topics=topics,
            group_id=self.group_id,
            auto_commit=self.auto_commit
        )

        await self._consumer.start()
        self._running = True

        # Start consumption loop
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(f"Consumer started, subscribed to topics: {topics}")

    async def stop(self) -> None:
        """Stop consuming messages."""
        if not self._running:
            return

        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self._consumer:
            await self._consumer.stop()
            self._consumer = None

        logger.info("Consumer stopped")

    # =============================================================================
    # CONSUMPTION LOOP
    # =============================================================================

    async def _consume_loop(self) -> None:
        """Main consumption loop."""
        while self._running:
            try:
                async for msg in self._consumer:
                    if not self._running:
                        break

                    try:
                        await self._process_message(msg)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        # Don't commit offset on error for retry

                    # Commit offset if auto_commit is disabled
                    if not self.auto_commit:
                        self._consumer.commit()

            except ConsumerStoppedError:
                logger.info("Consumer stopped")
                break
            except Exception as e:
                logger.error(f"Consumer loop error: {e}")
                await asyncio.sleep(5)  # Backoff before reconnect

    async def _process_message(self, msg: Any) -> None:
        """
        Process a single Kafka message.

        Args:
            msg: Kafka message
        """
        if msg.value is None:
            return

        event = msg.value
        event_type = event.get("event_type", "unknown")

        logger.debug(f"Processing event: {event_type} from {msg.topic}")

        # Find handlers for this event type
        handlers = self._handlers.get(event_type, [])

        if not handlers:
            logger.debug(f"No handlers registered for event type: {event_type}")
            return

        # Call all registered handlers
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event_type}: {e}")

    # =============================================================================
    # UTILITY METHODS
    # =============================================================================

    @property
    def is_running(self) -> bool:
        """Check if consumer is running."""
        return self._running

    def get_stats(self) -> Dict[str, Any]:
        """Get consumer statistics."""
        return {
            "running": self._running,
            "group_id": self.group_id,
            "handlers_count": sum(len(h) for h in self._handlers.values()),
            "topics": list(self._handlers.keys())
        }


# =============================================================================
# MESSAGE PROCESSOR WORKER
# =============================================================================

class MessageProcessorWorker:
    """
    Worker that processes messages from Kafka topics.

    This is the main entry point for the worker process.
    """

    def __init__(self):
        """Initialize worker."""
        self.consumer: Optional[KafkaConsumer] = None
        self._running = False

    async def start(self) -> None:
        """Start the worker."""
        logger.info("Starting message processor worker...")

        # Create consumer
        self.consumer = KafkaConsumer(
            group_id="customer-success-worker",
            auto_commit=True
        )

        # Register handlers
        self.consumer.register_handler(
            "email.inbound",
            self._handle_email_inbound
        )
        self.consumer.register_handler(
            "whatsapp.inbound",
            self._handle_whatsapp_inbound
        )
        self.consumer.register_handler(
            "web_form.submission",
            self._handle_web_form_submission
        )
        self.consumer.register_handler(
            "escalation.created",
            self._handle_escalation
        )

        # Start consuming
        await self.consumer.start()
        self._running = True

        logger.info("Message processor worker started")

    async def stop(self) -> None:
        """Stop the worker."""
        self._running = False
        if self.consumer:
            await self.consumer.stop()
        logger.info("Message processor worker stopped")

    # =============================================================================
    # MESSAGE HANDLERS
    # =============================================================================

    async def _handle_email_inbound(self, event: Dict[str, Any]) -> None:
        """Handle inbound email event."""
        logger.info(f"Processing inbound email: {event.get('event_id')}")
        # In production, call Gmail handler
        # await gmail_handler.process_inbound_email(event['data'])

    async def _handle_whatsapp_inbound(self, event: Dict[str, Any]) -> None:
        """Handle inbound WhatsApp event."""
        logger.info(f"Processing inbound WhatsApp: {event.get('event_id')}")
        # In production, call WhatsApp handler
        # await whatsapp_handler.process_inbound_message(event['data'])

    async def _handle_web_form_submission(self, event: Dict[str, Any]) -> None:
        """Handle web form submission event."""
        logger.info(f"Processing web form submission: {event.get('event_id')}")
        # In production, call Web Form handler
        # await web_form_handler.process_form_submission(event['data'])

    async def _handle_escalation(self, event: Dict[str, Any]) -> None:
        """Handle escalation event."""
        logger.info(f"Processing escalation: {event.get('event_id')}")
        # In production, send notification to human agents
        # await notification_service.send_escalation_alert(event['data'])


# =============================================================================
# WORKER ENTRY POINT
# =============================================================================

async def run_worker() -> None:
    """Run the message processor worker."""
    worker = MessageProcessorWorker()

    try:
        await worker.start()

        # Keep running until interrupted
        while worker._running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down...")
    finally:
        await worker.stop()
