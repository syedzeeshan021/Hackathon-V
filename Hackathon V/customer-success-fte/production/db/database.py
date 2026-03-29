# Customer Success FTE - Database Connection Pool
# PostgreSQL + pgvector connection management

import asyncio
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Pool, Connection
import os

from ..core.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[Pool] = None


async def init_pool() -> Pool:
    """
    Initialize the database connection pool.

    This should be called once at application startup.
    """
    global _pool

    if _pool is not None:
        logger.warning("Connection pool already initialized")
        return _pool

    try:
        logger.info(f"Initializing database connection pool to {settings.db_host}:{settings.db_port}")

        _pool = await asyncpg.create_pool(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            min_size=settings.db_min_connections,
            max_size=settings.db_max_connections,
            command_timeout=settings.db_command_timeout,
            max_inactive_connection_lifetime=settings.db_max_inactive_lifetime,
        )

        # Verify connection
        async with _pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        logger.info(f"Database connection pool initialized successfully (min={settings.db_min_connections}, max={settings.db_max_connections})")
        return _pool

    except Exception as e:
        logger.error(f"Failed to initialize database connection pool: {e}")
        raise


async def close_pool() -> None:
    """
    Close the database connection pool.

    This should be called at application shutdown.
    """
    global _pool

    if _pool is not None:
        logger.info("Closing database connection pool")
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")


def get_pool() -> Optional[Pool]:
    """Get the current connection pool."""
    return _pool


@asynccontextmanager
async def get_connection() -> AsyncGenerator[Connection, None]:
    """
    Acquire a connection from the pool.

    Usage:
        async with get_connection() as conn:
            await conn.fetchval("SELECT 1")
    """
    if _pool is None:
        raise RuntimeError("Connection pool not initialized. Call init_pool() first.")

    async with _pool.acquire() as conn:
        yield conn


async def execute_query(query: str, *args) -> list:
    """
    Execute a query and return results.

    Args:
        query: SQL query with $1, $2, etc. placeholders
        *args: Query parameters

    Returns:
        List of result rows
    """
    async with get_connection() as conn:
        try:
            results = await conn.fetch(query, *args)
            logger.debug(f"Query executed successfully, returned {len(results)} rows")
            return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise


async def execute_one(query: str, *args) -> Optional[dict]:
    """
    Execute a query and return a single row as a dict.

    Args:
        query: SQL query with $1, $2, etc. placeholders
        *args: Query parameters

    Returns:
        Single row as dict or None if not found
    """
    async with get_connection() as conn:
        try:
            row = await conn.fetchrow(query, *args)
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise


async def execute_many(query: str, records: list) -> int:
    """
    Execute a query with multiple record sets.

    Args:
        query: SQL query with $1, $2, etc. placeholders
        records: List of parameter tuples

    Returns:
        Number of rows affected
    """
    async with get_connection() as conn:
        try:
            result = await conn.executemany(query, records)
            return len(records)
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

async def init_database() -> None:
    """
    Initialize database schema and extensions.

    This runs the schema.sql file to ensure all tables exist.
    """
    if _pool is None:
        raise RuntimeError("Connection pool not initialized")

    logger.info("Initializing database schema...")

    # Read schema file
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "database",
        "schema.sql"
    )

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    # Execute schema (pgvector extension should already be created by init script)
    async with get_connection() as conn:
        # We need to execute each statement separately due to asyncpg limitations
        statements = [s.strip() for s in schema_sql.split(";") if s.strip()]

        for statement in statements:
            if statement and not statement.startswith("--"):
                try:
                    # Skip CREATE EXTENSION if it already exists
                    if "CREATE EXTENSION" in statement:
                        try:
                            await conn.execute(statement)
                        except asyncpg.exceptions.DuplicateObjectError:
                            logger.debug("Extension already exists, skipping")
                    else:
                        await conn.execute(statement)
                except Exception as e:
                    # Log but continue - some statements may fail due to IF NOT EXISTS
                    logger.debug(f"Schema statement (continuing): {e}")

    logger.info("Database schema initialized successfully")


# =============================================================================
# HEALTH CHECK
# =============================================================================

async def health_check() -> dict:
    """
    Check database health.

    Returns:
        Health status dict
    """
    try:
        if _pool is None:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": "Connection pool not initialized"
            }

        async with get_connection() as conn:
            # Check pgvector extension
            has_vector = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )

            # Get connection pool stats
            stats = {
                "size": _pool.get_size(),
                "free": _pool.get_idle_size(),
            }

            return {
                "status": "healthy",
                "database": "connected",
                "pgvector_enabled": has_vector,
                "pool_stats": stats
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e)
        }
