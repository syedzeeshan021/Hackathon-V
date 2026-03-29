# TechCorp SaaS - Product Documentation

**Version:** 2026.1
**Last Updated:** 2026-03-17

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [API Reference](#api-reference)
4. [Rate Limiting](#rate-limiting)
5. [Webhooks](#webhooks)
6. [Analytics](#analytics)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

---

## Getting Started

### Creating an Account

1. Visit [https://dashboard.techcorp.com/signup](https://dashboard.techcorp.com/signup)
2. Enter your email and create a password
3. Verify your email address
4. Complete your profile setup

### Finding Your API Keys

1. Log in to your dashboard at [https://dashboard.techcorp.com](https://dashboard.techcorp.com)
2. Navigate to **Settings** → **API Keys** in the left sidebar
3. Click **Generate New Key** if you don't have one
4. Copy and securely store your API key (it won't be shown again)

**Important:** Never share your API key or commit it to version control.

### Your First API Call

```bash
curl -X GET "https://api.techcorp.com/v1/status" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Expected response:
```json
{
  "status": "operational",
  "version": "1.0.0"
}
```

### Quick Start Guide

1. **Install the SDK** (optional):
   ```bash
   # Python
   pip install techcorp-sdk

   # Node.js
   npm install @techcorp/sdk
   ```

2. **Make your first request**:
   ```python
   from techcorp import Client

   client = Client(api_key="your_api_key")
   status = client.get_status()
   print(status)
   ```

3. **Explore the dashboard** - Check out analytics, manage APIs, and configure settings.

---

## Authentication

### Overview

TechCorp API uses Bearer token authentication. Include your API key in the Authorization header:

```
Authorization: Bearer YOUR_API_KEY
```

### API Key Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Publishable Key** | Prefix: `pk_` | Client-side applications, browser apps |
| **Secret Key** | Prefix: `sk_` | Server-side applications, never expose to clients |

### OAuth2 Authentication

For applications that access user data on behalf of users:

1. **Register your application** in the dashboard under Settings → OAuth Apps
2. **Redirect users** to the authorization URL:
   ```
   https://dashboard.techcorp.com/oauth/authorize?
     client_id=YOUR_CLIENT_ID&
     redirect_uri=YOUR_REDIRECT_URI&
     response_type=code&
     scope=read write
   ```
3. **Exchange the code** for an access token:
   ```bash
   curl -X POST "https://api.techcorp.com/v1/oauth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=authorization_code" \
     -d "code=AUTH_CODE" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "redirect_uri=YOUR_REDIRECT_URI"
   ```

### Common Authentication Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Missing or invalid API key | Check your API key in the header |
| `403 Forbidden` | Valid key but insufficient permissions | Verify your plan includes this feature |
| `invalid_redirect_uri` | OAuth redirect URI mismatch | Add the exact URI in OAuth App settings |

---

## API Reference

### Base URL

```
https://api.techcorp.com/v1
```

### Endpoints

#### GET /status

Check API operational status.

**Response:**
```json
{
  "status": "operational",
  "version": "1.0.0",
  "timestamp": "2026-03-17T10:30:00Z"
}
```

#### GET /apis

List all APIs in your account.

**Response:**
```json
{
  "apis": [
    {
      "id": "api_abc123",
      "name": "My API",
      "status": "active",
      "created_at": "2026-01-15T08:00:00Z"
    }
  ]
}
```

#### POST /apis

Create a new API.

**Request:**
```json
{
  "name": "My New API",
  "description": "API for my application"
}
```

#### GET /apis/{api_id}

Get details for a specific API.

#### PUT /apis/{api_id}

Update an API configuration.

#### DELETE /apis/{api_id}

Delete an API.

#### GET /apis/{api_id}/keys

List API keys for a specific API.

#### POST /apis/{api_id}/keys

Create a new API key.

#### DELETE /apis/{api_id}/keys/{key_id}

Revoke an API key.

#### GET /analytics

Get usage analytics for your APIs.

**Query Parameters:**
- `start_date` - Start of date range (ISO 8601)
- `end_date` - End of date range (ISO 8601)
- `api_id` - Filter by specific API (optional)

**Response:**
```json
{
  "total_requests": 150000,
  "successful_requests": 148500,
  "failed_requests": 1500,
  "avg_latency_ms": 45,
  "by_endpoint": [...]
}
```

---

## Rate Limiting

### Overview

Rate limiting protects the API from abuse and ensures fair usage for all customers.

### Default Limits by Plan

| Plan | Requests/Minute | Requests/Day | Burst Limit |
|------|-----------------|--------------|-------------|
| Starter | 100 | 100,000 | 20 |
| Professional | 500 | 1,000,000 | 100 |
| Enterprise | Custom | Custom | Custom |

### Rate Limit Headers

Every response includes these headers:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed |
| `X-RateLimit-Remaining` | Requests remaining in window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |

### Handling Rate Limits

When you exceed the rate limit, you'll receive a `429 Too Many Requests` response:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please retry after 60 seconds.",
  "retry_after": 60
}
```

**Best Practices:**
1. Check rate limit headers before making requests
2. Implement exponential backoff when rate limited
3. Cache responses when possible
4. Use webhooks instead of polling for real-time updates

### Configuring Rate Limits

1. Go to **Dashboard** → **API Settings** → **Rate Limiting**
2. Toggle **Enable Rate Limiting** to ON
3. Set your desired requests per minute
4. Click **Save Changes**

---

## Webhooks

### Overview

Webhooks let you receive real-time notifications when events occur in your account.

### Supported Events

| Event | Description |
|-------|-------------|
| `api.created` | New API created |
| `api.deleted` | API deleted |
| `key.created` | New API key generated |
| `key.revoked` | API key revoked |
| `rate_limit.exceeded` | Rate limit exceeded |
| `error.spike` | Unusual error rate detected |

### Setting Up Webhooks

1. Go to **Dashboard** → **Settings** → **Webhooks**
2. Click **Add Endpoint**
3. Enter your webhook URL (must be HTTPS)
4. Select events to subscribe to
5. Click **Save**

### Webhook Payload

```json
{
  "id": "evt_abc123",
  "type": "api.created",
  "created_at": "2026-03-17T10:30:00Z",
  "data": {
    "api": {
      "id": "api_xyz789",
      "name": "New API",
      "status": "active"
    }
  }
}
```

### Verifying Webhooks

TechCorp signs all webhook payloads. Verify the signature:

```python
from techcorp.webhooks import verify_signature

def webhook_handler(request):
    payload = request.body
    signature = request.headers.get('X-TechCorp-Signature')

    if verify_signature(payload, signature, webhook_secret):
        # Process webhook
        return {"status": "ok"}
    else:
        return {"status": "invalid"}, 401
```

### Troubleshooting Webhooks

| Issue | Solution |
|-------|----------|
| Not receiving events | Check firewall, verify HTTPS, check webhook logs |
| Signature verification fails | Ensure you're using the correct webhook secret |
| Duplicate events | Implement idempotency using event ID |

---

## Analytics

### Dashboard Analytics

View real-time metrics in your dashboard:

- **Request Volume** - Total requests over time
- **Error Rates** - 4xx and 5xx errors
- **Latency** - Response time percentiles (p50, p95, p99)
- **Top Endpoints** - Most called endpoints
- **Geographic Distribution** - Requests by region

### API Analytics Endpoint

```bash
curl -X GET "https://api.techcorp.com/v1/analytics?start_date=2026-03-01&end_date=2026-03-17" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Custom Metrics

Create custom dashboards with the Metrics API:

```bash
curl -X POST "https://api.techcorp.com/v1/metrics" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Custom Metric",
    "query": "sum(requests) by endpoint",
    "interval": "1h"
  }'
```

---

## Troubleshooting

### Common Issues

#### 1. Getting 401 Unauthorized

**Causes:**
- API key is missing from the request
- API key is expired or revoked
- Using wrong key type (publishable vs secret)

**Solutions:**
1. Verify the Authorization header is present
2. Check that your API key is active in the dashboard
3. Ensure you're using a secret key for server-side requests

#### 2. Getting 403 Forbidden

**Causes:**
- API key is valid but lacks permissions
- Feature not included in your plan

**Solutions:**
1. Check your plan features in the dashboard
2. Verify the endpoint is available in your plan
3. Upgrade your plan if needed

#### 3. Getting 429 Too Many Requests

**Causes:**
- Exceeded rate limit

**Solutions:**
1. Implement request throttling
2. Use exponential backoff
3. Consider upgrading your plan

#### 4. Webhook Not Working

**Causes:**
- URL is not accessible
- SSL certificate issues
- Firewall blocking requests

**Solutions:**
1. Test your webhook endpoint manually
2. Ensure HTTPS with valid certificate
3. Check server logs for incoming requests

#### 5. High Latency

**Causes:**
- Network issues
- API server overload
- Large payload sizes

**Solutions:**
1. Check status.techcorp.com for outages
2. Use compression for large payloads
3. Implement caching where appropriate

### Getting Help

If you can't resolve an issue:

1. Check our [Status Page](https://status.techcorp.com)
2. Search the [Community Forum](https://community.techcorp.com)
3. Contact support via the web form or email

---

## FAQ

### General Questions

**Q: Is there a free tier?**
A: Yes, we offer a 14-day free trial with full access to all features. No credit card required.

**Q: Can I change my plan later?**
A: Yes, you can upgrade or downgrade your plan at any time from the dashboard.

**Q: Do you offer enterprise pricing?**
A: Yes, contact our sales team for custom enterprise solutions.

### Technical Questions

**Q: What SDKs do you offer?**
A: We officially support Python and JavaScript/TypeScript SDKs. Community SDKs are available for other languages.

**Q: Do you have a sandbox environment?**
A: Yes, use `https://sandbox-api.techcorp.com` for testing. Sandbox data is separate from production.

**Q: How do I migrate from another API platform?**
A: We offer migration assistance. Contact support for a personalized migration plan.

### Billing Questions

**Q: How is usage calculated?**
A: Usage is calculated based on the number of API requests. Each endpoint call counts as one request.

**Q: Can I prepay for annual billing?**
A: Yes, annual billing includes a 20% discount. Contact sales for details.

---

## Support

### Contact Methods

| Method | Availability | Response Time |
|--------|--------------|---------------|
| Web Form | 24/7 | < 5 minutes (AI), < 1 hour (human) |
| Email | 24/7 | < 4 hours |
| Community Forum | 24/7 | Varies |
| Enterprise Support | 24/7 | < 30 minutes |

### Status Page

Check [status.techcorp.com](https://status.techcorp.com) for:
- Current system status
- Scheduled maintenance
- Incident history

### Documentation Updates

This documentation is updated regularly. Check the version number at the top of this document.
