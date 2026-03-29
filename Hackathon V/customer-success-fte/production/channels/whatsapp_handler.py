# Customer Success FTE - WhatsApp Channel Handler
# Handles inbound/outbound messages via Twilio WhatsApp API

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
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


class WhatsAppHandler:
    """
    WhatsApp channel handler via Twilio API.

    Handles:
    - Inbound WhatsApp messages via Twilio webhook
    - Outbound message sending
    - Message templates for common responses
    - Session management for conversation context
    """

    # WhatsApp message limits
    MAX_MESSAGE_LENGTH = 1600  # WhatsApp character limit
    MAX_MEDIA_CAPTION_LENGTH = 1000

    def __init__(self, twilio_client=None, account_sid: str = None, auth_token: str = None, from_number: str = None):
        """
        Initialize WhatsApp handler.

        Args:
            twilio_client: Authenticated Twilio REST client
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: WhatsApp-enabled phone number (e.g., 'whatsapp:+14155238886')
        """
        self.twilio_client = twilio_client
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.enabled = True

        # Session cache for quick lookups (in production, use Redis)
        self._sessions: Dict[str, Dict[str, Any]] = {}

    # =============================================================================
    # INBOUND MESSAGE PROCESSING
    # =============================================================================

    async def process_inbound_message(
        self,
        webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process inbound WhatsApp message from Twilio webhook.

        Args:
            webhook_data: Twilio webhook payload

        Returns:
            Processing result dict
        """
        try:
            logger.info(f"Processing WhatsApp message from {webhook_data.get('From', 'unknown')}")

            # Extract message data
            from_number = webhook_data.get('From', '')
            to_number = webhook_data.get('To', '')
            body = webhook_data.get('Body', '')
            message_sid = webhook_data.get('MessageSid', '')
            num_media = int(webhook_data.get('NumMedia', 0))

            # Validate sender
            if not from_number.startswith('whatsapp:'):
                logger.warning(f"Invalid WhatsApp number: {from_number}")
                return {"status": "error", "message": "Invalid sender"}

            # Get or create customer by phone
            phone_number = from_number.replace('whatsapp:', '')
            customer = await CustomerRepository.create_or_get_customer(
                phone=phone_number
            )

            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                customer_id=customer['id'],
                channel='whatsapp',
                phone_number=from_number
            )

            # Handle media messages
            media_urls = []
            if num_media > 0:
                media_urls = await self._extract_media_urls(webhook_data, num_media)
                body = f"[Media message with {num_media} attachment(s)]\n{body}"

            # Add inbound message to conversation
            await ConversationRepository.add_message(
                conversation_id=conversation['id'],
                channel='whatsapp',
                direction='inbound',
                role='customer',
                content=body,
                channel_message_id=message_sid
            )

            # Create ticket
            ticket = await TicketRepository.create_ticket(
                customer_id=customer['id'],
                source_channel='whatsapp',
                issue=body[:200],
                category=self._categorize_message(body),
                priority=self._determine_priority(body),
                conversation_id=conversation['id']
            )

            logger.info(f"Created ticket {ticket['id']} for WhatsApp from {from_number}")

            # Update session cache
            self._sessions[from_number] = {
                'customer_id': customer['id'],
                'conversation_id': conversation['id'],
                'ticket_id': ticket['id'],
                'last_message': datetime.now(timezone.utc)
            }

            # Process with agent
            agent_response = await self._process_with_agent(
                customer_id=customer['id'],
                ticket_id=ticket['id'],
                conversation_id=conversation['id'],
                message=body,
                media_urls=media_urls
            )

            # Send response
            if agent_response.get('action') == 'respond':
                sent_sid = await self.send_message(
                    to_number=from_number,
                    body=agent_response['response']
                )

                # Add outbound message
                await ConversationRepository.add_message(
                    conversation_id=conversation['id'],
                    channel='whatsapp',
                    direction='outbound',
                    role='agent',
                    content=agent_response['response'],
                    channel_message_id=sent_sid
                )

            elif agent_response.get('action') == 'escalate':
                escalation = await EscalationRepository.create_escalation(
                    ticket_id=ticket['id'],
                    reason_code=agent_response['reason'],
                    urgency=agent_response.get('urgency', 'normal')
                )
                logger.info(f"Escalated ticket {ticket['id']} to {escalation['id']}")

                # Send acknowledgment
                await self.send_message(
                    to_number=from_number,
                    body="I'm connecting you with a specialist who can better assist you. Please hold on."
                )

            return {
                "status": "success",
                "ticket_id": ticket['id'],
                "conversation_id": conversation['id'],
                "action": agent_response.get('action')
            }

        except Exception as e:
            logger.error(f"Failed to process WhatsApp message: {e}")
            return {"status": "error", "message": str(e)}

    async def _extract_media_urls(
        self,
        webhook_data: Dict[str, Any],
        num_media: int
    ) -> List[str]:
        """Extract media URLs from webhook data."""
        media_urls = []
        for i in range(num_media):
            media_url = webhook_data.get(f'MediaUrl{i}')
            if media_url:
                media_urls.append(media_url)
        return media_urls

    async def _get_or_create_conversation(
        self,
        customer_id: str,
        channel: str,
        phone_number: str
    ) -> Dict[str, Any]:
        """Get existing conversation or create new one."""
        # Check session cache first
        if phone_number in self._sessions:
            session = self._sessions[phone_number]
            # Check if conversation is still active (within 24 hours)
            last_message = session.get('last_message')
            if last_message:
                age = datetime.now(timezone.utc) - last_message
                if age.total_seconds() < 86400:  # 24 hours
                    # Get existing conversation
                    conversations = await ConversationRepository.get_conversations_by_customer(
                        customer_id, limit=1
                    )
                    if conversations:
                        return conversations[0]

        # Create new conversation
        return await ConversationRepository.create_conversation(
            customer_id=customer_id,
            initial_channel=channel,
            metadata={'whatsapp_number': phone_number}
        )

    def _categorize_message(self, message: str) -> str:
        """Categorize WhatsApp message."""
        text_lower = message.lower()

        if any(word in text_lower for word in ['password', 'login', 'account', 'sign in']):
            return 'authentication'
        elif any(word in text_lower for word in ['api', 'key', 'code', 'integration']):
            return 'technical'
        elif any(word in text_lower for word in ['price', 'billing', 'payment', 'charge']):
            return 'billing'
        elif any(word in text_lower for word in ['bug', 'error', 'broken', 'not working']):
            return 'bug_report'

        return 'general'

    def _determine_priority(self, message: str) -> str:
        """Determine priority from message content."""
        text_lower = message.lower()

        if any(word in text_lower for word in ['urgent', 'emergency', 'critical', 'down']):
            return 'critical'
        elif any(word in text_lower for word in ['asap', 'hurry', 'frustrated', 'angry']):
            return 'high'

        return 'medium'

    async def _process_with_agent(
        self,
        customer_id: str,
        ticket_id: str,
        conversation_id: str,
        message: str,
        media_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Process message with AI agent."""
        try:
            # Analyze sentiment
            sentiment_result = await analyze_sentiment_raw(
                SentimentInput(text=message)
            )

            import json
            sentiment = json.loads(sentiment_result)

            # Check for escalation triggers
            if sentiment.get('label') == 'negative' and sentiment.get('score', 1.0) < 0.3:
                return {
                    'action': 'escalate',
                    'reason': 'negative_sentiment',
                    'urgency': 'high'
                }

            # Check for human request
            if any(word in message.lower() for word in ['human', 'agent', 'representative', 'person']):
                return {
                    'action': 'escalate',
                    'reason': 'human_request',
                    'urgency': 'normal'
                }

            # Search knowledge base
            kb_results = await search_knowledge_base_raw(
                KnowledgeSearchInput(query=message, max_results=3)
            )

            if 'No relevant documentation found' in kb_results:
                return {
                    'action': 'escalate',
                    'reason': 'unknown_topic',
                    'urgency': 'normal'
                }

            # Generate WhatsApp-optimized response
            response = await self._generate_whatsapp_response(
                message=message,
                kb_results=kb_results,
                sentiment=sentiment
            )

            return {
                'action': 'respond',
                'response': response,
                'sentiment': sentiment
            }

        except Exception as e:
            logger.error(f"Agent processing failed: {e}")
            return {
                'action': 'escalate',
                'reason': 'unknown_topic',
                'urgency': 'normal'
            }

    async def _generate_whatsapp_response(
        self,
        message: str,
        kb_results: str,
        sentiment: Dict[str, Any]
    ) -> str:
        """Generate WhatsApp-optimized response (concise, conversational)."""
        # Clean KB results for WhatsApp format
        kb_summary = kb_results.split('\n\n---\n\n')[0] if '\n\n---\n\n' in kb_results else kb_results

        # Extract just the title and first few lines
        lines = kb_summary.strip().split('\n')
        concise_info = '\n'.join(lines[:5])  # First 5 lines max

        # Add CTA for WhatsApp
        response = f"{concise_info}\n\n_Reply for more help or type 'human' for live support_"

        # Truncate if needed
        if len(response) > self.MAX_MESSAGE_LENGTH:
            response = response[:self.MAX_MESSAGE_LENGTH - 50] + "\n\n(Reply 'more' for full details)"

        return response

    # =============================================================================
    # OUTBOUND MESSAGING
    # =============================================================================

    async def send_message(
        self,
        to_number: str,
        body: str,
        media_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Send WhatsApp message via Twilio.

        Args:
            to_number: Recipient WhatsApp number (e.g., 'whatsapp:+1234567890')
            body: Message body
            media_url: Optional media URL (image, document, etc.)

        Returns:
            Message SID or None
        """
        if not self.twilio_client:
            # Fallback: try to create client from credentials
            if self.account_sid and self.auth_token:
                try:
                    from twilio.rest import Client
                    self.twilio_client = Client(self.account_sid, self.auth_token)
                except ImportError:
                    logger.warning("Twilio not installed, simulating send")
                    return f"simulated_{datetime.now().timestamp()}"
            else:
                logger.warning("Twilio not configured, simulating send")
                return f"simulated_{datetime.now().timestamp()}"

        try:
            # Ensure numbers are in WhatsApp format
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'

            from_number = self.from_number or 'whatsapp:+14155238886'

            # Send message
            message_params = {
                'body': body,
                'from_': from_number,
                'to': to_number
            }

            if media_url:
                message_params['media_url'] = [media_url]

            message = self.twilio_client.messages.create(**message_params)

            logger.info(f"Sent WhatsApp to {to_number}, SID: {message.sid}")
            return message.sid

        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return None

    async def send_template_message(
        self,
        to_number: str,
        template_name: str,
        template_params: List[str] = None
    ) -> Optional[str]:
        """
        Send WhatsApp template message (for outbound notifications).

        Args:
            to_number: Recipient number
            template_name: Approved template name
            template_params: Template variable values

        Returns:
            Message SID or None
        """
        if not self.twilio_client:
            logger.warning("Twilio not configured for template message")
            return None

        try:
            from_number = self.from_number or 'whatsapp:+14155238886'

            # Create content block for template
            content = [{
                "type": "text",
                "text": {
                    "body": template_name
                }
            }]

            if template_params:
                for param in template_params:
                    content.append({
                        "type": "text",
                        "text": {
                            "body": param
                        }
                    })

            message = self.twilio_client.messages.create(
                from_=from_number,
                to=to_number,
                content=json.dumps(content)
            )

            return message.sid

        except Exception as e:
            logger.error(f"Failed to send template message: {e}")
            return None

    # =============================================================================
    # WEBHOOK HANDLER
    # =============================================================================

    async def handle_twilio_webhook(
        self,
        form_data: Dict[str, Any]
    ) -> str:
        """
        Handle Twilio webhook for inbound messages.

        Args:
            form_data: Twilio form data

        Returns:
            TwiML response string
        """
        result = await self.process_inbound_message(form_data)

        # Twilio expects empty response for webhooks (we send messages async)
        return ""

    # =============================================================================
    # SESSION MANAGEMENT
    # =============================================================================

    async def get_session(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get session for phone number."""
        return self._sessions.get(phone_number)

    async def clear_session(self, phone_number: str) -> bool:
        """Clear session for phone number."""
        if phone_number in self._sessions:
            del self._sessions[phone_number]
            return True
        return False

    async def clear_expired_sessions(self, max_age_seconds: int = 86400) -> int:
        """Clear sessions older than max_age."""
        now = datetime.now(timezone.utc)
        expired = []

        for number, session in self._sessions.items():
            last_message = session.get('last_message')
            if last_message:
                age = (now - last_message).total_seconds()
                if age > max_age_seconds:
                    expired.append(number)

        for number in expired:
            del self._sessions[number]

        logger.info(f"Cleared {len(expired)} expired sessions")
        return len(expired)

    # =============================================================================
    # HEALTH CHECK
    # =============================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check WhatsApp handler health."""
        return {
            "channel": "whatsapp",
            "enabled": self.enabled,
            "twilio_configured": self.twilio_client is not None,
            "active_sessions": len(self._sessions),
            "status": "healthy" if self.enabled else "disabled"
        }
