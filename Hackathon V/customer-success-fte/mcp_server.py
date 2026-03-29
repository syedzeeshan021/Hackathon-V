#!/usr/bin/env python3
"""
Customer Success FTE - MCP Server Prototype
============================================
This is the Incubation phase prototype. It demonstrates the core tools
that will later be migrated to OpenAI Agents SDK @function_tool decorators.

Tools implemented:
1. search_knowledge_base - Find relevant product documentation
2. create_ticket - Log customer interactions
3. get_customer_history - Get cross-channel conversation history
4. escalate_to_human - Hand off to human support
5. send_response - Send reply via appropriate channel
6. analyze_sentiment - Analyze customer sentiment

Run with: python mcp_server.py
"""

from mcp.server import Server
from mcp.types import Tool, TextContent
from enum import Enum
from typing import Optional
from datetime import datetime
import json
import asyncio

# =============================================================================
# CONFIGURATION
# =============================================================================

# In-memory storage for prototype (will be PostgreSQL in production)
tickets_db = []
conversations_db = []
customers_db = []
knowledge_base = []
escalations_db = []

# Sample knowledge base entries (will be populated from product docs)
KNOWLEDGE_BASE_ENTRIES = [
    {
        "id": "kb-001",
        "title": "How to Reset Your Password",
        "content": """To reset your password (password reset):
1. Go to https://dashboard.techcorp.com/reset
2. Enter your email address
3. Check your email for a reset link
4. Click the link and set a new password
5. Log in with your new password

If you need a password reset link, follow the steps above.""",
        "category": "authentication"
    },
    {
        "id": "kb-002",
        "title": "Finding Your API Keys",
        "content": """To find your API keys:
1. Log in to your dashboard at https://dashboard.techcorp.com
2. Navigate to Settings → API Keys in the left sidebar
3. Click 'Generate New Key' if you don't have one
4. Copy and securely store your API key (it won't be shown again)

Never share your API key or commit it to version control.""",
        "category": "authentication"
    },
    {
        "id": "kb-003",
        "title": "Understanding Rate Limits",
        "content": """Rate limits by plan:
- Starter: 100 requests/minute, 100,000 requests/day
- Professional: 500 requests/minute, 1,000,000 requests/day
- Enterprise: Custom limits

When you exceed the rate limit, you'll receive a 429 status code.
Implement exponential backoff to handle rate limits gracefully.""",
        "category": "api_reference"
    },
    {
        "id": "kb-004",
        "title": "Setting Up Webhooks",
        "content": """To set up webhooks:
1. Go to Dashboard → Settings → Webhooks
2. Click 'Add Endpoint'
3. Enter your webhook URL (must be HTTPS)
4. Select events to subscribe to
5. Click 'Save'

Webhook payloads are signed with X-TechCorp-Signature header.
Verify signatures to ensure webhook authenticity.""",
        "category": "webhooks"
    },
    {
        "id": "kb-005",
        "title": "OAuth2 Authentication Flow",
        "content": """OAuth2 flow for third-party integrations:
1. Register your application in Dashboard → Settings → OAuth Apps
2. Redirect users to: /oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&response_type=code
3. Exchange the authorization code for an access token at /oauth/token
4. Use the access token to make requests on behalf of the user

Common error: 'invalid_redirect_uri' - ensure your redirect URI exactly matches what's registered.""",
        "category": "authentication"
    },
    {
        "id": "kb-006",
        "title": "Troubleshooting 401 Unauthorized",
        "content": """401 Unauthorized errors occur when:
- API key is missing from the request
- API key is expired or revoked
- Using wrong key type (publishable vs secret)

Solutions:
1. Verify the Authorization header: 'Authorization: Bearer YOUR_API_KEY'
2. Check that your API key is active in the dashboard
3. Ensure you're using a secret key (sk_...) for server-side requests""",
        "category": "troubleshooting"
    },
    {
        "id": "kb-007",
        "title": "API Status and Health",
        "content": """Check API status:
- GET /status endpoint returns current operational status
- Status page: https://status.techcorp.com
- For outages, check the status page or subscribe to notifications

Current status endpoint response:
{
  "status": "operational",
  "version": "1.0.0",
  "timestamp": "2026-03-17T10:30:00Z
}""",
        "category": "api_reference"
    }
]

# =============================================================================
# ENUMS AND TYPES
# =============================================================================

class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# =============================================================================
# MCP SERVER SETUP
# =============================================================================

server = Server("customer-success-fte")

# =============================================================================
# TOOL IMPLEMENTATIONS (as async functions)
# =============================================================================

async def search_knowledge_base_fn(query: str, max_results: int = 5, category: Optional[str] = None) -> str:
    """
    Search product documentation for relevant information.

    Use this when the customer asks questions about product features,
    how to use something, or needs technical information.

    Args:
        query: The search query from the customer
        max_results: Maximum number of results to return (default: 5)
        category: Optional category filter (authentication, api_reference, webhooks, troubleshooting)

    Returns:
        Formatted search results with relevance indicators
    """
    query_lower = query.lower()
    results = []

    for entry in knowledge_base:
        # Simple keyword matching (will be replaced with vector search in production)
        title_match = entry["title"].lower().find(query_lower) >= 0
        content_match = entry["content"].lower().find(query_lower) >= 0
        category_match = category is None or entry["category"] == category

        if title_match or (content_match and category_match):
            relevance = 2 if title_match else 1
            if category_match:
                relevance += 1
            results.append({
                "title": entry["title"],
                "content": entry["content"],
                "category": entry["category"],
                "relevance": relevance
            })

    # Sort by relevance
    results.sort(key=lambda x: x["relevance"], reverse=True)
    results = results[:max_results]

    if not results:
        return "No relevant documentation found. Consider escalating to human support if the question is complex."

    # Format results
    formatted = []
    for r in results:
        formatted.append(f"**{r['title']}** (Category: {r['category']}, Relevance: {'High' if r['relevance'] >= 2 else 'Medium'})\n{r['content']}")

    return "\n\n---\n\n".join(formatted)


async def create_ticket_fn(
    customer_id: str,
    issue: str,
    priority: str = "medium",
    category: Optional[str] = None,
    channel: str = "web_form"
) -> str:
    """
    Create a support ticket for tracking customer interactions.

    ALWAYS create a ticket at the start of every conversation.
    Include the source channel for proper tracking.

    Args:
        customer_id: Unique customer identifier (email or phone)
        issue: Description of the customer's issue
        priority: Ticket priority (low, medium, high, critical)
        category: Issue category (general, technical, billing, feedback, bug_report)
        channel: Source channel (email, whatsapp, web_form)

    Returns:
        Ticket ID for future reference
    """
    ticket_id = f"tkt-{len(tickets_db) + 1:04d}"

    ticket = {
        "id": ticket_id,
        "customer_id": customer_id,
        "issue": issue,
        "priority": priority,
        "category": category,
        "source_channel": channel,
        "status": "open",
        "created_at": datetime.utcnow().isoformat(),
        "resolved_at": None,
        "resolution_notes": None,
        "messages": []
    }

    tickets_db.append(ticket)

    return f"Ticket created: {ticket_id}. Status: open. Priority: {priority}."


async def get_customer_history_fn(customer_id: str, limit: int = 20) -> str:
    """
    Get customer's complete interaction history across ALL channels.

    Use this to understand context from previous conversations,
    even if they happened on a different channel.

    Args:
        customer_id: Unique customer identifier (email or phone)
        limit: Maximum number of conversations to return (default: 20)

    Returns:
        Formatted conversation history with channel information
    """
    # Find customer's tickets
    customer_tickets = [t for t in tickets_db if t["customer_id"] == customer_id]

    if not customer_tickets:
        return f"No prior conversation history found for customer {customer_id}. This appears to be a new customer."

    # Format history
    history = []
    for ticket in customer_tickets[-limit:]:
        history.append(f"""
---
**Ticket:** {ticket['id']}
**Channel:** {ticket['source_channel']}
**Status:** {ticket['status']}
**Created:** {ticket['created_at']}
**Issue:** {ticket['issue']}
""")
        # Add messages
        for msg in ticket.get("messages", [])[-5:]:
            history.append(f"  [{msg['role']}] ({msg['channel']}): {msg['content'][:100]}...")

    return f"Found {len(customer_tickets)} prior conversation(s) for customer {customer_id}:\n\n" + "\n".join(history)


async def escalate_to_human_fn(
    ticket_id: str,
    reason: str,
    urgency: str = "normal",
    context: Optional[dict] = None
) -> str:
    """
    Escalate a ticket to human support.

    Use this when:
    - Customer asks about pricing or refunds
    - Customer sentiment is negative or angry
    - You cannot find relevant information after 2 search attempts
    - Customer explicitly requests human help
    - Legal or compliance questions

    Args:
        ticket_id: The ticket ID to escalate
        reason: Reason code for escalation (pricing_inquiry, refund_request, legal_inquiry, negative_sentiment, human_request, unknown_topic)
        urgency: Escalation urgency (normal, high, critical)
        context: Additional context about the conversation

    Returns:
        Escalation confirmation with reference number
    """
    # Find the ticket
    ticket = None
    for t in tickets_db:
        if t["id"] == ticket_id:
            ticket = t
            break

    if not ticket:
        return f"Error: Ticket {ticket_id} not found."

    # Update ticket status
    ticket["status"] = "escalated"
    ticket["resolution_notes"] = f"Escalated: {reason}. Urgency: {urgency}."

    # Create escalation record
    escalation_id = f"esc-{len(escalations_db) + 1:04d}"
    escalation = {
        "id": escalation_id,
        "ticket_id": ticket_id,
        "reason": reason,
        "urgency": urgency,
        "context": context or {},
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    escalations_db.append(escalation)

    # Determine response based on reason
    response_templates = {
        "pricing_inquiry": "I'm connecting you with our sales team who can provide detailed pricing information.",
        "refund_request": "I'm escalating this to our billing team who can assist with refund requests.",
        "legal_inquiry": "I'm escalating this to our legal team for proper handling.",
        "negative_sentiment": "I understand this is frustrating. I'm having a specialist follow up personally.",
        "human_request": "I'm connecting you with a human agent who can provide personalized assistance.",
        "unknown_topic": "Let me get a specialist involved who can better assist with this question."
    }

    response = response_templates.get(reason, "I'm escalating this to a human specialist.")

    return f"Escalated to human support. Reference: {escalation_id}. Urgency: {urgency}. {response}"


async def send_response_fn(
    ticket_id: str,
    message: str,
    channel: str = "web_form"
) -> str:
    """
    Send response to customer via their preferred channel.

    The response will be automatically formatted for the channel:
    - Email: Formal with greeting and signature
    - WhatsApp: Concise and conversational
    - Web Form: Semi-formal

    Args:
        ticket_id: The ticket ID to respond to
        message: The response message content
        channel: The channel to send via (email, whatsapp, web_form)

    Returns:
        Delivery status confirmation
    """
    # Find the ticket
    ticket = None
    for t in tickets_db:
        if t["id"] == ticket_id:
            ticket = t
            break

    if not ticket:
        return f"Error: Ticket {ticket_id} not found."

    # Format response for channel
    formatted_message = format_for_channel(message, channel, ticket_id)

    # Store the response in ticket
    ticket["messages"].append({
        "role": "agent",
        "channel": channel,
        "content": formatted_message,
        "sent_at": datetime.utcnow().isoformat()
    })

    # Simulate sending (in production, this would call Gmail/Twilio APIs)
    delivery_status = "sent"  # Simulated

    return f"Response sent via {channel}. Status: {delivery_status}. Message length: {len(formatted_message)} chars."


def format_for_channel(message: str, channel: str, ticket_id: str) -> str:
    """Format response appropriately for the channel."""

    if channel == "email":
        return f"""Dear Customer,

Thank you for reaching out to TechCorp Support.

{message}

If you have any further questions, please don't hesitate to reply to this email.

Best regards,
TechCorp AI Support Team
---
Ticket Reference: {ticket_id}
This response was generated by our AI assistant. For complex issues, you can request human support."""

    elif channel == "whatsapp":
        # Keep it short for WhatsApp
        if len(message) > 300:
            message = message[:297] + "..."
        return f"{message}\n\n📱 Reply for more help or type 'human' for live support."

    else:  # web_form
        return f"""{message}

---
Need more help? Reply to this message or visit our support portal.
Ticket: {ticket_id}"""


async def analyze_sentiment_fn(text: str) -> str:
    """
    Analyze the sentiment of customer message.

    Use this to detect frustrated or angry customers who may need
    special handling or escalation.

    Args:
        text: The customer's message text

    Returns:
        Sentiment analysis result with score and recommendation
    """
    # Simple keyword-based sentiment analysis (will be improved in production)
    negative_keywords = [
        "ridiculous", "terrible", "awful", "hate", "angry", "frustrated",
        "useless", "broken", "worst", "disappointed", "waste", "sue", "lawyer"
    ]
    positive_keywords = [
        "great", "awesome", "thanks", "thank", "love", "helpful", "excellent",
        "perfect", "amazing", "wonderful", "appreciate"
    ]

    text_lower = text.lower()

    negative_count = sum(1 for word in negative_keywords if word in text_lower)
    positive_count = sum(1 for word in positive_keywords if word in text_lower)

    # Calculate sentiment score (-1 to 1)
    total = negative_count + positive_count
    if total == 0:
        score = 0.5  # Neutral
    else:
        score = 0.5 + (positive_count - negative_count) / (total * 2)

    # Determine sentiment label
    if score < 0.3:
        label = "negative"
        recommendation = "Consider escalating to human agent. Customer appears frustrated."
    elif score < 0.5:
        label = "somewhat negative"
        recommendation = "Show empathy and prioritize resolution."
    elif score < 0.7:
        label = "neutral"
        recommendation = "Standard handling."
    else:
        label = "positive"
        recommendation = "Customer is satisfied. Ensure issue is fully resolved."

    return json.dumps({
        "score": round(score, 2),
        "label": label,
        "negative_indicators": negative_count,
        "positive_indicators": positive_count,
        "recommendation": recommendation
    }, indent=2)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def initialize_knowledge_base():
    """Initialize the knowledge base with product documentation."""
    global knowledge_base
    knowledge_base = KNOWLEDGE_BASE_ENTRIES.copy()
    print(f"Loaded {len(knowledge_base)} knowledge base entries.")


# =============================================================================
# SERVER TOOL REGISTRATION
# =============================================================================

@server.call_tool()
async def handle_tool_call(name: str, arguments: dict) -> list:
    """Handle tool calls from MCP clients."""

    if name == "search_knowledge_base":
        result = await search_knowledge_base_fn(
            query=arguments.get("query", ""),
            max_results=arguments.get("max_results", 5),
            category=arguments.get("category")
        )
    elif name == "create_ticket":
        result = await create_ticket_fn(
            customer_id=arguments.get("customer_id", ""),
            issue=arguments.get("issue", ""),
            priority=arguments.get("priority", "medium"),
            category=arguments.get("category"),
            channel=arguments.get("channel", "web_form")
        )
    elif name == "get_customer_history":
        result = await get_customer_history_fn(
            customer_id=arguments.get("customer_id", ""),
            limit=arguments.get("limit", 20)
        )
    elif name == "escalate_to_human":
        result = await escalate_to_human_fn(
            ticket_id=arguments.get("ticket_id", ""),
            reason=arguments.get("reason", ""),
            urgency=arguments.get("urgency", "normal"),
            context=arguments.get("context")
        )
    elif name == "send_response":
        result = await send_response_fn(
            ticket_id=arguments.get("ticket_id", ""),
            message=arguments.get("message", ""),
            channel=arguments.get("channel", "web_form")
        )
    elif name == "analyze_sentiment":
        result = await analyze_sentiment_fn(
            text=arguments.get("text", "")
        )
    else:
        raise ValueError(f"Unknown tool: {name}")

    return [TextContent(type="text", text=result)]


@server.list_tools()
async def list_tools() -> list:
    """List available tools for MCP clients."""
    return [
        Tool(
            name="search_knowledge_base",
            description="Search product documentation for relevant information. Use when customer asks product questions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "max_results": {"type": "integer", "description": "Max results to return", "default": 5},
                    "category": {"type": "string", "description": "Optional category filter"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="create_ticket",
            description="Create a support ticket for tracking customer interactions. ALWAYS create at conversation start.",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer email or phone"},
                    "issue": {"type": "string", "description": "Description of the issue"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"], "default": "medium"},
                    "category": {"type": "string", "description": "Issue category"},
                    "channel": {"type": "string", "enum": ["email", "whatsapp", "web_form"], "default": "web_form"}
                },
                "required": ["customer_id", "issue"]
            }
        ),
        Tool(
            name="get_customer_history",
            description="Get customer's complete interaction history across ALL channels.",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer identifier"},
                    "limit": {"type": "integer", "description": "Max conversations to return", "default": 20}
                },
                "required": ["customer_id"]
            }
        ),
        Tool(
            name="escalate_to_human",
            description="Escalate a ticket to human support. Use for pricing, refunds, legal, angry customers, or complex issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Ticket ID to escalate"},
                    "reason": {"type": "string", "description": "Reason code: pricing_inquiry, refund_request, legal_inquiry, negative_sentiment, human_request, unknown_topic"},
                    "urgency": {"type": "string", "enum": ["normal", "high", "critical"], "default": "normal"},
                    "context": {"type": "object", "description": "Additional context"}
                },
                "required": ["ticket_id", "reason"]
            }
        ),
        Tool(
            name="send_response",
            description="Send response to customer via their preferred channel. Automatically formats for channel.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Ticket ID to respond to"},
                    "message": {"type": "string", "description": "Response message content"},
                    "channel": {"type": "string", "enum": ["email", "whatsapp", "web_form"], "default": "web_form"}
                },
                "required": ["ticket_id", "message"]
            }
        ),
        Tool(
            name="analyze_sentiment",
            description="Analyze the sentiment of customer message. Use to detect frustrated or angry customers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Customer message text"}
                },
                "required": ["text"]
            }
        )
    ]


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Customer Success FTE - MCP Server Prototype")
    print("=" * 60)
    print()

    # Initialize
    initialize_knowledge_base()

    print()
    print("Available Tools:")
    print("  1. search_knowledge_base(query, max_results, category)")
    print("  2. create_ticket(customer_id, issue, priority, category, channel)")
    print("  3. get_customer_history(customer_id, limit)")
    print("  4. escalate_to_human(ticket_id, reason, urgency, context)")
    print("  5. send_response(ticket_id, message, channel)")
    print("  6. analyze_sentiment(text)")
    print()

    # For standalone testing, run the test script instead
    print("To run tests: python test_mcp_server.py")
    print()
    print("To run as MCP server: python -m mcp_server")
    print()
