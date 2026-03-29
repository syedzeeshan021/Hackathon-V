# Customer Success FTE - Agent Definition
# OpenAI Agents SDK Implementation

from agents import Agent, Runner
from typing import Dict, Any, Optional, List
import logging

from .tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response,
    analyze_sentiment,
)
from .prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT

# =============================================================================
# LOGGING SETUP
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# AGENT DEFINITION
# =============================================================================

customer_success_agent = Agent(
    name="Customer Success FTE",
    model="gpt-4o",
    instructions=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
    tools=[
        search_knowledge_base,
        create_ticket,
        get_customer_history,
        escalate_to_human,
        send_response,
        analyze_sentiment,
    ],
)

# =============================================================================
# RUNNER HELPER FUNCTIONS
# =============================================================================


async def run_agent(
    message: str,
    customer_id: str,
    channel: str,
    conversation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run the Customer Success agent with the given message.

    Args:
        message: Customer's message
        customer_id: Customer identifier (email or phone)
        channel: Source channel (email, whatsapp, web_form)
        conversation_id: Optional conversation ID for continuity
        metadata: Optional additional metadata

    Returns:
        Dictionary with agent response and metadata
    """
    logger.info(f"Running agent for customer {customer_id} on channel {channel}")

    # Build context for the agent
    context = {
        "customer_id": customer_id,
        "channel": channel,
        "conversation_id": conversation_id,
        "metadata": metadata or {},
    }

    # Build messages array
    messages = [
        {"role": "user", "content": message}
    ]

    try:
        # Run the agent
        result = await Runner.run(
            customer_success_agent,
            input=messages,
            context=context,
        )

        logger.info(f"Agent run complete. Output: {result.final_output[:100]}...")

        return {
            "success": True,
            "output": result.final_output,
            "customer_id": customer_id,
            "channel": channel,
            "conversation_id": conversation_id,
            "tool_calls": getattr(result, 'tool_calls', []),
            "raw_result": result,
        }

    except Exception as e:
        logger.error(f"Agent run failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "customer_id": customer_id,
            "channel": channel,
            "conversation_id": conversation_id,
        }


async def run_agent_with_history(
    message: str,
    customer_id: str,
    channel: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run the agent with conversation history.

    Args:
        message: Customer's message
        customer_id: Customer identifier
        channel: Source channel
        conversation_history: Optional list of prior messages
        metadata: Optional additional metadata

    Returns:
        Dictionary with agent response and metadata
    """
    logger.info(f"Running agent with history for customer {customer_id}")

    # Build messages array with history
    messages = []

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": message})

    # Build context
    context = {
        "customer_id": customer_id,
        "channel": channel,
        "metadata": metadata or {},
    }

    try:
        result = await Runner.run(
            customer_success_agent,
            input=messages,
            context=context,
        )

        logger.info(f"Agent run with history complete")

        return {
            "success": True,
            "output": result.final_output,
            "customer_id": customer_id,
            "channel": channel,
            "tool_calls": getattr(result, 'tool_calls', []),
            "messages_count": len(messages),
        }

    except Exception as e:
        logger.error(f"Agent run with history failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "customer_id": customer_id,
            "channel": channel,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


async def handle_customer_message(
    message: str,
    customer_email: Optional[str] = None,
    customer_phone: Optional[str] = None,
    channel: str = "web_form",
    subject: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle a customer message from any channel.

    Args:
        message: Customer's message
        customer_email: Customer's email (for email/web_form channels)
        customer_phone: Customer's phone (for WhatsApp channel)
        channel: Source channel (email, whatsapp, web_form)
        subject: Optional subject line (for email)

    Returns:
        Dictionary with agent response
    """
    # Determine customer ID
    customer_id = customer_email or customer_phone
    if not customer_id:
        return {
            "success": False,
            "error": "Customer identifier required (email or phone)"
        }

    # Build metadata
    metadata = {}
    if subject:
        metadata["subject"] = subject
    if customer_email:
        metadata["email"] = customer_email
    if customer_phone:
        metadata["phone"] = customer_phone

    return await run_agent(
        message=message,
        customer_id=customer_id,
        channel=channel,
        metadata=metadata,
    )
