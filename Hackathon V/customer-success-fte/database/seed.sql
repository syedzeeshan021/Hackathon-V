-- =============================================================================
-- CUSTOMER SUCCESS FTE - INITIAL DATA SEED
-- =============================================================================
-- This file contains initial data for the knowledge base and other tables.
-- Run this after schema.sql to populate the database.
-- =============================================================================

-- =============================================================================
-- KNOWLEDGE BASE ENTRIES
-- =============================================================================

-- Authentication & Account Management
INSERT INTO knowledge_base (title, content, category) VALUES
('How to Reset Your Password', $$
To reset your password:
1. Go to https://dashboard.techcorp.com/reset
2. Enter your email address
3. Check your email for a reset link
4. Click the link and set a new password
5. Log in with your new password

Password reset links expire after 24 hours. If you don''t receive the email, check your spam folder.

Password requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character
$$, 'authentication'),

('Finding Your API Keys', $$
To find your API keys:
1. Log in to your dashboard at https://dashboard.techcorp.com
2. Navigate to Settings → API Keys in the left sidebar
3. Click ''Generate New Key'' if you don''t have one
4. Copy and securely store your API key

Important: API keys are shown only once. Never share your API key or commit it to version control.

Key types:
- Publishable key (pk_...): Safe for client-side use
- Secret key (sk_...): Server-side only, never expose to clients
$$, 'authentication'),

('OAuth2 Authentication Flow', $$
OAuth2 flow for third-party integrations:
1. Register your application in Dashboard → Settings → OAuth Apps
2. Redirect users to: /oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&response_type=code&scope=read write
3. Exchange the authorization code for an access token at /oauth/token
4. Use the access token to make requests on behalf of the user

Token endpoint example:
POST /oauth/token
Content-Type: application/x-www-form-urlencoded
grant_type=authorization_code&code=AUTH_CODE&redirect_uri=YOUR_REDIRECT_URI&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET

Common error: ''invalid_redirect_uri'' - ensure your redirect URI exactly matches what''s registered in your OAuth App settings.
$$, 'authentication'),

('Two-Factor Authentication (2FA)', $$
Enable 2FA for enhanced security:
1. Go to Settings → Security in your dashboard
2. Click ''Enable Two-Factor Authentication''
3. Scan the QR code with your authenticator app (Google Authenticator, Authy, etc.)
4. Enter the 6-digit code from your app
5. Save your backup codes in a secure location

To disable 2FA:
- Go to Settings → Security
- Click ''Disable Two-Factor Authentication''
- Enter your password and a 2FA code

If you lose access to your authenticator app, use one of your backup codes to regain access.
$$, 'authentication'),

-- API Reference
('Understanding Rate Limits', $$
Rate limits by plan:
- Starter: 100 requests/minute, 100,000 requests/day
- Professional: 500 requests/minute, 1,000,000 requests/day
- Enterprise: Custom limits

When you exceed the rate limit, you''ll receive a 429 Too Many Requests status code.
Implement exponential backoff to handle rate limits gracefully.

Rate limit headers included in responses:
- X-RateLimit-Limit: Maximum requests allowed
- X-RateLimit-Remaining: Requests remaining in window
- X-RateLimit-Reset: Unix timestamp when limit resets

Example backoff implementation:
```python
import time
import random

def exponential_backoff(retry_count, base_delay=1.0, max_delay=60.0):
    delay = min(base_delay * (2 ** retry_count), max_delay)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter
```
$$, 'api_reference'),

('API Status and Health', $$
Check API status:
- GET /status endpoint returns current operational status
- Status page: https://status.techcorp.com
- For outages, check the status page or subscribe to notifications

Current status endpoint response:
{
  "status": "operational",
  "version": "1.0.0",
  "timestamp": "2026-03-17T10:30:00Z",
  "regions": {
    "us-east": "operational",
    "us-west": "operational",
    "eu-west": "operational",
    "ap-south": "operational"
  }
}

Subscribe to status updates:
- Email notifications: https://status.techcorp.com/subscribe
- Slack webhook: Available for Enterprise customers
- SMS alerts: Available for critical incidents only
$$, 'api_reference'),

('Error Handling Best Practices', $$
API error response format:
{
  "error": {
    "code": "invalid_request_error",
    "message": "The request was invalid",
    "param": "field_name",
    "type": "validation_error"
  }
}

Common error codes:
- invalid_request_error: Request format is invalid
- authentication_error: Missing or invalid API key
- permission_error: API key lacks required permissions
- not_found_error: Resource does not exist
- rate_limit_error: Too many requests
- server_error: Internal server error

Retry strategy:
1. Only retry on 429 (rate limit) and 5xx (server errors)
2. Use exponential backoff with jitter
3. Log all errors with request IDs for debugging
4. Implement circuit breakers for repeated failures
$$, 'api_reference'),

-- Webhooks
('Setting Up Webhooks', $$
To set up webhooks:
1. Go to Dashboard → Settings → Webhooks
2. Click ''Add Endpoint''
3. Enter your webhook URL (must be HTTPS)
4. Select events to subscribe to
5. Click ''Save''

Supported events:
- api.created: New API key created
- api.deleted: API key deleted
- key.created: New key generated
- key.revoked: Key was revoked
- rate_limit.exceeded: Rate limit exceeded
- error.spike: Unusual error rate detected

Webhook payload example:
{
  "id": "evt_123456",
  "type": "key.created",
  "created": 1710681600,
  "data": {
    "object": { ... }
  }
}

Webhook headers:
- X-TechCorp-Signature: HMAC-SHA256 signature
- X-TechCorp-Timestamp: Unix timestamp
- User-Agent: TechCorp-Webhooks/1.0
$$, 'webhooks'),

('Verifying Webhook Signatures', $$
Always verify webhook signatures to ensure authenticity:

Python example:
```python
import hmac
import hashlib
from fastapi import Request, HTTPException

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)

@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-TechCorp-Signature")
    payload = await request.body()

    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process webhook
    return {"status": "ok"}
```

Security best practices:
- Always use HTTPS for webhook endpoints
- Verify signatures before processing
- Return 2xx status codes promptly
- Implement idempotency for duplicate events
$$, 'webhooks'),

-- Troubleshooting
('Troubleshooting 401 Unauthorized', $$
401 Unauthorized errors occur when:
- API key is missing from the request
- API key is expired or revoked
- Using wrong key type (publishable vs secret)

Solutions:
1. Verify the Authorization header: ''Authorization: Bearer YOUR_API_KEY''
2. Check that your API key is active in the dashboard
3. Ensure you''re using a secret key (sk_...) for server-side requests
4. If using OAuth, verify the access token hasn''t expired

Debug checklist:
- [ ] API key is present in request
- [ ] Key format is correct (sk_... for server-side)
- [ ] Key is not expired or revoked
- [ ] Key has required permissions/scopes
- [ ] Request is going to correct environment (prod vs staging)
$$, 'troubleshooting'),

('Troubleshooting 403 Forbidden', $$
403 Forbidden errors occur when:
- API key is valid but lacks required permissions
- Accessing a resource outside your organization
- Feature not available on your plan

Solutions:
1. Check your API key''s scopes in Dashboard → Settings → API Keys
2. Verify the resource belongs to your organization
3. Upgrade your plan if the feature requires a higher tier

Common scenarios:
- Reading another organization''s data → Check organization ID
- Using admin endpoints without admin scope → Add admin:read scope
- Enterprise feature on Starter plan → Upgrade plan
$$, 'troubleshooting'),

('Troubleshooting 404 Not Found', $$
404 Not Found errors occur when:
- Resource ID is incorrect or doesn''t exist
- Resource was deleted
- Wrong API version or endpoint

Solutions:
1. Verify the resource ID format (should start with prefix like ''res_'')
2. Check that the resource hasn''t been deleted
3. Ensure you''re using the correct API version

Debug checklist:
- [ ] Resource ID is correctly formatted
- [ ] Resource exists in the dashboard
- [ ] Using correct API endpoint
- [ ] API version supports this resource type
$$, 'troubleshooting'),

('Troubleshooting 429 Rate Limit', $$
429 Too Many Requests errors occur when:
- You''ve exceeded your plan''s rate limit
- Burst of requests in a short time window

Solutions:
1. Implement exponential backoff
2. Cache responses where possible
3. Batch requests when available
4. Consider upgrading your plan for higher limits

Rate limit headers:
- X-RateLimit-Limit: Your rate limit
- X-RateLimit-Remaining: Requests remaining
- X-RateLimit-Reset: When the limit resets

Example backoff:
```python
import time
import random

def make_request_with_backoff(url, max_retries=5):
    for attempt in range(max_retries):
        response = requests.get(url)
        if response.status_code != 429:
            return response

        retry_after = int(response.headers.get('Retry-After', 60))
        jitter = random.uniform(0, retry_after * 0.1)
        time.sleep(retry_after + jitter)

    raise Exception("Max retries exceeded")
```
$$, 'troubleshooting'),

-- Getting Started
('Quick Start Guide', $$
Welcome to TechCorp! Get started in 5 minutes:

1. Create your account
   - Visit https://dashboard.techcorp.com/signup
   - Enter your email and set a password
   - Verify your email address

2. Get your API keys
   - Go to Settings → API Keys
   - Click ''Generate New Key''
   - Copy and securely store your secret key

3. Make your first API call
   ```bash
   curl https://api.techcorp.com/v1/status \
     -H "Authorization: Bearer sk_your_key_here"
   ```

4. Explore the documentation
   - API Reference: https://docs.techcorp.com/api
   - SDKs: Available for Python, Node.js, Go, Ruby
   - Code examples: https://github.com/techcorp/examples

5. Join our community
   - Discord: https://discord.gg/techcorp
   - Stack Overflow: Tag your questions with ''techcorp''
$$, 'getting_started'),

('SDK Installation', $$
Official SDKs for popular languages:

Python:
```bash
pip install techcorp-sdk
```

```python
from techcorp import Client
client = Client(api_key="sk_...")
status = client.status()
```

Node.js:
```bash
npm install @techcorp/sdk
```

```javascript
import { Client } from '@techcorp/sdk';
const client = new Client({ apiKey: 'sk_...' });
const status = await client.status();
```

Go:
```bash
go get github.com/techcorp/go-sdk
```

```go
import "github.com/techcorp/go-sdk"
client := techcorp.NewClient("sk_...")
status, _ := client.Status()
```

Ruby:
```bash
gem install techcorp
```

```ruby
require 'techcorp'
client = TechCorp::Client.new(api_key: 'sk_...')
status = client.status
```

All SDKs support:
- Automatic retries with exponential backoff
- Type safety (Python stubs, TypeScript definitions)
- Async/await patterns
- Streaming responses
$$, 'getting_started');

-- =============================================================================
-- CHANNEL CONFIGS (if not already seeded by schema)
-- =============================================================================

INSERT INTO channel_configs (channel, enabled, config, max_response_length) VALUES
    ('email', TRUE, '{"greeting": "Dear Customer", "closing": "Best regards, TechCorp AI Support Team"}', 2000),
    ('whatsapp', TRUE, '{"greeting": "", "closing": "Reply for more help"}', 1600),
    ('web_form', TRUE, '{"greeting": "", "closing": "Need more help? Reply to this message"}', 1000)
ON CONFLICT (channel) DO NOTHING;

-- =============================================================================
-- SAMPLE CUSTOMERS (for testing)
-- =============================================================================

INSERT INTO customers (email, phone, name, metadata) VALUES
    ('test@example.com', '+1234567890', 'Test User', '{"plan": "professional"}'),
    ('john.doe@company.com', NULL, 'John Doe', '{"plan": "enterprise", "company": "Acme Inc"}'),
    ('jane.smith@startup.io', NULL, 'Jane Smith', '{"plan": "starter", "company": "Startup.io"}')
ON CONFLICT (email) DO NOTHING;

-- =============================================================================
-- SAMPLE ESCALATION ASSIGNMENTS
-- =============================================================================

-- Define team members for escalations (optional, for routing)
-- This is a reference table that can be used by the escalation logic

CREATE TABLE IF NOT EXISTS escalation_assignees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,  -- 'support_agent', 'senior_agent', 'manager', 'sales', 'billing', 'legal'
    enabled BOOLEAN DEFAULT TRUE,
    max_concurrent_escalations INTEGER DEFAULT 10,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO escalation_assignees (email, name, role) VALUES
    ('support@techcorp.com', 'Support Team', 'support_agent'),
    ('senior-support@techcorp.com', 'Senior Support', 'senior_agent'),
    ('sales@techcorp.com', 'Sales Team', 'sales'),
    ('billing@techcorp.com', 'Billing Team', 'billing'),
    ('legal@techcorp.com', 'Legal Team', 'legal')
ON CONFLICT (email) DO NOTHING;
