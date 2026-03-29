# Customer Success FTE - Database Repositories Package

from .database import (
    init_pool,
    close_pool,
    get_pool,
    get_connection,
    execute_query,
    execute_one,
    execute_many,
    init_database,
    health_check,
)

from .customers import CustomerRepository
from .tickets import TicketRepository
from .knowledge_base import KnowledgeBaseRepository
from .conversations import ConversationRepository
from .escalations import EscalationRepository

__all__ = [
    # Database connection
    "init_pool",
    "close_pool",
    "get_pool",
    "get_connection",
    "execute_query",
    "execute_one",
    "execute_many",
    "init_database",
    "health_check",
    # Repositories
    "CustomerRepository",
    "TicketRepository",
    "KnowledgeBaseRepository",
    "ConversationRepository",
    "EscalationRepository",
]
