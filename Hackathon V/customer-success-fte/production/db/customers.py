# Customer Success FTE - Customer Repository
# PostgreSQL operations for customer management

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncpg

from .database import get_connection

logger = logging.getLogger(__name__)


class CustomerRepository:
    """Repository for customer-related database operations."""

    # =============================================================================
    # CREATE / UPDATE
    # =============================================================================

    @staticmethod
    async def create_or_get_customer(
        email: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new customer or return existing one based on email/phone.

        Args:
            email: Customer email address
            phone: Customer phone number
            name: Customer name
            metadata: Additional metadata

        Returns:
            Customer record as dict
        """
        async with get_connection() as conn:
            # Try to find existing customer by email or phone
            if email:
                existing = await conn.fetchrow(
                    "SELECT * FROM customers WHERE email = $1",
                    email
                )
                if existing:
                    logger.debug(f"Found existing customer by email: {email}")
                    return dict(existing)

            if phone:
                existing = await conn.fetchrow(
                    "SELECT * FROM customers WHERE phone = $1",
                    phone
                )
                if existing:
                    logger.debug(f"Found existing customer by phone: {phone}")
                    return dict(existing)

            # Create new customer
            async with conn.transaction():
                customer_id = await conn.fetchval(
                    """
                    INSERT INTO customers (email, phone, name, metadata)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                    """,
                    email, phone, name, metadata or {}
                )

                # Add identifier
                if email:
                    await conn.execute(
                        """
                        INSERT INTO customer_identifiers (customer_id, identifier_type, identifier_value)
                        VALUES ($1, 'email', $2)
                        ON CONFLICT (identifier_type, identifier_value) DO NOTHING
                        """,
                        customer_id, email
                    )

                if phone:
                    await conn.execute(
                        """
                        INSERT INTO customer_identifiers (customer_id, identifier_type, identifier_value)
                        VALUES ($1, 'phone', $2)
                        ON CONFLICT (identifier_type, identifier_value) DO NOTHING
                        """,
                        customer_id, phone
                    )

                logger.info(f"Created new customer: {customer_id}")

                return await conn.fetchrow(
                    "SELECT * FROM customers WHERE id = $1",
                    customer_id
                )

    @staticmethod
    async def get_customer_by_id(customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by UUID."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM customers WHERE id = $1",
                customer_id
            )
            return dict(row) if row else None

    @staticmethod
    async def get_customer_by_identifier(
        identifier_type: str,
        identifier_value: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get customer by identifier (email, phone, whatsapp).

        Args:
            identifier_type: Type of identifier ('email', 'phone', 'whatsapp')
            identifier_value: The identifier value

        Returns:
            Customer record or None
        """
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT c.* FROM customers c
                JOIN customer_identifiers ci ON c.id = ci.customer_id
                WHERE ci.identifier_type = $1 AND ci.identifier_value = $2
                """,
                identifier_type, identifier_value
            )
            return dict(row) if row else None

    @staticmethod
    async def update_customer(
        customer_id: str,
        **updates: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Update customer fields.

        Args:
            customer_id: Customer UUID
            **updates: Fields to update (name, metadata, etc.)

        Returns:
            Updated customer record or None
        """
        if not updates:
            return await CustomerRepository.get_customer_by_id(customer_id)

        async with get_connection() as conn:
            # Build dynamic update query
            set_clauses = []
            values = [customer_id]

            for i, (key, value) in enumerate(updates.items(), start=1):
                set_clauses.append(f"{key} = ${i + 1}")
                values.append(value)

            query = f"""
            UPDATE customers
            SET {', '.join(set_clauses)}
            WHERE id = $1
            RETURNING *
            """

            row = await conn.fetchrow(query, *values)
            return dict(row) if row else None

    # =============================================================================
    # LIST / SEARCH
    # =============================================================================

    @staticmethod
    async def list_customers(
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at"
    ) -> List[Dict[str, Any]]:
        """List customers with pagination."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                f"""
                SELECT * FROM customers
                ORDER BY {order_by} DESC
                LIMIT $1 OFFSET $2
                """,
                limit, offset
            )
            return [dict(row) for row in rows]

    @staticmethod
    async def search_customers(query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search customers by name or email.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of matching customers
        """
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM customers
                WHERE name ILIKE $1 OR email ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                f"%{query}%", limit
            )
            return [dict(row) for row in rows]

    @staticmethod
    async def get_customer_count() -> int:
        """Get total customer count."""
        async with get_connection() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM customers")

    # =============================================================================
    # DELETE
    # =============================================================================

    @staticmethod
    async def delete_customer(customer_id: str) -> bool:
        """
        Delete a customer (cascades to related records).

        Args:
            customer_id: Customer UUID

        Returns:
            True if deleted, False if not found
        """
        async with get_connection() as conn:
            result = await conn.execute(
                "DELETE FROM customers WHERE id = $1",
                customer_id
            )
            deleted = result == "DELETE 1"
            if deleted:
                logger.info(f"Deleted customer: {customer_id}")
            return deleted
