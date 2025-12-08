# Verso-Backend Architecture Overview

This document provides a comprehensive overview of the Verso-Backend system architecture, designed to help developers understand the codebase structure, data flow, and design decisions.

## System Overview

Verso-Backend is a **Sovereign Monolith**—a self-contained Flask application that provides a complete business operating system without relying on external SaaS dependencies (except Stripe for payments).

```mermaid
graph TB
    subgraph "Client Layer"
        Browser["Web Browser"]
        Mobile["Mobile/PWA"]
        API["API Clients"]
    end
    
    subgraph "Application Layer"
        Flask["Flask App Factory"]
        Blueprints["Route Blueprints"]
        Templates["Jinja2 Templates"]
        Static["Static Assets"]
    end
    
    subgraph "Business Logic"
        Modules["Helper Modules"]
        Forms["WTForms"]
        Workers["Background Workers"]
    end
    
    subgraph "Data Layer"
        SQLAlchemy["SQLAlchemy ORM"]
        DB["PostgreSQL/SQLite"]
        Redis["Redis Cache"]
    end
    
    Browser --> Flask
    Mobile --> Flask
    API --> Flask
    Flask --> Blueprints
    Blueprints --> Templates
    Blueprints --> Modules
    Modules --> SQLAlchemy
    SQLAlchemy --> DB
    Modules --> Redis
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | Flask 2.3+ | Web application framework |
| **Database** | PostgreSQL / SQLite | Data persistence |
| **ORM** | SQLAlchemy 2.0 | Database abstraction |
| **Migrations** | Flask-Migrate (Alembic) | Schema versioning |
| **Authentication** | Flask-Login | Session management |
| **Forms** | WTForms + Flask-WTF | Input validation |
| **Templates** | Jinja2 | Server-side rendering |
| **Rich Text** | CKEditor 5 | Content editing |
| **Caching** | Flask-Caching + Redis | Performance optimization |
| **Email** | Flask-Mail | Transactional email |
| **i18n** | Flask-Babel | Internationalization |
| **Payments** | Stripe | Payment processing |
| **Frontend** | React (Islands) + HTMX | Interactive components |

## Directory Structure

```
verso-backend/
├── app/                          # Main application package
│   ├── __init__.py               # App factory (create_app)
│   ├── config.py                 # Configuration classes
│   ├── database.py               # Database initialization
│   ├── extensions.py             # Flask extensions
│   ├── models.py                 # SQLAlchemy models (4000+ lines)
│   ├── forms.py                  # WTForms definitions
│   ├── worker.py                 # Background task processor
│   │
│   ├── routes/                   # Blueprint modules (45 files)
│   │   ├── admin.py              # Admin dashboard & management
│   │   ├── api.py                # REST API endpoints
│   │   ├── auth.py               # Authentication routes
│   │   ├── blog.py               # Blog & CMS
│   │   ├── cart.py               # Shopping cart
│   │   ├── crm.py                # Lead management
│   │   ├── ecommerce.py          # Public shop routes
│   │   ├── ecommerce_admin.py    # E-commerce administration
│   │   ├── employee.py           # Employee portal
│   │   ├── messaging.py          # Internal messaging
│   │   └── ...                   # Additional route modules
│   │
│   ├── modules/                  # Business logic helpers (35 files)
│   │   ├── auth_manager.py       # RBAC decorators
│   │   ├── ecommerce.py          # Cart/order calculations
│   │   ├── email_marketing.py    # Campaign management
│   │   ├── security.py           # Security utilities
│   │   ├── mfa.py                # Multi-factor auth
│   │   └── ...                   # Additional modules
│   │
│   ├── templates/                # Jinja2 templates
│   │   ├── base.html             # Master template
│   │   ├── admin/                # Admin interface
│   │   ├── blog/                 # Blog templates
│   │   ├── shop/                 # E-commerce templates
│   │   └── ...                   # Additional template dirs
│   │
│   ├── static/                   # Static assets
│   │   ├── css/                  # Stylesheets
│   │   ├── js/                   # JavaScript
│   │   ├── src/                  # React/TypeScript source
│   │   └── images/               # Image assets
│   │
│   └── tests/                    # Test suite
│
├── migrations/                   # Alembic migrations
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── k8s/                          # Kubernetes manifests
└── helm/                         # Helm charts
```

## Application Factory Pattern

Verso uses Flask's application factory pattern for flexibility and testability:

```python
# app/__init__.py
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    babel.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.blog import blog_bp
    # ... additional blueprints
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(blog_bp, url_prefix='/blog')
    
    return app
```

## Blueprint Architecture

Routes are organized into domain-specific blueprints:

```mermaid
graph LR
    subgraph "Public Blueprints"
        main["main_routes"]
        auth["auth"]
        blog["blog"]
        shop["shop"]
        cart["cart"]
        booking["booking_api"]
    end
    
    subgraph "Admin Blueprints"
        admin["admin"]
        shop_admin["shop_admin"]
        ecomm_admin["ecommerce_admin"]
        forms_admin["forms_admin"]
        email_admin["email_admin"]
    end
    
    subgraph "API Blueprints"
        api["api"]
        api_docs["api_docs"]
        webhooks["webhooks"]
    end
    
    subgraph "Portal Blueprints"
        employee["employee"]
        user["user"]
        messaging["messaging"]
    end
```

### Blueprint Registration

| Blueprint | URL Prefix | Description |
|-----------|------------|-------------|
| `main_bp` | `/` | Public pages, contact, about |
| `auth_bp` | `/auth` | Login, register, password reset |
| `admin_bp` | `/admin` | Admin dashboard and management |
| `blog_bp` | `/blog` | Blog posts and content |
| `shop_bp` | `/shop` | Product catalog |
| `cart_bp` | `/cart` | Shopping cart operations |
| `api_bp` | `/api/v1` | REST API endpoints |
| `employee_bp` | `/employee` | Employee portal |
| `messaging_bp` | `/messaging` | Internal messaging |

## Data Model Overview

Verso has 80+ database models across multiple domains:

```mermaid
erDiagram
    User ||--o{ Order : places
    User ||--o{ Appointment : books
    User ||--o{ Post : authors
    User ||--o{ Lead : manages
    User }|--|| Role : has
    
    Product ||--o{ OrderItem : contains
    Product ||--o{ ProductVariant : has
    Product }o--|| Category : belongs_to
    Product ||--o{ ProductImage : has
    
    Order ||--|{ OrderItem : contains
    Order }o--o| Discount : applies
    Order }o--o| GiftCard : uses
    
    Appointment }o--|| Estimator : assigned_to
    Appointment }o--|| Service : for
    Appointment }o--|| AppointmentType : type
    
    Post }o--|| Category : in
    Post ||--o{ Comment : has
    Post ||--o{ PostRevision : versions
    
    Channel ||--o{ Message : contains
    Channel ||--o{ ChannelMember : has
    Message }o--|| User : sent_by
```

### Core Model Categories

| Category | Models | Description |
|----------|--------|-------------|
| **Identity** | User, Role, TOTPDevice, BackupCode | Authentication & authorization |
| **E-commerce** | Product, Order, Cart, Discount, GiftCard | Online store |
| **Content** | Post, Page, Category, Media | CMS functionality |
| **Scheduling** | Appointment, Availability, AppointmentType | Calendar & booking |
| **CRM** | Lead, ContactFormSubmission, Pipeline | Customer management |
| **Communication** | Channel, Message, EmailCampaign | Messaging & email |
| **Forms** | FormDefinition, FormSubmission, Survey | Data collection |
| **Analytics** | PageView, VisitorSession, Conversion | Tracking & reporting |

## Request/Response Flow

```mermaid
sequenceDiagram
    participant Client
    participant Flask
    participant Blueprint
    participant Module
    participant Model
    participant Database
    
    Client->>Flask: HTTP Request
    Flask->>Flask: Middleware (CSRF, Headers)
    Flask->>Blueprint: Route Handler
    Blueprint->>Module: Business Logic
    Module->>Model: Query/Mutate
    Model->>Database: SQL
    Database-->>Model: Result
    Model-->>Module: Objects
    Module-->>Blueprint: Data
    Blueprint->>Flask: Render Template
    Flask-->>Client: HTTP Response
```

## Authentication & Authorization

### Authentication Flow

```mermaid
flowchart TD
    A[User Submits Credentials] --> B{Valid?}
    B -->|No| C[Return Error]
    B -->|Yes| D{MFA Enabled?}
    D -->|No| E[Create Session]
    D -->|Yes| F[Request TOTP]
    F --> G{Valid TOTP?}
    G -->|No| C
    G -->|Yes| E
    E --> H[Set Session Cookie]
    H --> I[Redirect to Dashboard]
```

### Role-Based Access Control

```python
# app/modules/auth_manager.py
def require_role(*roles):
    """Decorator to require specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not any(current_user.has_role(role) for role in roles):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage in routes
@admin_bp.route('/users')
@login_required
@require_role('admin')
def list_users():
    ...
```

### Default Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full system access |
| `user` | Standard user access |
| `commercial` | Sales/CRM access |
| `blogger` | Content creation access |
| `employee` | Employee portal access |

## Background Task System

Verso uses a database-backed task queue for background processing:

```mermaid
flowchart LR
    subgraph "Task Creation"
        Route["Route Handler"]
        Task["Task Model"]
    end
    
    subgraph "Task Processing"
        Worker["Worker Process"]
        Handler["Task Handler"]
    end
    
    Route -->|Create| Task
    Task -->|Store| DB[(Database)]
    Worker -->|Poll| DB
    DB -->|Pending Tasks| Worker
    Worker -->|Execute| Handler
    Handler -->|Update Status| DB
```

### Task Types

| Type | Handler | Description |
|------|---------|-------------|
| `send_email` | `handle_send_email` | Transactional emails |
| `send_campaign` | `handle_send_campaign` | Marketing campaigns |
| `generate_report` | `handle_generate_report` | Report generation |
| `cleanup` | `handle_cleanup` | Data cleanup tasks |

## Caching Strategy

```mermaid
flowchart TD
    Request["Incoming Request"]
    Cache{{"Redis Cache"}}
    DB[(Database)]
    Response["Response"]
    
    Request --> Cache
    Cache -->|Hit| Response
    Cache -->|Miss| DB
    DB --> Cache
    Cache --> Response
```

### Cached Resources

| Resource | TTL | Invalidation |
|----------|-----|--------------|
| User sessions | 24h | On logout |
| Product listings | 5m | On product update |
| Blog posts | 10m | On post update |
| Config settings | 1h | On config change |
| Analytics aggregates | 15m | On new data |

## Security Architecture

### Defense Layers

1. **Input Validation**: WTForms with strict validators
2. **CSRF Protection**: Flask-WTF CSRF tokens
3. **XSS Prevention**: Jinja2 auto-escaping + Bleach sanitization
4. **SQL Injection**: SQLAlchemy ORM parameterization
5. **Authentication**: Flask-Login with secure sessions
6. **Authorization**: RBAC with role decorators
7. **Rate Limiting**: Request throttling per endpoint
8. **Security Headers**: CSP, HSTS, X-Frame-Options

### Security Headers Middleware

```python
# app/modules/security_headers.py
class SecurityHeadersMiddleware:
    def __call__(self, environ, start_response):
        response = self.app(environ, start_response)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response
```

## Frontend Architecture

### React Islands Pattern

Verso uses "React Islands"—isolated React components embedded in server-rendered pages:

```html
<!-- Jinja2 Template -->
<div id="admin-data-table" 
     data-columns='{{ columns_json }}'
     data-data='{{ data_json }}'
     data-actions='{{ actions_json }}'>
</div>

<script type="module">
import { AdminDataTable } from '/static/dist/bundle.js';
AdminDataTable.mount('#admin-data-table');
</script>
```

### Component Library

| Component | Purpose |
|-----------|---------|
| `AdminDataTable` | Sortable, searchable data tables |
| `Chart` | Recharts-based data visualization |
| `ImageGallery` | Product image galleries |
| `Toast` | Notification toasts |
| `Dropdown` | Interactive dropdowns |
| `Modal` | Modal dialogs |
| `DatePicker` | Date/time selection |

## Configuration Management

### Environment Variables

```bash
# Required
FLASK_APP=app
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/verso

# Email
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=user@example.com
MAIL_PASSWORD=password

# Stripe
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Optional
REDIS_URL=redis://localhost:6379
SENTRY_DSN=https://...
```

### Configuration Classes

```python
# app/config.py
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
```

## Deployment Architecture

### Production Stack

```mermaid
graph TB
    subgraph "Load Balancer"
        Nginx["Nginx"]
    end
    
    subgraph "Application Tier"
        Gunicorn1["Gunicorn Worker 1"]
        Gunicorn2["Gunicorn Worker 2"]
        Gunicorn3["Gunicorn Worker 3"]
    end
    
    subgraph "Background Processing"
        Worker["Task Worker"]
    end
    
    subgraph "Data Tier"
        PostgreSQL[(PostgreSQL)]
        Redis[(Redis)]
    end
    
    Nginx --> Gunicorn1
    Nginx --> Gunicorn2
    Nginx --> Gunicorn3
    Gunicorn1 --> PostgreSQL
    Gunicorn2 --> PostgreSQL
    Gunicorn3 --> PostgreSQL
    Gunicorn1 --> Redis
    Worker --> PostgreSQL
    Worker --> Redis
```

## Design Decisions

### Why a Monolith?

1. **Simplicity**: Single deployment unit, no service coordination
2. **Latency**: All operations happen in-process or single database
3. **Sovereignty**: Complete data ownership, no SaaS dependencies
4. **Cost**: Runs on $20/month VPS, not $2,000/month microservices

### Why Server-Side Rendering?

1. **SEO**: Full HTML delivered for search engine indexing
2. **Performance**: No hydration delays, instant FCP
3. **Accessibility**: Works without JavaScript
4. **Simplicity**: No complex state management

### Why Flask over Django?

1. **Flexibility**: Choose your own components
2. **Simplicity**: Minimal framework overhead
3. **Explicitness**: No magic, everything visible

---

*Last Updated: December 2024*
