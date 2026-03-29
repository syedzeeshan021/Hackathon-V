# Customer Success FTE - Kafka Client
# Centralized Kafka client with connection management

import logging
from typing import Optional, Dict, Any, List
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
import asyncio
import json

from ..core.config import settings
from .topics import TopicNames, TOPIC_CONFIGS, get_all_topics

logger = logging.getLogger(__name__)

# Global client instance
_kafka_client: Optional["KafkaClient"] = None


class KafkaClient:
    """
    Kafka client with connection management.

    Handles:
    - Producer and consumer creation
    - Topic management
    - Connection health monitoring
    - Automatic reconnection
    """

    def __init__(self, bootstrap_servers: str = None):
        """
        Initialize Kafka client.

        Args:
            bootstrap_servers: Kafka bootstrap servers (comma-separated)
        """
        self.bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self._producer: Optional[AIOKafkaProducer] = None
        self._admin_client: Optional[AIOKafkaAdminClient] = None
        self._connected = False
        self._reconnect_task: Optional[asyncio.Task] = None

    # =============================================================================
    # CONNECTION MANAGEMENT
    # =============================================================================

    async def connect(self) -> bool:
        """
        Establish connection to Kafka cluster.

        Returns:
            True if connected successfully
        """
        try:
            logger.info(f"Connecting to Kafka at {self.bootstrap_servers}")

            # Create producer
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retries=3,
                retry_backoff_ms=100,
            )
            await self._producer.start()

            # Create admin client
            self._admin_client = AIOKafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
            )

            # Verify connection
            await self._producer.send(TopicNames.METRICS.value, {"type": "connection_test"})
            await self._producer.flush()

            self._connected = True
            logger.info("Connected to Kafka successfully")

            # Ensure topics exist
            await self.ensure_topics()

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close Kafka connections."""
        try:
            if self._reconnect_task:
                self._reconnect_task.cancel()

            if self._producer:
                await self._producer.stop()
                self._producer = None

            if self._admin_client:
                await self._admin_client.close()
                self._admin_client = None

            self._connected = False
            logger.info("Disconnected from Kafka")

        except Exception as e:
            logger.error(f"Error disconnecting from Kafka: {e}")

    async def ensure_connected(self) -> bool:
        """Ensure connection is active, reconnect if needed."""
        if not self._connected:
            return await self.connect()

        # Check if producer is still alive
        if self._producer and not self._producer._closed:
            return True

        # Attempt reconnection
        return await self.connect()

    # =============================================================================
    # TOPIC MANAGEMENT
    # =============================================================================

    async def ensure_topics(self) -> Dict[str, bool]:
        """
        Ensure all required topics exist.

        Returns:
            Dict of topic_name -> created (True) or exists (False)
        """
        if not self._admin_client:
            logger.warning("Admin client not available, skipping topic creation")
            return {}

        results = {}
        existing_topics = await self._get_existing_topics()

        for topic_name in get_all_topics():
            if topic_name in existing_topics:
                results[topic_name] = False  # Exists
                continue

            # Create topic
            config = TOPIC_CONFIGS.get(topic_name, {})
            new_topic = NewTopic(
                name=topic_name,
                num_partitions=config.get("partitions", 1),
                replication_factor=config.get("replication_factor", 1),
                topic_configs=config.get("config", {})
            )

            try:
                await self._admin_client.create_topics([new_topic])
                results[topic_name] = True  # Created
                logger.info(f"Created topic: {topic_name}")
            except Exception as e:
                logger.error(f"Failed to create topic {topic_name}: {e}")
                results[topic_name] = False

        return results

    async def _get_existing_topics(self) -> List[str]:
        """Get list of existing topics."""
        if not self._admin_client:
            return []

        try:
            metadata = await self._admin_client.describe_topics()
            return [topic.topic for topic in metadata]
        except Exception:
            return []

    # =============================================================================
    # PRODUCER OPERATIONS
    # =============================================================================

    async def produce(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[List[tuple]] = None
    ) -> bool:
        """
        Produce a message to a Kafka topic.

        Args:
            topic: Topic name
            value: Message value (will be JSON serialized)
            key: Optional message key
            headers: Optional headers list

        Returns:
            True if sent successfully
        """
        if not await self.ensure_connected():
            logger.error("Cannot produce: not connected to Kafka")
            return False

        try:
            await self._producer.send_and_wait(
                topic=topic,
                value=value,
                key=key,
                headers=headers
            )
            logger.debug(f"Produced message to {topic}")
            return True

        except Exception as e:
            logger.error(f"Failed to produce message to {topic}: {e}")
            return False

    async def produce_batch(
        self,
        topic: str,
        messages: List[Dict[str, Any]],
        keys: Optional[List[str]] = None
    ) -> int:
        """
        Produce multiple messages to a topic.

        Args:
            topic: Topic name
            messages: List of message values
            keys: Optional list of keys (same length as messages)

        Returns:
            Number of messages sent successfully
        """
        if not await self.ensure_connected():
            return 0

        sent_count = 0
        for i, message in enumerate(messages):
            key = keys[i] if keys else None
            if await self.produce(topic, message, key):
                sent_count += 1

        return sent_count

    # =============================================================================
    # CONSUMER FACTORY
    # =============================================================================

    def create_consumer(
        self,
        topics: List[str],
        group_id: str,
        auto_commit: bool = True,
        auto_offset_reset: str = "latest"
    ) -> AIOKafkaConsumer:
        """
        Create a new consumer for specified topics.

        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group ID
            auto_commit: Enable auto commit
            auto_offset_reset: Offset reset policy

        Returns:
            AIOKafkaConsumer instance
        """
        return AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            auto_commit=auto_commit,
            auto_offset_reset=auto_offset_reset,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')) if v else None,
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
        )

    # =============================================================================
    # HEALTH CHECK
    # =============================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check Kafka connection health."""
        try:
            if not await self.ensure_connected():
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "error": "Connection failed"
                }

            # Try to get cluster metadata
            if self._admin_client:
                metadata = await self._admin_client.describe_topics()
                topic_count = len(metadata) if metadata else 0
            else:
                topic_count = 0

            return {
                "status": "healthy",
                "connected": True,
                "bootstrap_servers": self.bootstrap_servers,
                "topic_count": topic_count,
                "producer_active": self._producer is not None and not self._producer._closed
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }

    @property
    def is_connected(self) -> bool:
        """Check if connected to Kafka."""
        return self._connected


# =============================================================================
# GLOBAL CLIENT INSTANCE
# =============================================================================

def get_kafka_client() -> Optional[KafkaClient]:
    """Get or create global Kafka client instance."""
    global _kafka_client
    if _kafka_client is None:
        _kafka_client = KafkaClient()
    return _kafka_client


async def init_kafka() -> bool:
    """Initialize global Kafka client."""
    client = get_kafka_client()
    return await client.connect()


async def close_kafka() -> None:
    """Close global Kafka client."""
    global _kafka_client
    if _kafka_client:
        await _kafka_client.disconnect()
        _kafka_client = None
