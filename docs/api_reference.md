# API Reference

Verso Backend provides a REST API to access key resources such as Leads, Orders, and Products programmatically.

## Authentication

Authentication is performed via **Bearer Token**. You must include your API Key in the `Authorization` header of each request.

```http
Authorization: Bearer sk_live_...
```

To generate an API Key, navigate to the **Admin Dashboard > Manage API Keys** and click "Generate New Key".

## Base URL

Where `<your-domain>` is the host of your Verso instance:

```
https://<your-domain>/api/v1
```

## Endpoints

### Leads (Contact Form Submissions)
**GET** `/leads`

Retrieves a list of all contact form submissions.

**Scope Required:** `read:leads`

**Response:**
```json
[
  {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "message": "Interested in your services.",
    "submitted_at": "2023-10-27T10:00:00"
  },
  ...
]
```

### Orders
**GET** `/orders`

Retrieves a list of all orders.

**Scope Required:** `read:orders`

**Response:**
```json
[
  {
    "id": 101,
    "status": "paid",
    "total_amount": 2999,
    "currency": "usd",
    "created_at": "2023-10-27T12:30:00",
    "items_count": 2
  },
  ...
]
```

### Products
**GET** `/products`

Retrieves a list of all products.

**Scope Required:** `read:products`

**Response:**
```json
[
  {
    "id": 10,
    "name": "E-Book: 10 Tips",
    "price": 999,
    "inventory_count": 0,
    "is_digital": true
  },
  ...
]
```

## Errors

The API returns standard HTTP status codes.

- **401 Unauthorized**: Missing or invalid API key.
- **403 Forbidden**: Valid key but insufficient permissions (scope) for the endpoint.
- **404 Not Found**: Endpoint not found.
- **500 Internal Server Error**: Server processing error.

**Error Body:**
```json
{
  "error": "Error message details"
}
```
