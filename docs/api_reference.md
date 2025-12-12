# API Reference

Verso-Backend provides a comprehensive REST API for programmatic access to leads, orders, products, appointments, and webhooks.

## Table of Contents

- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Pagination](#pagination)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
  - [Leads](#leads)
  - [Orders](#orders)
  - [Products](#products)
  - [Appointments](#appointments)
  - [Webhooks](#webhooks)

---

## Authentication

All API endpoints require **Bearer Token** authentication. Include your API key in the `Authorization` header:

```http
Authorization: Bearer sk_live_your_api_key_here
```

### Generating an API Key

1. Navigate to **Admin Dashboard → Settings → API Keys**
2. Click **Generate New Key**
3. Select the required scopes (permissions)
4. Copy and securely store the key (it won't be shown again)

### API Key Scopes

| Scope | Permission |
|-------|------------|
| `read:leads` | View contact form submissions |
| `write:leads` | Create and update leads |
| `read:orders` | View orders |
| `write:orders` | Update order status |
| `read:products` | View product catalog |
| `write:products` | Create and update products |
| `read:appointments` | View appointments |
| `write:appointments` | Create and update appointments |
| `manage:webhooks` | Configure outbound webhooks |

---

## Base URL

```
https://your-domain.com/api/v1
```

Development:
```
http://localhost:5000/api/v1
```

---

## Rate Limiting

API requests are rate limited to prevent abuse:

| Operation Type | Limit |
|----------------|-------|
| Read operations (GET) | 100 requests/minute |
| Write operations (POST, PATCH, DELETE) | 30 requests/minute |

Rate limit information is included in response headers:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |

**Example Response Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702345678
```

When rate limited, the API returns `429 Too Many Requests`.

---

## Pagination

List endpoints support pagination via query parameters:

| Parameter | Default | Maximum | Description |
|-----------|---------|---------|-------------|
| `page` | 1 | - | Page number (1-indexed) |
| `per_page` | 25 | 100 | Items per page |

**Example Request:**
```bash
curl "https://your-domain.com/api/v1/products?page=2&per_page=50" \
  -H "Authorization: Bearer sk_live_..."
```

**Paginated Response Format:**
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 50,
    "total": 230,
    "pages": 5
  }
}
```

---

## Error Handling

The API uses standard HTTP status codes and returns errors in a consistent format.

### Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request - Invalid parameters |
| `401` | Unauthorized - Missing or invalid API key |
| `403` | Forbidden - Valid key but insufficient scope |
| `404` | Not Found - Resource doesn't exist |
| `422` | Unprocessable Entity - Validation error |
| `429` | Too Many Requests - Rate limit exceeded |
| `500` | Internal Server Error |

### Error Response Format

```json
{
  "error": "Error message description",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional context"
  }
}
```

**Example Error:**
```json
{
  "error": "Lead not found",
  "code": "NOT_FOUND"
}
```

---

## Endpoints

### Leads

Contact form submissions and CRM lead management.

#### List Leads

```http
GET /api/v1/leads
```

**Scope Required:** `read:leads`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `per_page` | integer | Items per page (max 100) |
| `status` | string | Filter by status |
| `sort` | string | Sort field (default: `submitted_at`) |
| `order` | string | `asc` or `desc` (default: `desc`) |
| `created_after` | datetime | Filter by creation date |
| `created_before` | datetime | Filter by creation date |

**Example Request:**
```bash
curl "https://your-domain.com/api/v1/leads?status=New&per_page=10" \
  -H "Authorization: Bearer sk_live_..."
```

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "phone": "+1-555-123-4567",
      "message": "Interested in your services",
      "status": "New",
      "source": "website",
      "notes": null,
      "tags": ["enterprise", "urgent"],
      "submitted_at": "2024-12-01T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 45,
    "pages": 5
  }
}
```

---

#### Get Lead

```http
GET /api/v1/leads/{id}
```

**Scope Required:** `read:leads`

**Example Request:**
```bash
curl "https://your-domain.com/api/v1/leads/1" \
  -H "Authorization: Bearer sk_live_..."
```

**Response:**
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+1-555-123-4567",
  "message": "Interested in your services",
  "status": "New",
  "source": "website",
  "notes": null,
  "tags": ["enterprise"],
  "submitted_at": "2024-12-01T10:30:00Z"
}
```

---

#### Create Lead

```http
POST /api/v1/leads
```

**Scope Required:** `write:leads`

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `first_name` | string | Yes | First name |
| `last_name` | string | Yes | Last name |
| `email` | string | Yes | Email address |
| `phone` | string | Yes | Phone number |
| `message` | string | Yes | Lead message/inquiry |
| `status` | string | No | Lead status (default: "New") |
| `source` | string | No | Lead source (default: "api") |
| `notes` | string | No | Internal notes |
| `tags` | array | No | Array of tag strings |

**Example Request:**
```bash
curl -X POST "https://your-domain.com/api/v1/leads" \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com",
    "phone": "+1-555-987-6543",
    "message": "Looking for enterprise pricing",
    "tags": ["enterprise", "priority"]
  }'
```

**Response (201 Created):**
```json
{
  "id": 46,
  "message": "Lead created successfully"
}
```

---

#### Update Lead

```http
PATCH /api/v1/leads/{id}
```

**Scope Required:** `write:leads`

Only include fields you want to update.

**Example Request:**
```bash
curl -X PATCH "https://your-domain.com/api/v1/leads/1" \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "status": "Contacted",
    "notes": "Called on 12/5, follow up scheduled"
  }'
```

**Response:**
```json
{
  "id": 1,
  "message": "Lead updated successfully"
}
```

---

### Orders

E-commerce order management.

#### List Orders

```http
GET /api/v1/orders
```

**Scope Required:** `read:orders`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (pending, paid, shipped, etc.) |
| `created_after` | datetime | Filter by creation date |
| `created_before` | datetime | Filter by creation date |
| `page` | integer | Page number |
| `per_page` | integer | Items per page |

**Example Request:**
```bash
curl "https://your-domain.com/api/v1/orders?status=paid" \
  -H "Authorization: Bearer sk_live_..."
```

**Response:**
```json
{
  "data": [
    {
      "id": 101,
      "order_number": "ORD-2024-0101",
      "status": "paid",
      "total_amount": 2999,
      "currency": "usd",
      "email": "customer@example.com",
      "tracking_number": null,
      "created_at": "2024-12-01T12:30:00Z",
      "items_count": 2
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 150,
    "pages": 6
  }
}
```

---

#### Get Order

```http
GET /api/v1/orders/{id}
```

**Scope Required:** `read:orders`

Returns order details including line items.

**Response:**
```json
{
  "id": 101,
  "order_number": "ORD-2024-0101",
  "status": "paid",
  "total_amount": 2999,
  "subtotal_amount": 2999,
  "discount_amount": 0,
  "tax_amount": 0,
  "shipping_amount": 0,
  "currency": "usd",
  "email": "customer@example.com",
  "tracking_number": null,
  "shipping_address": {
    "line1": "123 Main St",
    "city": "Springfield",
    "state": "IL",
    "postal_code": "62701",
    "country": "US"
  },
  "items": [
    {
      "id": 1,
      "product_id": 10,
      "product_name": "Premium Widget",
      "quantity": 2,
      "unit_price": 1499
    }
  ],
  "created_at": "2024-12-01T12:30:00Z"
}
```

---

#### Update Order

```http
PATCH /api/v1/orders/{id}
```

**Scope Required:** `write:orders`

Update order status or fulfillment details.

**Request Body:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Order status |
| `tracking_number` | string | Shipping tracking number |
| `fulfillment_status` | string | Fulfillment status |

**Example Request:**
```bash
curl -X PATCH "https://your-domain.com/api/v1/orders/101" \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "status": "shipped",
    "tracking_number": "1Z999AA10123456784"
  }'
```

---

### Products

Product catalog management.

#### List Products

```http
GET /api/v1/products
```

**Scope Required:** `read:products`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `is_digital` | boolean | Filter digital/physical products |
| `in_stock` | boolean | Filter by stock availability |
| `category_id` | integer | Filter by category |
| `page` | integer | Page number |
| `per_page` | integer | Items per page |

**Response:**
```json
{
  "data": [
    {
      "id": 10,
      "name": "Premium Widget",
      "slug": "premium-widget",
      "description": "A high-quality widget for professionals",
      "price": 4999,
      "compare_at_price": null,
      "inventory_count": 50,
      "is_digital": false,
      "is_active": true,
      "category_id": 3
    }
  ],
  "pagination": {...}
}
```

---

#### Get Product

```http
GET /api/v1/products/{id}
```

**Scope Required:** `read:products`

---

#### Create Product

```http
POST /api/v1/products
```

**Scope Required:** `write:products`

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Product name |
| `price` | integer | Yes | Price in cents |
| `description` | string | No | Product description |
| `sku` | string | No | Stock keeping unit |
| `inventory_count` | integer | No | Stock quantity (default: 0) |
| `is_digital` | boolean | No | Digital product flag |
| `category_id` | integer | No | Category ID |

**Example Request:**
```bash
curl -X POST "https://your-domain.com/api/v1/products" \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Widget",
    "price": 2999,
    "description": "Our latest widget model",
    "inventory_count": 100
  }'
```

---

#### Update Product

```http
PATCH /api/v1/products/{id}
```

**Scope Required:** `write:products`

---

### Appointments

Scheduling and booking management.

#### List Appointments

```http
GET /api/v1/appointments
```

**Scope Required:** `read:appointments`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status |
| `estimator_id` | integer | Filter by assigned estimator |
| `date_from` | date | Start of date range |
| `date_to` | date | End of date range |

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "phone": "+1-555-123-4567",
      "scheduled_time": "2024-12-10T14:00:00Z",
      "duration_minutes": 60,
      "status": "scheduled",
      "service_id": 1,
      "estimator_id": 2,
      "notes": null
    }
  ],
  "pagination": {...}
}
```

---

### Webhooks

Configure outbound webhooks to receive notifications about events.

#### List Webhooks

```http
GET /api/v1/webhooks
```

**Scope Required:** `manage:webhooks`

---

#### Create Webhook

```http
POST /api/v1/webhooks
```

**Scope Required:** `manage:webhooks`

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Webhook name |
| `url` | string | Yes | Endpoint URL |
| `events` | array | Yes | Events to subscribe to |
| `secret` | string | No | HMAC signing secret |
| `is_active` | boolean | No | Active status (default: true) |

**Available Events:**
- `lead.created` - New lead submitted
- `lead.updated` - Lead status changed
- `order.created` - New order placed
- `order.updated` - Order status changed
- `product.created` - New product added
- `appointment.created` - New appointment booked
- `appointment.updated` - Appointment changed

**Example Request:**
```bash
curl -X POST "https://your-domain.com/api/v1/webhooks" \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Order Notifications",
    "url": "https://your-server.com/webhooks/verso",
    "events": ["order.created", "order.updated"],
    "secret": "whsec_your_signing_secret"
  }'
```

---

## Code Examples

### Python

```python
import requests

API_KEY = "sk_live_your_api_key"
BASE_URL = "https://your-domain.com/api/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Get all leads
response = requests.get(f"{BASE_URL}/leads", headers=headers)
leads = response.json()["data"]

# Create a lead
new_lead = {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com",
    "phone": "+1-555-987-6543",
    "message": "API test lead"
}
response = requests.post(f"{BASE_URL}/leads", json=new_lead, headers=headers)
print(response.json())
```

### JavaScript (Node.js)

```javascript
const API_KEY = 'sk_live_your_api_key';
const BASE_URL = 'https://your-domain.com/api/v1';

const headers = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type': 'application/json'
};

// Get all products
async function getProducts() {
  const response = await fetch(`${BASE_URL}/products`, { headers });
  const data = await response.json();
  return data.data;
}

// Update order status
async function updateOrder(orderId, status, trackingNumber) {
  const response = await fetch(`${BASE_URL}/orders/${orderId}`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify({ status, tracking_number: trackingNumber })
  });
  return response.json();
}
```

---

## OpenAPI Specification

For a complete, machine-readable API specification, see [openapi.yaml](openapi.yaml).

Import into tools like Postman, Swagger UI, or Insomnia for interactive API exploration.

---

*Last Updated: December 2024*
