### Prompt for Implementing a Feature in the Verso Flask Application

**Objective**: Provide step-by-step instructions for implementing a specified feature, system, or enhancement in the Verso Flask application, using the **React Islands + Jinja2 hybrid architecture**. The solution should prioritize security (OWASP guidelines), performance, maintainability, and SEO compliance.

---

## Architecture Context

Verso uses a **React Islands Architecture** where:
- **Static content** renders via Jinja2 templates (SEO-friendly, server-rendered)
- **Interactive components** mount as React "islands" within the Jinja2 templates
- **Components** are registered in `app/static/src/registry.ts`
- **Props** are passed via `data-react-props` JSON attributes
- **Styling** uses custom CSS with CSS variables from `base.css` (no Tailwind)

### When to Use React vs Jinja2

| Use Jinja2 | Use React Island |
|------------|------------------|
| Static content pages | Interactive forms with live validation |
| SEO-critical content | Real-time data updates |
| Simple forms | Drag-and-drop interfaces |
| Server-rendered lists | Data tables with sort/filter/pagination |
| Authentication flows | Calendars, charts, kanban boards |

---

## Instructions

1. **Input**: Accept the user-provided task description with:
   - Feature description (e.g., "Build a product inventory system with CRUD operations")
   - Interactivity requirements (will help determine React vs Jinja2)
   - Target user roles (admin, customer, employee)
   - Performance/SEO constraints

2. **Output**: A detailed, step-by-step guide structured as follows:

---

### Step Structure

For each implementation step:

- **Purpose**: The goal of this step
- **Location**: File paths to create or modify
- **Actions**: Specific tasks to complete
- **Integration**: How it connects with existing codebase
- **Considerations**: Security, performance, and maintainability notes

---

## Implementation Patterns

### Pattern A: Pure Jinja2 (Static Content)

Use for pages where SEO and initial load speed are critical.

**Route Pattern:**
```python
@bp.route('/page')
def page():
    data = Model.query.all()
    return render_template('page.html', data=data)
```

**Template Pattern:**
```html
{% extends "base.html" %}
{% block title %}Page Title - Brand{% endblock %}
{% block description %}SEO-friendly description of page content.{% endblock %}

{% block content %}
<section class="page-section">
    <h1>Page Heading</h1>
    {% for item in data %}
    <article class="item-card">
        <h2>{{ item.name }}</h2>
        <p>{{ item.description }}</p>
    </article>
    {% endfor %}
</section>
{% endblock %}
```

---

### Pattern B: React Island (Interactive Component)

Use for complex interactive elements that need client-side state.

**Route Pattern:**
```python
import json

@bp.route('/interactive-page')
def interactive_page():
    items = Model.query.all()
    items_json = json.dumps([{
        'id': item.id,
        'name': item.name,
        'status': item.status
    } for item in items])
    
    return render_template('interactive.html', items_json=items_json)
```

**Template Pattern:**
```html
{% extends "base.html" %}
{% block title %}Interactive Page - Brand{% endblock %}

{% block content %}
<section class="page-section">
    <h1>Page Heading</h1>
    
    <!-- React Island Mount Point -->
    <div data-react-component="ComponentName"
         data-react-props='{"items": {{ items_json|safe }}}'>
        <!-- Optional: SSR fallback content for SEO -->
        <noscript>
            <p>This feature requires JavaScript.</p>
        </noscript>
    </div>
</section>
{% endblock %}
```

**Component Registration (registry.ts):**
```typescript
registerComponent('ComponentName', () => import('./components/features/category/ComponentName'))
```

---

### Pattern C: Hybrid (Mixed Content)

Use when a page has both static SEO content and interactive elements.

**Template Pattern:**
```html
{% extends "base.html" %}
{% block title %}Product Details - {{ product.name }}{% endblock %}
{% block description %}{{ product.short_description }}{% endblock %}

{% block head %}
<!-- Structured data for SEO -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{{ product.name }}",
  "description": "{{ product.description }}"
}
</script>
{% endblock %}

{% block content %}
<!-- Static SEO content -->
<article class="product-detail">
    <h1>{{ product.name }}</h1>
    <p class="description">{{ product.description }}</p>
    
    <!-- React Island for interactive gallery -->
    <div data-react-component="ImageGallery"
         data-react-props='{"images": {{ images_json|safe }}}'>
    </div>
    
    <!-- Static pricing (SEO-visible) -->
    <div class="pricing">
        <span class="price">${{ product.price }}</span>
    </div>
    
    <!-- React Island for add-to-cart -->
    <div data-react-component="AddToCart"
         data-react-props='{"productId": {{ product.id }}, "price": {{ product.price }}}'>
    </div>
</article>
{% endblock %}
```

---

## Available React Components

Reference the component registry for existing components:

| Component | Purpose | Props |
|-----------|---------|-------|
| `AdminDataTable` | Data tables with sort/filter | `columns`, `data`, `bulkActions` |
| `KanbanBoard` | Drag-drop board | `stages`, `leads` |
| `BookingWizard` | Multi-step booking | - |
| `ImageGallery` | Image carousel | `images` |
| `Chart` | Data visualization | `type`, `data`, `options` |
| `Calendar` | Event calendar | `events` |
| `NotificationBell` | Real-time notifications | - |
| `ShoppingCartWidget` | Cart drawer | - |

---

## CSS Guidelines

1. **Use CSS variables** from `base.css`:
   ```css
   .my-component {
       background: var(--glass-bg);
       color: var(--text-primary);
       border-radius: var(--theme-radius);
   }
   ```

2. **Create component-specific CSS** in `app/static/css/components/`:
   ```
   app/static/css/components/my-component.css
   ```

3. **Import in component index**:
   ```css
   /* app/static/css/components/index.css */
   @import './my-component.css';
   ```

4. **Mobile-first responsive design**:
   ```css
   .my-component {
       padding: 1rem;
   }
   
   @media (min-width: 768px) {
       .my-component {
           padding: 2rem;
       }
   }
   ```

---

## Security Checklist

For each implementation step, verify:

- [ ] Input validation on server side
- [ ] CSRF tokens on forms (automatic with Flask-WTF)
- [ ] User content sanitized (`bleach` for HTML, `|e` filter for text)
- [ ] Authorization checks for protected routes
- [ ] SQL injection prevention (use SQLAlchemy ORM)
- [ ] XSS prevention (use `|safe` only for trusted JSON)

---

## SEO Checklist

For public-facing pages:

- [ ] Unique `{% block title %}` with keywords
- [ ] Descriptive `{% block description %}`
- [ ] Single `<h1>` matching page topic
- [ ] Alt text on images
- [ ] Structured data for rich results
- [ ] Critical content server-rendered (not React-only)

---

## File Organization

```
app/
├── routes/
│   └── feature.py          # Flask routes and blueprints
├── models.py                # Database models
├── templates/
│   └── feature/
│       └── page.html        # Jinja2 templates
├── static/
│   ├── css/
│   │   └── components/
│   │       └── feature.css  # Component CSS
│   └── src/
│       └── components/
│           └── features/
│               └── feature/
│                   └── Component.tsx  # React components
```

---

## Prompt Template

```
Implement the following feature in the Verso Flask application using the React Islands + Jinja2 hybrid architecture. Determine which parts should be server-rendered (Jinja2) for SEO and which should be React Islands for interactivity.

Feature: [describe feature]
User roles: [admin/customer/employee]
Interactivity needs: [describe dynamic behavior]
SEO requirements: [public/internal]

Please provide step-by-step implementation instructions following the patterns above.
```

||

{Replace with your feature description, interactivity requirements, user roles, and SEO constraints.}