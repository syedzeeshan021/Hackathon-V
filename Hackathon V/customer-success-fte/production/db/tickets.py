# Customer Success FTE - Ticket Repository
# PostgreSQL operations for ticket management

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum

from .database import get_connection

logger = logging.getLogger(__name__)


class TicketStatus(str, Enum):
    """Ticket status values."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Ticket priority values."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketRepository:
    """Repository for ticket-related database operations."""

    # =============================================================================
    # CREATE / UPDATE
    # =============================================================================

    @staticmethod
    async def create_ticket(
        customer_id: str,
        source_channel: str,
        issue: Optional[str] = None,
        category: Optional[str] = None,
        priority: str = "medium",
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new support ticket.

        Args:
            customer_id: Customer UUID
            source_channel: Channel where ticket originated
            issue: Issue description
            category: Issue category
            priority: Ticket priority
            conversation_id: Related conversation UUID

        Returns:
            Created ticket record as dict
        """
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO tickets (
                    customer_id,
                    source_channel,
                    category,
                    priority,
                    status,
                    conversation_id
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                customer_id,
                source_channel,
                category,
                priority,
                TicketStatus.OPEN.value,
                conversation_id
            )

            ticket = dict(row)
            logger.info(f"Created ticket: {ticket['id']} for customer {customer_id}")
            return ticket

    @staticmethod
    async def update_ticket_status(
        ticket_id: str,
        status: str,
        resolution_notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update ticket status.

        Args:
            ticket_id: Ticket UUID
            status: New status value
            resolution_notes: Optional resolution notes

        Returns:
            Updated ticket record or None
        """
        async with get_connection() as conn:
            updates = ["status = $2"]
            values = [ticket_id, status]
            param_count = 3

            if resolution_notes:
                updates.append(f"resolution_notes = ${param_count}")
                values.append(resolution_notes)
                param_count += 1

            if status == TicketStatus.RESOLVED.value:
                updates.append(f"resolved_at = ${param_count}")
                values.append(datetime.now(timezone.utc))

            query = f"""
            UPDATE tickets
            SET {', '.join(updates)}
            WHERE id = $1
            RETURNING *
            """

            row = await conn.fetchrow(query, *values)
            return dict(row) if row else None

    @staticmethod
    async def update_ticket_priority(
        ticket_id: str,
        priority: str
    ) -> Optional[Dict[str, Any]]:
        """Update ticket priority."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                UPDATE tickets
                SET priority = $2
                WHERE id = $1
                RETURNING *
                """,
                ticket_id, priority
            )
            return dict(row) if row else None

    # =============================================================================
    # GET
    # =============================================================================

    @staticmethod
    async def get_ticket_by_id(ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by UUID."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT t.*, c.email as customer_email, c.name as customer_name
                FROM tickets t
                LEFT JOIN customers c ON t.customer_id = c.id
                WHERE t.id = $1
                """,
                ticket_id
            )
            return dict(row) if row else None

    @staticmethod
    async def get_tickets_by_customer(
        customer_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get all tickets for a customer."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM tickets
                WHERE customer_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                customer_id, limit
            )
            return [dict(row) for row in rows]

    @staticmethod
    async def get_open_tickets(
        customer_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get open tickets, optionally filtered by customer."""
        async with get_connection() as conn:
            if customer_id:
                rows = await conn.fetch(
                    """
                    SELECT * FROM tickets
                    WHERE customer_id = $1 AND status = ANY($2)
                    ORDER BY created_at DESC
                    LIMIT $3
                    """,
                    customer_id,
                    [TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value],
                    limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM tickets
                    WHERE status = ANY($1)
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    [TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value],
                    limit
                )
            return [dict(row) for row in rows]

    # =============================================================================
    # LIST / SEARCH
    # =============================================================================

    @staticmethod
    async def list_tickets(
        status: Optional[str] = None,
        channel: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List tickets with filters.

        Args:
            status: Filter by status
            channel: Filter by source channel
            priority: Filter by priority
            limit: Max results
            offset: Pagination offset

        Returns:
            List of tickets
        """
        async with get_connection() as conn:
            # Build dynamic query
            conditions = []
            values = []
            param_count = 1

            if status:
                conditions.append(f"status = ${param_count}")
                values.append(status)
                param_count += 1

            if channel:
                conditions.append(f"source_channel = ${param_count}")
                values.append(channel)
                param_count += 1

            if priority:
                conditions.append(f"priority = ${param_count}")
                values.append(priority)
                param_count += 1

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            query = f"""
            SELECT * FROM tickets
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
            """

            values.extend([limit, offset])
            rows = await conn.fetch(query, *values)
            return [dict(row) for row in rows]

    @staticmethod
    async def get_ticket_count(
        status: Optional[str] = None,
        channel: Optional[str] = None
    ) -> int:
        """Get ticket count with optional filters."""
        async with get_connection() as conn:
            conditions = []
            values = []
            param_count = 1

            if status:
                conditions.append(f"status = ${param_count}")
                values.append(status)
                param_count += 1

            if channel:
                conditions.append(f"source_channel = ${param_count}")
                values.append(channel)

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            query = f"""
            SELECT COUNT(*) FROM tickets
            {where_clause}
            """

            return await conn.fetchval(query, *values)

    # =============================================================================
    # METRICS
    # =============================================================================

    @staticmethod
    async def get_resolution_stats(
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get ticket resolution statistics for the last N hours.

        Args:
            hours: Time window in hours

        Returns:
            Statistics dict
        """
        async with get_connection() as conn:
            # Get counts by status
            status_counts = await conn.fetch(
                """
                SELECT status, COUNT(*) as count
                FROM tickets
                WHERE created_at > NOW() - INTERVAL '1 hour' * $1
                GROUP BY status
                """,
                hours
            )

            # Get average resolution time (for resolved tickets)
            avg_resolution = await conn.fetchval(
                """
                SELECT AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)))
                FROM tickets
                WHERE status = 'resolved'
                AND resolved_at > NOW() - INTERVAL '1 hour' * $1
                """,
                hours
            )

            return {
                "by_status": {row["status"]: row["count"] for row in status_counts},
                "avg_resolution_time_seconds": avg_resolution,
                "period_hours": hours
            }
