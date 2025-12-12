# Developer Conventions

Code style and contribution guidelines for Verso-Backend development.

## Table of Contents

- [Python Style](#python-style)
- [TypeScript/React Style](#typescriptreact-style)
- [Git Workflow](#git-workflow)
- [File Naming](#file-naming)
- [Documentation](#documentation)

---

## Python Style

### General Rules

- Follow **PEP 8** with a line length of **100 characters**
- Use **4 spaces** for indentation (no tabs)
- Use **type hints** for function signatures

### Imports

Order imports as follows:

```python
# 1. Standard library
import os
from datetime import datetime

# 2. Third-party packages
from flask import Blueprint, render_template, request
from sqlalchemy import Column, String

# 3. Local imports
from app.models import User, Order
from app.modules.auth_manager import require_role
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Variables | `snake_case` | `user_count` |
| Functions | `snake_case` | `get_user_by_email()` |
| Classes | `PascalCase` | `EmailCampaign` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_UPLOAD_SIZE` |
| Files | `snake_case.py` | `email_marketing.py` |
| Blueprints | `{name}_bp` | `admin_bp` |

### Docstrings

Use Google-style docstrings:

```python
def calculate_discount(order: Order, code: str) -> int:
    """Calculate discount amount for an order.
    
    Args:
        order: The order to apply discount to.
        code: The discount code to validate.
    
    Returns:
        Discount amount in cents.
    
    Raises:
        InvalidDiscountError: If code is expired or invalid.
    """
```

### Route Handlers

```python
@admin_bp.route('/users/<int:user_id>', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def edit_user(user_id: int):
    """Edit user details.
    
    GET: Display edit form
    POST: Process form submission
    """
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    
    if form.validate_on_submit():
        form.populate_obj(user)
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.list_users'))
    
    return render_template('admin/edit_user.html', form=form, user=user)
```

---

## TypeScript/React Style

### General Rules

- Use **TypeScript** for all new components
- Use **functional components** with hooks
- Use **2 spaces** for indentation

### Component Structure

```tsx
// 1. Imports
import React, { useState, useEffect } from 'react';
import { api } from '../api';

// 2. Types
interface ProductCardProps {
  product: Product;
  onAddToCart: (id: number) => void;
}

// 3. Component
export const ProductCard: React.FC<ProductCardProps> = ({ 
  product, 
  onAddToCart 
}) => {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    await onAddToCart(product.id);
    setLoading(false);
  };

  return (
    <div className="product-card">
      <h3>{product.name}</h3>
      <p>${(product.price / 100).toFixed(2)}</p>
      <button onClick={handleClick} disabled={loading}>
        {loading ? 'Adding...' : 'Add to Cart'}
      </button>
    </div>
  );
};
```

### File Naming

| Element | Convention | Example |
|---------|------------|---------|
| Components | `PascalCase.tsx` | `ProductCard.tsx` |
| Utilities | `camelCase.ts` | `formatCurrency.ts` |
| Types | `types.ts` | In component directory |
| CSS | `kebab-case.css` | `product-card.css` |

### CSS Conventions

Use CSS custom properties from `base.css`:

```css
.product-card {
  background: var(--glass-bg);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-md);
  box-shadow: var(--shadow-soft);
}

.product-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-elevated);
}
```

---

## Git Workflow

### Branch Naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/description` | `feature/product-variants` |
| Bug fix | `fix/description` | `fix/cart-total-calculation` |
| Docs | `docs/description` | `docs/api-reference` |
| Refactor | `refactor/description` | `refactor/order-service` |

### Commit Messages

Use conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code change that neither fixes bug nor adds feature
- `test`: Adding or updating tests
- `chore`: Build process, dependencies

**Examples:**
```
feat(ecommerce): add product variant support

- Add ProductVariant model
- Update cart to handle variants
- Add variant selector component

Closes #123
```

```
fix(auth): prevent session fixation on login
```

### Pull Requests

Every PR should:
- Have a clear title and description
- Reference related issues
- Include screenshots for UI changes
- Pass all CI checks
- Have at least one approval

---

## File Naming

### Python Files

```
app/
├── routes/
│   ├── admin.py           # Blueprint for /admin
│   ├── ecommerce_admin.py # Blueprint for /admin/shop
│   └── api.py             # REST API endpoints
├── modules/
│   ├── auth_manager.py    # Authentication helpers
│   └── file_manager.py    # File upload utilities
└── templates/
    ├── admin/
    │   └── dashboard.html
    └── shop/
        └── product.html
```

### React Files

```
app/static/src/
├── components/
│   ├── AdminDashboard.tsx
│   ├── ProductCard.tsx
│   └── Toast.tsx
├── css/
│   ├── admin-dashboard.css
│   └── product-card.css
├── api.ts
├── registry.ts
└── types.ts
```

---

## Documentation

### Code Comments

Comment **why**, not **what**:

```python
# Bad
# Increment counter
counter += 1

# Good
# Track retry attempts for exponential backoff
counter += 1
```

### README for New Features

When adding a major feature, include:

1. Purpose and use case
2. Configuration options
3. Example usage
4. API endpoints (if applicable)

### Update Changelog

Add entries to `CHANGELOG.md` for:

- New features
- Breaking changes
- Bug fixes
- Deprecations

---

## Code Review Checklist

Before submitting for review:

- [ ] Code follows style conventions
- [ ] Tests pass locally
- [ ] No console.log/print statements
- [ ] Type hints added (Python) / Types defined (TypeScript)
- [ ] Documentation updated if needed
- [ ] No sensitive data in code
- [ ] Error handling in place

---

*Last Updated: December 2024*
