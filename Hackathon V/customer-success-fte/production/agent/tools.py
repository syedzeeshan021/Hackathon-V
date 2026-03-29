# Customer Success FTE - Agent Tools
# OpenAI Agents SDK @function_tool implementation

from agents import function_tool
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timezone
import logging
import json

from .formatters import format_for_channel, Channel
from .prompts import ESCALATION_REASONS, ESCALATION_URGENCY_LEVELS

# Try to import database modules (will fail in test environment, use in-memory fallback)
try:
    from ..db import (
        CustomerRepository,
        TicketRepository,
        ConversationRepository,
        EscalationRepository,
        KnowledgeBaseRepository,
        get_connection,
    )
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# =============================================================================
# LOGGING SETUP
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# INPUT SCHEMAS (Pydantic Models)
# =============================================================================


class ChannelType(str, Enum):
    """Supported communication channels."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


class PriorityType(str, Enum):
    """Ticket priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationReason(str, Enum):
    """Valid escalation reason codes."""
    PRICING_INQUIRY = "pricing_inquiry"
    REFUND_REQUEST = "refund_request"
    LEGAL_INQUIRY = "legal_inquiry"
    NEGATIVE_SENTIMENT = "negative_sentiment"
    HUMAN_REQUEST = "human_request"
    UNKNOWN_TOPIC = "unknown_topic"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"


class UrgencyType(str, Enum):
    """Escalation urgency levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# TOOL INPUT MODELS
# =============================================================================


class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge base search."""
    model_config = ConfigDict(use_enum_values=True)

    query: str = Field(..., description="The search query from the customer")
    max_results: int = Field(default=5, ge=1, le=10, description="Maximum results to return (1-10)")
    category: Optional[str] = Field(default=None, description="Optional category filter")

    @field_validator('query')
    @classmethod
    def query_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class TicketInput(BaseModel):
    """Input schema for creating a ticket."""
    model_config = ConfigDict(use_enum_values=True)

    customer_id: str = Field(..., description="Customer identifier (email or phone)")
    issue: str = Field(..., description="Description of the customer's issue")
    priority: PriorityType = Field(default=PriorityType.MEDIUM, description="Ticket priority")
    category: Optional[str] = Field(default=None, description="Issue category")
    channel: ChannelType = Field(default=ChannelType.WEB_FORM, description="Source channel")

    @field_validator('customer_id')
    @classmethod
    def customer_id_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Customer ID cannot be empty")
        return v.strip()

    @field_validator('issue')
    @classmethod
    def issue_must_have_content(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError("Issue must be at least 5 characters")
        return v.strip()


class CustomerHistoryInput(BaseModel):
    """Input schema for getting customer history."""
    model_config = ConfigDict(use_enum_values=True)

    customer_id: str = Field(..., description="Customer identifier")
    limit: int = Field(default=20, ge=1, le=50, description="Max conversations to return (1-50)")


class EscalationInput(BaseModel):
    """Input schema for escalating to human."""
    model_config = ConfigDict(use_enum_values=True)

    ticket_id: str = Field(..., description="Ticket ID to escalate")
    reason: EscalationReason = Field(..., description="Reason code for escalation")
    urgency: UrgencyType = Field(default=UrgencyType.NORMAL, description="Escalation urgency")
    context: Optional[str] = Field(default=None, description="Additional context as string")

    @field_validator('ticket_id')
    @classmethod
    def ticket_id_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Ticket ID cannot be empty")
        return v.strip()


class ResponseInput(BaseModel):
    """Input schema for sending response."""
    model_config = ConfigDict(use_enum_values=True)

    ticket_id: str = Field(..., description="Ticket ID to respond to")
    message: str = Field(..., description="Response message content")
    channel: ChannelType = Field(..., description="Channel to send via")

    @field_validator('ticket_id')
    @classmethod
    def ticket_id_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Ticket ID cannot be empty")
        return v.strip()

    @field_validator('message')
    @classmethod
    def message_must_have_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v


class SentimentInput(BaseModel):
    """Input schema for sentiment analysis."""
    model_config = ConfigDict(use_enum_values=True)

    text: str = Field(..., description="Customer message text to analyze")

    @field_validator('text')
    @classmethod
    def text_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v


# =============================================================================
# IN-MEMORY DATABASE FALLBACK (for testing without DB)
# =============================================================================

# In-memory storage for prototype/testing fallback
_tickets_db: List[Dict[str, Any]] = []
_conversations_db: List[Dict[str, Any]] = []
_customers_db: List[Dict[str, Any]] = []
_escalations_db: List[Dict[str, Any]] = []
_knowledge_base_fallback: List[Dict[str, Any]] = []


def _init_knowledge_base_fallback():
    """Initialize fallback knowledge base with sample entries."""
    global _knowledge_base_fallback
    _knowledge_base_fallback = [
        {
            "id": "kb-001",
            "title": "How to Reset Your Password",
            "content": """To reset your password:
1. Go to https://dashboard.techcorp.com/reset
2. Enter your email address
3. Check your email for a reset link
4. Click the link and set a new password
5. Log in with your new password

Password reset links expire after 24 hours. If you don't receive the email, check your spam folder.""",
            "category": "authentication"
        },
        {
            "id": "kb-002",
            "title": "Finding Your API Keys",
            "content": """To find your API keys:
1. Log in to your dashboard at https://dashboard.techcorp.com
2. Navigate to Settings → API Keys in the left sidebar
3. Click 'Generate New Key' if you don't have one
4. Copy and securely store your API key

Important: API keys are shown only once. Never share your API key or commit it to version control.""",
            "category": "authentication"
        },
        {
            "id": "kb-003",
            "title": "Understanding Rate Limits",
            "content": """Rate limits by plan:
- Starter: 100 requests/minute, 100,000 requests/day
- Professional: 500 requests/minute, 1,000,000 requests/day
- Enterprise: Custom limits

When you exceed the rate limit, you'll receive a 429 Too Many Requests status code.
Implement exponential backoff to handle rate limits gracefully.

Rate limit headers included in responses:
- X-RateLimit-Limit: Maximum requests allowed
- X-RateLimit-Remaining: Requests remaining in window
- X-RateLimit-Reset: Unix timestamp when limit resets""",
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

Supported events: api.created, api.deleted, key.created, key.revoked, rate_limit.exceeded, error.spike

Webhook payloads are signed with X-TechCorp-Signature header. Verify signatures to ensure authenticity.""",
            "category": "webhooks"
        },
        {
            "id": "kb-005",
            "title": "OAuth2 Authentication Flow",
            "content": """OAuth2 flow for third-party integrations:
1. Register your application in Dashboard → Settings → OAuth Apps
2. Redirect users to: /oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&response_type=code&scope=read write
3. Exchange the authorization code for an access token at /oauth/token
4. Use the access token to make requests on behalf of the user

Common error: 'invalid_redirect_uri' - ensure your redirect URI exactly matches what's registered in your OAuth App settings.""",
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
3. Ensure you're using a secret key (sk_...) for server-side requests
4. If using OAuth, verify the access token hasn't expired""",
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
  "timestamp": "2026-03-17T10:30:00Z"
}""",
            "category": "api_reference"
        }
    ]


# Initialize fallback knowledge base on module load
_init_knowledge_base_fallback()

# =============================================================================
# RAW TOOL IMPLEMENTATIONS (for testing)
# =============================================================================


async def search_knowledge_base_raw(input: KnowledgeSearchInput) -> str:
    """
    Search product documentation for relevant information.
    Raw implementation for testing.
    """
    try:
        logger.info(f"Searching knowledge base for: {input.query}")

        query_lower = input.query.lower()
        results = []

        # Use database if available, otherwise fallback to in-memory
        if DB_AVAILABLE:
            try:
                results = await KnowledgeBaseRepository.search_hybrid(
                    query_text=input.query,
                    limit=input.max_results,
                    category=input.category
                )
                if not results:
                    return "No relevant documentation found. Consider escalating to human support if the question is complex."

                formatted = []
                for r in results:
                    formatted.append(
                        f"**{r['title']}** (Category: {r.get('category', 'general')}, Similarity: {r.get('similarity', 0):.2f})\n{r['content']}"
                    )
                return "\n\n---\n\n".join(formatted)
            except Exception as e:
                logger.error(f"Database knowledge base search failed: {e}, using fallback")
                # Fall through to in-memory search

        # Fallback to in-memory search
        for entry in _knowledge_base_fallback:
            title_match = entry["title"].lower().find(query_lower) >= 0
            content_match = entry["content"].lower().find(query_lower) >= 0
            category_match = input.category is None or entry["category"] == input.category

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

        results.sort(key=lambda x: x["relevance"], reverse=True)
        results = results[:input.max_results]

        if not results:
            return "No relevant documentation found. Consider escalating to human support if the question is complex."

        formatted = []
        for r in results:
            formatted.append(
                f"**{r['title']}** (Category: {r['category']}, Relevance: {'High' if r['relevance'] >= 2 else 'Medium'})\n{r['content']}"
            )

        result_text = "\n\n---\n\n".join(formatted)
        logger.info(f"Found {len(results)} results")
        return result_text

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        return "Knowledge base temporarily unavailable. Please try again or escalate to human support."


async def create_ticket_raw(input: TicketInput) -> str:
    """
    Create a support ticket for tracking customer interactions.
    Raw implementation for testing.
    """
    try:
        logger.info(f"Creating ticket for customer: {input.customer_id}, channel: {input.channel}")

        if DB_AVAILABLE:
            # Use database - first create/get customer
            customer = await CustomerRepository.create_or_get_customer(
                email=input.customer_id if "@" in input.customer_id else None,
                phone=input.customer_id if "@" not in input.customer_id else None
            )

            # Create ticket
            ticket = await TicketRepository.create_ticket(
                customer_id=customer['id'],
                source_channel=str(input.channel),
                issue=input.issue,
                category=input.category,
                priority=str(input.priority)
            )

            logger.info(f"Ticket created: {ticket['id']}")
            return f"Ticket created: {ticket['id']}. Status: open. Priority: {input.priority}."

        # Fallback to in-memory
        ticket_id = f"tkt-{len(_tickets_db) + 1:04d}"
        ticket = {
            "id": ticket_id,
            "customer_id": input.customer_id,
            "issue": input.issue,
            "priority": str(input.priority),
            "category": input.category,
            "source_channel": str(input.channel),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "resolved_at": None,
            "resolution_notes": None,
            "messages": []
        }
        _tickets_db.append(ticket)
        logger.info(f"Ticket created: {ticket_id}")
        return f"Ticket created: {ticket_id}. Status: open. Priority: {input.priority}."

    except Exception as e:
        logger.error(f"Failed to create ticket: {e}")
        return f"Error creating ticket: {str(e)}. Please try again or escalate."


async def get_customer_history_raw(input: CustomerHistoryInput) -> str:
    """
    Get customer's complete interaction history across ALL channels.
    Raw implementation for testing.
    """
    try:
        logger.info(f"Getting history for customer: {input.customer_id}")

        if DB_AVAILABLE:
            # Try to find customer by email or phone
            customer = None
            if "@" in input.customer_id:
                customer = await CustomerRepository.get_customer_by_identifier("email", input.customer_id)
            else:
                customer = await CustomerRepository.get_customer_by_identifier("phone", input.customer_id)

            if not customer:
                return f"No prior conversation history found for customer {input.customer_id}. This appears to be a new customer."

            # Get customer's tickets
            tickets = await TicketRepository.get_tickets_by_customer(customer['id'], limit=input.limit)

            if not tickets:
                return f"No prior conversation history found for customer {input.customer_id}. This appears to be a new customer."

            history = []
            for ticket in tickets:
                history.append(f"""
---
**Ticket:** {ticket['id']}
**Channel:** {ticket['source_channel']}
**Status:** {ticket['status']}
**Created:** {ticket['created_at']}
**Issue:** {ticket.get('category', 'General')}
""")

            result_text = f"Found {len(tickets)} prior conversation(s) for customer {input.customer_id}:\n\n" + "\n".join(history)
            logger.info(f"Found {len(tickets)} conversations")
            return result_text

        # Fallback to in-memory
        customer_tickets = [t for t in _tickets_db if t["customer_id"] == input.customer_id]

        if not customer_tickets:
            return f"No prior conversation history found for customer {input.customer_id}. This appears to be a new customer."

        history = []
        for ticket in customer_tickets[-input.limit:]:
            history.append(f"""
---
**Ticket:** {ticket['id']}
**Channel:** {ticket['source_channel']}
**Status:** {ticket['status']}
**Created:** {ticket['created_at']}
**Issue:** {ticket['issue']}
""")
            for msg in ticket.get("messages", [])[-5:]:
                content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                history.append(f"  [{msg['role']}] ({msg['channel']}): {content_preview}")

        result_text = f"Found {len(customer_tickets)} prior conversation(s) for customer {input.customer_id}:\n\n" + "\n".join(history)
        logger.info(f"Found {len(customer_tickets)} conversations")
        return result_text

    except Exception as e:
        logger.error(f"Failed to get customer history: {e}")
        return f"Error retrieving customer history: {str(e)}"


async def escalate_to_human_raw(input: EscalationInput) -> str:
    """
    Escalate a ticket to human support.
    Raw implementation for testing.
    """
    try:
        logger.info(f"Escalating ticket {input.ticket_id} for reason: {input.reason}")

        if DB_AVAILABLE:
            # Get ticket from database
            ticket = await TicketRepository.get_ticket_by_id(input.ticket_id)
            if not ticket:
                return f"Error: Ticket {input.ticket_id} not found."

            # Update ticket status
            await TicketRepository.update_ticket_status(input.ticket_id, "escalated")

            # Create escalation
            escalation = await EscalationRepository.create_escalation(
                ticket_id=input.ticket_id,
                reason_code=str(input.reason),
                urgency=str(input.urgency),
                context={"source": "agent_escalation"}
            )

            response_templates = {
                "pricing_inquiry": "I'm connecting you with our sales team who can provide detailed pricing information.",
                "refund_request": "I'm escalating this to our billing team who can assist with refund requests.",
                "legal_inquiry": "I'm escalating this to our legal team for proper handling.",
                "negative_sentiment": "I understand this is frustrating. I'm having a specialist follow up personally.",
                "human_request": "I'm connecting you with a human agent who can provide personalized assistance.",
                "unknown_topic": "Let me get a specialist involved who can better assist with this question.",
                "bug_report": "I'm escalating this to our engineering team for investigation.",
                "feature_request": "I'm sharing this with our product team for consideration."
            }

            response = response_templates.get(str(input.reason), "I'm escalating this to a human specialist.")
            logger.info(f"Escalation created: {escalation['id']}")
            return f"Escalated to human support. Reference: {escalation['id']}. Urgency: {input.urgency}. {response}"

        # Fallback to in-memory
        ticket = None
        for t in _tickets_db:
            if t["id"] == input.ticket_id:
                ticket = t
                break

        if not ticket:
            return f"Error: Ticket {input.ticket_id} not found."

        ticket["status"] = "escalated"
        ticket["resolution_notes"] = f"Escalated: {input.reason}. Urgency: {input.urgency}."

        escalation_id = f"esc-{len(_escalations_db) + 1:04d}"
        escalation = {
            "id": escalation_id,
            "ticket_id": input.ticket_id,
            "reason": str(input.reason),
            "urgency": str(input.urgency),
            "context": input.context or {},
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        _escalations_db.append(escalation)

        response_templates = {
            "pricing_inquiry": "I'm connecting you with our sales team who can provide detailed pricing information.",
            "refund_request": "I'm escalating this to our billing team who can assist with refund requests.",
            "legal_inquiry": "I'm escalating this to our legal team for proper handling.",
            "negative_sentiment": "I understand this is frustrating. I'm having a specialist follow up personally.",
            "human_request": "I'm connecting you with a human agent who can provide personalized assistance.",
            "unknown_topic": "Let me get a specialist involved who can better assist with this question.",
            "bug_report": "I'm escalating this to our engineering team for investigation.",
            "feature_request": "I'm sharing this with our product team for consideration."
        }

        response = response_templates.get(str(input.reason), "I'm escalating this to a human specialist.")

        logger.info(f"Escalation created: {escalation_id}")
        return f"Escalated to human support. Reference: {escalation_id}. Urgency: {input.urgency}. {response}"

    except Exception as e:
        logger.error(f"Failed to escalate: {e}")
        return f"Error escalating ticket: {str(e)}. Please inform the customer that a human will follow up."


async def send_response_raw(input: ResponseInput) -> str:
    """
    Send response to customer via their preferred channel.
    Raw implementation for testing.
    """
    try:
        logger.info(f"Sending response to ticket {input.ticket_id} via {input.channel}")

        if DB_AVAILABLE:
            # Get ticket from database
            ticket = await TicketRepository.get_ticket_by_id(input.ticket_id)
            if not ticket:
                return f"Error: Ticket {input.ticket_id} not found."

            # Get customer name
            customer = await CustomerRepository.get_customer_by_id(ticket['customer_id'])
            customer_name = customer.get('name') if customer else None

            # Format message for channel
            formatted_message = format_for_channel(
                message=input.message,
                channel=str(input.channel),
                ticket_id=input.ticket_id,
                customer_name=customer_name
            )

            # Get or create conversation for this ticket
            conversations = await ConversationRepository.get_conversations_by_customer(
                ticket['customer_id'], limit=1
            )
            conversation_id = conversations[0]['id'] if conversations else None

            # Add message to conversation
            await ConversationRepository.add_message(
                conversation_id=conversation_id,
                channel=str(input.channel),
                direction="outbound",
                role="agent",
                content=formatted_message
            )

            logger.info(f"Response sent via {input.channel}, length: {len(formatted_message)} chars")
            return f"Response sent via {input.channel}. Status: delivered. Message length: {len(formatted_message)} chars."

        # Fallback to in-memory
        ticket = None
        for t in _tickets_db:
            if t["id"] == input.ticket_id:
                ticket = t
                break

        if not ticket:
            return f"Error: Ticket {input.ticket_id} not found."

        customer_name = ticket.get("customer_name")
        formatted_message = format_for_channel(
            message=input.message,
            channel=str(input.channel),
            ticket_id=input.ticket_id,
            customer_name=customer_name
        )

        ticket["messages"].append({
            "role": "agent",
            "channel": str(input.channel),
            "content": formatted_message,
            "sent_at": datetime.now(timezone.utc).isoformat()
        })

        delivery_status = "sent"
        logger.info(f"Response sent via {input.channel}, length: {len(formatted_message)} chars")
        return f"Response sent via {input.channel}. Status: {delivery_status}. Message length: {len(formatted_message)} chars."

    except Exception as e:
        logger.error(f"Failed to send response: {e}")
        return f"Error sending response: {str(e)}. Please escalate for manual follow-up."


async def analyze_sentiment_raw(input: SentimentInput) -> str:
    """
    Analyze the sentiment of customer message.
    Raw implementation for testing.
    """
    try:
        logger.info("Analyzing sentiment")

        text_lower = input.text.lower()

        negative_keywords = [
            "ridiculous", "terrible", "awful", "hate", "angry", "frustrated",
            "useless", "broken", "worst", "disappointed", "waste", "sue", "lawyer"
        ]
        positive_keywords = [
            "great", "awesome", "thanks", "thank", "love", "helpful", "excellent",
            "perfect", "amazing", "wonderful", "appreciate"
        ]

        negative_count = sum(1 for word in negative_keywords if word in text_lower)
        positive_count = sum(1 for word in positive_keywords if word in text_lower)

        total = negative_count + positive_count
        if total == 0:
            score = 0.5
        else:
            score = 0.5 + (positive_count - negative_count) / (total * 2)

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

        result = {
            "score": round(score, 2),
            "label": label,
            "negative_indicators": negative_count,
            "positive_indicators": positive_count,
            "recommendation": recommendation
        }

        import json
        logger.info(f"Sentiment analysis complete: {label} (score: {score:.2f})")
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        import json
        return json.dumps({
            "score": 0.5,
            "label": "unknown",
            "error": str(e),
            "recommendation": "Proceed with standard handling."
        }, indent=2)


# =============================================================================
# @function_tool WRAPPED VERSIONS (for agent use)
# =============================================================================

search_knowledge_base = function_tool(search_knowledge_base_raw)
create_ticket = function_tool(create_ticket_raw)
get_customer_history = function_tool(get_customer_history_raw)
escalate_to_human = function_tool(escalate_to_human_raw)
send_response = function_tool(send_response_raw)
analyze_sentiment = function_tool(analyze_sentiment_raw)
