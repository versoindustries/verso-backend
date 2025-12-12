# React Islands Architecture

Verso-Backend uses the "React Islands" pattern — isolated React components embedded in server-rendered Jinja2 templates.

## Table of Contents

- [Concept](#concept)
- [Directory Structure](#directory-structure)
- [Creating a Component](#creating-a-component)
- [Component Registry](#component-registry)
- [Data Passing](#data-passing)
- [Styling](#styling)
- [Build System](#build-system)

---

## Concept

React Islands provide interactive UI components within server-rendered pages:

```
┌────────────────────────────────────────────┐
│  Jinja2 Template (Server-Rendered HTML)    │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │  React Island (Interactive)          │  │
│  │  - Admin Dashboard                   │  │
│  │  - Data Tables                       │  │
│  │  - Charts                            │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  Static HTML continues...                  │
└────────────────────────────────────────────┘
```

**Benefits:**
- SEO-friendly (full HTML delivered)
- Fast initial load (no full SPA hydration)
- Progressive enhancement
- Isolated component state

---

## Directory Structure

```
app/static/src/
├── components/              # React components
│   ├── AdminDashboard.tsx
│   ├── EmployeeDashboard.tsx
│   ├── UnifiedMessagingDashboard.tsx
│   └── Toast.tsx
├── css/                     # Component styles
│   ├── admin-dashboard.css
│   └── messaging-dashboard.css
├── api.ts                   # API client utilities
├── registry.ts              # Component registry & mounting
├── types.ts                 # Shared TypeScript types
└── main.tsx                 # Vite entry point
```

---

## Creating a Component

### 1. Create the Component File

```tsx
// app/static/src/components/ProductGallery.tsx
import React, { useState } from 'react';
import '../css/product-gallery.css';

interface Product {
  id: number;
  name: string;
  images: string[];
}

interface ProductGalleryProps {
  products: Product[];
}

export const ProductGallery: React.FC<ProductGalleryProps> = ({ products }) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  return (
    <div className="product-gallery">
      {products.map((product, index) => (
        <div 
          key={product.id}
          className={`gallery-item ${index === selectedIndex ? 'active' : ''}`}
          onClick={() => setSelectedIndex(index)}
        >
          <img src={product.images[0]} alt={product.name} />
          <h3>{product.name}</h3>
        </div>
      ))}
    </div>
  );
};
```

### 2. Register the Component

```tsx
// app/static/src/registry.ts
import { ProductGallery } from './components/ProductGallery';

export const componentRegistry = {
  'admin-dashboard': AdminDashboard,
  'employee-dashboard': EmployeeDashboard,
  'product-gallery': ProductGallery,  // Add here
  // ... other components
};
```

### 3. Create Mount Point in Template

```html
<!-- app/templates/shop/products.html -->
{% extends "base.html" %}

{% block content %}
<div id="product-gallery-mount"
     data-component="product-gallery"
     data-props='{{ products_json | safe }}'>
</div>
{% endblock %}

{% block scripts %}
<script type="module">
  import { mountComponent } from '/static/dist/main.js';
  mountComponent('product-gallery-mount');
</script>
{% endblock %}
```

---

## Component Registry

The registry maps component names to implementations and handles mounting:

```tsx
// app/static/src/registry.ts
import React from 'react';
import { createRoot } from 'react-dom/client';

// Import all components
import { AdminDashboard } from './components/AdminDashboard';
import { Toast } from './components/Toast';

export const componentRegistry: Record<string, React.FC<any>> = {
  'admin-dashboard': AdminDashboard,
  'toast': Toast,
};

/**
 * Mount a component to a DOM element
 */
export function mountComponent(elementId: string) {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`Element ${elementId} not found`);
    return;
  }

  const componentName = element.dataset.component;
  if (!componentName) {
    console.error(`No data-component attribute on ${elementId}`);
    return;
  }

  const Component = componentRegistry[componentName];
  if (!Component) {
    console.error(`Component ${componentName} not found in registry`);
    return;
  }

  // Parse props from data attributes
  let props = {};
  if (element.dataset.props) {
    try {
      props = JSON.parse(element.dataset.props);
    } catch (e) {
      console.error(`Failed to parse props for ${componentName}`, e);
    }
  }

  // Mount React component
  const root = createRoot(element);
  root.render(<Component {...props} />);
}
```

---

## Data Passing

### From Jinja2 to React

Pass data via `data-` attributes:

```python
# routes/admin.py
@admin_bp.route('/dashboard')
def dashboard():
    stats = {
        'orders_today': Order.query.filter(...).count(),
        'revenue_today': calculate_revenue(),
        'appointments': get_todays_appointments(),
    }
    return render_template(
        'admin/dashboard.html',
        stats_json=json.dumps(stats)
    )
```

```html
<!-- templates/admin/dashboard.html -->
<div id="admin-dashboard"
     data-component="admin-dashboard"
     data-props='{{ stats_json | safe }}'>
</div>
```

### Using Window Context

For global data, use `window.versoContext`:

```html
<!-- templates/base.html -->
<script>
  window.versoContext = {
    csrfToken: '{{ csrf_token() }}',
    currentUser: {{ current_user_json | safe }},
    businessConfig: {{ business_config_json | safe }},
    featureFlags: {{ feature_flags_json | safe }}
  };
</script>
```

```tsx
// Access in component
const { csrfToken, currentUser } = window.versoContext;
```

---

## Styling

### CSS Variables

Use CSS variables from `base.css` for consistency:

```css
/* app/static/src/css/product-gallery.css */
.product-gallery {
  /* Use theme colors */
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--border-radius-lg);
  
  /* Use spacing system */
  padding: var(--spacing-lg);
  gap: var(--spacing-md);
  
  /* Use shadows */
  box-shadow: var(--shadow-soft);
}

.gallery-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-elevated);
  transition: all var(--transition-normal);
}
```

### Key CSS Variables

```css
/* Colors */
--primary-color: #7c3aed;
--primary-hover: #6d28d9;
--text-primary: #1a1a2e;
--text-secondary: #64748b;

/* Glassmorphism */
--glass-bg: rgba(255, 255, 255, 0.7);
--glass-border: rgba(255, 255, 255, 0.3);

/* Spacing */
--spacing-xs: 0.25rem;
--spacing-sm: 0.5rem;
--spacing-md: 1rem;
--spacing-lg: 1.5rem;
--spacing-xl: 2rem;

/* Shadows */
--shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.1);
--shadow-elevated: 0 8px 24px rgba(0, 0, 0, 0.15);

/* Transitions */
--transition-fast: 150ms ease;
--transition-normal: 250ms ease;
```

### Component CSS Organization

Each component should have its own CSS file:

```
components/
├── AdminDashboard.tsx
└── (uses) css/admin-dashboard.css

├── ProductGallery.tsx  
└── (uses) css/product-gallery.css
```

Import CSS in the component:

```tsx
import '../css/admin-dashboard.css';

export const AdminDashboard: React.FC = () => {
  // ...
};
```

---

## Build System

### Vite Configuration

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  root: 'app/static/src',
  build: {
    outDir: '../dist',
    rollupOptions: {
      input: 'app/static/src/main.tsx',
      output: {
        entryFileNames: 'main.js',
        assetFileNames: '[name][extname]'
      }
    }
  }
});
```

### Build Commands

```bash
# Development with hot reload
npm run dev

# Production build
npm run build

# Type checking only
npm run typecheck
```

### Development Workflow

1. Start Flask server: `flask run --debug`
2. Start Vite dev server: `npm run dev`
3. Vite proxies to Flask at localhost:5000
4. Changes to .tsx files hot reload instantly

---

## Best Practices

### DO:

- ✅ Keep islands small and focused
- ✅ Use TypeScript for type safety
- ✅ Fetch data in useEffect, not on mount
- ✅ Handle loading and error states
- ✅ Use CSS variables for theming

### DON'T:

- ❌ Create giant monolithic components
- ❌ Store sensitive data in component state
- ❌ Use inline styles (use CSS files)
- ❌ Skip error boundaries for complex components
- ❌ Forget to clean up subscriptions/timers

### Error Handling

Wrap islands in error boundaries:

```tsx
import { ErrorBoundary } from './ErrorBoundary';

<ErrorBoundary fallback={<div>Something went wrong</div>}>
  <AdminDashboard {...props} />
</ErrorBoundary>
```

---

*Last Updated: December 2024*
