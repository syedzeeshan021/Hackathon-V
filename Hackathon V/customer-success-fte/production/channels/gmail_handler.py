# Customer Success FTE - Gmail Channel Handler
# Handles inbound/outbound emails via Gmail API + Pub/Sub webhooks

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio

from ..db import (
    CustomerRepository,
    ConversationRepository,
    TicketRepository,
    execute_query,
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


class GmailHandler:
    """
    Gmail channel handler for customer support.

    Handles:
    - Inbound email processing via Pub/Sub webhooks
    - Outbound email sending via Gmail API
    - Thread management for conversation continuity
    """

    def __init__(self, gmail_service=None):
        """
        Initialize Gmail handler.

        Args:
            gmail_service: Authenticated Gmail API service instance
        """
        self.gmail_service = gmail_service
        self.enabled = True

    # =============================================================================
    # INBOUND EMAIL PROCESSING
    # =============================================================================

    async def process_inbound_email(
        self,
        message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an inbound email from Gmail Pub/Sub webhook.

        Args:
            message_data: Webhook payload with email data

        Returns:
            Processing result dict
        """
        try:
            logger.info(f"Processing inbound email: {message_data.get('messageId', 'unknown')}")

            # Parse email data
            email_data = self._parse_email_payload(message_data)
            sender = email_data.get('from', '')
            subject = email_data.get('subject', '')
            body = email_data.get('body', '')
            message_id = email_data.get('message_id', '')
            thread_id = email_data.get('thread_id', '')

            # Extract sender email
            sender_email = self._extract_email_address(sender)
            if not sender_email:
                logger.error(f"Could not extract email from: {sender}")
                return {"status": "error", "message": "Invalid sender"}

            # Get or create customer
            customer = await CustomerRepository.create_or_get_customer(
                email=sender_email
            )

            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                customer_id=customer['id'],
                channel='email',
                thread_id=thread_id
            )

            # Add inbound message to conversation
            await ConversationRepository.add_message(
                conversation_id=conversation['id'],
                channel='email',
                direction='inbound',
                role='customer',
                content=body,
                channel_message_id=message_id
            )

            # Create ticket for this conversation
            ticket = await TicketRepository.create_ticket(
                customer_id=customer['id'],
                source_channel='email',
                issue=subject[:200],  # Truncate subject
                category=self._categorize_email(subject, body),
                priority=self._determine_priority(subject, body),
                conversation_id=conversation['id']
            )

            logger.info(f"Created ticket {ticket['id']} for email from {sender_email}")

            # Process with agent
            agent_response = await self._process_with_agent(
                customer_id=customer['id'],
                ticket_id=ticket['id'],
                conversation_id=conversation['id'],
                message=body,
                subject=subject
            )

            # Send response
            if agent_response.get('action') == 'respond':
                await self.send_email_response(
                    to_email=sender_email,
                    subject=f"Re: {subject}",
                    body=agent_response['response'],
                    thread_id=thread_id,
                    ticket_id=ticket['id']
                )

                # Add outbound message
                await ConversationRepository.add_message(
                    conversation_id=conversation['id'],
                    channel='email',
                    direction='outbound',
                    role='agent',
                    content=agent_response['response'],
                    channel_message_id=agent_response.get('sent_message_id')
                )

            elif agent_response.get('action') == 'escalate':
                # Handle escalation
                escalation = await EscalationRepository.create_escalation(
                    ticket_id=ticket['id'],
                    reason_code=agent_response['reason'],
                    urgency=agent_response.get('urgency', 'normal')
                )
                logger.info(f"Escalated ticket {ticket['id']} to {escalation['id']}")

            return {
                "status": "success",
                "ticket_id": ticket['id'],
                "conversation_id": conversation['id'],
                "action": agent_response.get('action')
            }

        except Exception as e:
            logger.error(f"Failed to process inbound email: {e}")
            return {"status": "error", "message": str(e)}

    def _parse_email_payload(self, message_data: Dict[str, Any]) -> Dict[str, str]:
        """Parse Gmail API message payload."""
        payload = message_data.get('payload', {})
        headers = {h['name']: h['value'] for h in payload.get('headers', [])}

        # Decode body
        body = ''
        if 'body' in payload:
            body_data = payload['body'].get('data', '')
            if body_data:
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')

        # Check parts for multipart messages
        if not body and 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    part_data = part.get('body', {}).get('data', '')
                    if part_data:
                        body = base64.urlsafe_b64decode(part_data).decode('utf-8')
                        break

        return {
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'subject': headers.get('Subject', ''),
            'body': body,
            'message_id': message_data.get('id', ''),
            'thread_id': message_data.get('threadId', '')
        }

    def _extract_email_address(self, from_header: str) -> Optional[str]:
        """Extract email address from From header."""
        import re
        match = re.search(r'<([^>]+)>', from_header)
        if match:
            return match.group(1)
        # If no angle brackets, return as-is if it looks like an email
        if '@' in from_header:
            return from_header.strip()
        return None

    async def _get_or_create_conversation(
        self,
        customer_id: str,
        channel: str,
        thread_id: str
    ) -> Dict[str, Any]:
        """Get existing conversation by thread_id or create new one."""
        # Try to find existing conversation by thread_id in metadata
        # For now, create new conversation (can be enhanced with metadata lookup)
        return await ConversationRepository.create_conversation(
            customer_id=customer_id,
            initial_channel=channel,
            metadata={'gmail_thread_id': thread_id}
        )

    def _categorize_email(self, subject: str, body: str) -> str:
        """Categorize email based on content."""
        subject_lower = subject.lower()
        body_lower = body.lower()

        if any(word in subject_lower for word in ['password', 'login', 'account']):
            return 'authentication'
        elif any(word in subject_lower for word in ['api', 'key', 'integration']):
            return 'technical'
        elif any(word in subject_lower for word in ['billing', 'payment', 'invoice', 'price']):
            return 'billing'
        elif any(word in subject_lower for word in ['bug', 'error', 'issue', 'problem']):
            return 'bug_report'
        elif any(word in subject_lower for word in ['feature', 'request', 'suggestion']):
            return 'feature_request'

        return 'general'

    def _determine_priority(self, subject: str, body: str) -> str:
        """Determine ticket priority from content."""
        text = (subject + ' ' + body).lower()

        # Critical indicators
        if any(word in text for word in ['urgent', 'critical', 'down', 'outage', 'emergency']):
            return 'critical'
        # High indicators
        elif any(word in text for word in ['asap', 'important', 'immediately', 'frustrated', 'angry']):
            return 'high'
        # Medium is default
        return 'medium'

    async def _process_with_agent(
        self,
        customer_id: str,
        ticket_id: str,
        conversation_id: str,
        message: str,
        subject: str
    ) -> Dict[str, Any]:
        """
        Process message with the AI agent.

        Returns:
            Dict with action ('respond' or 'escalate') and response/reason
        """
        try:
            # Analyze sentiment
            sentiment_result = await analyze_sentiment_raw(
                SentimentInput(text=message)
            )

            import json
            sentiment = json.loads(sentiment_result)

            # Check for immediate escalation triggers
            if sentiment.get('label') == 'negative' and sentiment.get('score', 1.0) < 0.3:
                return {
                    'action': 'escalate',
                    'reason': 'negative_sentiment',
                    'urgency': 'high'
                }

            # Search knowledge base
            kb_results = await search_knowledge_base_raw(
                KnowledgeSearchInput(query=message, max_results=3)
            )

            if 'No relevant documentation found' in kb_results:
                # No KB results - escalate
                return {
                    'action': 'escalate',
                    'reason': 'unknown_topic',
                    'urgency': 'normal'
                }

            # Generate response using agent
            # In production, this would use the full agent runner
            response = await self._generate_response(
                message=message,
                subject=subject,
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

    async def _generate_response(
        self,
        message: str,
        subject: str,
        kb_results: str,
        sentiment: Dict[str, Any]
    ) -> str:
        """Generate email response based on KB results."""
        # In production, this would use the OpenAI agent
        # For now, create a helpful response template

        greeting = "Dear Customer,"
        if sentiment.get('label') == 'negative':
            greeting = "Dear Valued Customer,\n\nThank you for reaching out, and I apologize for any inconvenience you've experienced."

        response = f"""{greeting}

Thank you for contacting TechCorp Support regarding: {subject}

Based on your inquiry, here's how I can help:

{kb_results[:500]}...

If you need further assistance, please don't hesitate to reply to this email.

Best regards,
TechCorp AI Support Team
"""
        return response

    # =============================================================================
    # OUTBOUND EMAIL
    # =============================================================================

    async def send_email_response(
        self,
        to_email: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
        ticket_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Send email response via Gmail API.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            thread_id: Optional thread ID for reply
            ticket_id: Optional ticket ID for tracking

        Returns:
            Sent message ID or None
        """
        if not self.gmail_service:
            logger.warning("Gmail service not configured, simulating send")
            return f"simulated_{datetime.now().timestamp()}"

        try:
            # Create message
            message = self._create_gmail_message(to_email, subject, body, thread_id)

            # Send via Gmail API
            sent_message = self.gmail_service.users().messages().send(
                userId='me',
                body=message
            ).execute()

            logger.info(f"Sent email to {to_email}, message ID: {sent_message['id']}")
            return sent_message['id']

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return None

    def _create_gmail_message(
        self,
        to_email: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create Gmail API message."""
        message = MIMEMultipart('alternative')
        message['to'] = to_email
        message['from'] = 'TechCorp Support <support@techcorp.com>'
        message['subject'] = subject

        if thread_id:
            message['References'] = thread_id

        # Add plain text and HTML versions
        message.attach(MIMEText(body, 'plain'))
        message.attach(MIMEText(body.replace('\n', '<br>'), 'html'))

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}

    # =============================================================================
    # WEBHOOK HANDLER
    # =============================================================================

    async def handle_pubsub_webhook(
        self,
        webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle Gmail Pub/Sub webhook notification.

        Args:
            webhook_data: Pub/Sub message data

        Returns:
            Processing result
        """
        try:
            # Decode Pub/Sub message
            if 'message' in webhook_data:
                message_data = webhook_data['message']
                if 'data' in message_data:
                    # Decode base64 data
                    data = base64.b64decode(message_data['data']).decode('utf-8')
                    import json
                    email_info = json.loads(data)
                else:
                    email_info = message_data
            else:
                email_info = webhook_data

            # Process the email
            result = await self.process_inbound_email(email_info)
            return result

        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return {"status": "error", "message": str(e)}

    # =============================================================================
    # HEALTH CHECK
    # =============================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check Gmail handler health."""
        return {
            "channel": "gmail",
            "enabled": self.enabled,
            "service_configured": self.gmail_service is not None,
            "status": "healthy" if (self.enabled and self.gmail_service) else "degraded"
        }
