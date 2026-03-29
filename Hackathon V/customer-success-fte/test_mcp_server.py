#!/usr/bin/env python3
"""
MCP Server Test Script
======================
Test the MCP server prototype with sample scenarios from the hackathon.

Run with: python test_mcp_server.py
"""

import asyncio
from mcp.server import Server
from mcp_server import (
    search_knowledge_base_fn as search_knowledge_base,
    create_ticket_fn as create_ticket,
    get_customer_history_fn as get_customer_history,
    escalate_to_human_fn as escalate_to_human,
    send_response_fn as send_response,
    analyze_sentiment_fn as analyze_sentiment,
    initialize_knowledge_base
)


# =============================================================================
# TEST SCENARIOS
# =============================================================================

async def test_scenario_1_password_reset():
    """Test: Customer asks about password reset (email channel)."""
    print("\n" + "=" * 60)
    print("TEST SCENARIO 1: Password Reset (Email)")
    print("=" * 60)

    customer_email = "john@example.com"

    # Step 1: Create ticket
    print("\n1. Creating ticket...")
    ticket_result = await create_ticket(
        customer_id=customer_email,
        issue="Customer needs help resetting password",
        priority="medium",
        category="technical",
        channel="email"
    )
    print(f"   Result: {ticket_result}")
    ticket_id = ticket_result.split(": ")[1].split(".")[0]
    print(f"   Ticket ID: {ticket_id}")

    # Step 2: Search knowledge base
    print("\n2. Searching knowledge base for 'password reset'...")
    search_result = await search_knowledge_base(
        query="password reset",
        max_results=3
    )
    print(f"   Found documentation:\n{search_result[:500]}...")

    # Step 3: Check customer history
    print("\n3. Checking customer history...")
    history_result = await get_customer_history(
        customer_id=customer_email,
        limit=5
    )
    print(f"   History: {history_result[:200]}...")

    # Step 4: Send response
    print("\n4. Sending response via email...")
    response_message = """To reset your password, please follow these steps:

1. Go to https://dashboard.techcorp.com/reset
2. Enter your email address (john@example.com)
3. Check your email for a reset link
4. Click the link and set a new password
5. Log in with your new password

The reset link will expire in 24 hours. If you don't receive the email within a few minutes, please check your spam folder.

Let me know if you need any further assistance!"""

    send_result = await send_response(
        ticket_id=ticket_id,
        message=response_message,
        channel="email"
    )
    print(f"   Result: {send_result}")

    print("\n[OK] Scenario 1 Complete")


async def test_scenario_2_pricing_escalation():
    """Test: Customer asks about pricing (must escalate)."""
    print("\n" + "=" * 60)
    print("TEST SCENARIO 2: Pricing Inquiry (Escalation)")
    print("=" * 60)

    customer_email = "sarah@company.com"

    # Step 1: Create ticket
    print("\n1. Creating ticket...")
    ticket_result = await create_ticket(
        customer_id=customer_email,
        issue="Customer asking about Enterprise plan pricing",
        priority="high",
        category="billing",
        channel="email"
    )
    print(f"   Result: {ticket_result}")
    ticket_id = ticket_result.split(": ")[1].split(".")[0]

    # Step 2: Analyze sentiment (should be neutral)
    print("\n2. Analyzing sentiment...")
    sentiment_result = await analyze_sentiment(
        text="We're interested in the Enterprise plan for our team of 50 developers. What's the pricing?"
    )
    print(f"   Sentiment: {sentiment_result}")

    # Step 3: Escalate (pricing inquiry)
    print("\n3. Escalating to human (pricing inquiry)...")
    escalation_result = await escalate_to_human(
        ticket_id=ticket_id,
        reason="pricing_inquiry",
        urgency="high",
        context={
            "customer_interest": "Enterprise plan",
            "team_size": 50
        }
    )
    print(f"   Result: {escalation_result}")

    # Step 4: Send response
    print("\n4. Sending response...")
    response_message = """I understand you're interested in our Enterprise plan. I'm connecting you with our sales team who can provide detailed pricing information tailored to your needs.

A sales representative will contact you within 2 hours to discuss your requirements.

Reference: Your ticket ID"""

    send_result = await send_response(
        ticket_id=ticket_id,
        message=response_message,
        channel="email"
    )
    print(f"   Result: {send_result}")

    print("\n[OK] Scenario 2 Complete")


async def test_scenario_3_angry_customer():
    """Test: Angry customer on WhatsApp (sentiment + escalation)."""
    print("\n" + "=" * 60)
    print("TEST SCENARIO 3: Angry Customer (WhatsApp)")
    print("=" * 60)

    customer_phone = "+1234567890"

    # Step 1: Analyze sentiment
    print("\n1. Analyzing sentiment of angry message...")
    angry_message = "This is ridiculous! Your API has been down for 2 hours! I'm losing money because of this!"
    sentiment_result = await analyze_sentiment(text=angry_message)
    print(f"   Sentiment: {sentiment_result}")

    # Step 2: Create ticket
    print("\n2. Creating ticket...")
    ticket_result = await create_ticket(
        customer_id=customer_phone,
        issue="Angry customer - API down complaint",
        priority="critical",
        category="technical",
        channel="whatsapp"
    )
    print(f"   Result: {ticket_result}")
    ticket_id = ticket_result.split(": ")[1].split(".")[0]

    # Step 3: Escalate due to negative sentiment
    print("\n3. Escalating due to negative sentiment...")
    escalation_result = await escalate_to_human(
        ticket_id=ticket_id,
        reason="negative_sentiment",
        urgency="critical",
        context={
            "complaint": "API downtime",
            "customer_impact": "losing money"
        }
    )
    print(f"   Result: {escalation_result}")

    # Step 4: Send empathetic response via WhatsApp
    print("\n4. Sending empathetic response via WhatsApp...")
    response_message = "I completely understand your frustration, and I'm sorry you're dealing with this. I'm having our engineering team lead follow up with you immediately. They'll check your specific situation and get this resolved."

    send_result = await send_response(
        ticket_id=ticket_id,
        message=response_message,
        channel="whatsapp"
    )
    print(f"   Result: {send_result}")

    print("\n[OK] Scenario 3 Complete")


async def test_scenario_4_whatsapp_short_response():
    """Test: Simple question on WhatsApp (short response)."""
    print("\n" + "=" * 60)
    print("TEST SCENARIO 4: Simple Question (WhatsApp)")
    print("=" * 60)

    customer_phone = "+9876543210"

    # Step 1: Create ticket
    print("\n1. Creating ticket...")
    ticket_result = await create_ticket(
        customer_id=customer_phone,
        issue="API authentication question",
        priority="medium",
        category="technical",
        channel="whatsapp"
    )
    print(f"   Result: {ticket_result}")
    ticket_id = ticket_result.split(": ")[1].split(".")[0]

    # Step 2: Search knowledge base
    print("\n2. Searching knowledge base for 'API key'...")
    search_result = await search_knowledge_base(
        query="API key where to find",
        max_results=2
    )
    print(f"   Found: {search_result[:300]}...")

    # Step 3: Send WhatsApp-appropriate response
    print("\n3. Sending concise WhatsApp response...")
    response_message = "To find your API keys: Log in to dashboard.techcorp.com → Settings → API Keys → Click 'Generate New Key'. Keep it secure! 🔑"

    send_result = await send_response(
        ticket_id=ticket_id,
        message=response_message,
        channel="whatsapp"
    )
    print(f"   Result: {send_result}")

    print("\n[OK] Scenario 4 Complete")


async def test_scenario_5_cross_channel_continuity():
    """Test: Customer follows up on different channel."""
    print("\n" + "=" * 60)
    print("TEST SCENARIO 5: Cross-Channel Continuity")
    print("=" * 60)

    customer_email = "dev@startup.io"

    # First interaction: WhatsApp
    print("\n--- First Interaction (WhatsApp) ---")
    ticket1_result = await create_ticket(
        customer_id=customer_email,
        issue="Initial question about rate limits",
        priority="medium",
        category="technical",
        channel="whatsapp"
    )
    print(f"   Ticket 1 (WhatsApp): {ticket1_result}")

    # Second interaction: Email (same customer)
    print("\n--- Follow-up (Email) - Same Customer ---")
    ticket2_result = await create_ticket(
        customer_id=customer_email,
        issue="Follow-up: Need higher rate limits",
        priority="medium",
        category="technical",
        channel="email"
    )
    print(f"   Ticket 2 (Email): {ticket2_result}")

    # Check history (should show both conversations)
    print("\n--- Checking Customer History ---")
    history_result = await get_customer_history(
        customer_id=customer_email,
        limit=10
    )
    print(f"   History:\n{history_result}")

    print("\n[OK] Scenario 5 Complete")


async def test_scenario_6_empty_message():
    """Test: Edge case - empty message."""
    print("\n" + "=" * 60)
    print("TEST SCENARIO 6: Edge Case - Empty Message")
    print("=" * 60)

    customer_email = "test@example.com"

    # Step 1: Create ticket
    print("\n1. Creating ticket for empty message...")
    ticket_result = await create_ticket(
        customer_id=customer_email,
        issue="Customer sent empty message",
        priority="low",
        category="general",
        channel="web_form"
    )
    print(f"   Result: {ticket_result}")
    ticket_id = ticket_result.split(": ")[1].split(".")[0]

    # Step 2: Send clarification request
    print("\n2. Sending clarification request...")
    response_message = """Hi there!

It looks like your message came through empty. Could you please provide more details about your question or issue?

To help you better, please include:
- What you're trying to accomplish
- Any error messages you're seeing
- Steps you've already tried

We're here to help!"""

    send_result = await send_response(
        ticket_id=ticket_id,
        message=response_message,
        channel="web_form"
    )
    print(f"   Result: {send_result}")

    print("\n[OK] Scenario 6 Complete")


async def test_scenario_7_human_request():
    """Test: Customer explicitly requests human."""
    print("\n" + "=" * 60)
    print("TEST SCENARIO 7: Human Request (WhatsApp)")
    print("=" * 60)

    customer_phone = "+1122334455"

    # Step 1: Create ticket
    print("\n1. Creating ticket...")
    ticket_result = await create_ticket(
        customer_id=customer_phone,
        issue="Customer requested human agent",
        priority="high",
        category="general",
        channel="whatsapp"
    )
    print(f"   Result: {ticket_result}")
    ticket_id = ticket_result.split(": ")[1].split(".")[0]

    # Step 2: Immediate escalation
    print("\n2. Escalating (customer requested human)...")
    escalation_result = await escalate_to_human(
        ticket_id=ticket_id,
        reason="human_request",
        urgency="high",
        context={
            "customer_message": "human"
        }
    )
    print(f"   Result: {escalation_result}")

    # Step 3: Send acknowledgment
    print("\n3. Sending acknowledgment...")
    response_message = "I'm connecting you with a human agent. They'll review your conversation and respond shortly. Thanks for your patience!"

    send_result = await send_response(
        ticket_id=ticket_id,
        message=response_message,
        channel="whatsapp"
    )
    print(f"   Result: {send_result}")

    print("\n[OK] Scenario 7 Complete")


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

async def run_all_tests():
    """Run all test scenarios."""
    print("\n" + "=" * 70)
    print("   MCP SERVER TEST SUITE - Customer Success FTE")
    print("   Hackathon 5: Digital FTE Factory")
    print("=" * 70)

    # Initialize knowledge base
    initialize_knowledge_base()

    # Run all scenarios
    await test_scenario_1_password_reset()
    await test_scenario_2_pricing_escalation()
    await test_scenario_3_angry_customer()
    await test_scenario_4_whatsapp_short_response()
    await test_scenario_5_cross_channel_continuity()
    await test_scenario_6_empty_message()
    await test_scenario_7_human_request()

    # Summary
    print("\n" + "=" * 70)
    print("   TEST SUMMARY")
    print("=" * 70)
    print("""
All 7 test scenarios completed:

[OK] Scenario 1: Password Reset (Email) - Basic flow
[OK] Scenario 2: Pricing Inquiry - Escalation flow
[OK] Scenario 3: Angry Customer - Sentiment + Escalation
[OK] Scenario 4: WhatsApp Short Response - Channel formatting
[OK] Scenario 5: Cross-Channel Continuity - History tracking
[OK] Scenario 6: Empty Message - Edge case handling
[OK] Scenario 7: Human Request - Direct escalation

Tools tested:
  [OK] search_knowledge_base
  [OK] create_ticket
  [OK] get_customer_history
  [OK] escalate_to_human
  [OK] send_response
  [OK] analyze_sentiment
    """)
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
