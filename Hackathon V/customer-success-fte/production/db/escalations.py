# Customer Success FTE - Escalation Repository
# PostgreSQL operations for escalation management

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from .database import get_connection

logger = logging.getLogger(__name__)


class EscalationRepository:
    """Repository for escalation-related database operations."""

    # =============================================================================
    # CREATE / UPDATE
    # =============================================================================

    @staticmethod
    async def create_escalation(
        ticket_id: str,
        reason_code: str,
        urgency: str = "normal",
        assigned_to: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new escalation.

        Args:
            ticket_id: Ticket UUID to escalate
            reason_code: Reason code (pricing_inquiry, refund_request, etc.)
            urgency: Urgency level (normal, high, critical)
            assigned_to: Optional assignee email
            context: Additional context data

        Returns:
            Created escalation record as dict
        """
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO escalations (
                    ticket_id,
                    reason_code,
                    urgency,
                    assigned_to,
                    status,
                    context
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                ticket_id,
                reason_code,
                urgency,
                assigned_to,
                "pending",
                context or {}
            )

            escalation = dict(row)
            logger.info(f"Created escalation: {escalation['id']} for ticket {ticket_id}")
            return escalation

    @staticmethod
    async def update_escalation_status(
        escalation_id: str,
        status: str,
        assigned_to: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update escalation status.

        Args:
            escalation_id: Escalation UUID
            status: New status (pending, assigned, resolved)
            assigned_to: Optional assignee

        Returns:
            Updated escalation or None
        """
        async with get_connection() as conn:
            updates = ["status = $2"]
            values = [escalation_id, status]
            param_count = 3

            if assigned_to:
                updates.append(f"assigned_to = ${param_count}")
                values.append(assigned_to)
                param_count += 1

            if status == "resolved":
                updates.append(f"resolved_at = ${param_count}")
                values.append(datetime.now(timezone.utc))

            query = f"""
            UPDATE escalations
            SET {', '.join(updates)}
            WHERE id = $1
            RETURNING *
            """

            row = await conn.fetchrow(query, *values)
            return dict(row) if row else None

    @staticmethod
    async def assign_escalation(
        escalation_id: str,
        assigned_to: str
    ) -> Optional[Dict[str, Any]]:
        """Assign escalation to a person."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                UPDATE escalations
                SET assigned_to = $2, status = 'assigned'
                WHERE id = $1
                RETURNING *
                """,
                escalation_id, assigned_to
            )
            return dict(row) if row else None

    @staticmethod
    async def resolve_escalation(
        escalation_id: str,
        context_updates: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Resolve an escalation."""
        async with get_connection() as conn:
            if context_updates:
                # Get existing context and merge
                current = await conn.fetchrow(
                    "SELECT context FROM escalations WHERE id = $1",
                    escalation_id
                )
                existing_context = dict(current['context']) if current else {}
                merged_context = {**existing_context, **context_updates}

                row = await conn.fetchrow(
                    """
                    UPDATE escalations
                    SET status = 'resolved',
                        resolved_at = NOW(),
                        context = $3
                    WHERE id = $1
                    RETURNING *
                    """,
                    escalation_id, merged_context
                )
            else:
                row = await conn.fetchrow(
                    """
                    UPDATE escalations
                    SET status = 'resolved', resolved_at = NOW()
                    WHERE id = $1
                    RETURNING *
                    """,
                    escalation_id
                )
            return dict(row) if row else None

    # =============================================================================
    # GET
    # =============================================================================

    @staticmethod
    async def get_escalation_by_id(escalation_id: str) -> Optional[Dict[str, Any]]:
        """Get escalation by UUID."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT e.*, t.customer_id, t.source_channel
                FROM escalations e
                JOIN tickets t ON e.ticket_id = t.id
                WHERE e.id = $1
                """,
                escalation_id
            )
            return dict(row) if row else None

    @staticmethod
    async def get_escalations_by_ticket(
        ticket_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get all escalations for a ticket."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM escalations
                WHERE ticket_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                ticket_id, limit
            )
            return [dict(row) for row in rows]

    @staticmethod
    async def get_pending_escalations(
        urgency: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get pending escalations.

        Args:
            urgency: Optional urgency filter
            limit: Max results

        Returns:
            List of pending escalations
        """
        async with get_connection() as conn:
            if urgency:
                rows = await conn.fetch(
                    """
                    SELECT e.*, t.customer_id, t.source_channel
                    FROM escalations e
                    JOIN tickets t ON e.ticket_id = t.id
                    WHERE e.status = 'pending' AND e.urgency = $1
                    ORDER BY
                        CASE e.urgency
                            WHEN 'critical' THEN 1
                            WHEN 'high' THEN 2
                            ELSE 3
                        END,
                        e.created_at ASC
                    LIMIT $2
                    """,
                    urgency, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT e.*, t.customer_id, t.source_channel
                    FROM escalations e
                    JOIN tickets t ON e.ticket_id = t.id
                    WHERE e.status = 'pending'
                    ORDER BY
                        CASE e.urgency
                            WHEN 'critical' THEN 1
                            WHEN 'high' THEN 2
                            ELSE 3
                        END,
                        e.created_at ASC
                    LIMIT $1
                    """,
                    limit
                )
            return [dict(row) for row in rows]

    @staticmethod
    async def get_escalations_by_assignee(
        assigned_to: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get escalations assigned to a person."""
        async with get_connection() as conn:
            if status:
                rows = await conn.fetch(
                    """
                    SELECT * FROM escalations
                    WHERE assigned_to = $1 AND status = $2
                    ORDER BY created_at DESC
                    LIMIT $3
                    """,
                    assigned_to, status, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM escalations
                    WHERE assigned_to = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    assigned_to, limit
                )
            return [dict(row) for row in rows]

    # =============================================================================
    # LIST / SEARCH
    # =============================================================================

    @staticmethod
    async def list_escalations(
        status: Optional[str] = None,
        reason_code: Optional[str] = None,
        urgency: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List escalations with filters."""
        async with get_connection() as conn:
            conditions = []
            values = []
            param_count = 1

            if status:
                conditions.append(f"status = ${param_count}")
                values.append(status)
                param_count += 1

            if reason_code:
                conditions.append(f"reason_code = ${param_count}")
                values.append(reason_code)
                param_count += 1

            if urgency:
                conditions.append(f"urgency = ${param_count}")
                values.append(urgency)
                param_count += 1

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            query = f"""
            SELECT e.*, t.customer_id, t.source_channel
            FROM escalations e
            JOIN tickets t ON e.ticket_id = t.id
            {where_clause}
            ORDER BY e.created_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
            """

            values.extend([limit, offset])
            rows = await conn.fetch(query, *values)
            return [dict(row) for row in rows]

    # =============================================================================
    # METRICS
    # =============================================================================

    @staticmethod
    async def get_escalation_stats(
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get escalation statistics.

        Args:
            hours: Time window in hours

        Returns:
            Statistics dict
        """
        async with get_connection() as conn:
            # Count by status
            status_counts = await conn.fetch(
                """
                SELECT status, COUNT(*) as count
                FROM escalations
                WHERE created_at > NOW() - INTERVAL '1 hour' * $1
                GROUP BY status
                """,
                hours
            )

            # Count by reason
            reason_counts = await conn.fetch(
                """
                SELECT reason_code, COUNT(*) as count
                FROM escalations
                WHERE created_at > NOW() - INTERVAL '1 hour' * $1
                GROUP BY reason_code
                ORDER BY count DESC
                """,
                hours
            )

            # Count by urgency
            urgency_counts = await conn.fetch(
                """
                SELECT urgency, COUNT(*) as count
                FROM escalations
                WHERE created_at > NOW() - INTERVAL '1 hour' * $1
                GROUP BY urgency
                """,
                hours
            )

            # Average resolution time
            avg_resolution = await conn.fetchval(
                """
                SELECT AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)))
                FROM escalations
                WHERE status = 'resolved'
                AND resolved_at > NOW() - INTERVAL '1 hour' * $1
                """,
                hours
            )

            return {
                "by_status": {row["status"]: row["count"] for row in status_counts},
                "by_reason": {row["reason_code"]: row["count"] for row in reason_counts},
                "by_urgency": {row["urgency"]: row["count"] for row in urgency_counts},
                "avg_resolution_time_seconds": avg_resolution,
                "period_hours": hours
            }

    @staticmethod
    async def get_pending_count() -> int:
        """Get count of pending escalations."""
        async with get_connection() as conn:
            return await conn.fetchval(
                "SELECT COUNT(*) FROM escalations WHERE status = 'pending'"
            )
