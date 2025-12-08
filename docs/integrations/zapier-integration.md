# Verso API - Zapier Integration Guide

This guide explains how to connect Verso to Zapier for workflow automation.

## Overview

Verso's REST API enables Zapier integration through:
- **Triggers**: Webhooks that fire when events occur (lead created, order updated)
- **Actions**: API endpoints to create/update data in Verso

## Prerequisites

1. Admin access to your Verso installation
2. A Zapier account (free tier works for basic automations)
3. A Verso API key with appropriate scopes

## Creating an API Key

1. Log in to Verso Admin panel
2. Navigate to **Admin → API Keys → New API Key**
3. Name your key (e.g., "Zapier Integration")
4. Select scopes:
   - `read:leads` - Read lead data
   - `write:leads` - Create/update leads
   - `read:orders` - Read order data
   - `write:orders` - Update order status
   - `read:products` - Access product catalog
5. Click **Create Key**
6. **Copy the key immediately** - it won't be shown again!

## Setting Up Webhooks (Triggers)

Webhooks allow Zapier to receive data when events occur in Verso.

### Available Events

| Event | Description | Payload |
|-------|-------------|---------|
| `lead.created` | New lead submitted | id, first_name, last_name, email, source |
| `lead.updated` | Lead status changed | id, status |
| `order.created` | New order placed | id, total_amount, customer_email |
| `order.updated` | Order status changed | id, old_status, new_status, fulfillment_status |
| `product.created` | New product added | id, name, price |

### Configure Webhook in Verso

1. Go to **Admin → API → Webhooks → New Webhook**
2. Configure:
   - **Name**: "Zapier - Lead Events"
   - **URL**: Your Zapier webhook URL (from Webhooks by Zapier trigger)
   - **Events**: Select events you want to receive
3. Save the webhook - note the **Secret** for signature verification

### Zapier Setup (Trigger)

1. Create a new Zap
2. Choose **Webhooks by Zapier** as trigger
3. Select **Catch Hook**
4. Copy the webhook URL
5. Paste into Verso webhook configuration
6. Test by creating a lead in Verso
7. Zapier should receive the event!

### Verifying Webhook Signatures

For security, verify the `X-Webhook-Signature` header:

```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Remove 'sha256=' prefix
    provided = signature.replace('sha256=', '')
    return hmac.compare_digest(expected, provided)
```

## API Actions

Use Zapier's **Webhooks by Zapier** action to call Verso API endpoints.

### Create a Lead

**Zap Action**: Webhooks by Zapier → POST

- **URL**: `https://your-verso.com/api/v1/leads`
- **Payload Type**: JSON
- **Headers**:
  - `Authorization`: `Bearer YOUR_API_KEY`
  - `Content-Type`: `application/json`
- **Data**:
```json
{
  "first_name": "{{Name First}}",
  "last_name": "{{Name Last}}",
  "email": "{{Email}}",
  "phone": "{{Phone}}",
  "message": "Lead from Zapier",
  "source": "zapier"
}
```

### Update Order Status

**Zap Action**: Webhooks by Zapier → PATCH

- **URL**: `https://your-verso.com/api/v1/orders/{{order_id}}`
- **Headers**:
  - `Authorization`: `Bearer YOUR_API_KEY`
- **Data**:
```json
{
  "fulfillment_status": "shipped",
  "tracking_number": "{{tracking_number}}"
}
```

## Common Zap Examples

### 1. Lead → Google Sheets
**Trigger**: Webhook (lead.created)
**Action**: Google Sheets → Create Row

### 2. Lead → Email Notification
**Trigger**: Webhook (lead.created)  
**Action**: Gmail → Send Email

### 3. Typeform → Verso Lead
**Trigger**: Typeform → New Entry
**Action**: Webhooks → POST to /api/v1/leads

### 4. Shopify Order → Verso Order Update
**Trigger**: Shopify → New Order
**Action**: Webhooks → PATCH to /api/v1/orders/:id

### 5. Calendario Booking → Verso Lead
**Trigger**: Calendly → Invitee Created
**Action**: Webhooks → POST to /api/v1/leads

## Troubleshooting

### Webhook not receiving events
- Verify webhook is **Active** in Verso admin
- Check the webhook URL is accessible from internet
- Review webhook failure count in admin

### API returning 401
- Verify API key is active
- Check Authorization header format: `Bearer YOUR_KEY`

### API returning 403
- API key lacks required scope
- Add missing scope and try again

### API returning 400
- Check required fields are present
- Verify JSON is properly formatted

## Rate Limits

- API: 100 requests per minute per API key
- Webhooks: 10 retries with exponential backoff
- Webhooks disabled after 10 consecutive failures

## Security Best Practices

1. **Never share API keys** - Create separate keys for each integration
2. **Use minimal scopes** - Only grant permissions the integration needs
3. **Verify webhook signatures** - Prevent spoofed webhook calls
4. **Rotate keys periodically** - Delete unused keys regularly
5. **Monitor API usage** - Check last_used_at in API key list
