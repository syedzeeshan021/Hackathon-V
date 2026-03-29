# Customer Success FTE Agent
# OpenAI Agents SDK Implementation

from .customer_success_agent import customer_success_agent
from .tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response,
    analyze_sentiment,
)
from .prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from .formatters import format_for_channel

__all__ = [
    "customer_success_agent",
    "search_knowledge_base",
    "create_ticket",
    "get_customer_history",
    "escalate_to_human",
    "send_response",
    "analyze_sentiment",
    "CUSTOMER_SUCCESS_SYSTEM_PROMPT",
    "format_for_channel",
]
