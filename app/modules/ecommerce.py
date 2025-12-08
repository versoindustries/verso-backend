"""
E-Commerce Business Logic Module

Core calculation functions for discounts, shipping, tax, gift cards,
and cart totals. Used by cart routes and checkout flow.
"""

from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from flask import current_app
from flask_login import current_user
from app.database import db


def get_cart_subtotal(cart_items: List[Dict]) -> int:
    """
    Calculate cart subtotal in cents.
    
    Args:
        cart_items: List of dicts with 'product', 'variant', 'quantity', 'price'
        
    Returns:
        Subtotal in cents
    """
    total = 0
    for item in cart_items:
        price = item.get('price', 0)
        quantity = item.get('quantity', 1)
        total += price * quantity
    return total


def validate_discount(discount, cart_items: List[Dict], user=None) -> Tuple[bool, Optional[str]]:
    """
    Check if a discount code is valid for the given cart and user.
    
    Args:
        discount: Discount model instance
        cart_items: Cart items list
        user: Optional User model instance
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if discount is None:
        return False, "Discount not found"
    
    subtotal = get_cart_subtotal(cart_items)
    return discount.is_valid(subtotal, user)


def apply_discount(cart_items: List[Dict], discount) -> Tuple[int, List[Dict]]:
    """
    Apply discount to cart items and return savings.
    
    Args:
        cart_items: Cart items list
        discount: Discount model instance
        
    Returns:
        Tuple of (savings_cents, updated_cart_items)
    """
    if discount is None:
        return 0, cart_items
    
    subtotal = get_cart_subtotal(cart_items)
    
    # Check if discount applies to specific products/collections
    if discount.applies_to == 'specific_products':
        applicable_total = sum(
            item['price'] * item['quantity']
            for item in cart_items
            if item.get('product_id') in (discount.applies_to_ids or [])
        )
        savings = discount.calculate_savings(applicable_total)
    elif discount.applies_to == 'specific_collections':
        # Would need to check each product's collection membership
        # For now, apply to all if any product is in a collection
        savings = discount.calculate_savings(subtotal)
    else:
        savings = discount.calculate_savings(subtotal)
    
    return savings, cart_items


def validate_gift_card(gift_card) -> Tuple[bool, Optional[str]]:
    """
    Check if a gift card is valid for use.
    
    Args:
        gift_card: GiftCard model instance
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if gift_card is None:
        return False, "Gift card not found"
    
    return gift_card.is_valid()


def apply_gift_card(gift_card, amount_cents: int, order_id: int) -> int:
    """
    Apply gift card to payment and return amount applied.
    
    Args:
        gift_card: GiftCard model instance
        amount_cents: Amount to apply (up to balance)
        order_id: Order ID for transaction tracking
        
    Returns:
        Amount actually applied in cents
    """
    if gift_card is None:
        return 0
    
    return gift_card.redeem(amount_cents, order_id)


def match_shipping_zone(country: str, state: Optional[str] = None, 
                        zip_code: Optional[str] = None):
    """
    Find the shipping zone that matches the given address.
    
    Args:
        country: ISO 2-letter country code
        state: State/province code
        zip_code: ZIP/postal code
        
    Returns:
        ShippingZone instance or None
    """
    from app.models import ShippingZone
    
    zones = ShippingZone.query.filter_by(is_active=True).all()
    
    # First pass: look for specific matches (zip > state > country)
    for zone in zones:
        if not zone.is_rest_of_world and zone.matches_address(country, state, zip_code):
            return zone
    
    # Second pass: look for rest-of-world fallback
    for zone in zones:
        if zone.is_rest_of_world:
            return zone
    
    return None


def calculate_shipping(items: List[Dict], country: str, state: Optional[str] = None,
                       zip_code: Optional[str] = None, 
                       selected_rate_id: Optional[int] = None) -> Tuple[int, List[Dict]]:
    """
    Calculate shipping rates for the given items and destination.
    
    Args:
        items: Cart items list
        country: Destination country code
        state: Destination state code
        zip_code: Destination ZIP code
        selected_rate_id: Specific rate to use (optional)
        
    Returns:
        Tuple of (shipping_cents, available_rates_list)
    """
    from app.models import ShippingRate
    
    zone = match_shipping_zone(country, state, zip_code)
    if zone is None:
        return 0, []
    
    subtotal = get_cart_subtotal(items)
    
    # Calculate total weight if products have weight
    weight_grams = sum(
        (item.get('weight_grams', 0) or 0) * item.get('quantity', 1)
        for item in items
    )
    
    # Get applicable rates
    rates = []
    for rate in zone.rates.filter_by(is_active=True).all():
        if rate.is_applicable(subtotal, weight_grams):
            rate_amount = rate.calculate_rate(subtotal, weight_grams)
            rates.append({
                'id': rate.id,
                'name': rate.name,
                'price_cents': rate_amount,
                'estimated_days_min': rate.estimated_days_min,
                'estimated_days_max': rate.estimated_days_max
            })
    
    # Sort by price
    rates.sort(key=lambda r: r['price_cents'])
    
    # Return selected rate or cheapest
    if selected_rate_id:
        for rate in rates:
            if rate['id'] == selected_rate_id:
                return rate['price_cents'], rates
    
    # Return cheapest rate
    if rates:
        return rates[0]['price_cents'], rates
    
    return 0, rates


def calculate_tax(items: List[Dict], country: str, state: Optional[str] = None,
                  zip_code: Optional[str] = None, 
                  shipping_cents: int = 0) -> Tuple[int, List[Dict]]:
    """
    Calculate tax for the given items and destination.
    
    Args:
        items: Cart items list
        country: Destination country code
        state: Destination state code
        zip_code: Destination ZIP code
        shipping_cents: Shipping amount (for taxable shipping)
        
    Returns:
        Tuple of (tax_cents, applied_tax_rates)
    """
    from app.models import TaxRate
    
    subtotal = get_cart_subtotal(items)
    
    # Find applicable tax rates
    applicable_rates = []
    all_rates = TaxRate.query.filter_by(is_active=True).order_by(TaxRate.priority).all()
    
    for rate in all_rates:
        if rate.matches_address(country, state, zip_code):
            applicable_rates.append(rate)
    
    if not applicable_rates:
        return 0, []
    
    # Calculate tax
    total_tax = 0
    taxable_amount = subtotal
    applied_rates = []
    
    for rate in applicable_rates:
        # Add shipping to taxable amount if applicable
        rate_taxable = taxable_amount
        if rate.applies_to_shipping:
            rate_taxable += shipping_cents
        
        # Calculate tax for this rate
        if rate.is_compound:
            # Compound tax: apply to amount + previous taxes
            rate_taxable += total_tax
        
        tax_amount = int(rate_taxable * rate.rate)
        total_tax += tax_amount
        
        applied_rates.append({
            'name': rate.name,
            'rate': rate.rate,
            'amount_cents': tax_amount
        })
    
    return total_tax, applied_rates


def calculate_cart_totals(cart_items: List[Dict], 
                          discount_code: Optional[str] = None,
                          gift_card_code: Optional[str] = None,
                          country: Optional[str] = None,
                          state: Optional[str] = None,
                          zip_code: Optional[str] = None,
                          shipping_rate_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Calculate complete cart totals including subtotal, discount, 
    shipping, tax, gift card, and final total.
    
    Args:
        cart_items: Cart items list
        discount_code: Optional discount/coupon code
        gift_card_code: Optional gift card code
        country: Shipping destination country
        state: Shipping destination state
        zip_code: Shipping destination ZIP
        shipping_rate_id: Selected shipping rate ID
        
    Returns:
        Dict with all calculated values
    """
    from app.models import Discount, GiftCard
    
    result = {
        'subtotal_cents': 0,
        'discount_cents': 0,
        'discount_code': None,
        'discount_name': None,
        'discount_error': None,
        'shipping_cents': 0,
        'shipping_rates': [],
        'tax_cents': 0,
        'tax_rates': [],
        'gift_card_cents': 0,
        'gift_card_code': None,
        'gift_card_balance': 0,
        'gift_card_error': None,
        'total_cents': 0,
        'amount_due_cents': 0  # After gift card
    }
    
    # Calculate subtotal
    result['subtotal_cents'] = get_cart_subtotal(cart_items)
    
    # Apply discount
    if discount_code:
        discount = Discount.query.filter_by(code=discount_code.upper(), is_active=True).first()
        if discount:
            # Handle case where current_user may not be available (e.g., tests)
            try:
                user = current_user if current_user and current_user.is_authenticated else None
            except:
                user = None
            
            is_valid, error = validate_discount(discount, cart_items, user)
            if is_valid:
                savings, _ = apply_discount(cart_items, discount)
                result['discount_cents'] = savings
                result['discount_code'] = discount.code
                result['discount_name'] = discount.name
            else:
                result['discount_error'] = error
        else:
            result['discount_error'] = "Discount code not found"
    
    # Also check for automatic discounts
    auto_discounts = Discount.query.filter_by(is_automatic=True, is_active=True).all()
    for auto_discount in auto_discounts:
        try:
            user = current_user if current_user and current_user.is_authenticated else None
        except:
            user = None
        is_valid, _ = validate_discount(auto_discount, cart_items, user)
        if is_valid and not result['discount_code']:
            savings, _ = apply_discount(cart_items, auto_discount)
            if savings > result['discount_cents']:
                result['discount_cents'] = savings
                result['discount_name'] = auto_discount.name
    
    # Calculate shipping
    if country:
        shipping, rates = calculate_shipping(cart_items, country, state, zip_code, shipping_rate_id)
        result['shipping_cents'] = shipping
        result['shipping_rates'] = rates
    
    # Calculate tax
    if country:
        tax, tax_rates = calculate_tax(cart_items, country, state, zip_code, result['shipping_cents'])
        result['tax_cents'] = tax
        result['tax_rates'] = tax_rates
    
    # Calculate pre-gift-card total
    result['total_cents'] = (
        result['subtotal_cents'] 
        - result['discount_cents'] 
        + result['shipping_cents'] 
        + result['tax_cents']
    )
    
    # Apply gift card
    if gift_card_code:
        gift_card = GiftCard.query.filter_by(code=gift_card_code.upper(), is_active=True).first()
        if gift_card:
            is_valid, error = validate_gift_card(gift_card)
            if is_valid:
                # Don't actually redeem, just show what would be applied
                applicable = min(result['total_cents'], gift_card.current_balance_cents)
                result['gift_card_cents'] = applicable
                result['gift_card_code'] = gift_card.code
                result['gift_card_balance'] = gift_card.current_balance_cents
            else:
                result['gift_card_error'] = error
        else:
            result['gift_card_error'] = "Gift card not found"
    
    # Calculate final amount due (after gift card)
    result['amount_due_cents'] = max(0, result['total_cents'] - result['gift_card_cents'])
    
    return result


def generate_variant_matrix(product, attribute_ids: List[int]) -> List[Dict]:
    """
    Auto-generate all variant combinations from selected attributes.
    
    Args:
        product: Product model instance
        attribute_ids: List of ProductAttribute IDs to combine
        
    Returns:
        List of variant dicts with attribute combinations
    """
    from app.models import ProductAttribute, ProductAttributeValue
    from itertools import product as cartesian_product
    
    # Get all attribute values for selected attributes
    attribute_values = {}
    for attr_id in attribute_ids:
        attr = ProductAttribute.query.get(attr_id)
        if attr:
            values = ProductAttributeValue.query.filter_by(attribute_id=attr_id).order_by(
                ProductAttributeValue.position
            ).all()
            if values:
                attribute_values[attr.name] = [(v.id, v.value, v.slug) for v in values]
    
    if not attribute_values:
        return []
    
    # Generate all combinations
    keys = list(attribute_values.keys())
    value_lists = [attribute_values[k] for k in keys]
    
    variants = []
    for combo in cartesian_product(*value_lists):
        # Build variant name and attributes
        name_parts = [v[1] for v in combo]
        attrs = {keys[i]: combo[i][1] for i in range(len(keys))}
        attr_ids = {keys[i]: combo[i][0] for i in range(len(keys))}
        
        # Generate SKU from product and variant slugs
        sku_parts = [product.id if hasattr(product, 'id') else 'NEW']
        sku_parts.extend([v[2] for v in combo])
        
        variants.append({
            'name': ' / '.join(name_parts),
            'sku': '-'.join(str(p) for p in sku_parts).upper(),
            'attributes': attrs,
            'attribute_value_ids': attr_ids,
            'price_adjustment': 0,
            'inventory_count': 0
        })
    
    return variants


def get_related_products(product_id: int, relation_type: str = 'cross_sell', 
                         limit: int = 4) -> List:
    """
    Get related products for cross-sell/up-sell display.
    
    Args:
        product_id: Source product ID
        relation_type: Type of relation (cross_sell, up_sell, accessory)
        limit: Maximum number of products to return
        
    Returns:
        List of Product model instances
    """
    from app.models import RelatedProduct, Product
    
    relations = RelatedProduct.query.filter_by(
        product_id=product_id,
        relation_type=relation_type
    ).order_by(RelatedProduct.position).limit(limit).all()
    
    product_ids = [r.related_product_id for r in relations]
    
    if not product_ids:
        return []
    
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    
    # Maintain order from relations
    product_map = {p.id: p for p in products}
    return [product_map[pid] for pid in product_ids if pid in product_map]


def get_collection_products(collection, limit: Optional[int] = None) -> List:
    """
    Get products for a collection, handling both manual and smart collections.
    
    Args:
        collection: Collection model instance
        limit: Optional limit on products returned
        
    Returns:
        List of Product model instances
    """
    from app.models import Product, CollectionProduct, Category
    
    if collection.collection_type == 'manual':
        # Manual collection: get products by position
        query = CollectionProduct.query.filter_by(collection_id=collection.id)\
            .order_by(CollectionProduct.position)
        
        if limit:
            query = query.limit(limit)
        
        return [cp.product for cp in query.all() if cp.product]
    
    else:
        # Smart collection: apply rules
        query = Product.query
        
        for rule in collection.rules:
            if rule.field == 'category':
                if rule.condition == 'equals':
                    query = query.filter(Product.category_id == int(rule.value))
                elif rule.condition == 'not_equals':
                    query = query.filter(Product.category_id != int(rule.value))
            
            elif rule.field == 'price':
                if rule.condition == 'greater_than':
                    query = query.filter(Product.price > int(rule.value))
                elif rule.condition == 'less_than':
                    query = query.filter(Product.price < int(rule.value))
            
            elif rule.field == 'in_stock':
                if rule.value.lower() == 'true':
                    query = query.filter(Product.inventory_count > 0)
                else:
                    query = query.filter(Product.inventory_count <= 0)
        
        # Apply sorting
        if collection.sort_order == 'newest':
            query = query.order_by(Product.created_at.desc())
        elif collection.sort_order == 'price_asc':
            query = query.order_by(Product.price.asc())
        elif collection.sort_order == 'price_desc':
            query = query.order_by(Product.price.desc())
        elif collection.sort_order == 'alpha':
            query = query.order_by(Product.name.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()


def generate_gift_card_code(length: int = 16) -> str:
    """
    Generate a unique gift card code.
    
    Args:
        length: Length of the code (default 16)
        
    Returns:
        Uppercase alphanumeric code with dashes
    """
    import secrets
    import string
    
    # Use only easily readable characters
    alphabet = string.ascii_uppercase + string.digits
    # Remove confusing characters (0, O, I, 1, L)
    alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('1', '').replace('L', '')
    
    code = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Format with dashes every 4 characters
    formatted = '-'.join(code[i:i+4] for i in range(0, len(code), 4))
    
    return formatted


def generate_discount_code(length: int = 8) -> str:
    """
    Generate a unique discount code.
    
    Args:
        length: Length of the code (default 8)
        
    Returns:
        Uppercase alphanumeric code
    """
    import secrets
    import string
    
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
