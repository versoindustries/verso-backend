"""
E-Commerce Admin Routes

Admin interface for managing collections, bundles, discounts, 
gift cards, shipping, and tax configuration.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.database import db
from app.models import (
    Collection, CollectionRule, CollectionProduct, Product,
    ProductBundle, BundleItem, ProductVariant,
    Discount, DiscountRule, DiscountUsage,
    GiftCard, GiftCardTransaction,
    ShippingZone, ShippingRate, TaxRate,
    ProductAttribute, ProductAttributeValue
)
from app.modules.decorators import role_required
from app.modules.ecommerce import generate_gift_card_code, generate_discount_code
from datetime import datetime
import re

def slugify(text):
    """Generate URL-friendly slug from text."""
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text

ecommerce_admin_bp = Blueprint('ecommerce_admin', __name__, url_prefix='/admin/ecommerce')


# =============================================================================
# Collections Management
# =============================================================================

@ecommerce_admin_bp.route('/collections')
@login_required
@role_required('admin')
def list_collections():
    """List all collections."""
    import json
    collections = Collection.query.order_by(Collection.created_at.desc()).all()
    
    # Serialize for React AdminDataTable
    collections_json = json.dumps([
        {
            'id': c.id,
            'name': f'<strong>{c.name}</strong><br><small class="text-muted">/collections/{c.slug}</small>',
            'type': f'<span class="badge bg-{"info" if c.collection_type == "smart" else "secondary"}">{c.collection_type.title()}</span>',
            'products': c.products.count(),
            'status': '<span class="badge bg-success">Active</span>' if c.is_active() else '<span class="badge bg-warning">Inactive</span>',
            'homepage': '<i class="fas fa-check text-success"></i>' if c.show_on_homepage else '<i class="fas fa-times text-muted"></i>',
            'actions': f'''<a href="{url_for('ecommerce_admin.edit_collection', id=c.id)}" class="btn btn-sm btn-outline-primary"><i class="fas fa-edit"></i></a>
                <a href="{url_for('ecommerce.view_collection', slug=c.slug)}" class="btn btn-sm btn-outline-info" target="_blank"><i class="fas fa-external-link-alt"></i></a>'''
        }
        for c in collections
    ])
    
    return render_template('admin/ecommerce/collections/index.html', collections=collections, collections_json=collections_json)


@ecommerce_admin_bp.route('/collections/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_collection():
    """Create a new collection."""
    if request.method == 'POST':
        name = request.form.get('name')
        slug = slugify(request.form.get('slug') or name)
        description = request.form.get('description')
        collection_type = request.form.get('collection_type', 'manual')
        is_published = request.form.get('is_published') == 'on'
        show_on_homepage = request.form.get('show_on_homepage') == 'on'
        sort_order = request.form.get('sort_order', 'manual')
        seo_title = request.form.get('seo_title')
        seo_description = request.form.get('seo_description')
        
        collection = Collection(
            name=name,
            slug=slug,
            description=description,
            collection_type=collection_type,
            is_published=is_published,
            show_on_homepage=show_on_homepage,
            sort_order=sort_order,
            seo_title=seo_title,
            seo_description=seo_description
        )
        
        db.session.add(collection)
        db.session.commit()
        
        # Add rules for smart collections
        if collection_type == 'smart':
            rule_fields = request.form.getlist('rule_field[]')
            rule_conditions = request.form.getlist('rule_condition[]')
            rule_values = request.form.getlist('rule_value[]')
            
            for i in range(len(rule_fields)):
                if rule_fields[i] and rule_values[i]:
                    rule = CollectionRule(
                        collection_id=collection.id,
                        field=rule_fields[i],
                        condition=rule_conditions[i] if i < len(rule_conditions) else 'equals',
                        value=rule_values[i]
                    )
                    db.session.add(rule)
            
            db.session.commit()
        
        # Add products for manual collections
        if collection_type == 'manual':
            product_ids = request.form.getlist('product_ids[]')
            for i, pid in enumerate(product_ids):
                if pid:
                    cp = CollectionProduct(
                        collection_id=collection.id,
                        product_id=int(pid),
                        position=i
                    )
                    db.session.add(cp)
            
            db.session.commit()
        
        flash(f'Collection "{name}" created successfully!', 'success')
        return redirect(url_for('ecommerce_admin.list_collections'))
    
    products = Product.query.order_by(Product.name).all()
    return render_template('admin/ecommerce/collections/form.html', 
                          collection=None, products=products)


@ecommerce_admin_bp.route('/collections/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_collection(id):
    """Edit an existing collection."""
    collection = Collection.query.get_or_404(id)
    
    if request.method == 'POST':
        collection.name = request.form.get('name')
        collection.slug = slugify(request.form.get('slug') or collection.name)
        collection.description = request.form.get('description')
        collection.is_published = request.form.get('is_published') == 'on'
        collection.show_on_homepage = request.form.get('show_on_homepage') == 'on'
        collection.sort_order = request.form.get('sort_order', 'manual')
        collection.seo_title = request.form.get('seo_title')
        collection.seo_description = request.form.get('seo_description')
        
        # Update rules for smart collections
        if collection.collection_type == 'smart':
            # Clear existing rules
            CollectionRule.query.filter_by(collection_id=collection.id).delete()
            
            rule_fields = request.form.getlist('rule_field[]')
            rule_conditions = request.form.getlist('rule_condition[]')
            rule_values = request.form.getlist('rule_value[]')
            
            for i in range(len(rule_fields)):
                if rule_fields[i] and rule_values[i]:
                    rule = CollectionRule(
                        collection_id=collection.id,
                        field=rule_fields[i],
                        condition=rule_conditions[i] if i < len(rule_conditions) else 'equals',
                        value=rule_values[i]
                    )
                    db.session.add(rule)
        
        # Update products for manual collections
        if collection.collection_type == 'manual':
            # Clear existing product assignments
            CollectionProduct.query.filter_by(collection_id=collection.id).delete()
            
            product_ids = request.form.getlist('product_ids[]')
            for i, pid in enumerate(product_ids):
                if pid:
                    cp = CollectionProduct(
                        collection_id=collection.id,
                        product_id=int(pid),
                        position=i
                    )
                    db.session.add(cp)
        
        db.session.commit()
        flash('Collection updated successfully!', 'success')
        return redirect(url_for('ecommerce_admin.list_collections'))
    
    products = Product.query.order_by(Product.name).all()
    collection_product_ids = [cp.product_id for cp in collection.products]
    
    return render_template('admin/ecommerce/collections/form.html', 
                          collection=collection, 
                          products=products,
                          collection_product_ids=collection_product_ids)


@ecommerce_admin_bp.route('/collections/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_collection(id):
    """Delete a collection."""
    collection = Collection.query.get_or_404(id)
    name = collection.name
    db.session.delete(collection)
    db.session.commit()
    flash(f'Collection "{name}" deleted.', 'success')
    return redirect(url_for('ecommerce_admin.list_collections'))


# =============================================================================
# Bundles Management
# =============================================================================

@ecommerce_admin_bp.route('/bundles')
@login_required
@role_required('admin')
def list_bundles():
    """List all product bundles."""
    bundles = ProductBundle.query.order_by(ProductBundle.created_at.desc()).all()
    return render_template('admin/ecommerce/bundles/index.html', bundles=bundles)


@ecommerce_admin_bp.route('/bundles/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_bundle():
    """Create a new product bundle."""
    if request.method == 'POST':
        name = request.form.get('name')
        slug = slugify(request.form.get('slug') or name)
        description = request.form.get('description')
        discount_type = request.form.get('discount_type', 'percentage')
        discount_value = int(request.form.get('discount_value', 0))
        bundle_price = request.form.get('bundle_price')
        bundle_price_cents = int(float(bundle_price) * 100) if bundle_price else None
        is_active = request.form.get('is_active') == 'on'
        requires_all_items = request.form.get('requires_all_items') == 'on'
        
        bundle = ProductBundle(
            name=name,
            slug=slug,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            bundle_price_cents=bundle_price_cents,
            is_active=is_active,
            requires_all_items=requires_all_items
        )
        
        db.session.add(bundle)
        db.session.commit()
        
        # Add bundle items
        product_ids = request.form.getlist('product_ids[]')
        quantities = request.form.getlist('quantities[]')
        optionals = request.form.getlist('optionals[]')
        
        for i, pid in enumerate(product_ids):
            if pid:
                item = BundleItem(
                    bundle_id=bundle.id,
                    product_id=int(pid),
                    quantity=int(quantities[i]) if i < len(quantities) and quantities[i] else 1,
                    is_optional=str(i) in optionals
                )
                db.session.add(item)
        
        db.session.commit()
        
        flash(f'Bundle "{name}" created successfully!', 'success')
        return redirect(url_for('ecommerce_admin.list_bundles'))
    
    products = Product.query.order_by(Product.name).all()
    return render_template('admin/ecommerce/bundles/form.html', bundle=None, products=products)


@ecommerce_admin_bp.route('/bundles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_bundle(id):
    """Edit an existing bundle."""
    bundle = ProductBundle.query.get_or_404(id)
    
    if request.method == 'POST':
        bundle.name = request.form.get('name')
        bundle.slug = slugify(request.form.get('slug') or bundle.name)
        bundle.description = request.form.get('description')
        bundle.discount_type = request.form.get('discount_type', 'percentage')
        bundle.discount_value = int(request.form.get('discount_value', 0))
        bundle_price = request.form.get('bundle_price')
        bundle.bundle_price_cents = int(float(bundle_price) * 100) if bundle_price else None
        bundle.is_active = request.form.get('is_active') == 'on'
        bundle.requires_all_items = request.form.get('requires_all_items') == 'on'
        
        # Clear and re-add items
        BundleItem.query.filter_by(bundle_id=bundle.id).delete()
        
        product_ids = request.form.getlist('product_ids[]')
        quantities = request.form.getlist('quantities[]')
        optionals = request.form.getlist('optionals[]')
        
        for i, pid in enumerate(product_ids):
            if pid:
                item = BundleItem(
                    bundle_id=bundle.id,
                    product_id=int(pid),
                    quantity=int(quantities[i]) if i < len(quantities) and quantities[i] else 1,
                    is_optional=str(i) in optionals
                )
                db.session.add(item)
        
        db.session.commit()
        flash('Bundle updated successfully!', 'success')
        return redirect(url_for('ecommerce_admin.list_bundles'))
    
    products = Product.query.order_by(Product.name).all()
    return render_template('admin/ecommerce/bundles/form.html', bundle=bundle, products=products)


@ecommerce_admin_bp.route('/bundles/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_bundle(id):
    """Delete a bundle."""
    bundle = ProductBundle.query.get_or_404(id)
    name = bundle.name
    db.session.delete(bundle)
    db.session.commit()
    flash(f'Bundle "{name}" deleted.', 'success')
    return redirect(url_for('ecommerce_admin.list_bundles'))


# =============================================================================
# Discounts Management
# =============================================================================

@ecommerce_admin_bp.route('/discounts')
@login_required
@role_required('admin')
def list_discounts():
    """List all discounts."""
    import json
    discounts = Discount.query.order_by(Discount.created_at.desc()).all()
    
    # Serialize for React AdminDataTable
    def get_type_badge(d):
        if d.discount_type == 'percentage':
            return '<span class="badge bg-primary">Percentage</span>'
        elif d.discount_type == 'fixed_amount':
            return '<span class="badge bg-success">Fixed Amount</span>'
        elif d.discount_type == 'free_shipping':
            return '<span class="badge bg-warning">Free Shipping</span>'
        return f'<span class="badge bg-secondary">{d.discount_type}</span>'
    
    def get_value_display(d):
        if d.discount_type == 'percentage':
            return f'{d.value}%'
        elif d.discount_type == 'fixed_amount':
            return f'${d.value / 100:.2f}'
        return '-'
    
    def get_status_badge(d):
        valid, _ = d.is_valid(0)
        if valid:
            return '<span class="badge bg-success">Active</span>'
        return '<span class="badge bg-danger">Inactive</span>'
    
    discounts_json = json.dumps([
        {
            'id': d.id,
            'code': f'<code class="bg-light px-2 py-1">{d.code}</code>' if d.code else '<span class="badge bg-info">Auto-Apply</span>',
            'name': d.name,
            'type': get_type_badge(d),
            'value': get_value_display(d),
            'uses': f'{d.used_count}{f" / {d.maximum_uses}" if d.maximum_uses else ""}',
            'status': get_status_badge(d),
            'actions': f'''<a href="{url_for('ecommerce_admin.edit_discount', id=d.id)}" class="btn btn-sm btn-outline-primary"><i class="fas fa-edit"></i></a>
                <a href="{url_for('ecommerce_admin.discount_usage', id=d.id)}" class="btn btn-sm btn-outline-info"><i class="fas fa-chart-bar"></i></a>'''
        }
        for d in discounts
    ])
    
    return render_template('admin/ecommerce/discounts/index.html', discounts=discounts, discounts_json=discounts_json)


@ecommerce_admin_bp.route('/discounts/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_discount():
    """Create a new discount."""
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code', '').upper() or generate_discount_code()
        discount_type = request.form.get('discount_type', 'percentage')
        value = int(request.form.get('value', 0))
        min_order = request.form.get('minimum_order')
        minimum_order_cents = int(float(min_order) * 100) if min_order else 0
        max_discount = request.form.get('maximum_discount')
        maximum_discount_cents = int(float(max_discount) * 100) if max_discount else None
        maximum_uses = request.form.get('maximum_uses')
        maximum_uses = int(maximum_uses) if maximum_uses else None
        is_active = request.form.get('is_active') == 'on'
        is_automatic = request.form.get('is_automatic') == 'on'
        combine = request.form.get('combine_with_other_discounts') == 'on'
        starts_at = request.form.get('starts_at')
        ends_at = request.form.get('ends_at')
        
        discount = Discount(
            name=name,
            code=code if not is_automatic else None,
            discount_type=discount_type,
            value=value,
            minimum_order_cents=minimum_order_cents,
            maximum_discount_cents=maximum_discount_cents,
            maximum_uses=maximum_uses,
            is_active=is_active,
            is_automatic=is_automatic,
            combine_with_other_discounts=combine,
            starts_at=datetime.fromisoformat(starts_at) if starts_at else None,
            ends_at=datetime.fromisoformat(ends_at) if ends_at else None,
            created_by_id=current_user.id
        )
        
        db.session.add(discount)
        db.session.commit()
        
        flash(f'Discount "{name}" created with code: {code}', 'success')
        return redirect(url_for('ecommerce_admin.list_discounts'))
    
    return render_template('admin/ecommerce/discounts/form.html', discount=None)


@ecommerce_admin_bp.route('/discounts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_discount(id):
    """Edit an existing discount."""
    discount = Discount.query.get_or_404(id)
    
    if request.method == 'POST':
        discount.name = request.form.get('name')
        discount.discount_type = request.form.get('discount_type', 'percentage')
        discount.value = int(request.form.get('value', 0))
        min_order = request.form.get('minimum_order')
        discount.minimum_order_cents = int(float(min_order) * 100) if min_order else 0
        max_discount = request.form.get('maximum_discount')
        discount.maximum_discount_cents = int(float(max_discount) * 100) if max_discount else None
        maximum_uses = request.form.get('maximum_uses')
        discount.maximum_uses = int(maximum_uses) if maximum_uses else None
        discount.is_active = request.form.get('is_active') == 'on'
        discount.combine_with_other_discounts = request.form.get('combine_with_other_discounts') == 'on'
        starts_at = request.form.get('starts_at')
        ends_at = request.form.get('ends_at')
        discount.starts_at = datetime.fromisoformat(starts_at) if starts_at else None
        discount.ends_at = datetime.fromisoformat(ends_at) if ends_at else None
        
        db.session.commit()
        flash('Discount updated successfully!', 'success')
        return redirect(url_for('ecommerce_admin.list_discounts'))
    
    return render_template('admin/ecommerce/discounts/form.html', discount=discount)


@ecommerce_admin_bp.route('/discounts/<int:id>/usage')
@login_required
@role_required('admin')
def discount_usage(id):
    """View discount usage analytics."""
    discount = Discount.query.get_or_404(id)
    usages = DiscountUsage.query.filter_by(discount_id=id)\
        .order_by(DiscountUsage.used_at.desc()).limit(100).all()
    
    total_saved = db.session.query(db.func.sum(DiscountUsage.amount_saved_cents))\
        .filter_by(discount_id=id).scalar() or 0
    
    return render_template('admin/ecommerce/discounts/usage.html', 
                          discount=discount, usages=usages, total_saved=total_saved)


@ecommerce_admin_bp.route('/discounts/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_discount(id):
    """Delete a discount."""
    discount = Discount.query.get_or_404(id)
    name = discount.name
    db.session.delete(discount)
    db.session.commit()
    flash(f'Discount "{name}" deleted.', 'success')
    return redirect(url_for('ecommerce_admin.list_discounts'))


# =============================================================================
# Gift Cards Management
# =============================================================================

@ecommerce_admin_bp.route('/gift-cards')
@login_required
@role_required('admin')
def list_gift_cards():
    """List all gift cards."""
    import json
    gift_cards = GiftCard.query.order_by(GiftCard.created_at.desc()).all()
    
    # Serialize for React AdminDataTable
    def get_status_badge(gc):
        if gc.is_active and gc.current_balance_cents > 0:
            return '<span class="badge bg-success">Active</span>'
        elif not gc.is_active:
            return '<span class="badge bg-danger">Deactivated</span>'
        return '<span class="badge bg-secondary">Depleted</span>'
    
    def get_balance_display(gc):
        balance_class = 'text-success' if gc.current_balance_cents > 0 else 'text-muted'
        return f'<strong class="{balance_class}">${gc.current_balance_cents / 100:.2f}</strong>'
    
    gift_cards_json = json.dumps([
        {
            'id': gc.id,
            'code': f'<code class="bg-light px-2 py-1">{gc.code}</code>',
            'recipient': gc.recipient_name or gc.recipient_email or '<span class="text-muted">-</span>',
            'initial': f'${gc.initial_balance_cents / 100:.2f}',
            'balance': get_balance_display(gc),
            'status': get_status_badge(gc),
            'expires': gc.expires_at.strftime('%Y-%m-%d') if gc.expires_at else '<span class="text-muted">Never</span>',
            'actions': f'<a href="{url_for("ecommerce_admin.gift_card_detail", id=gc.id)}" class="btn btn-sm btn-outline-primary"><i class="fas fa-eye"></i></a>'
        }
        for gc in gift_cards
    ])
    
    # Calculate summary stats
    total_issued = sum(gc.initial_balance_cents for gc in gift_cards) / 100
    outstanding = sum(gc.current_balance_cents for gc in gift_cards) / 100
    active_count = len([gc for gc in gift_cards if gc.is_active])
    
    return render_template('admin/ecommerce/gift-cards/index.html', 
                          gift_cards=gift_cards,
                          gift_cards_json=gift_cards_json,
                          total_issued=total_issued,
                          outstanding=outstanding,
                          active_count=active_count)


@ecommerce_admin_bp.route('/gift-cards/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_gift_card():
    """Issue a new gift card."""
    if request.method == 'POST':
        amount = request.form.get('amount')
        amount_cents = int(float(amount) * 100)
        recipient_email = request.form.get('recipient_email')
        recipient_name = request.form.get('recipient_name')
        sender_name = request.form.get('sender_name')
        message = request.form.get('message')
        expires_at = request.form.get('expires_at')
        
        code = generate_gift_card_code()
        
        gift_card = GiftCard(
            code=code,
            initial_balance_cents=amount_cents,
            current_balance_cents=amount_cents,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            sender_name=sender_name,
            message=message,
            expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
            created_by_id=current_user.id,
            is_active=True
        )
        
        db.session.add(gift_card)
        db.session.commit()
        
        # Create initial transaction
        transaction = GiftCardTransaction(
            gift_card_id=gift_card.id,
            amount_cents=amount_cents,
            transaction_type='purchase',
            note='Initial balance - Admin issued',
            created_by_id=current_user.id
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Gift card created with code: {code}', 'success')
        return redirect(url_for('ecommerce_admin.list_gift_cards'))
    
    return render_template('admin/ecommerce/gift-cards/form.html')


@ecommerce_admin_bp.route('/gift-cards/<int:id>')
@login_required
@role_required('admin')
def gift_card_detail(id):
    """View gift card details and transactions."""
    gift_card = GiftCard.query.get_or_404(id)
    transactions = GiftCardTransaction.query.filter_by(gift_card_id=id)\
        .order_by(GiftCardTransaction.created_at.desc()).all()
    
    return render_template('admin/ecommerce/gift-cards/detail.html', 
                          gift_card=gift_card, transactions=transactions)


@ecommerce_admin_bp.route('/gift-cards/<int:id>/adjust', methods=['POST'])
@login_required
@role_required('admin')
def adjust_gift_card(id):
    """Manual balance adjustment for a gift card."""
    gift_card = GiftCard.query.get_or_404(id)
    
    adjustment = request.form.get('adjustment')
    adjustment_cents = int(float(adjustment) * 100)
    note = request.form.get('note', 'Admin adjustment')
    
    gift_card.current_balance_cents += adjustment_cents
    
    transaction = GiftCardTransaction(
        gift_card_id=gift_card.id,
        amount_cents=adjustment_cents,
        transaction_type='adjustment',
        note=note,
        created_by_id=current_user.id
    )
    db.session.add(transaction)
    db.session.commit()
    
    flash(f'Gift card balance adjusted by ${adjustment_cents/100:.2f}', 'success')
    return redirect(url_for('ecommerce_admin.gift_card_detail', id=id))


@ecommerce_admin_bp.route('/gift-cards/<int:id>/deactivate', methods=['POST'])
@login_required
@role_required('admin')
def deactivate_gift_card(id):
    """Deactivate a gift card."""
    gift_card = GiftCard.query.get_or_404(id)
    gift_card.is_active = False
    db.session.commit()
    flash('Gift card deactivated.', 'success')
    return redirect(url_for('ecommerce_admin.gift_card_detail', id=id))


# =============================================================================
# Shipping Configuration
# =============================================================================

@ecommerce_admin_bp.route('/shipping')
@login_required
@role_required('admin')
def shipping_config():
    """Shipping zone and rate configuration."""
    zones = ShippingZone.query.order_by(ShippingZone.name).all()
    return render_template('admin/ecommerce/shipping/index.html', zones=zones)


@ecommerce_admin_bp.route('/shipping/zones', methods=['POST'])
@login_required
@role_required('admin')
def create_shipping_zone():
    """Create a new shipping zone."""
    name = request.form.get('name')
    countries = request.form.get('countries', '').split(',')
    countries = [c.strip().upper() for c in countries if c.strip()]
    states = request.form.get('states', '').split(',')
    states = [s.strip().upper() for s in states if s.strip()]
    is_rest_of_world = request.form.get('is_rest_of_world') == 'on'
    
    zone = ShippingZone(
        name=name,
        countries=countries,
        states=states,
        is_rest_of_world=is_rest_of_world,
        is_active=True
    )
    
    db.session.add(zone)
    db.session.commit()
    
    flash(f'Shipping zone "{name}" created.', 'success')
    return redirect(url_for('ecommerce_admin.shipping_config'))


@ecommerce_admin_bp.route('/shipping/rates', methods=['POST'])
@login_required
@role_required('admin')
def create_shipping_rate():
    """Add a shipping rate to a zone."""
    zone_id = request.form.get('zone_id')
    name = request.form.get('name')
    rate_type = request.form.get('rate_type', 'flat')
    price = request.form.get('price', 0)
    price_cents = int(float(price) * 100)
    free_threshold = request.form.get('free_shipping_threshold')
    free_threshold_cents = int(float(free_threshold) * 100) if free_threshold else None
    days_min = request.form.get('estimated_days_min')
    days_max = request.form.get('estimated_days_max')
    
    rate = ShippingRate(
        zone_id=int(zone_id),
        name=name,
        rate_type=rate_type,
        price_cents=price_cents,
        free_shipping_threshold_cents=free_threshold_cents,
        estimated_days_min=int(days_min) if days_min else None,
        estimated_days_max=int(days_max) if days_max else None,
        is_active=True
    )
    
    db.session.add(rate)
    db.session.commit()
    
    flash(f'Shipping rate "{name}" added.', 'success')
    return redirect(url_for('ecommerce_admin.shipping_config'))


@ecommerce_admin_bp.route('/shipping/zones/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_shipping_zone(id):
    """Delete a shipping zone."""
    zone = ShippingZone.query.get_or_404(id)
    name = zone.name
    db.session.delete(zone)
    db.session.commit()
    flash(f'Shipping zone "{name}" deleted.', 'success')
    return redirect(url_for('ecommerce_admin.shipping_config'))


@ecommerce_admin_bp.route('/shipping/rates/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_shipping_rate(id):
    """Delete a shipping rate."""
    rate = ShippingRate.query.get_or_404(id)
    db.session.delete(rate)
    db.session.commit()
    flash('Shipping rate deleted.', 'success')
    return redirect(url_for('ecommerce_admin.shipping_config'))


# =============================================================================
# Tax Configuration
# =============================================================================

@ecommerce_admin_bp.route('/tax')
@login_required
@role_required('admin')
def tax_config():
    """Tax rate configuration."""
    rates = TaxRate.query.order_by(TaxRate.priority, TaxRate.country, TaxRate.state).all()
    return render_template('admin/ecommerce/tax/index.html', rates=rates)


@ecommerce_admin_bp.route('/tax/rates', methods=['POST'])
@login_required
@role_required('admin')
def create_tax_rate():
    """Create a new tax rate."""
    name = request.form.get('name')
    rate = float(request.form.get('rate', 0)) / 100  # Convert percentage to decimal
    country = request.form.get('country', '').upper() or None
    state = request.form.get('state', '').upper() or None
    zip_code = request.form.get('zip_code') or None
    tax_type = request.form.get('tax_type', 'sales')
    applies_to_shipping = request.form.get('applies_to_shipping') == 'on'
    is_compound = request.form.get('is_compound') == 'on'
    priority = int(request.form.get('priority', 0))
    
    tax_rate = TaxRate(
        name=name,
        rate=rate,
        country=country,
        state=state,
        zip_code=zip_code,
        tax_type=tax_type,
        applies_to_shipping=applies_to_shipping,
        is_compound=is_compound,
        priority=priority,
        is_active=True
    )
    
    db.session.add(tax_rate)
    db.session.commit()
    
    flash(f'Tax rate "{name}" created.', 'success')
    return redirect(url_for('ecommerce_admin.tax_config'))


@ecommerce_admin_bp.route('/tax/rates/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_tax_rate(id):
    """Delete a tax rate."""
    rate = TaxRate.query.get_or_404(id)
    name = rate.name
    db.session.delete(rate)
    db.session.commit()
    flash(f'Tax rate "{name}" deleted.', 'success')
    return redirect(url_for('ecommerce_admin.tax_config'))


# =============================================================================
# Attributes Management
# =============================================================================

@ecommerce_admin_bp.route('/attributes')
@login_required
@role_required('admin')
def list_attributes():
    """List all product attributes."""
    attributes = ProductAttribute.query.order_by(ProductAttribute.position, ProductAttribute.name).all()
    return render_template('admin/ecommerce/attributes/index.html', attributes=attributes)


@ecommerce_admin_bp.route('/attributes/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_attribute():
    """Create a new product attribute."""
    if request.method == 'POST':
        name = request.form.get('name')
        slug = slugify(name)
        attribute_type = request.form.get('attribute_type', 'select')
        is_required = request.form.get('is_required') == 'on'
        
        attribute = ProductAttribute(
            name=name,
            slug=slug,
            attribute_type=attribute_type,
            is_required=is_required
        )
        
        db.session.add(attribute)
        db.session.commit()
        
        # Add values
        values = request.form.getlist('values[]')
        color_hexes = request.form.getlist('color_hexes[]')
        
        for i, v in enumerate(values):
            if v:
                attr_value = ProductAttributeValue(
                    attribute_id=attribute.id,
                    value=v,
                    slug=slugify(v),
                    color_hex=color_hexes[i] if i < len(color_hexes) and color_hexes[i] else None,
                    position=i
                )
                db.session.add(attr_value)
        
        db.session.commit()
        
        flash(f'Attribute "{name}" created.', 'success')
        return redirect(url_for('ecommerce_admin.list_attributes'))
    
    return render_template('admin/ecommerce/attributes/form.html', attribute=None)


@ecommerce_admin_bp.route('/attributes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_attribute(id):
    """Edit an existing attribute."""
    attribute = ProductAttribute.query.get_or_404(id)
    
    if request.method == 'POST':
        attribute.name = request.form.get('name')
        attribute.slug = slugify(attribute.name)
        attribute.attribute_type = request.form.get('attribute_type', 'select')
        attribute.is_required = request.form.get('is_required') == 'on'
        
        # Clear and re-add values
        ProductAttributeValue.query.filter_by(attribute_id=attribute.id).delete()
        
        values = request.form.getlist('values[]')
        color_hexes = request.form.getlist('color_hexes[]')
        
        for i, v in enumerate(values):
            if v:
                attr_value = ProductAttributeValue(
                    attribute_id=attribute.id,
                    value=v,
                    slug=slugify(v),
                    color_hex=color_hexes[i] if i < len(color_hexes) and color_hexes[i] else None,
                    position=i
                )
                db.session.add(attr_value)
        
        db.session.commit()
        flash('Attribute updated.', 'success')
        return redirect(url_for('ecommerce_admin.list_attributes'))
    
    return render_template('admin/ecommerce/attributes/form.html', attribute=attribute)


@ecommerce_admin_bp.route('/attributes/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_attribute(id):
    """Delete an attribute."""
    attribute = ProductAttribute.query.get_or_404(id)
    name = attribute.name
    db.session.delete(attribute)
    db.session.commit()
    flash(f'Attribute "{name}" deleted.', 'success')
    return redirect(url_for('ecommerce_admin.list_attributes'))


# =============================================================================
# Product Variants Management
# =============================================================================

@ecommerce_admin_bp.route('/products/<int:product_id>/variants')
@login_required
@role_required('admin')
def list_variants(product_id):
    """List all variants for a product."""
    product = Product.query.get_or_404(product_id)
    variants = ProductVariant.query.filter_by(product_id=product_id).order_by(ProductVariant.name).all()
    return render_template('admin/ecommerce/variants/index.html', product=product, variants=variants)


@ecommerce_admin_bp.route('/products/<int:product_id>/variants/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_variant(product_id):
    """Create a new product variant."""
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        sku = request.form.get('sku')
        price_adjustment = int(float(request.form.get('price_adjustment', 0)) * 100)  # Convert to cents
        inventory_count = int(request.form.get('inventory_count', 0))
        is_active = request.form.get('is_active') == 'on'
        
        # Parse attributes from form
        attributes = {}
        for key in request.form:
            if key.startswith('attr_'):
                attr_name = key.replace('attr_', '')
                attributes[attr_name] = request.form.get(key)
        
        # Validate SKU uniqueness
        existing = ProductVariant.query.filter_by(sku=sku).first()
        if existing:
            flash(f'SKU "{sku}" already exists.', 'danger')
            return render_template('admin/ecommerce/variants/form.html', product=product, variant=None)
        
        variant = ProductVariant(
            product_id=product_id,
            name=name,
            sku=sku,
            price_adjustment=price_adjustment,
            inventory_count=inventory_count,
            is_active=is_active,
            attributes=attributes
        )
        
        db.session.add(variant)
        db.session.commit()
        
        flash(f'Variant "{name}" created.', 'success')
        return redirect(url_for('ecommerce_admin.list_variants', product_id=product_id))
    
    return render_template('admin/ecommerce/variants/form.html', product=product, variant=None)


@ecommerce_admin_bp.route('/variants/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_variant(id):
    """Edit a product variant."""
    variant = ProductVariant.query.get_or_404(id)
    product = variant.product
    
    if request.method == 'POST':
        variant.name = request.form.get('name')
        new_sku = request.form.get('sku')
        
        # Validate SKU uniqueness if changed
        if new_sku != variant.sku:
            existing = ProductVariant.query.filter_by(sku=new_sku).first()
            if existing:
                flash(f'SKU "{new_sku}" already exists.', 'danger')
                return render_template('admin/ecommerce/variants/form.html', product=product, variant=variant)
        
        variant.sku = new_sku
        variant.price_adjustment = int(float(request.form.get('price_adjustment', 0)) * 100)
        variant.inventory_count = int(request.form.get('inventory_count', 0))
        variant.is_active = request.form.get('is_active') == 'on'
        
        # Parse attributes
        attributes = {}
        for key in request.form:
            if key.startswith('attr_'):
                attr_name = key.replace('attr_', '')
                attributes[attr_name] = request.form.get(key)
        variant.attributes = attributes
        
        db.session.commit()
        flash('Variant updated.', 'success')
        return redirect(url_for('ecommerce_admin.list_variants', product_id=product.id))
    
    return render_template('admin/ecommerce/variants/form.html', product=product, variant=variant)


@ecommerce_admin_bp.route('/variants/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_variant(id):
    """Delete a product variant."""
    variant = ProductVariant.query.get_or_404(id)
    product_id = variant.product_id
    name = variant.name
    db.session.delete(variant)
    db.session.commit()
    flash(f'Variant "{name}" deleted.', 'success')
    return redirect(url_for('ecommerce_admin.list_variants', product_id=product_id))


@ecommerce_admin_bp.route('/variants/<int:id>/json')
@login_required
@role_required('admin')
def get_variant_json(id):
    """Get variant data as JSON for AJAX."""
    variant = ProductVariant.query.get_or_404(id)
    return jsonify({
        'id': variant.id,
        'name': variant.name,
        'sku': variant.sku,
        'price_adjustment': variant.price_adjustment / 100,
        'inventory_count': variant.inventory_count,
        'is_active': variant.is_active,
        'attributes': variant.attributes,
        'final_price': variant.get_price() / 100
    })


# =============================================================================
# Discount Rules Management
# =============================================================================

@ecommerce_admin_bp.route('/discounts/<int:discount_id>/rules')
@login_required
@role_required('admin')
def list_discount_rules(discount_id):
    """List all rules for a discount."""
    discount = Discount.query.get_or_404(discount_id)
    rules = DiscountRule.query.filter_by(discount_id=discount_id).all()
    return render_template('admin/ecommerce/discounts/rules.html', discount=discount, rules=rules)


@ecommerce_admin_bp.route('/discounts/<int:discount_id>/rules/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_discount_rule(discount_id):
    """Create a new discount rule."""
    discount = Discount.query.get_or_404(discount_id)
    
    if request.method == 'POST':
        rule_type = request.form.get('rule_type')
        condition = request.form.get('condition')
        value = request.form.get('value')
        
        rule = DiscountRule(
            discount_id=discount_id,
            rule_type=rule_type,
            condition=condition,
            value=value
        )
        
        db.session.add(rule)
        db.session.commit()
        
        flash(f'Rule added to "{discount.code}".', 'success')
        return redirect(url_for('ecommerce_admin.list_discount_rules', discount_id=discount_id))
    
    # Rule type options
    rule_types = [
        ('min_quantity', 'Minimum Quantity'),
        ('min_amount', 'Minimum Order Amount'),
        ('customer_tag', 'Customer Tag'),
        ('first_order', 'First Order Only'),
        ('specific_product', 'Specific Product'),
        ('specific_collection', 'Specific Collection'),
    ]
    
    conditions = [
        ('equals', 'Equals'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('contains', 'Contains'),
    ]
    
    return render_template('admin/ecommerce/discounts/rule_form.html', 
                          discount=discount, rule=None, 
                          rule_types=rule_types, conditions=conditions)


@ecommerce_admin_bp.route('/rules/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_discount_rule(id):
    """Edit a discount rule."""
    rule = DiscountRule.query.get_or_404(id)
    discount = Discount.query.get_or_404(rule.discount_id)
    
    if request.method == 'POST':
        rule.rule_type = request.form.get('rule_type')
        rule.condition = request.form.get('condition')
        rule.value = request.form.get('value')
        
        db.session.commit()
        flash('Rule updated.', 'success')
        return redirect(url_for('ecommerce_admin.list_discount_rules', discount_id=discount.id))
    
    rule_types = [
        ('min_quantity', 'Minimum Quantity'),
        ('min_amount', 'Minimum Order Amount'),
        ('customer_tag', 'Customer Tag'),
        ('first_order', 'First Order Only'),
        ('specific_product', 'Specific Product'),
        ('specific_collection', 'Specific Collection'),
    ]
    
    conditions = [
        ('equals', 'Equals'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('contains', 'Contains'),
    ]
    
    return render_template('admin/ecommerce/discounts/rule_form.html',
                          discount=discount, rule=rule,
                          rule_types=rule_types, conditions=conditions)


@ecommerce_admin_bp.route('/rules/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_discount_rule(id):
    """Delete a discount rule."""
    rule = DiscountRule.query.get_or_404(id)
    discount_id = rule.discount_id
    db.session.delete(rule)
    db.session.commit()
    flash('Rule deleted.', 'success')
    return redirect(url_for('ecommerce_admin.list_discount_rules', discount_id=discount_id))


@ecommerce_admin_bp.route('/api/discounts/<int:discount_id>/evaluate', methods=['POST'])
@login_required
@role_required('admin')
def evaluate_discount_rules(discount_id):
    """Evaluate discount rules against test data (for admin testing)."""
    discount = Discount.query.get_or_404(discount_id)
    rules = DiscountRule.query.filter_by(discount_id=discount_id).all()
    
    if not rules:
        return jsonify({'valid': True, 'message': 'No rules to evaluate'})
    
    data = request.get_json() or {}
    results = []
    all_pass = True
    
    for rule in rules:
        passed = False
        test_value = data.get(rule.rule_type)
        
        if test_value is not None:
            if rule.condition == 'equals':
                passed = str(test_value) == rule.value
            elif rule.condition == 'greater_than':
                passed = float(test_value) > float(rule.value)
            elif rule.condition == 'less_than':
                passed = float(test_value) < float(rule.value)
            elif rule.condition == 'contains':
                passed = rule.value in str(test_value)
        
        results.append({
            'rule_type': rule.rule_type,
            'condition': rule.condition,
            'value': rule.value,
            'passed': passed
        })
        
        if not passed:
            all_pass = False
    
    return jsonify({
        'valid': all_pass,
        'rules_evaluated': len(rules),
        'results': results
    })

