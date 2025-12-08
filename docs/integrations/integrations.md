# Verso Integration Marketplace

A directory of supported integrations and guides for connecting Verso to external services.

## Overview

Verso provides a REST API and outbound webhooks for integration with third-party services. This marketplace lists verified integrations with setup guides.

---

## Official Integrations

### Payment Processing

| Integration | Status | Description |
|-------------|--------|-------------|
| **Stripe** | ✅ Built-in | Payment processing, subscriptions, invoicing |

Stripe is natively integrated. Configure via environment variables:
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`

---

### CRM & Marketing

| Integration | Status | Guide |
|-------------|--------|-------|
| **Zapier** | ✅ Documented | [zapier-integration.md](./zapier-integration.md) |
| **Make (Integromat)** | 🔧 API Compatible | Use REST API endpoints |
| **n8n** | 🔧 API Compatible | Self-hosted automation |

---

### Communication

| Integration | Method | Notes |
|-------------|--------|-------|
| **Email (SMTP)** | ✅ Built-in | Any SMTP provider (SendGrid, Mailgun, SES) |
| **Slack** | 🔧 Webhook | Create Slack webhook, configure in Verso webhooks |
| **Discord** | 🔧 Webhook | Similar to Slack setup |
| **Twilio** | 🔧 Custom | Use API + worker task for SMS |

#### Slack Integration Example

1. Create Slack Incoming Webhook at api.slack.com
2. In Verso Admin → Webhooks → New Webhook:
   - URL: Your Slack webhook URL
   - Events: `lead.created`
3. Leads will post to your Slack channel

---

### Calendar & Scheduling

| Integration | Method | Notes |
|-------------|--------|-------|
| **Google Calendar** | 📅 ICS Export | Subscribe to staff ICS feeds |
| **Outlook** | 📅 ICS Export | Subscribe to ICS feed URLs |
| **Calendly** | 🔧 API | Webhook → POST /api/v1/leads |

#### ICS Calendar Sync

Each staff member has an ICS feed URL:
```
https://your-verso.com/calendar/staff/{user_id}/feed.ics
```

Subscribe to this URL in Google Calendar or Outlook for read-only sync.

---

### E-Commerce

| Integration | Method | Notes |
|-------------|--------|-------|
| **Stripe** | ✅ Built-in | Orders, payments, refunds |
| **ShipStation** | 🔧 Webhook | order.updated → ShipStation API |
| **EasyPost** | 🔧 Custom | Integrate via worker tasks |

#### Shipping Integration Pattern

1. Configure webhook for `order.updated` events
2. When `fulfillment_status` = `processing`:
   - Call shipping API to create label
   - Update order with tracking via PATCH /api/v1/orders/:id

---

### Analytics & Reporting

| Integration | Method | Notes |
|-------------|--------|-------|
| **Google Analytics 4** | ✅ Built-in | Configure GA4 ID in Business Config |
| **Segment** | 🔧 Webhook | Forward events to Segment |
| **Custom BI** | 🔧 API | Use read endpoints for data extraction |

---

## Building Custom Integrations

### REST API

Full REST API documentation: `/api/docs`

Key endpoints:
- `GET /api/v1/leads` - List/filter leads
- `POST /api/v1/leads` - Create lead
- `GET /api/v1/orders` - List/filter orders
- `PATCH /api/v1/orders/:id` - Update order
- `GET /api/v1/products` - Product catalog
- `POST /api/v1/products` - Create product

### Webhooks

Outbound webhooks fire on events:
- `lead.created`, `lead.updated`
- `order.created`, `order.updated`
- `product.created`

Features:
- HMAC-SHA256 signature verification
- Automatic retry with exponential backoff
- Failure tracking and auto-disable

### Authentication

- Bearer token authentication
- Scope-based permissions
- Rate limiting: 100 req/min per key

---

## Integration Request

Need an integration not listed here?

1. Check if API + Webhooks can support your use case
2. For custom integrations, extend worker tasks
3. Community contributions welcome via PR

---

## Status Legend

| Icon | Meaning |
|------|---------|
| ✅ | Built-in / Officially Supported |
| 📅 | Scheduled / Planned |
| 🔧 | Works via API/Webhooks (DIY) |
