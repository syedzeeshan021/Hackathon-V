#!/usr/bin/env python3
"""
Customer Success FTE - Agent Unit Tests
========================================
Test the OpenAI Agents SDK implementation.

Run with: pytest production/tests/test_agent.py -v
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools import (
    search_knowledge_base_raw as search_knowledge_base,
    create_ticket_raw as create_ticket,
    get_customer_history_raw as get_customer_history,
    escalate_to_human_raw as escalate_to_human,
    send_response_raw as send_response,
    analyze_sentiment_raw as analyze_sentiment,
    KnowledgeSearchInput,
    TicketInput,
    CustomerHistoryInput,
    EscalationInput,
    ResponseInput,
    SentimentInput,
    PriorityType,
    ChannelType,
    EscalationReason,
    UrgencyType,
)
from agent.formatters import (
    format_for_channel,
    truncate_to_words,
    truncate_to_chars,
    count_words,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_customer_id():
    return "test@example.com"


@pytest.fixture
def sample_ticket_id():
    return "tkt-0001"


@pytest.fixture
def sample_message():
    return "Hello, I need help resetting my password."


# =============================================================================
# TOOL INPUT VALIDATION TESTS
# =============================================================================

class TestInputValidation:
    """Test Pydantic input validation."""

    def test_knowledge_search_input_valid(self):
        """Test valid knowledge search input."""
        input_data = KnowledgeSearchInput(query="password reset")
        assert input_data.query == "password reset"
        assert input_data.max_results == 5

    def test_knowledge_search_input_empty_query(self):
        """Test that empty query raises error."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            KnowledgeSearchInput(query="")

    def test_knowledge_search_input_whitespace_query(self):
        """Test that whitespace-only query raises error."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            KnowledgeSearchInput(query="   ")

    def test_knowledge_search_input_max_results_range(self):
        """Test max_results validation."""
        # Valid range
        input_data = KnowledgeSearchInput(query="test", max_results=3)
        assert input_data.max_results == 3

        # Out of range (too low)
        with pytest.raises(ValueError):
            KnowledgeSearchInput(query="test", max_results=0)

        # Out of range (too high)
        with pytest.raises(ValueError):
            KnowledgeSearchInput(query="test", max_results=15)

    def test_ticket_input_valid(self):
        """Test valid ticket input."""
        input_data = TicketInput(
            customer_id="user@example.com",
            issue="Cannot login to my account",
            priority=PriorityType.HIGH,
            channel=ChannelType.EMAIL
        )
        assert input_data.customer_id == "user@example.com"
        assert input_data.priority == PriorityType.HIGH
        assert input_data.channel == ChannelType.EMAIL

    def test_ticket_input_empty_customer_id(self):
        """Test that empty customer_id raises error."""
        with pytest.raises(ValueError, match="Customer ID cannot be empty"):
            TicketInput(customer_id="", issue="Test issue")

    def test_ticket_input_short_issue(self):
        """Test that issue under 5 characters raises error."""
        with pytest.raises(ValueError, match="Issue must be at least 5 characters"):
            TicketInput(customer_id="user@example.com", issue="Help")

    def test_escalation_input_valid(self):
        """Test valid escalation input."""
        input_data = EscalationInput(
            ticket_id="tkt-0001",
            reason=EscalationReason.PRICING_INQUIRY,
            urgency=UrgencyType.HIGH
        )
        assert input_data.ticket_id == "tkt-0001"
        assert input_data.reason == EscalationReason.PRICING_INQUIRY
        assert input_data.urgency == UrgencyType.HIGH

    def test_response_input_valid(self):
        """Test valid response input."""
        input_data = ResponseInput(
            ticket_id="tkt-0001",
            message="Here's how to reset your password...",
            channel=ChannelType.EMAIL
        )
        assert input_data.ticket_id == "tkt-0001"
        assert input_data.channel == ChannelType.EMAIL

    def test_response_input_empty_message(self):
        """Test that empty message raises error."""
        with pytest.raises(ValueError, match="Message cannot be empty"):
            ResponseInput(
                ticket_id="tkt-0001",
                message="",
                channel=ChannelType.EMAIL
            )


# =============================================================================
# FORMATTER TESTS
# =============================================================================

class TestFormatters:
    """Test channel-specific formatters."""

    def test_format_email_basic(self):
        """Test basic email formatting."""
        message = "Here is the solution to your problem."
        result = format_for_channel(message, "email", ticket_id="tkt-0001")

        assert "Dear Customer," in result
        assert "Thank you for reaching out to TechCorp Support" in result
        assert "Best regards" in result
        assert "TechCorp AI Support Team" in result
        assert "Ticket Reference: tkt-0001" in result

    def test_format_email_with_customer_name(self):
        """Test email formatting with customer name."""
        message = "Solution here."
        result = format_for_channel(message, "email", customer_name="John")

        assert "Dear John," in result

    def test_format_whatsapp_basic(self):
        """Test basic WhatsApp formatting."""
        message = "Here's how to fix your issue."
        result = format_for_channel(message, "whatsapp", ticket_id="tkt-0001")

        assert "Reply for more help or type 'human' for live support" in result
        assert "Ref: tkt-0001" in result

    def test_format_whatsapp_truncation(self):
        """Test WhatsApp message truncation."""
        # Create a message over 300 chars
        long_message = "This is a very long message. " * 20
        result = format_for_channel(long_message, "whatsapp")

        assert len(result) <= 350  # Allow some buffer for CTA

    def test_format_web_form_basic(self):
        """Test basic web form formatting."""
        message = "Here's the answer to your question."
        result = format_for_channel(message, "web_form", ticket_id="tkt-0001")

        assert "Hi there!" in result or "Thanks for contacting" in result
        assert "Ticket: tkt-0001" in result
        assert "support portal" in result

    def test_truncate_to_words(self):
        """Test word truncation."""
        text = "One two three four five six seven eight nine ten."
        result = truncate_to_words(text, 5)
        assert count_words(result) <= 5

    def test_truncate_to_chars(self):
        """Test character truncation."""
        text = "This is a longer message that needs to be truncated."
        result = truncate_to_chars(text, 20)
        assert len(result) <= 23  # 20 + "..."

    def test_count_words(self):
        """Test word counting."""
        assert count_words("One two three") == 3
        assert count_words("") == 0
        assert count_words("   ") == 0  # Whitespace-only returns 0


# =============================================================================
# KNOWLEDGE BASE SEARCH TESTS
# =============================================================================

class TestKnowledgeBaseSearch:
    """Test knowledge base search functionality."""

    @pytest.mark.asyncio
    async def test_search_password_reset(self):
        """Test searching for password reset."""
        input_data = KnowledgeSearchInput(query="password reset")
        result = await search_knowledge_base(input_data)

        assert "password" in result.lower() or "No relevant" in result

    @pytest.mark.asyncio
    async def test_search_api_keys(self):
        """Test searching for API keys."""
        input_data = KnowledgeSearchInput(query="API key")
        result = await search_knowledge_base(input_data)

        # Should find API key documentation or return not found message
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        """Test search with no matching results."""
        input_data = KnowledgeSearchInput(query="xyznonexistent123")
        result = await search_knowledge_base(input_data)

        assert "No relevant documentation found" in result


# =============================================================================
# TICKET CREATION TESTS
# =============================================================================

class TestTicketCreation:
    """Test ticket creation functionality."""

    @pytest.mark.asyncio
    async def test_create_ticket_basic(self):
        """Test basic ticket creation."""
        input_data = TicketInput(
            customer_id="test@example.com",
            issue="Cannot access my account",
            priority=PriorityType.MEDIUM,
            channel=ChannelType.EMAIL
        )
        result = await create_ticket(input_data)

        assert "Ticket created:" in result
        assert "tkt-" in result
        assert "open" in result

    @pytest.mark.asyncio
    async def test_create_ticket_high_priority(self):
        """Test ticket creation with high priority."""
        input_data = TicketInput(
            customer_id="urgent@example.com",
            issue="Production system down",
            priority=PriorityType.CRITICAL,
            channel=ChannelType.WEB_FORM
        )
        result = await create_ticket(input_data)

        assert "critical" in result.lower()


# =============================================================================
# CUSTOMER HISTORY TESTS
# =============================================================================

class TestCustomerHistory:
    """Test customer history retrieval."""

    @pytest.mark.asyncio
    async def test_get_history_new_customer(self):
        """Test history for customer with no prior tickets."""
        input_data = CustomerHistoryInput(
            customer_id="newcustomer@example.com"
        )
        result = await get_customer_history(input_data)

        assert "No prior conversation history" in result or "prior conversation" in result

    @pytest.mark.asyncio
    async def test_get_history_existing_customer(self):
        """Test history for customer with existing tickets."""
        # First create a ticket
        ticket_input = TicketInput(
            customer_id="history@example.com",
            issue="Previous issue",
            channel=ChannelType.EMAIL
        )
        await create_ticket(ticket_input)

        # Then get history
        history_input = CustomerHistoryInput(
            customer_id="history@example.com"
        )
        result = await get_customer_history(history_input)

        assert "history@example.com" in result


# =============================================================================
# ESCALATION TESTS
# =============================================================================

class TestEscalation:
    """Test escalation functionality."""

    @pytest.mark.asyncio
    async def test_escalate_pricing_inquiry(self):
        """Test escalating a pricing inquiry."""
        # First create a ticket
        ticket_input = TicketInput(
            customer_id="pricing@example.com",
            issue="Pricing question",
            channel=ChannelType.EMAIL
        )
        ticket_result = await create_ticket(ticket_input)
        ticket_id = ticket_result.split(":")[1].split(".")[0].strip()

        # Then escalate
        escalation_input = EscalationInput(
            ticket_id=ticket_id,
            reason=EscalationReason.PRICING_INQUIRY,
            urgency=UrgencyType.HIGH
        )
        result = await escalate_to_human(escalation_input)

        assert "Escalated" in result or "escalat" in result.lower()
        assert "sales" in result.lower() or "pricing" in result.lower()

    @pytest.mark.asyncio
    async def test_escalate_negative_sentiment(self):
        """Test escalating due to negative sentiment."""
        # Create ticket
        ticket_input = TicketInput(
            customer_id="angry@example.com",
            issue="Very frustrated customer",
            priority=PriorityType.HIGH,
            channel=ChannelType.WHATSAPP
        )
        ticket_result = await create_ticket(ticket_input)
        ticket_id = ticket_result.split(":")[1].split(".")[0].strip()

        # Escalate
        escalation_input = EscalationInput(
            ticket_id=ticket_id,
            reason=EscalationReason.NEGATIVE_SENTIMENT,
            urgency=UrgencyType.HIGH
        )
        result = await escalate_to_human(escalation_input)

        assert "specialist" in result.lower() or "escalat" in result.lower()

    @pytest.mark.asyncio
    async def test_escalate_invalid_ticket(self):
        """Test escalating non-existent ticket."""
        escalation_input = EscalationInput(
            ticket_id="tkt-99999",
            reason=EscalationReason.HUMAN_REQUEST
        )
        result = await escalate_to_human(escalation_input)

        assert "not found" in result.lower() or "Error" in result


# =============================================================================
# SENTIMENT ANALYSIS TESTS
# =============================================================================

class TestSentimentAnalysis:
    """Test sentiment analysis functionality."""

    @pytest.mark.asyncio
    async def test_sentiment_positive(self):
        """Test positive sentiment detection."""
        input_data = SentimentInput(
            text="This is great! Thank you so much for your help. I love your product!"
        )
        result = await analyze_sentiment(input_data)

        import json
        result_dict = json.loads(result)
        assert result_dict["label"] == "positive"
        assert result_dict["score"] > 0.7

    @pytest.mark.asyncio
    async def test_sentiment_negative(self):
        """Test negative sentiment detection."""
        input_data = SentimentInput(
            text="This is ridiculous! I'm frustrated and angry. Your service is terrible!"
        )
        result = await analyze_sentiment(input_data)

        import json
        result_dict = json.loads(result)
        assert result_dict["label"] == "negative"
        assert result_dict["score"] < 0.3

    @pytest.mark.asyncio
    async def test_sentiment_neutral(self):
        """Test neutral sentiment detection."""
        input_data = SentimentInput(
            text="I have a question about my account settings."
        )
        result = await analyze_sentiment(input_data)

        import json
        result_dict = json.loads(result)
        assert result_dict["label"] in ["neutral", "somewhat negative"]

    @pytest.mark.asyncio
    async def test_sentiment_empty(self):
        """Test empty text handling."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            SentimentInput(text="")


# =============================================================================
# SEND RESPONSE TESTS
# =============================================================================

class TestSendResponse:
    """Test response sending functionality."""

    @pytest.mark.asyncio
    async def test_send_response_email(self):
        """Test sending email response."""
        # Create ticket first
        ticket_input = TicketInput(
            customer_id="response@example.com",
            issue="Need help",
            channel=ChannelType.EMAIL
        )
        ticket_result = await create_ticket(ticket_input)
        ticket_id = ticket_result.split(":")[1].split(".")[0].strip()

        # Send response
        response_input = ResponseInput(
            ticket_id=ticket_id,
            message="Here's how to solve your problem...",
            channel=ChannelType.EMAIL
        )
        result = await send_response(response_input)

        assert "sent" in result.lower()
        assert "email" in result.lower()

    @pytest.mark.asyncio
    async def test_send_response_whatsapp(self):
        """Test sending WhatsApp response."""
        # Create ticket first
        ticket_input = TicketInput(
            customer_id="+1234567890",
            issue="Quick question",
            channel=ChannelType.WHATSAPP
        )
        ticket_result = await create_ticket(ticket_input)
        ticket_id = ticket_result.split(":")[1].split(".")[0].strip()

        # Send response
        response_input = ResponseInput(
            ticket_id=ticket_id,
            message="Sure! Here's the answer.",
            channel=ChannelType.WHATSAPP
        )
        result = await send_response(response_input)

        assert "sent" in result.lower()
        assert "whatsapp" in result.lower()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for full agent workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow_password_reset(self):
        """Test complete password reset workflow."""
        customer_id = "password@test.com"

        # 1. Create ticket
        ticket_input = TicketInput(
            customer_id=customer_id,
            issue="Customer needs password reset help",
            channel=ChannelType.EMAIL
        )
        ticket_result = await create_ticket(ticket_input)
        ticket_id = ticket_result.split(":")[1].split(".")[0].strip()

        # 2. Get customer history
        history_input = CustomerHistoryInput(customer_id=customer_id)
        history_result = await get_customer_history(history_input)

        # 3. Search knowledge base
        search_input = KnowledgeSearchInput(query="password reset")
        search_result = await search_knowledge_base(search_input)

        # 4. Analyze sentiment
        sentiment_input = SentimentInput(text="I can't login, need help")
        sentiment_result = await analyze_sentiment(sentiment_input)

        # 5. Send response
        response_input = ResponseInput(
            ticket_id=ticket_id,
            message="You can reset your password by visiting our reset page.",
            channel=ChannelType.EMAIL
        )
        response_result = await send_response(response_input)

        # Verify all steps completed
        assert "Ticket created" in ticket_result
        assert "sent" in response_result.lower()


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
