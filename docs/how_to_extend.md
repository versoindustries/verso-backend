# How to Extend Verso Backend

This guide provides comprehensive instructions for developers looking to add new features, routes, models, and React components to the Verso Backend application.

## Table of Contents

- [Project Structure](#project-structure)
- [Adding a New Route](#adding-a-new-route)
- [Adding a New Model](#adding-a-new-model)
- [Adding a Form](#adding-a-form)
- [Adding a React Island Component](#adding-a-react-island-component)
- [Adding a Background Task](#adding-a-background-task)
- [Adding a Module](#adding-a-module)
- [Flask CLI Commands](#flask-cli-commands)
- [Testing Your Changes](#testing-your-changes)

---

## Project Structure

```
app/
├── __init__.py          # Flask app factory and extension setup
├── config.py            # Configuration classes
├── models.py            # SQLAlchemy database models
├── forms.py             # Flask-WTF forms
├── worker.py            # Background task processor
│
├── routes/              # Blueprints (47 files)
│   ├── admin.py         # Admin dashboard
│   ├── api.py           # REST API endpoints
│   ├── auth.py          # Authentication
│   ├── blog.py          # Blog/CMS
│   ├── ecommerce.py     # E-commerce public
│   └── ...
│
├── modules/             # Helper modules (35 files)
│   ├── auth_manager.py  # RBAC decorators
│   ├── file_manager.py  # File uploads
│   ├── security.py      # Security utilities
│   └── ...
│
├── templates/           # Jinja2 templates
│   ├── base.html        # Master template
│   ├── admin/           # Admin templates
│   ├── shop/            # E-commerce templates
│   └── ...
│
└── static/
    └── src/             # React/TypeScript source
        ├── components/  # React components
        ├── css/         # Component styles
        ├── api.ts       # API utilities
        ├── registry.ts  # Component registry
        └── types.ts     # TypeScript types
```

---

## Adding a New Route

### Step 1: Create Blueprint

Create a new file in `app/routes/`:

```python
# app/routes/feature.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database import db
from app.models import MyModel
from app.forms import MyFeatureForm
from app.modules.auth_manager import require_role

feature_bp = Blueprint('feature', __name__, url_prefix='/feature')


@feature_bp.route('/')
def index():
    """Feature landing page."""
    items = MyModel.query.all()
    return render_template('feature/index.html', items=items)


@feature_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new item."""
    form = MyFeatureForm()
    if form.validate_on_submit():
        item = MyModel(
            name=form.name.data,
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        flash('Item created successfully', 'success')
        return redirect(url_for('feature.index'))
    return render_template('feature/create.html', form=form)


@feature_bp.route('/<int:item_id>')
def detail(item_id: int):
    """View item details."""
    item = MyModel.query.get_or_404(item_id)
    return render_template('feature/detail.html', item=item)


@feature_bp.route('/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('admin')
def edit(item_id: int):
    """Edit an item (admin only)."""
    item = MyModel.query.get_or_404(item_id)
    form = MyFeatureForm(obj=item)
    if form.validate_on_submit():
        form.populate_obj(item)
        db.session.commit()
        flash('Item updated', 'success')
        return redirect(url_for('feature.detail', item_id=item.id))
    return render_template('feature/edit.html', form=form, item=item)
```

### Step 2: Register Blueprint

In `app/__init__.py`, import and register:

```python
# app/__init__.py
def create_app(config_class=Config):
    app = Flask(__name__)
    # ... extension initialization ...
    
    # Import and register blueprint
    from app.routes.feature import feature_bp
    app.register_blueprint(feature_bp)
    
    return app
```

### Step 3: Create Templates

Create templates in `app/templates/feature/`:

```html
<!-- app/templates/feature/index.html -->
{% extends "base.html" %}

{% block title %}My Feature{% endblock %}

{% block content %}
<div class="container">
    <h1>My Feature</h1>
    
    {% if current_user.is_authenticated %}
    <a href="{{ url_for('feature.create') }}" class="btn btn-primary">
        Create New
    </a>
    {% endif %}
    
    <div class="items-grid">
        {% for item in items %}
        <div class="item-card">
            <h3>{{ item.name }}</h3>
            <a href="{{ url_for('feature.detail', item_id=item.id) }}">
                View Details
            </a>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

---

## Adding a New Model

### Step 1: Define the Model

Add to `app/models.py`:

```python
class Feature(db.Model):
    """Feature model for storing feature data."""
    __tablename__ = 'features'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='active')
    priority = db.Column(db.Integer, default=0)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('features', lazy='dynamic'))
    
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    category = db.relationship('Category', backref='features')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_feature_status', 'status'),
        db.Index('idx_feature_user', 'user_id'),
    )
    
    def __repr__(self):
        return f'<Feature {self.name}>'
    
    @property
    def is_active(self):
        """Check if feature is active."""
        return self.status == 'active'
    
    def to_dict(self):
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
        }
```

### Step 2: Create Migration

```bash
# Generate migration
flask db migrate -m "Add Feature model"

# Review migration file in migrations/versions/
# Apply migration
flask db upgrade
```

### Step 3: Add to API (Optional)

```python
# app/routes/api.py
@api_bp.route('/features', methods=['GET'])
@require_api_key(['read:features'])
def get_features():
    features = Feature.query.all()
    return jsonify({
        'data': [f.to_dict() for f in features]
    })
```

---

## Adding a Form

### Step 1: Define the Form

Add to `app/forms.py`:

```python
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class FeatureForm(FlaskForm):
    """Form for creating/editing features."""
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=2, max=200)
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=2000)
    ])
    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending')
    ])
    priority = IntegerField('Priority', validators=[
        Optional(),
        NumberRange(min=0, max=100)
    ], default=0)
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate choices dynamically
        from app.models import Category
        self.category_id.choices = [(0, '-- Select --')] + [
            (c.id, c.name) for c in Category.query.all()
        ]
```

### Step 2: Use in Route

```python
@feature_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    form = FeatureForm()
    if form.validate_on_submit():
        feature = Feature(
            name=form.name.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            category_id=form.category_id.data if form.category_id.data else None,
            user_id=current_user.id
        )
        db.session.add(feature)
        db.session.commit()
        flash('Feature created!', 'success')
        return redirect(url_for('feature.index'))
    return render_template('feature/create.html', form=form)
```

---

## Adding a React Island Component

### Step 1: Create Component

```tsx
// app/static/src/components/FeatureList.tsx
import React, { useState, useEffect } from 'react';
import { api } from '../api';
import '../css/feature-list.css';

interface Feature {
  id: number;
  name: string;
  description: string;
  status: string;
}

interface FeatureListProps {
  initialFeatures?: Feature[];
  showActions?: boolean;
}

export const FeatureList: React.FC<FeatureListProps> = ({
  initialFeatures = [],
  showActions = true
}) => {
  const [features, setFeatures] = useState<Feature[]>(initialFeatures);
  const [loading, setLoading] = useState(!initialFeatures.length);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!initialFeatures.length) {
      fetchFeatures();
    }
  }, []);

  const fetchFeatures = async () => {
    try {
      const response = await api.get('/api/v1/features');
      setFeatures(response.data);
    } catch (err) {
      setError('Failed to load features');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="feature-list">
      {features.map(feature => (
        <div key={feature.id} className={`feature-card status-${feature.status}`}>
          <h3>{feature.name}</h3>
          <p>{feature.description}</p>
          {showActions && (
            <div className="feature-actions">
              <button onClick={() => window.location.href = `/feature/${feature.id}`}>
                View
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
```

### Step 2: Register Component

```tsx
// app/static/src/registry.ts
import { FeatureList } from './components/FeatureList';

export const componentRegistry = {
  // ... existing components
  'feature-list': FeatureList,
};
```

### Step 3: Mount in Template

```html
<!-- app/templates/feature/index.html -->
<div id="feature-list-mount"
     data-component="feature-list"
     data-props='{{ features_json | safe }}'>
</div>

<script type="module">
  import { mountComponent } from '/static/dist/main.js';
  mountComponent('feature-list-mount');
</script>
```

### Step 4: Build Frontend

```bash
npm run build
```

---

## Adding a Background Task

### Step 1: Define Task Handler

```python
# app/worker.py (add to existing handlers)
def handle_feature_notification(payload):
    """Send notification about feature changes.
    
    Args:
        payload: dict with 'feature_id', 'action', 'recipients'
    """
    from app.models import Feature
    from app.modules.email import send_email
    
    feature = Feature.query.get(payload['feature_id'])
    if not feature:
        return {'success': False, 'error': 'Feature not found'}
    
    for recipient in payload['recipients']:
        send_email(
            to=recipient,
            subject=f"Feature Update: {feature.name}",
            template='emails/feature_notification.html',
            feature=feature,
            action=payload['action']
        )
    
    return {'success': True, 'sent': len(payload['recipients'])}

# Register handler
TASK_HANDLERS['feature_notification'] = handle_feature_notification
```

### Step 2: Enqueue Task

```python
# In your route or service
from app.models import Task
from app.database import db

def notify_feature_update(feature, action):
    """Queue notification task."""
    task = Task(
        name='feature_notification',
        payload={
            'feature_id': feature.id,
            'action': action,
            'recipients': get_subscribed_users()
        },
        status='pending'
    )
    db.session.add(task)
    db.session.commit()
```

---

## Adding a Module

Create a helper module in `app/modules/`:

```python
# app/modules/feature_manager.py
"""Feature management utilities."""
from datetime import datetime
from typing import List, Optional
from app.models import Feature
from app.database import db


def get_active_features(user_id: Optional[int] = None) -> List[Feature]:
    """Get all active features, optionally filtered by user.
    
    Args:
        user_id: Optional user ID to filter by
    
    Returns:
        List of active Feature objects
    """
    query = Feature.query.filter_by(status='active')
    if user_id:
        query = query.filter_by(user_id=user_id)
    return query.order_by(Feature.priority.desc()).all()


def archive_old_features(days: int = 90) -> int:
    """Archive features older than specified days.
    
    Args:
        days: Number of days after which to archive
    
    Returns:
        Number of features archived
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    count = Feature.query.filter(
        Feature.created_at < cutoff,
        Feature.status == 'active'
    ).update({'status': 'archived'})
    db.session.commit()
    return count


def duplicate_feature(feature_id: int, user_id: int) -> Feature:
    """Create a copy of an existing feature.
    
    Args:
        feature_id: ID of feature to duplicate
        user_id: User ID for the new feature
    
    Returns:
        New Feature object
    """
    original = Feature.query.get_or_404(feature_id)
    new_feature = Feature(
        name=f"{original.name} (Copy)",
        description=original.description,
        status='active',
        priority=original.priority,
        user_id=user_id
    )
    db.session.add(new_feature)
    db.session.commit()
    return new_feature
```

---

## Flask CLI Commands

### View Available Commands

```bash
flask --help
```

### Key Commands

| Command | Description |
|---------|-------------|
| `flask run` | Start development server |
| `flask shell` | Open Python shell with app context |
| `flask db migrate -m "message"` | Create migration |
| `flask db upgrade` | Apply migrations |
| `flask db downgrade` | Rollback last migration |
| `flask create-roles` | Create default roles |
| `flask seed-business-config` | Seed business settings |
| `flask set-admin <email>` | Grant admin role |
| `flask run-worker` | Start background worker |

### Adding Custom Commands

```python
# app/__init__.py
import click

def create_app():
    app = Flask(__name__)
    # ...
    
    @app.cli.command('my-command')
    @click.argument('name')
    @click.option('--force', is_flag=True, help='Force operation')
    def my_command(name, force):
        """Description of command."""
        click.echo(f'Running my-command with {name}')
        # Your logic here
    
    return app
```

---

## Testing Your Changes

### Run Test Suite

```bash
# All tests
pytest

# Specific file
pytest app/tests/test_feature.py

# With coverage
pytest --cov=app
```

### Write Tests

```python
# app/tests/test_feature.py
import pytest
from app.models import Feature


class TestFeatureModel:
    def test_create_feature(self, session, test_user):
        feature = Feature(name='Test', user_id=test_user.id)
        session.add(feature)
        session.commit()
        assert feature.id is not None
        assert feature.is_active

    def test_feature_to_dict(self, session, test_user):
        feature = Feature(name='Test', user_id=test_user.id)
        session.add(feature)
        session.commit()
        data = feature.to_dict()
        assert data['name'] == 'Test'


class TestFeatureRoutes:
    def test_index_page(self, client):
        response = client.get('/feature/')
        assert response.status_code == 200

    def test_create_requires_login(self, client):
        response = client.get('/feature/new')
        assert response.status_code == 302
        assert '/login' in response.location
```

### Manual Testing Checklist

- [ ] Route loads without errors
- [ ] Form validation works
- [ ] Database operations succeed
- [ ] Authorization enforced correctly
- [ ] React component renders
- [ ] API endpoints respond correctly

---

*Last Updated: December 2024*
