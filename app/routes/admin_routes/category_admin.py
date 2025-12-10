"""
Category Admin Routes
Admin management of product categories with hierarchical support.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app.models import Category, Product, db
from app.modules.decorators import role_required
import re

category_admin_bp = Blueprint('category_admin', __name__, url_prefix='/admin/shop')


def slugify(text):
    """Generate URL-friendly slug from text."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


@category_admin_bp.route('/categories')
@login_required
@role_required('admin')
def categories_list():
    """List all categories with hierarchy."""
    import json
    from flask_wtf.csrf import generate_csrf
    
    # Get root categories (no parent)
    root_categories = Category.query.filter_by(parent_id=None).order_by(Category.display_order, Category.name).all()
    all_categories = Category.query.order_by(Category.display_order, Category.name).all()
    
    # Flatten hierarchy for table display with indentation
    categories_data = []
    csrf_token = generate_csrf()
    for category in root_categories:
        # Add parent category
        categories_data.append({
            'id': category.id,
            'name': f'<strong>{category.name}</strong>',
            'slug': f'<code>{category.slug}</code>',
            'description': category.description or '-',
            'products': category.products.count() if hasattr(category.products, 'count') else len(category.products) if category.products else 0,
            'display_order': category.display_order,
            'actions': f'''<a href="{url_for('category_admin.edit_category', category_id=category.id)}" class="btn btn-sm btn-outline-primary">Edit</a>
                <form action="{url_for('category_admin.delete_category', category_id=category.id)}" method="post" class="d-inline" onsubmit="return confirm('Delete this category?');">
                    <input type="hidden" name="csrf_token" value="{csrf_token}">
                    <button type="submit" class="btn btn-sm btn-outline-danger">Delete</button>
                </form>'''
        })
        # Add child categories with indentation
        for child in category.children:
            categories_data.append({
                'id': child.id,
                'name': f'<span style="padding-left: 1.5rem;">↳ {child.name}</span>',
                'slug': f'<code>{child.slug}</code>',
                'description': child.description or '-',
                'products': child.products.count() if hasattr(child.products, 'count') else len(child.products) if child.products else 0,
                'display_order': child.display_order,
                'actions': f'''<a href="{url_for('category_admin.edit_category', category_id=child.id)}" class="btn btn-sm btn-outline-primary">Edit</a>
                    <form action="{url_for('category_admin.delete_category', category_id=child.id)}" method="post" class="d-inline" onsubmit="return confirm('Delete this category?');">
                        <input type="hidden" name="csrf_token" value="{csrf_token}">
                        <button type="submit" class="btn btn-sm btn-outline-danger">Delete</button>
                    </form>'''
            })
    
    categories_json = json.dumps(categories_data)
    
    return render_template('admin/shop/categories.html', 
                         root_categories=root_categories,
                         all_categories=all_categories,
                         categories_json=categories_json)


@category_admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_category():
    """Create a new category."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        parent_id = request.form.get('parent_id')
        display_order = int(request.form.get('display_order', 0))
        
        if not name:
            flash('Category name is required.', 'danger')
            return redirect(url_for('category_admin.create_category'))
        
        # Generate slug
        slug = slugify(name)
        base_slug = slug
        counter = 1
        while Category.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        category = Category(
            name=name,
            slug=slug,
            description=description or None,
            parent_id=int(parent_id) if parent_id else None,
            display_order=display_order
        )
        db.session.add(category)
        db.session.commit()
        
        flash(f'Category "{name}" created successfully!', 'success')
        return redirect(url_for('category_admin.categories_list'))
    
    # GET - show form
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/shop/category_form.html', 
                         category=None, 
                         categories=categories,
                         action='create')


@category_admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_category(category_id):
    """Edit an existing category."""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form.get('name', '').strip()
        category.description = request.form.get('description', '').strip() or None
        parent_id = request.form.get('parent_id')
        category.display_order = int(request.form.get('display_order', 0))
        
        # Prevent self-reference
        if parent_id and int(parent_id) == category.id:
            flash('Category cannot be its own parent.', 'danger')
            return redirect(url_for('category_admin.edit_category', category_id=category_id))
        
        category.parent_id = int(parent_id) if parent_id else None
        
        # Update slug if name changed
        new_slug = slugify(category.name)
        if new_slug != category.slug:
            base_slug = new_slug
            counter = 1
            while Category.query.filter(Category.slug == new_slug, Category.id != category.id).first():
                new_slug = f"{base_slug}-{counter}"
                counter += 1
            category.slug = new_slug
        
        db.session.commit()
        flash(f'Category "{category.name}" updated!', 'success')
        return redirect(url_for('category_admin.categories_list'))
    
    # GET - show form
    categories = Category.query.filter(Category.id != category_id).order_by(Category.name).all()
    return render_template('admin/shop/category_form.html', 
                         category=category, 
                         categories=categories,
                         action='edit')


@category_admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_category(category_id):
    """Delete a category."""
    category = Category.query.get_or_404(category_id)
    
    # Check for products in this category
    product_count = Product.query.filter_by(category_id=category_id).count()
    if product_count > 0:
        flash(f'Cannot delete category with {product_count} products. Reassign products first.', 'danger')
        return redirect(url_for('category_admin.categories_list'))
    
    # Check for child categories
    child_count = Category.query.filter_by(parent_id=category_id).count()
    if child_count > 0:
        flash(f'Cannot delete category with {child_count} subcategories.', 'danger')
        return redirect(url_for('category_admin.categories_list'))
    
    name = category.name
    db.session.delete(category)
    db.session.commit()
    
    flash(f'Category "{name}" deleted.', 'success')
    return redirect(url_for('category_admin.categories_list'))
