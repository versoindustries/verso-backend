# Module Reference

Documentation for the 35+ helper modules in `app/modules/`.

## Table of Contents

- [Authentication & Authorization](#authentication--authorization)
- [File & Media](#file--media)
- [Communication](#communication)
- [E-commerce](#e-commerce)
- [Security](#security)
- [SEO & Indexing](#seo--indexing)
- [Utilities](#utilities)

---

## Authentication & Authorization

### auth_manager.py

Role-based access control decorators and authentication helpers.

**Key Functions:**

```python
from app.modules.auth_manager import require_role, require_any_role

# Require specific role
@login_required
@require_role('admin')
def admin_only_route():
    pass

# Require any of multiple roles
@login_required
@require_any_role('admin', 'manager', 'owner')
def management_route():
    pass
```

**Decorators:**

| Decorator | Description |
|-----------|-------------|
| `@require_role(role)` | Require exact role |
| `@require_any_role(*roles)` | Require any of listed roles |
| `@require_all_roles(*roles)` | Require all listed roles |
| `@owner_or_admin_required` | Allow resource owner or admin |

---

### mfa.py

Multi-factor authentication using TOTP (Time-based One-Time Passwords).

**Key Functions:**

```python
from app.modules.mfa import generate_totp_secret, verify_totp, generate_backup_codes

# Generate new TOTP secret for user
secret = generate_totp_secret()

# Verify code from authenticator app
is_valid = verify_totp(user.totp_secret, '123456')

# Generate backup codes
codes = generate_backup_codes(count=10)
```

---

## File & Media

### file_manager.py

File upload, validation, and storage management.

**Key Functions:**

```python
from app.modules.file_manager import (
    save_upload,
    delete_file,
    get_file_url,
    validate_file_type,
    compress_image
)

# Save uploaded file
file = request.files['image']
path = save_upload(file, folder='products', allowed_types=['image/jpeg', 'image/png'])

# Get public URL
url = get_file_url(path)

# Compress image to target size
compressed = compress_image(file, max_size_kb=500, quality=85)
```

**Configuration:**

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_UPLOAD_SIZE` | 16MB | Maximum file size |
| `ALLOWED_EXTENSIONS` | Images, PDFs | Permitted file types |
| `UPLOAD_FOLDER` | `app/static/uploads` | Storage location |

---

## Communication

### email_marketing.py

Email campaign management and sending.

**Key Functions:**

```python
from app.modules.email_marketing import (
    send_campaign,
    schedule_campaign,
    track_open,
    track_click
)

# Send campaign to audience
result = send_campaign(
    campaign_id=1,
    audience_id=3,
    template_id=5
)

# Schedule for later
schedule_campaign(
    campaign_id=1,
    send_at=datetime(2024, 12, 25, 9, 0)
)
```

---

### sms.py

SMS notifications and marketing (requires Twilio or similar).

**Key Functions:**

```python
from app.modules.sms import send_sms, check_consent

# Verify opt-in before sending
if check_consent(phone_number):
    send_sms(
        to=phone_number,
        message="Your order has shipped!"
    )
```

---

## E-commerce

### ecommerce.py

Cart calculations, pricing, and order processing.

**Key Functions:**

```python
from app.modules.ecommerce import (
    calculate_cart_total,
    apply_discount,
    calculate_tax,
    calculate_shipping
)

# Calculate full cart with discount and tax
cart_total = calculate_cart_total(cart_items)
discount = apply_discount(cart_total, discount_code)
tax = calculate_tax(cart_total - discount, tax_rate)
shipping = calculate_shipping(cart_items, destination)

final_total = cart_total - discount + tax + shipping
```

---

### inventory.py

Stock management and low-stock alerts.

**Key Functions:**

```python
from app.modules.inventory import (
    reserve_stock,
    release_stock,
    check_availability,
    get_low_stock_products
)

# Reserve stock during checkout
if check_availability(product_id, quantity):
    reserve_stock(product_id, quantity, order_id)

# Get products needing reorder
low_stock = get_low_stock_products(threshold=10)
```

---

## Security

### security.py

Security utilities and middleware.

**Key Functions:**

```python
from app.modules.security import (
    sanitize_html,
    generate_secure_token,
    hash_password,
    verify_password,
    rate_limit
)

# Sanitize user-provided HTML
clean_html = sanitize_html(user_input, allowed_tags=['p', 'strong', 'em'])

# Generate secure random token
token = generate_secure_token(length=32)

# Rate limiting decorator
@rate_limit(requests=100, window=60)  # 100 per minute
def api_endpoint():
    pass
```

---

### security_headers.py

HTTP security headers middleware.

**Headers Applied:**

| Header | Value |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `SAMEORIGIN` |
| `X-XSS-Protection` | `1; mode=block` |
| `Strict-Transport-Security` | `max-age=31536000` |
| `Content-Security-Policy` | Configured per environment |

---

### csrf.py

CSRF protection utilities.

```python
from app.modules.csrf import generate_csrf_token, validate_csrf_token

# In form template
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

# Validate in route
if not validate_csrf_token(request.form.get('csrf_token')):
    abort(403)
```

---

## SEO & Indexing

### indexing.py

Sitemap generation and SEO helpers.

**Key Functions:**

```python
from app.modules.indexing import (
    generate_sitemap,
    generate_json_ld,
    get_meta_tags
)

# Generate sitemap.xml
sitemap_xml = generate_sitemap(include_blog=True, include_products=True)

# Generate JSON-LD structured data
json_ld = generate_json_ld(
    type='Product',
    name=product.name,
    price=product.price,
    description=product.description
)
```

---

### seo.py

SEO analysis and optimization.

**Key Functions:**

```python
from app.modules.seo import (
    analyze_page_seo,
    generate_meta_description,
    check_duplicate_content
)

# Analyze page SEO score
score = analyze_page_seo(
    title=page.title,
    description=page.meta_description,
    content=page.content,
    url=page.url
)
```

---

## Utilities

### locations.py

Business location and timezone management.

**Key Functions:**

```python
from app.modules.locations import (
    get_hq_location,
    get_business_hours,
    is_open_now,
    get_timezone
)

# Get headquarters location
hq = get_hq_location()
print(hq.address, hq.city, hq.state)

# Check if currently open
if is_open_now():
    print("We're open!")
```

---

### roles.py

Role seeding and management.

**Flask CLI Commands:**

```bash
# Create default roles
flask create-roles

# This creates: admin, user, commercial, blogger, employee, owner, manager, marketing
```

---

### cache.py

Caching utilities.

**Key Functions:**

```python
from app.modules.cache import cached, invalidate_cache

# Cache function result
@cached(timeout=300, key='products_list')
def get_all_products():
    return Product.query.all()

# Invalidate when data changes
invalidate_cache('products_list')
```

---

### task_queue.py

Background task management.

**Key Functions:**

```python
from app.modules.task_queue import enqueue_task, get_task_status

# Enqueue background task
task_id = enqueue_task(
    name='send_email',
    payload={'to': 'user@example.com', 'template': 'welcome'}
)

# Check status
status = get_task_status(task_id)  # 'pending', 'running', 'completed', 'failed'
```

---

## Module Index

| Module | Purpose |
|--------|---------|
| `auth_manager.py` | RBAC decorators |
| `cache.py` | Caching utilities |
| `csrf.py` | CSRF protection |
| `ecommerce.py` | Cart and pricing |
| `email_marketing.py` | Email campaigns |
| `file_manager.py` | File uploads |
| `indexing.py` | Sitemaps and SEO |
| `inventory.py` | Stock management |
| `locations.py` | Business locations |
| `mfa.py` | Multi-factor auth |
| `roles.py` | Role management |
| `security.py` | Security utilities |
| `security_headers.py` | HTTP headers |
| `seo.py` | SEO analysis |
| `sms.py` | SMS notifications |
| `task_queue.py` | Background tasks |

---

*Last Updated: December 2024*
