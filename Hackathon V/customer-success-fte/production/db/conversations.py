# Customer Success FTE - Conversation Repository
# PostgreSQL operations for conversation management

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from .database import get_connection

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for conversation-related database operations."""

    # =============================================================================
    # CREATE / UPDATE
    # =============================================================================

    @staticmethod
    async def create_conversation(
        customer_id: str,
        initial_channel: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation.

        Args:
            customer_id: Customer UUID
            initial_channel: Channel where conversation started
            metadata: Optional metadata

        Returns:
            Created conversation record as dict
        """
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO conversations (
                    customer_id,
                    initial_channel,
                    status,
                    metadata
                )
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                customer_id,
                initial_channel,
                "active",
                metadata or {}
            )

            conversation = dict(row)
            logger.info(f"Created conversation: {conversation['id']} for customer {customer_id}")
            return conversation

    @staticmethod
    async def update_conversation_status(
        conversation_id: str,
        status: str,
        ended_at: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """Update conversation status."""
        async with get_connection() as conn:
            updates = ["status = $2"]
            values = [conversation_id, status]

            if status == "closed" and ended_at is None:
                ended_at = datetime.now(timezone.utc)

            if ended_at:
                updates.append("ended_at = $3")
                values.append(ended_at)

            query = f"""
            UPDATE conversations
            SET {', '.join(updates)}
            WHERE id = $1
            RETURNING *
            """

            row = await conn.fetchrow(query, *values)
            return dict(row) if row else None

    @staticmethod
    async def update_sentiment(
        conversation_id: str,
        sentiment_score: float
    ) -> Optional[Dict[str, Any]]:
        """Update conversation sentiment score."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                UPDATE conversations
                SET sentiment_score = $2
                WHERE id = $1
                RETURNING *
                """,
                conversation_id, sentiment_score
            )
            return dict(row) if row else None

    @staticmethod
    async def escalate_conversation(
        conversation_id: str,
        escalated_to: str
    ) -> Optional[Dict[str, Any]]:
        """Mark conversation as escalated."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                UPDATE conversations
                SET status = 'escalated', escalated_to = $2
                WHERE id = $1
                RETURNING *
                """,
                conversation_id, escalated_to
            )
            return dict(row) if row else None

    # =============================================================================
    # GET
    # =============================================================================

    @staticmethod
    async def get_conversation_by_id(
        conversation_id: str,
        include_messages: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get conversation by UUID with optional messages."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT c.*, cu.email as customer_email, cu.name as customer_name
                FROM conversations c
                LEFT JOIN customers cu ON c.customer_id = cu.id
                WHERE c.id = $1
                """,
                conversation_id
            )

            if not row:
                return None

            conversation = dict(row)

            if include_messages:
                messages = await conn.fetch(
                    """
                    SELECT * FROM messages
                    WHERE conversation_id = $1
                    ORDER BY created_at ASC
                    """,
                    conversation_id
                )
                conversation['messages'] = [dict(msg) for msg in messages]

            return conversation

    @staticmethod
    async def get_conversations_by_customer(
        customer_id: str,
        limit: int = 20,
        include_messages: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all conversations for a customer."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM conversations
                WHERE customer_id = $1
                ORDER BY started_at DESC
                LIMIT $2
                """,
                customer_id, limit
            )

            conversations = [dict(row) for row in rows]

            if include_messages:
                for conv in conversations:
                    messages = await conn.fetch(
                        """
                        SELECT * FROM messages
                        WHERE conversation_id = $1
                        ORDER BY created_at ASC
                        """,
                        conv['id']
                    )
                    conv['messages'] = [dict(msg) for msg in messages]

            return conversations

    @staticmethod
    async def get_active_conversations(
        customer_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get active conversations."""
        async with get_connection() as conn:
            if customer_id:
                rows = await conn.fetch(
                    """
                    SELECT * FROM conversations
                    WHERE customer_id = $1 AND status = 'active'
                    ORDER BY started_at DESC
                    LIMIT $2
                    """,
                    customer_id, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM conversations
                    WHERE status = 'active'
                    ORDER BY started_at DESC
                    LIMIT $1
                    """,
                    limit
                )
            return [dict(row) for row in rows]

    # =============================================================================
    # MESSAGES
    # =============================================================================

    @staticmethod
    async def add_message(
        conversation_id: str,
        channel: str,
        direction: str,
        role: str,
        content: str,
        channel_message_id: Optional[str] = None,
        tokens_used: Optional[int] = None,
        latency_ms: Optional[int] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Add a message to a conversation.

        Args:
            conversation_id: Conversation UUID
            channel: Message channel
            direction: 'inbound' or 'outbound'
            role: 'customer', 'agent', or 'system'
            content: Message content
            channel_message_id: External message ID (Gmail ID, Twilio SID)
            tokens_used: Tokens used for this message
            latency_ms: Response latency in milliseconds
            tool_calls: Tool calls made for this message

        Returns:
            Created message record
        """
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO messages (
                    conversation_id,
                    channel,
                    direction,
                    role,
                    content,
                    channel_message_id,
                    tokens_used,
                    latency_ms,
                    tool_calls,
                    delivery_status
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING *
                """,
                conversation_id,
                channel,
                direction,
                role,
                content,
                channel_message_id,
                tokens_used,
                latency_ms,
                tool_calls or [],
                "delivered" if direction == "outbound" else "received"
            )

            message = dict(row)
            logger.debug(f"Added message to conversation {conversation_id}: {message['id']}")
            return message

    @staticmethod
    async def get_messages(
        conversation_id: str,
        limit: int = 100,
        before: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get messages for a conversation."""
        async with get_connection() as conn:
            if before:
                rows = await conn.fetch(
                    """
                    SELECT * FROM messages
                    WHERE conversation_id = $1 AND created_at < $2
                    ORDER BY created_at DESC
                    LIMIT $3
                    """,
                    conversation_id, before, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM messages
                    WHERE conversation_id = $1
                    ORDER BY created_at ASC
                    LIMIT $2
                    """,
                    conversation_id, limit
                )
            return [dict(msg) for msg in rows]

    @staticmethod
    async def update_message_delivery(
        message_id: str,
        delivery_status: str
    ) -> Optional[Dict[str, Any]]:
        """Update message delivery status."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                UPDATE messages
                SET delivery_status = $2
                WHERE id = $1
                RETURNING *
                """,
                message_id, delivery_status
            )
            return dict(row) if row else None

    # =============================================================================
    # METRICS
    # =============================================================================

    @staticmethod
    async def get_conversation_count(
        status: Optional[str] = None,
        hours: int = 24
    ) -> int:
        """Get conversation count."""
        async with get_connection() as conn:
            if status:
                return await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM conversations
                    WHERE status = $1 AND started_at > NOW() - INTERVAL '1 hour' * $2
                    """,
                    status, hours
                )
            return await conn.fetchval(
                """
                SELECT COUNT(*) FROM conversations
                WHERE started_at > NOW() - INTERVAL '1 hour' * $1
                """,
                hours
            )

    @staticmethod
    async def get_average_messages_per_conversation(hours: int = 24) -> float:
        """Get average messages per conversation."""
        async with get_connection() as conn:
            result = await conn.fetchrow(
                """
                SELECT
                    COUNT(m.id) as total_messages,
                    COUNT(DISTINCT c.id) as total_conversations
                FROM conversations c
                LEFT JOIN messages m ON m.conversation_id = c.id
                WHERE c.started_at > NOW() - INTERVAL '1 hour' * $1
                """,
                hours
            )
            if result['total_conversations'] == 0:
                return 0.0
            return result['total_messages'] / result['total_conversations']
