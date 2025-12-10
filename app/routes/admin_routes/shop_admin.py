from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models import Product, Media, db
from app.modules.decorators import role_required
from datetime import datetime
from werkzeug.utils import secure_filename

shop_admin_bp = Blueprint('shop_admin', __name__, url_prefix='/admin/shop')

@shop_admin_bp.route('/products')
@login_required
@role_required('admin')
def products():
    import json
    from app.forms import CSRFTokenForm
    
    product_list = Product.query.order_by(Product.created_at.desc()).all()
    form = CSRFTokenForm()
    
    # Serialize for AdminDataTable
    products_json = json.dumps([{
        'id': p.id,
        'image': f'<img src="{url_for("media_bp.serve_media", media_id=p.media_id)}" alt="{p.name}" style="height: 50px; width: 50px; object-fit: cover;">' if p.image else '<span class="text-muted">No Image</span>',
        'name': p.name,
        'price': f'${p.price / 100:.2f}',
        'inventory': str(p.inventory_count),
        'type': '<span class="badge bg-info">Digital</span>' if p.is_digital else '<span class="badge bg-secondary">Physical</span>',
        'actions': (
            f'<a href="{url_for("shop_admin.edit_product", id=p.id)}" class="btn btn-sm btn-info"><i class="fas fa-edit"></i> Edit</a> '
            f'<form action="{url_for("shop_admin.delete_product", id=p.id)}" method="POST" class="d-inline" onsubmit="return confirm(\'Delete this product?\');"><input type="hidden" name="csrf_token" value="{form.csrf_token._value()}" /><button type="submit" class="btn btn-sm btn-danger"><i class="fas fa-trash"></i></button></form>'
        )
    } for p in product_list])
    
    return render_template('admin/shop/products.html', products=product_list, products_json=products_json)

@shop_admin_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price_dollars = request.form.get('price') # Input as dollars
        price_cents = int(float(price_dollars) * 100)
        inventory = int(request.form.get('inventory'))
        is_digital = request.form.get('is_digital') == 'on'
        
        # Image Upload
        image_file = request.files.get('image')
        media_id = None
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            mimetype = image_file.mimetype
            data = image_file.read()
            
            media = Media(
                filename=filename,
                data=data,
                mimetype=mimetype,
                size=len(data),
                uploaded_by_id=current_user.id
            )
            db.session.add(media)
            db.session.flush() # Get ID
            media_id = media.id
            
        product = Product(
            name=name,
            description=description,
            price=price_cents,
            inventory_count=inventory,
            is_digital=is_digital,
            media_id=media_id
        )
        db.session.add(product)
        db.session.commit()
        flash('Product created successfully!', 'success')
        return redirect(url_for('shop_admin.products'))
        
    return render_template('admin/shop/create_product.html')

@shop_admin_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        price_dollars = request.form.get('price')
        product.price = int(float(price_dollars) * 100)
        product.inventory_count = int(request.form.get('inventory'))
        product.is_digital = request.form.get('is_digital') == 'on'
        
        # Image Update
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            mimetype = image_file.mimetype
            data = image_file.read()
            
            media = Media(
                filename=filename,
                data=data,
                mimetype=mimetype,
                size=len(data),
                uploaded_by_id=current_user.id
            )
            db.session.add(media)
            db.session.flush()
            product.media_id = media.id
            
        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('shop_admin.products'))
        
    return render_template('admin/shop/edit_product.html', product=product)

@shop_admin_bp.route('/products/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'success')
    return redirect(url_for('shop_admin.products'))
