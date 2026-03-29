# Customer Success FTE - Web Form Channel Handler
# Handles support form submissions via FastAPI endpoint

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, EmailStr
import asyncio

from ..db import (
    CustomerRepository,
    ConversationRepository,
    TicketRepository,
    EscalationRepository,
)
from ..agent.tools import (
    search_knowledge_base_raw,
    create_ticket_raw,
    get_customer_history_raw,
    escalate_to_human_raw,
    send_response_raw,
    analyze_sentiment_raw,
    KnowledgeSearchInput,
    TicketInput,
    CustomerHistoryInput,
    EscalationInput,
    ResponseInput,
    SentimentInput,
    ChannelType,
    PriorityType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class WebFormSubmitRequest(BaseModel):
    """Web form submission request."""
    email: str = Field(..., description="Customer email address")
    name: Optional[str] = Field(default=None, description="Customer name")
    subject: str = Field(..., description="Support request subject")
    message: str = Field(..., description="Support message body")
    category: Optional[str] = Field(default="general", description="Issue category")
    priority: Optional[str] = Field(default="medium", description="Requested priority")
    attachments: Optional[List[str]] = Field(default=None, description="Attachment URLs")


class WebFormSubmitResponse(BaseModel):
    """Web form submission response."""
    status: str
    ticket_id: str
    message: str
    estimated_response_time: str = "24 hours"


class WebFormStatusResponse(BaseModel):
    """Ticket status check response."""
    ticket_id: str
    status: str
    subject: str
    created_at: str
    last_updated: str
    messages: List[Dict[str, Any]]


# =============================================================================
# HANDLER CLASS
# =============================================================================

class WebFormHandler:
    """
    Web form handler for customer support.

    Handles:
    - Form submissions via FastAPI endpoint
    - Real-time AI responses
    - File attachment handling
    - Ticket status checking
    """

    def __init__(self):
        """Initialize web form handler."""
        self.enabled = True
        self._form_submissions: Dict[str, Dict[str, Any]] = {}

    # =============================================================================
    # FORM PROCESSING
    # =============================================================================

    async def process_form_submission(
        self,
        form_data: WebFormSubmitRequest
    ) -> WebFormSubmitResponse:
        """
        Process a web form submission.

        Args:
            form_data: Form submission data

        Returns:
            Submission response with ticket ID
        """
        try:
            logger.info(f"Processing web form from {form_data.email}")

            # Get or create customer
            customer = await CustomerRepository.create_or_get_customer(
                email=form_data.email,
                name=form_data.name
            )

            # Create conversation
            conversation = await ConversationRepository.create_conversation(
                customer_id=customer['id'],
                initial_channel='web_form',
                metadata={
                    'subject': form_data.subject,
                    'category': form_data.category
                }
            )

            # Add inbound message
            message_content = f"Subject: {form_data.subject}\n\n{form_data.message}"
            if form_data.attachments:
                message_content += f"\n\nAttachments: {', '.join(form_data.attachments)}"

            await ConversationRepository.add_message(
                conversation_id=conversation['id'],
                channel='web_form',
                direction='inbound',
                role='customer',
                content=message_content
            )

            # Create ticket
            ticket = await TicketRepository.create_ticket(
                customer_id=customer['id'],
                source_channel='web_form',
                issue=form_data.subject,
                category=form_data.category,
                priority=form_data.priority or 'medium',
                conversation_id=conversation['id']
            )

            logger.info(f"Created ticket {ticket['id']} from web form")

            # Store submission for status checking
            self._form_submissions[ticket['id']] = {
                'customer_id': customer['id'],
                'conversation_id': conversation['id'],
                'email': form_data.email,
                'subject': form_data.subject
            }

            # Process with AI agent (async, don't wait)
            asyncio.create_task(
                self._process_with_agent(
                    customer_id=customer['id'],
                    ticket_id=ticket['id'],
                    conversation_id=conversation['id'],
                    message=form_data.message,
                    subject=form_data.subject
                )
            )

            return WebFormSubmitResponse(
                status="submitted",
                ticket_id=ticket['id'],
                message="Your support request has been submitted. We'll respond within 24 hours.",
                estimated_response_time="24 hours"
            )

        except Exception as e:
            logger.error(f"Failed to process form submission: {e}")
            raise

    async def _process_with_agent(
        self,
        customer_id: str,
        ticket_id: str,
        conversation_id: str,
        message: str,
        subject: str
    ) -> None:
        """Process form submission with AI agent."""
        try:
            # Analyze sentiment
            sentiment_result = await analyze_sentiment_raw(
                SentimentInput(text=message)
            )

            import json
            sentiment = json.loads(sentiment_result)

            # Check for escalation
            if sentiment.get('label') == 'negative' and sentiment.get('score', 1.0) < 0.3:
                await EscalationRepository.create_escalation(
                    ticket_id=ticket_id,
                    reason_code='negative_sentiment',
                    urgency='high'
                )
                return

            # Search knowledge base
            kb_results = await search_knowledge_base_raw(
                KnowledgeSearchInput(query=message, max_results=3)
            )

            if 'No relevant documentation found' in kb_results:
                await EscalationRepository.create_escalation(
                    ticket_id=ticket_id,
                    reason_code='unknown_topic',
                    urgency='normal'
                )
                return

            # Generate response
            response = await self._generate_web_form_response(
                message=message,
                subject=subject,
                kb_results=kb_results
            )

            # Send response via email (web form doesn't have real-time channel)
            # In production, this would integrate with email service
            logger.info(f"Generated response for ticket {ticket_id}")

            # Add outbound message to conversation
            await ConversationRepository.add_message(
                conversation_id=conversation_id,
                channel='web_form',
                direction='outbound',
                role='agent',
                content=response
            )

            # Update ticket status
            await TicketRepository.update_ticket_status(ticket_id, 'resolved')

        except Exception as e:
            logger.error(f"Agent processing failed: {e}")
            # Create escalation on error
            await EscalationRepository.create_escalation(
                ticket_id=ticket_id,
                reason_code='unknown_topic',
                urgency='normal'
            )

    async def _generate_web_form_response(
        self,
        message: str,
        subject: str,
        kb_results: str
    ) -> str:
        """Generate web form response."""
        response = f"""Thank you for contacting TechCorp Support.

Regarding your inquiry: {subject}

Here's how we can help:

{kb_results}

If you need further assistance, please reply to this ticket or submit a new form.

Best regards,
TechCorp Support Team
"""
        return response

    # =============================================================================
    # TICKET STATUS
    # =============================================================================

    async def get_ticket_status(self, ticket_id: str) -> WebFormStatusResponse:
        """
        Get ticket status for customer.

        Args:
            ticket_id: Ticket ID to check

        Returns:
            Ticket status response
        """
        ticket = await TicketRepository.get_ticket_by_id(ticket_id)

        if not ticket:
            raise ValueError(f"Ticket not found: {ticket_id}")

        # Get messages
        messages = await ConversationRepository.get_messages(
            ticket['conversation_id']
        ) if ticket.get('conversation_id') else []

        return WebFormStatusResponse(
            ticket_id=ticket['id'],
            status=ticket['status'],
            subject=ticket.get('issue', 'Support Request'),
            created_at=ticket['created_at'].isoformat() if ticket.get('created_at') else '',
            last_updated=ticket['created_at'].isoformat() if ticket.get('created_at') else '',
            messages=[
                {
                    'role': msg['role'],
                    'content': msg['content'],
                    'created_at': msg['created_at'].isoformat() if msg.get('created_at') else ''
                }
                for msg in messages
            ]
        )

    # =============================================================================
    # INSTANT RESPONSE (Real-time chat)
    # =============================================================================

    async def process_instant_message(
        self,
        email: str,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process instant message (real-time chat on web form).

        Args:
            email: Customer email
            message: Message content
            session_id: Optional session ID for conversation continuity

        Returns:
            Response dict with AI reply
        """
        try:
            # Get or create customer
            customer = await CustomerRepository.create_or_get_customer(email=email)

            # Get or create conversation by session
            if session_id and session_id in self._form_submissions:
                conversation_id = self._form_submissions[session_id].get('conversation_id')
            else:
                conversation = await ConversationRepository.create_conversation(
                    customer_id=customer['id'],
                    initial_channel='web_form'
                )
                conversation_id = conversation['id']

                # Store session
                self._form_submissions[session_id or customer['id']] = {
                    'customer_id': customer['id'],
                    'conversation_id': conversation_id,
                    'email': email
                }

            # Add message
            await ConversationRepository.add_message(
                conversation_id=conversation_id,
                channel='web_form',
                direction='inbound',
                role='customer',
                content=message
            )

            # Process with agent
            sentiment_result = await analyze_sentiment_raw(
                SentimentInput(text=message)
            )
            import json
            sentiment = json.loads(sentiment_result)

            kb_results = await search_knowledge_base_raw(
                KnowledgeSearchInput(query=message, max_results=2)
            )

            # Generate instant response
            if 'No relevant documentation found' in kb_results:
                response = {
                    'reply': "I'm not sure about that. Let me connect you with a human agent.",
                    'escalate': True
                }
            else:
                response = {
                    'reply': kb_results[:500],
                    'escalate': False
                }

            return {
                'status': 'success',
                **response
            }

        except Exception as e:
            logger.error(f"Instant message processing failed: {e}")
            return {
                'status': 'error',
                'reply': "Sorry, I encountered an error. Please try again."
            }

    # =============================================================================
    # HEALTH CHECK
    # =============================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check web form handler health."""
        return {
            "channel": "web_form",
            "enabled": self.enabled,
            "active_sessions": len(self._form_submissions),
            "status": "healthy" if self.enabled else "disabled"
        }
