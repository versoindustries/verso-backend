"""
Public Routes Package

Customer-facing routes that don't require authentication or have optional auth.
These handle the public website, storefront, booking, and content pages.
"""

# Re-export public route blueprints from main routes folder
# This allows future migration to move files here while maintaining compatibility

# Public blueprints (imported when needed):
# - main_routes.main
# - auth.auth
# - blog.blog
# - cart.cart_bp
# - shop.shop
# - ecommerce.ecommerce_bp
# - booking_api.booking_api_bp
# - newsletter.newsletter_bp
# - pages.pages_bp
# - support.support_bp (public parts)
# - privacy.privacy_bp
