### Prompt for Generating Jinja2 Templates with React Islands

**Objective**: Generate a Jinja2 template that extends `base.html` based on a provided layout description, implementing the **React Islands Architecture** for interactive components while maintaining SEO compliance and server-rendered static content.

---

## Architecture Overview

Verso templates use a hybrid approach:

```
┌─────────────────────────────────────────────────────────────┐
│ Jinja2 Template (base.html)                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ <div data-react-component="Header"></div>               │ │ ← React Island
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ <main class="container">                                    │
│   <h1>Server-Rendered SEO Content</h1>                      │ ← Jinja2 (static)
│   <p>{{ page.description }}</p>                             │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ <div data-react-component="ImageGallery"              │ │ ← React Island
│   │      data-react-props='{"images": [...]}'></div>      │ │
│   └───────────────────────────────────────────────────────┘ │
│                                                             │
│   <section class="static-content">                          │ ← Jinja2 (static)
│     {% for item in items %}...{% endfor %}                  │
│   </section>                                                │
│ </main>                                                     │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ <div data-react-component="Footer"></div>               │ │ ← React Island
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Instructions

### Input
A layout description specifying:
- Sections with their content
- Render method (Jinja2 static vs React Island)
- React component names for interactive sections
- SEO requirements

### Output
A complete Jinja2 template that:
1. Extends `base.html`
2. Fills all required blocks (`title`, `description`, `head`, `content`, `scripts`)
3. Uses React Islands for interactive components via `data-react-component`
4. Includes SEO meta tags and structured data
5. Links to component-specific CSS

---

## Template Structure

### Base Template Blocks

```html
{% extends "base.html" %}

{# Page Title - SEO critical #}
{% block title %}Page Title - Brand Name{% endblock %}

{# Meta Description - SEO critical #}
{% block description %}Compelling description of page content for search results.{% endblock %}

{# Additional CSS - Component styles #}
{% block additional_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/pages/page-name.css') }}">
{% endblock %}

{# Head - SEO meta tags and structured data #}
{% block head %}
<!-- Open Graph -->
<meta property="og:title" content="Page Title">
<meta property="og:description" content="Page description">
<meta property="og:image" content="{{ url_for('static', filename='images/og-image.jpg', _external=True) }}">
<meta property="og:url" content="{{ request.url }}">
<meta property="og:type" content="website">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Page Title">
<meta name="twitter:description" content="Page description">

<!-- Canonical URL -->
<link rel="canonical" href="{{ request.url }}">

<!-- Structured Data -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "Page Title",
  "description": "Page description"
}
</script>
{% endblock %}

{# Main Content #}
{% block content %}
<!-- Content sections here -->
{% endblock %}

{# Additional Scripts #}
{% block scripts %}
<script>
// Page-specific JavaScript (if needed beyond React)
</script>
{% endblock %}
```

---

## React Island Mount Point Patterns

### Basic Mount Point
```html
<div data-react-component="ComponentName"></div>
```

### With Props from Flask
```html
{# In Flask route: items_json = json.dumps([...]) #}
<div data-react-component="AdminDataTable"
     data-react-props='{
       "columns": {{ columns_json|safe }},
       "data": {{ items_json|safe }}
     }'>
</div>
```

### With Inline Props
```html
<div data-react-component="ImageGallery"
     data-react-props='{
       "images": [
         {"src": "/static/images/1.jpg", "alt": "Image 1"},
         {"src": "/static/images/2.jpg", "alt": "Image 2"}
       ]
     }'>
</div>
```

### With SSR Fallback (for graceful degradation)
```html
<div data-react-component="DataTable"
     data-react-props='{"data": {{ data_json|safe }}}'>
    <!-- Fallback content shown while React loads -->
    <noscript>
        <table class="static-table">
            {% for item in items %}
            <tr><td>{{ item.name }}</td></tr>
            {% endfor %}
        </table>
    </noscript>
</div>
```

---

## Available React Components

| Component | Purpose | Required Props |
|-----------|---------|----------------|
| `Header` | Site header/nav | None (uses `window.versoContext`) |
| `Footer` | Site footer | None |
| `AlertBar` | Promotional banner | `message`, `ctaText`, `ctaUrl` |
| `FlashAlerts` | Flash messages | `messages` |
| `ImageGallery` | Image carousel | `images` array |
| `BookingWizard` | Multi-step booking | None |
| `BookingPage` | Full booking page | Service/date data |
| `AdminDataTable` | Sortable data table | `columns`, `data`, `bulkActions` |
| `KanbanBoard` | Drag-drop board | `stages`, `leads` |
| `Chart` | Data visualization | `type`, `data`, `options` |
| `Calendar` | Event calendar | `events` |
| `EmployeeCalendar` | Employee schedule | Calendar data |
| `AdminCalendar` | Admin calendar | Calendar data |
| `ProductView` | Product details | `product` object |
| `CartPage` | Shopping cart | None |
| `NotificationBell` | Notifications | None |
| `ShoppingCartWidget` | Cart drawer | None |
| `ThemeEditor` | Theme customization | Theme config |
| `AnalyticsDashboard` | Analytics view | Analytics data |
| `MessagingChannel` | Chat interface | Channel data |

---

## Complete Template Example

### Flask Route
```python
import json
from flask import render_template

@bp.route('/products')
def product_list():
    products = Product.query.filter_by(active=True).all()
    
    # Serialize data for React component
    products_json = json.dumps([{
        'id': p.id,
        'name': p.name,
        'price': str(p.price),
        'image': p.image_url,
        'category': p.category.name if p.category else 'Uncategorized'
    } for p in products])
    
    columns_json = json.dumps([
        {'key': 'name', 'label': 'Product', 'sortable': True},
        {'key': 'price', 'label': 'Price', 'sortable': True},
        {'key': 'category', 'label': 'Category', 'sortable': True}
    ])
    
    return render_template(
        'shop/products.html',
        products=products,  # For static content
        products_json=products_json,  # For React
        columns_json=columns_json
    )
```

### Jinja2 Template
```html
{% extends "base.html" %}

{% block title %}Products - {{ business_config.get('business_name', 'Our Store') }}{% endblock %}

{% block description %}Browse our collection of products. Quality items at competitive prices with fast shipping.{% endblock %}

{% block additional_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/pages/products.css') }}">
{% endblock %}

{% block head %}
<!-- Breadcrumb Structured Data -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "{{ url_for('main_routes.index', _external=True) }}"},
    {"@type": "ListItem", "position": 2, "name": "Products", "item": "{{ request.url }}"}
  ]
}
</script>

<!-- Product List Structured Data -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "itemListElement": [
    {% for product in products[:10] %}
    {
      "@type": "ListItem",
      "position": {{ loop.index }},
      "item": {
        "@type": "Product",
        "name": "{{ product.name }}",
        "url": "{{ url_for('shop.product', slug=product.slug, _external=True) }}"
      }
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  ]
}
</script>
{% endblock %}

{% block content %}
<div class="products-page">
    <!-- Static SEO Content -->
    <header class="page-header">
        <h1>Our Products</h1>
        <p class="lead">Discover our curated selection of quality products.</p>
    </header>

    <!-- Breadcrumbs (static, SEO-visible) -->
    <nav class="breadcrumbs" aria-label="Breadcrumb">
        <ol>
            <li><a href="{{ url_for('main_routes.index') }}">Home</a></li>
            <li aria-current="page">Products</li>
        </ol>
    </nav>

    <!-- React Island: Interactive Product Table -->
    <section class="products-table-section">
        <div data-react-component="AdminDataTable"
             data-react-props='{
               "columns": {{ columns_json|safe }},
               "data": {{ products_json|safe }},
               "searchable": true,
               "pageSize": 20
             }'>
            <!-- Fallback for SEO/no-JS -->
            <noscript>
                <ul class="product-list-fallback">
                    {% for product in products %}
                    <li>
                        <a href="{{ url_for('shop.product', slug=product.slug) }}">
                            {{ product.name }} - ${{ product.price }}
                        </a>
                    </li>
                    {% endfor %}
                </ul>
            </noscript>
        </div>
    </section>

    <!-- Static CTA Section -->
    <section class="cta-section">
        <h2>Need Help Finding Something?</h2>
        <p>Our team is here to assist you.</p>
        <a href="{{ url_for('main_routes.contact') }}" class="btn-primary">Contact Us</a>
    </section>
</div>
{% endblock %}

{% block scripts %}
<script>
// Optional: Page-specific analytics or interactions
document.addEventListener('DOMContentLoaded', function() {
    // Track page view
    if (window.gtag) {
        gtag('event', 'view_item_list', {
            'item_list_name': 'Products'
        });
    }
});
</script>
{% endblock %}
```

---

## SEO Checklist for Generated Templates

- [ ] Unique, descriptive `{% block title %}`
- [ ] Compelling `{% block description %}` (150-160 chars)
- [ ] Single `<h1>` tag matching page topic
- [ ] Proper heading hierarchy (H1 → H2 → H3)
- [ ] Breadcrumb structured data
- [ ] Page-specific structured data (Article, Product, etc.)
- [ ] Open Graph meta tags
- [ ] Twitter Card meta tags
- [ ] Canonical URL
- [ ] Alt text on all images
- [ ] SEO-critical content in Jinja2 (not React-only)
- [ ] `<noscript>` fallback for React components with critical content

---

## Prompt Template

```
Generate a Jinja2 template with React Islands based on the following layout description. 
Use the pattern of extending base.html and mounting React components via data-react-component attributes.

Layout Description:
[paste layout specification here]

Flask Route Data:
[describe what data the route will pass to the template]

SEO Requirements:
- Page title: [title]
- Meta description: [description]
- Structured data type: [WebPage, Product, Article, etc.]

React Components Needed:
[list components from the registry that should be used]
```

||

{Replace with your layout description, Flask route data, and SEO requirements.}
