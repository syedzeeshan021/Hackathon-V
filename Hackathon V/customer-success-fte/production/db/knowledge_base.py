# Customer Success FTE - Knowledge Base Repository
# PostgreSQL operations for knowledge base with pgvector semantic search

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from .database import get_connection

logger = logging.getLogger(__name__)


class KnowledgeBaseRepository:
    """Repository for knowledge base operations with vector search."""

    # =============================================================================
    # CREATE / UPDATE
    # =============================================================================

    @staticmethod
    async def create_entry(
        title: str,
        content: str,
        category: Optional[str] = None,
        embedding: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Create a new knowledge base entry.

        Args:
            title: Entry title
            content: Entry content
            category: Optional category
            embedding: Optional vector embedding (1536 dimensions)

        Returns:
            Created entry as dict
        """
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO knowledge_base (title, content, category, embedding)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                title, content, category, embedding
            )

            entry = dict(row)
            logger.info(f"Created knowledge base entry: {entry['id']} - {entry['title']}")
            return entry

    @staticmethod
    async def update_entry(
        entry_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        embedding: Optional[List[float]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a knowledge base entry.

        Args:
            entry_id: Entry UUID
            title: New title (optional)
            content: New content (optional)
            category: New category (optional)
            embedding: New embedding (optional)

        Returns:
            Updated entry or None
        """
        async with get_connection() as conn:
            # Build dynamic update
            updates = []
            values = [entry_id]
            param_count = 2

            if title:
                updates.append(f"title = ${param_count}")
                values.append(title)
                param_count += 1

            if content:
                updates.append(f"content = ${param_count}")
                values.append(content)
                param_count += 1

            if category:
                updates.append(f"category = ${param_count}")
                values.append(category)
                param_count += 1

            if embedding:
                updates.append(f"embedding = ${param_count}::vector")
                values.append(str(embedding))
                param_count += 1

            if not updates:
                return await KnowledgeBaseRepository.get_entry_by_id(entry_id)

            query = f"""
            UPDATE knowledge_base
            SET {', '.join(updates)}
            WHERE id = $1
            RETURNING *
            """

            row = await conn.fetchrow(query, *values)
            return dict(row) if row else None

    @staticmethod
    async def delete_entry(entry_id: str) -> bool:
        """Delete a knowledge base entry."""
        async with get_connection() as conn:
            result = await conn.execute(
                "DELETE FROM knowledge_base WHERE id = $1",
                entry_id
            )
            return result == "DELETE 1"

    # =============================================================================
    # GET
    # =============================================================================

    @staticmethod
    async def get_entry_by_id(entry_id: str) -> Optional[Dict[str, Any]]:
        """Get entry by UUID."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM knowledge_base WHERE id = $1",
                entry_id
            )
            return dict(row) if row else None

    @staticmethod
    async def get_entries_by_category(
        category: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get all entries in a category."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM knowledge_base
                WHERE category = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                category, limit
            )
            return [dict(row) for row in rows]

    # =============================================================================
    # SEMANTIC SEARCH (Vector Similarity)
    # =============================================================================

    @staticmethod
    async def search_by_embedding(
        query_embedding: List[float],
        limit: int = 5,
        category: Optional[str] = None,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base by vector similarity.

        Args:
            query_embedding: Query vector (1536 dimensions)
            limit: Max results to return
            category: Optional category filter
            threshold: Minimum similarity threshold (0-1)

        Returns:
            List of matching entries with similarity scores
        """
        async with get_connection() as conn:
            if category:
                rows = await conn.fetch(
                    """
                    SELECT *,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM knowledge_base
                    WHERE category = $2
                      AND 1 - (embedding <=> $1::vector) > $3
                    ORDER BY similarity DESC
                    LIMIT $4
                    """,
                    str(query_embedding), category, threshold, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT *,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM knowledge_base
                    WHERE 1 - (embedding <=> $1::vector) > $2
                    ORDER BY similarity DESC
                    LIMIT $3
                    """,
                    str(query_embedding), threshold, limit
                )

            results = []
            for row in rows:
                entry = dict(row)
                entry['similarity'] = float(entry['similarity']) if entry['similarity'] else 0.0
                results.append(entry)

            logger.debug(f"Vector search returned {len(results)} results")
            return results

    @staticmethod
    async def search_hybrid(
        query_text: str,
        query_embedding: Optional[List[float]] = None,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search: combines keyword matching with vector similarity.

        Args:
            query_text: Text query for keyword search
            query_embedding: Optional vector for semantic search
            limit: Max results
            category: Optional category filter

        Returns:
            Ranked results combining both search methods
        """
        async with get_connection() as conn:
            results = {}

            # Keyword search (title and content)
            keyword_query = """
            SELECT id, title, content, category, created_at,
                   2 as keyword_score
            FROM knowledge_base
            WHERE title ILIKE $1 OR content ILIKE $1
            """

            if category:
                keyword_query += " AND category = $2"

            keyword_params = [f"%{query_text}%"]
            if category:
                keyword_params.append(category)

            keyword_rows = await conn.fetch(keyword_query, *keyword_params)

            for row in keyword_rows:
                entry = dict(row)
                results[entry['id']] = {
                    **entry,
                    'keyword_score': 2.0,
                    'similarity': 0.0
                }

            # Vector search (if embedding provided)
            if query_embedding:
                vector_results = await KnowledgeBaseRepository.search_by_embedding(
                    query_embedding,
                    limit=limit * 2,
                    category=category
                )

                for entry in vector_results:
                    entry_id = entry['id']
                    if entry_id in results:
                        # Boost existing result
                        results[entry_id]['similarity'] = entry['similarity']
                        results[entry_id]['combined_score'] = (
                            results[entry_id]['keyword_score'] * 2 +
                            entry['similarity']
                        )
                    else:
                        entry['keyword_score'] = 0.0
                        entry['combined_score'] = entry['similarity']
                        results[entry_id] = entry

            # Sort by combined score and return top results
            sorted_results = sorted(
                results.values(),
                key=lambda x: x.get('combined_score', 0),
                reverse=True
            )[:limit]

            logger.debug(f"Hybrid search returned {len(sorted_results)} results")
            return sorted_results

    # =============================================================================
    # LIST
    # =============================================================================

    @staticmethod
    async def list_entries(
        limit: int = 50,
        offset: int = 0,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all entries with pagination."""
        async with get_connection() as conn:
            if category:
                rows = await conn.fetch(
                    """
                    SELECT * FROM knowledge_base
                    WHERE category = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    category, limit, offset
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM knowledge_base
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                    """,
                    limit, offset
                )
            return [dict(row) for row in rows]

    @staticmethod
    async def get_entry_count(category: Optional[str] = None) -> int:
        """Get total entry count."""
        async with get_connection() as conn:
            if category:
                return await conn.fetchval(
                    "SELECT COUNT(*) FROM knowledge_base WHERE category = $1",
                    category
                )
            return await conn.fetchval("SELECT COUNT(*) FROM knowledge_base")

    @staticmethod
    async def get_categories() -> List[str]:
        """Get all unique categories."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                "SELECT DISTINCT category FROM knowledge_base WHERE category IS NOT NULL"
            )
            return [row['category'] for row in rows]

    # =============================================================================
    # BULK OPERATIONS
    # =============================================================================

    @staticmethod
    async def bulk_create(
        entries: List[Dict[str, Any]]
    ) -> int:
        """
        Bulk create knowledge base entries.

        Args:
            entries: List of dicts with keys: title, content, category, embedding

        Returns:
            Number of entries created
        """
        async with get_connection() as conn:
            count = 0
            for entry in entries:
                try:
                    await conn.execute(
                        """
                        INSERT INTO knowledge_base (title, content, category, embedding)
                        VALUES ($1, $2, $3, $4)
                        """,
                        entry['title'],
                        entry['content'],
                        entry.get('category'),
                        entry.get('embedding')
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to create entry '{entry.get('title')}': {e}")

            logger.info(f"Bulk created {count}/{len(entries)} entries")
            return count
