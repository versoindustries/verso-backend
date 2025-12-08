"""
Phase 13: Shopify-Killer E-Commerce Test Suite

Comprehensive tests for:
- Discount validation and application
- Gift card operations
- Shipping zone matching and rate calculation
- Tax calculation
- Collection product fetching (smart/manual)
- Variant matrix generation
- Cart total calculations
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from app import create_app
from app.database import db
from app.models import (
    User, Product, ProductVariant, Category,
    ProductAttribute, ProductAttributeValue, ProductAttributeAssignment,
    Collection, CollectionRule, CollectionProduct,
    ProductBundle, BundleItem,
    Discount, DiscountRule, DiscountUsage,
    GiftCard, GiftCardTransaction,
    ShippingZone, ShippingRate,
    TaxRate,
    Wishlist, RecentlyViewed, RelatedProduct
)
from app.modules.ecommerce import (
    calculate_cart_totals, validate_discount, apply_discount,
    validate_gift_card, apply_gift_card,
    match_shipping_zone, calculate_shipping, calculate_tax,
    generate_variant_matrix, get_collection_products,
    generate_gift_card_code, generate_discount_code
)


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing."""
    with app.app_context():
        user = User(
            email='test@example.com',
            name='Test User'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def sample_products(app):
    """Create sample products for testing."""
    with app.app_context():
        products = []
        for i in range(3):
            product = Product(
                name=f'Test Product {i+1}',
                description=f'Description for product {i+1}',
                price=1000 * (i + 1),  # $10, $20, $30
                inventory_count=10,
                is_digital=False
            )
            db.session.add(product)
            products.append(product)
        
        db.session.commit()
        return [p.id for p in products]


# =============================================================================
# Discount Tests
# =============================================================================

class TestDiscounts:
    """Test discount validation and application."""
    
    def test_percentage_discount(self, app, sample_products):
        """Test percentage discount calculation."""
        with app.app_context():
            discount = Discount(
                name='20% Off',
                code='SAVE20',
                discount_type='percentage',
                value=20,
                is_active=True
            )
            db.session.add(discount)
            db.session.commit()
            
            cart_items = [{'product_id': sample_products[0], 'price': 1000, 'quantity': 2}]
            
            is_valid, error = validate_discount(discount, cart_items)
            assert is_valid is True
            assert error is None
            
            savings, _ = apply_discount(cart_items, discount)
            # 20% of $20 (2 x $10) = $4 = 400 cents
            assert savings == 400
    
    def test_fixed_amount_discount(self, app, sample_products):
        """Test fixed amount discount calculation."""
        with app.app_context():
            discount = Discount(
                name='$5 Off',
                code='SAVE5',
                discount_type='fixed_amount',
                value=500,  # $5 in cents
                is_active=True
            )
            db.session.add(discount)
            db.session.commit()
            
            cart_items = [{'product_id': sample_products[0], 'price': 1000, 'quantity': 1}]
            
            savings, _ = apply_discount(cart_items, discount)
            assert savings == 500
    
    def test_discount_minimum_order(self, app, sample_products):
        """Test discount with minimum order requirement."""
        with app.app_context():
            discount = Discount(
                name='10% Off $50+',
                code='MIN50',
                discount_type='percentage',
                value=10,
                minimum_order_cents=5000,  # $50 minimum
                is_active=True
            )
            db.session.add(discount)
            db.session.commit()
            
            # Cart under minimum
            cart_items = [{'product_id': sample_products[0], 'price': 1000, 'quantity': 1}]
            is_valid, error = validate_discount(discount, cart_items)
            assert is_valid is False
            assert 'minimum' in error.lower()
            
            # Cart over minimum
            cart_items = [{'product_id': sample_products[0], 'price': 1000, 'quantity': 6}]
            is_valid, error = validate_discount(discount, cart_items)
            assert is_valid is True
    
    def test_discount_expiration(self, app):
        """Test expired discount rejection."""
        with app.app_context():
            discount = Discount(
                name='Expired Discount',
                code='EXPIRED',
                discount_type='percentage',
                value=10,
                is_active=True,
                ends_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(discount)
            db.session.commit()
            
            cart_items = [{'price': 1000, 'quantity': 1}]
            is_valid, error = validate_discount(discount, cart_items)
            assert is_valid is False
            assert 'expired' in error.lower()
    
    def test_discount_not_yet_active(self, app):
        """Test discount that hasn't started yet."""
        with app.app_context():
            discount = Discount(
                name='Future Discount',
                code='FUTURE',
                discount_type='percentage',
                value=10,
                is_active=True,
                starts_at=datetime.utcnow() + timedelta(days=1)
            )
            db.session.add(discount)
            db.session.commit()
            
            cart_items = [{'price': 1000, 'quantity': 1}]
            is_valid, error = validate_discount(discount, cart_items)
            assert is_valid is False
            assert 'started' in error.lower()


# =============================================================================
# Gift Card Tests
# =============================================================================

class TestGiftCards:
    """Test gift card validation and redemption."""
    
    def test_gift_card_generation(self, app):
        """Test gift card code generation."""
        code = generate_gift_card_code()
        assert len(code.replace('-', '')) == 16
        assert '-' in code  # Formatted with dashes
        assert code.isupper() or code.replace('-', '').isalnum()
    
    def test_gift_card_validation(self, app):
        """Test gift card validation logic."""
        with app.app_context():
            gift_card = GiftCard(
                code='TEST-1234-ABCD-EFGH',
                initial_balance_cents=5000,
                current_balance_cents=5000,
                is_active=True
            )
            db.session.add(gift_card)
            db.session.commit()
            
            is_valid, error = validate_gift_card(gift_card)
            assert is_valid is True
            assert error is None
    
    def test_gift_card_expired(self, app):
        """Test expired gift card rejection."""
        with app.app_context():
            gift_card = GiftCard(
                code='EXPIRED-CARD-TEST',
                initial_balance_cents=5000,
                current_balance_cents=5000,
                is_active=True,
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(gift_card)
            db.session.commit()
            
            is_valid, error = validate_gift_card(gift_card)
            assert is_valid is False
            assert 'expired' in error.lower()
    
    def test_gift_card_zero_balance(self, app):
        """Test gift card with zero balance."""
        with app.app_context():
            gift_card = GiftCard(
                code='EMPTY-CARD-TEST',
                initial_balance_cents=5000,
                current_balance_cents=0,
                is_active=True
            )
            db.session.add(gift_card)
            db.session.commit()
            
            is_valid, error = validate_gift_card(gift_card)
            assert is_valid is False
            assert 'balance' in error.lower()
    
    def test_gift_card_redemption(self, app):
        """Test gift card redemption reduces balance."""
        with app.app_context():
            gift_card = GiftCard(
                code='REDEEM-TEST-CARD',
                initial_balance_cents=5000,
                current_balance_cents=5000,
                is_active=True
            )
            db.session.add(gift_card)
            db.session.commit()
            
            amount_applied = apply_gift_card(gift_card, 2000, order_id=1)
            
            assert amount_applied == 2000
            assert gift_card.current_balance_cents == 3000


# =============================================================================
# Shipping Tests
# =============================================================================

class TestShipping:
    """Test shipping zone matching and rate calculation."""
    
    def test_shipping_zone_matching(self, app):
        """Test shipping zone country/state matching."""
        with app.app_context():
            us_zone = ShippingZone(
                name='United States',
                countries=['US'],
                states=[],
                is_active=True
            )
            db.session.add(us_zone)
            db.session.commit()
            
            matched = match_shipping_zone('US', 'CO', '80202')
            assert matched is not None
            assert matched.name == 'United States'
            
            # Test non-matching country
            matched = match_shipping_zone('CA', 'ON')
            assert matched is None
    
    def test_rest_of_world_fallback(self, app):
        """Test rest-of-world zone fallback."""
        with app.app_context():
            row_zone = ShippingZone(
                name='International',
                countries=[],
                is_rest_of_world=True,
                is_active=True
            )
            db.session.add(row_zone)
            db.session.commit()
            
            matched = match_shipping_zone('UK')
            assert matched is not None
            assert matched.name == 'International'
    
    def test_flat_rate_shipping(self, app):
        """Test flat rate shipping calculation."""
        with app.app_context():
            zone = ShippingZone(
                name='Domestic',
                countries=['US'],
                is_active=True
            )
            db.session.add(zone)
            db.session.flush()
            
            rate = ShippingRate(
                zone_id=zone.id,
                name='Standard Shipping',
                rate_type='flat',
                price_cents=599,
                is_active=True
            )
            db.session.add(rate)
            db.session.commit()
            
            cart_items = [{'price': 1000, 'quantity': 1, 'weight_grams': 500}]
            shipping, rates = calculate_shipping(cart_items, 'US', 'CO')
            
            assert shipping == 599
            assert len(rates) == 1
            assert rates[0]['name'] == 'Standard Shipping'
    
    def test_free_shipping_threshold(self, app):
        """Test free shipping for orders over threshold."""
        with app.app_context():
            zone = ShippingZone(
                name='Domestic',
                countries=['US'],
                is_active=True
            )
            db.session.add(zone)
            db.session.flush()
            
            rate = ShippingRate(
                zone_id=zone.id,
                name='Standard (Free over $50)',
                rate_type='flat',
                price_cents=599,
                free_shipping_threshold_cents=5000,
                is_active=True
            )
            db.session.add(rate)
            db.session.commit()
            
            # Under threshold
            cart_items = [{'price': 2000, 'quantity': 1}]
            shipping, _ = calculate_shipping(cart_items, 'US', 'CO')
            assert shipping == 599
            
            # Over threshold
            cart_items = [{'price': 6000, 'quantity': 1}]
            shipping, _ = calculate_shipping(cart_items, 'US', 'CO')
            assert shipping == 0


# =============================================================================
# Tax Tests
# =============================================================================

class TestTax:
    """Test tax calculation logic."""
    
    def test_state_tax_rate(self, app):
        """Test state-level tax calculation."""
        with app.app_context():
            tax_rate = TaxRate(
                name='Colorado Sales Tax',
                rate=0.029,  # 2.9%
                country='US',
                state='CO',
                is_active=True
            )
            db.session.add(tax_rate)
            db.session.commit()
            
            cart_items = [{'price': 1000, 'quantity': 1}]  # $10
            tax, rates = calculate_tax(cart_items, 'US', 'CO')
            
            # 2.9% of $10 = $0.29 = 29 cents
            assert tax == 29
            assert len(rates) == 1
    
    def test_tax_on_shipping(self, app):
        """Test tax applied to shipping."""
        with app.app_context():
            tax_rate = TaxRate(
                name='Tax With Shipping',
                rate=0.10,  # 10%
                country='US',
                state='NY',
                applies_to_shipping=True,
                is_active=True
            )
            db.session.add(tax_rate)
            db.session.commit()
            
            cart_items = [{'price': 1000, 'quantity': 1}]  # $10
            shipping = 500  # $5 shipping
            tax, _ = calculate_tax(cart_items, 'US', 'NY', shipping_cents=shipping)
            
            # 10% of ($10 + $5) = $1.50 = 150 cents
            assert tax == 150
    
    def test_no_tax_for_unmatched_location(self, app):
        """Test no tax for locations without defined rates."""
        with app.app_context():
            tax_rate = TaxRate(
                name='Colorado Tax',
                rate=0.05,
                country='US',
                state='CO',
                is_active=True
            )
            db.session.add(tax_rate)
            db.session.commit()
            
            cart_items = [{'price': 1000, 'quantity': 1}]
            tax, rates = calculate_tax(cart_items, 'US', 'TX')  # Texas, not Colorado
            
            assert tax == 0
            assert len(rates) == 0


# =============================================================================
# Collection Tests
# =============================================================================

class TestCollections:
    """Test collection product fetching."""
    
    def test_manual_collection(self, app, sample_products):
        """Test manual collection returns assigned products."""
        with app.app_context():
            collection = Collection(
                name='Featured',
                slug='featured',
                collection_type='manual',
                is_published=True
            )
            db.session.add(collection)
            db.session.flush()
            
            # Add first two products
            for i, pid in enumerate(sample_products[:2]):
                cp = CollectionProduct(
                    collection_id=collection.id,
                    product_id=pid,
                    position=i
                )
                db.session.add(cp)
            
            db.session.commit()
            
            products = get_collection_products(collection)
            assert len(products) == 2
    
    def test_smart_collection_price_rule(self, app, sample_products):
        """Test smart collection with price rule."""
        with app.app_context():
            collection = Collection(
                name='Under $25',
                slug='under-25',
                collection_type='smart',
                is_published=True
            )
            db.session.add(collection)
            db.session.flush()
            
            rule = CollectionRule(
                collection_id=collection.id,
                field='price',
                condition='less_than',
                value='2500'  # $25 in cents
            )
            db.session.add(rule)
            db.session.commit()
            
            products = get_collection_products(collection)
            # Products priced $10 and $20 should match
            assert len(products) == 2
            for p in products:
                assert p.price < 2500


# =============================================================================
# Variant Matrix Tests
# =============================================================================

class TestVariantMatrix:
    """Test variant matrix generation."""
    
    def test_generate_size_color_variants(self, app, sample_products):
        """Test generating Size x Color variant combinations."""
        with app.app_context():
            product = Product.query.get(sample_products[0])
            
            # Create Size attribute
            size_attr = ProductAttribute(name='Size', slug='size')
            db.session.add(size_attr)
            db.session.flush()
            
            for i, size in enumerate(['Small', 'Medium', 'Large']):
                val = ProductAttributeValue(
                    attribute_id=size_attr.id,
                    value=size,
                    slug=size.lower(),
                    position=i
                )
                db.session.add(val)
            
            # Create Color attribute
            color_attr = ProductAttribute(name='Color', slug='color')
            db.session.add(color_attr)
            db.session.flush()
            
            for i, color in enumerate(['Red', 'Blue']):
                val = ProductAttributeValue(
                    attribute_id=color_attr.id,
                    value=color,
                    slug=color.lower(),
                    position=i
                )
                db.session.add(val)
            
            db.session.commit()
            
            variants = generate_variant_matrix(product, [size_attr.id, color_attr.id])
            
            # Should generate 3 sizes x 2 colors = 6 variants
            assert len(variants) == 6
            
            # Check variant names include both attributes
            names = [v['name'] for v in variants]
            assert 'Small / Red' in names
            assert 'Large / Blue' in names


# =============================================================================
# Cart Totals Tests
# =============================================================================

class TestCartTotals:
    """Test complete cart total calculations."""
    
    def test_cart_subtotal(self, app):
        """Test basic cart subtotal calculation."""
        with app.app_context():
            cart_items = [
                {'price': 1000, 'quantity': 2},  # $20
                {'price': 2500, 'quantity': 1},  # $25
            ]
            
            totals = calculate_cart_totals(cart_items)
            assert totals['subtotal_cents'] == 4500  # $45
    
    def test_cart_with_discount(self, app):
        """Test cart totals with discount applied."""
        with app.app_context():
            discount = Discount(
                name='10% Off',
                code='SAVE10',
                discount_type='percentage',
                value=10,
                is_active=True
            )
            db.session.add(discount)
            db.session.commit()
            
            cart_items = [{'price': 1000, 'quantity': 1}]
            
            totals = calculate_cart_totals(cart_items, discount_code='SAVE10')
            
            assert totals['subtotal_cents'] == 1000
            assert totals['discount_cents'] == 100  # 10% of $10
            assert totals['total_cents'] == 900


# =============================================================================
# Code Generation Tests
# =============================================================================

class TestCodeGeneration:
    """Test unique code generation."""
    
    def test_gift_card_code_format(self):
        """Test gift card code format and uniqueness."""
        codes = set()
        for _ in range(100):
            code = generate_gift_card_code()
            assert code not in codes
            codes.add(code)
            
            # Check format: XXXX-XXXX-XXXX-XXXX
            parts = code.split('-')
            assert len(parts) == 4
            for part in parts:
                assert len(part) == 4
    
    def test_discount_code_format(self):
        """Test discount code format."""
        code = generate_discount_code()
        assert len(code) == 8
        assert code.isalnum()
        assert code.isupper()


# =============================================================================
# Route Integration Tests
# =============================================================================

class TestEcommerceRoutes:
    """Test e-commerce route responses."""
    
    def test_collections_list(self, client, app):
        """Test collections list page loads."""
        with app.app_context():
            collection = Collection(
                name='Test Collection',
                slug='test-collection',
                is_published=True
            )
            db.session.add(collection)
            db.session.commit()
        
        response = client.get('/collections')
        assert response.status_code == 200
    
    def test_gift_card_balance_check(self, client, app):
        """Test gift card balance check page."""
        response = client.get('/gift-cards/check-balance')
        assert response.status_code == 200
    
    def test_wishlist_requires_login(self, client):
        """Test wishlist page requires authentication."""
        response = client.get('/wishlist')
        # Should redirect to login
        assert response.status_code == 302
        assert 'login' in response.location.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
