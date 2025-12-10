"""
Slash Commands Module for Enterprise Messaging.

Provides data referencing commands for internal channels:
- /order <id> - Display order summary
- /lead <id> - Display lead/contact info
- /appointment <id> - Display appointment details
- /product <id|sku> - Display product card
- /contact <email|id> - Search for contact
- /help - List available commands

Usage:
    from app.modules.slash_commands import process_slash_command
    result = process_slash_command('/order 123', current_user, channel_id)
"""
import re
from typing import Optional, Dict, Any
from flask import current_app, url_for
from flask_login import current_user


# Command registry
COMMANDS = {}


def register_command(name: str, description: str, usage: str):
    """Decorator to register a slash command handler."""
    def decorator(func):
        COMMANDS[name] = {
            'handler': func,
            'description': description,
            'usage': usage,
        }
        return func
    return decorator


def process_slash_command(content: str, user, channel_id: int) -> Dict[str, Any]:
    """
    Process a slash command and return the result.
    
    Args:
        content: Full message content starting with /
        user: Current user executing the command
        channel_id: Channel where command was executed
        
    Returns:
        Dict with:
        - success: bool
        - display_text: Text to show in message
        - card: Optional data card for rich display
        - error: Optional error message
    """
    if not content.startswith('/'):
        return {'success': False, 'error': 'Not a slash command'}
    
    # Parse command and arguments
    parts = content[1:].split(maxsplit=1)
    command_name = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ''
    
    # Look up command handler
    if command_name not in COMMANDS:
        return {
            'success': False,
            'display_text': content,
            'error': f'Unknown command: /{command_name}. Use /help for available commands.'
        }
    
    command = COMMANDS[command_name]
    
    try:
        result = command['handler'](args, user, channel_id)
        return {
            'success': True,
            **result
        }
    except Exception as e:
        current_app.logger.error(f"Slash command error: {e}")
        return {
            'success': False,
            'display_text': content,
            'error': str(e)
        }


# =============================================================================
# Command Handlers
# =============================================================================

@register_command('help', 'List available slash commands', '/help')
def cmd_help(args: str, user, channel_id: int) -> Dict[str, Any]:
    """Show available commands."""
    lines = ["**Available Commands:**\n"]
    for name, cmd in sorted(COMMANDS.items()):
        lines.append(f"• `{cmd['usage']}` - {cmd['description']}")
    
    return {
        'display_text': '\n'.join(lines),
        'card': None
    }


@register_command('order', 'Display order details', '/order <order_id>')
def cmd_order(args: str, user, channel_id: int) -> Dict[str, Any]:
    """Look up and display order information."""
    from app.models import Order
    
    if not args:
        return {'display_text': '❌ Usage: `/order <order_id>`', 'card': None}
    
    try:
        order_id = int(args.strip())
    except ValueError:
        return {'display_text': f'❌ Invalid order ID: {args}', 'card': None}
    
    order = Order.query.get(order_id)
    if not order:
        return {'display_text': f'❌ Order #{order_id} not found', 'card': None}
    
    # Build order card
    items_summary = []
    for item in order.items[:3]:  # Show first 3 items
        items_summary.append(f"{item.product.name if item.product else 'Product'} x{item.quantity}")
    if len(order.items) > 3:
        items_summary.append(f"+{len(order.items) - 3} more...")
    
    card = {
        'type': 'order',
        'id': order.id,
        'title': f'Order #{order.id}',
        'status': order.status or 'pending',
        'total': f'${order.total_amount / 100:.2f}' if order.total_amount else '$0.00',
        'customer': order.customer_email or (order.user.email if order.user else 'Guest'),
        'items': items_summary,
        'created_at': order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else None,
        'url': url_for('admin.order_detail', order_id=order.id, _external=True)
    }
    
    display = f"📦 **Order #{order.id}** | {order.status or 'pending'} | {card['total']}"
    
    return {'display_text': display, 'card': card}


@register_command('lead', 'Display lead/contact details', '/lead <lead_id>')
def cmd_lead(args: str, user, channel_id: int) -> Dict[str, Any]:
    """Look up and display lead information."""
    from app.models import ContactFormSubmission, Lead
    
    if not args:
        return {'display_text': '❌ Usage: `/lead <lead_id>`', 'card': None}
    
    try:
        lead_id = int(args.strip())
    except ValueError:
        return {'display_text': f'❌ Invalid lead ID: {args}', 'card': None}
    
    # Try ContactFormSubmission first, then Lead
    lead = ContactFormSubmission.query.get(lead_id)
    model_type = 'contact'
    
    if not lead:
        lead = Lead.query.get(lead_id) if hasattr(Lead, 'query') else None
        model_type = 'lead'
    
    if not lead:
        return {'display_text': f'❌ Lead #{lead_id} not found', 'card': None}
    
    name = f"{getattr(lead, 'first_name', '')} {getattr(lead, 'last_name', '')}".strip() or 'Unknown'
    
    card = {
        'type': 'lead',
        'id': lead.id,
        'title': name,
        'email': getattr(lead, 'email', None),
        'phone': getattr(lead, 'phone', None),
        'status': getattr(lead, 'status', 'new'),
        'message': (getattr(lead, 'message', '') or '')[:100],
        'created_at': lead.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(lead, 'created_at') and lead.created_at else None,
        'url': url_for('crm.lead_detail', lead_id=lead.id, _external=True) if model_type == 'contact' else None
    }
    
    display = f"👤 **{name}** | {card['email'] or 'No email'} | {card['status']}"
    
    return {'display_text': display, 'card': card}


@register_command('appointment', 'Display appointment details', '/appointment <id>')
def cmd_appointment(args: str, user, channel_id: int) -> Dict[str, Any]:
    """Look up and display appointment information."""
    from app.models import Appointment
    
    if not args:
        return {'display_text': '❌ Usage: `/appointment <id>`', 'card': None}
    
    try:
        appt_id = int(args.strip())
    except ValueError:
        return {'display_text': f'❌ Invalid appointment ID: {args}', 'card': None}
    
    appt = Appointment.query.get(appt_id)
    if not appt:
        return {'display_text': f'❌ Appointment #{appt_id} not found', 'card': None}
    
    # Get service and estimator names
    service_name = appt.service.name if appt.service else 'No service'
    estimator_name = appt.estimator.name if appt.estimator else 'Unassigned'
    
    card = {
        'type': 'appointment',
        'id': appt.id,
        'title': f'Appointment #{appt.id}',
        'service': service_name,
        'estimator': estimator_name,
        'status': getattr(appt, 'status', 'scheduled'),
        'date': appt.date.strftime('%Y-%m-%d') if appt.date else None,
        'time': appt.time.strftime('%H:%M') if hasattr(appt, 'time') and appt.time else None,
        'customer_name': getattr(appt, 'customer_name', None),
        'customer_email': getattr(appt, 'customer_email', None),
        'url': url_for('admin.appointments', _external=True)
    }
    
    display = f"📅 **Appointment #{appt.id}** | {service_name} | {card['date'] or 'No date'}"
    
    return {'display_text': display, 'card': card}


@register_command('product', 'Display product details', '/product <id|sku>')
def cmd_product(args: str, user, channel_id: int) -> Dict[str, Any]:
    """Look up and display product information."""
    from app.models import Product
    
    if not args:
        return {'display_text': '❌ Usage: `/product <id|sku>`', 'card': None}
    
    query = args.strip()
    
    # Try by ID first
    product = None
    try:
        product_id = int(query)
        product = Product.query.get(product_id)
    except ValueError:
        # Try by SKU
        product = Product.query.filter_by(sku=query).first()
    
    if not product:
        return {'display_text': f'❌ Product "{query}" not found', 'card': None}
    
    card = {
        'type': 'product',
        'id': product.id,
        'title': product.name,
        'sku': getattr(product, 'sku', None),
        'price': f'${product.price / 100:.2f}' if product.price else '$0.00',
        'inventory': getattr(product, 'inventory_count', 0),
        'is_active': getattr(product, 'is_active', True),
        'description': (product.description or '')[:100],
        'url': url_for('shop.product_detail', product_id=product.id, _external=True)
    }
    
    stock_status = f"In Stock ({card['inventory']})" if card['inventory'] > 0 else "Out of Stock"
    display = f"🛍️ **{product.name}** | {card['price']} | {stock_status}"
    
    return {'display_text': display, 'card': card}


@register_command('contact', 'Search for a contact by email or ID', '/contact <email|id>')
def cmd_contact(args: str, user, channel_id: int) -> Dict[str, Any]:
    """Search for a contact by email or ID."""
    from app.models import ContactFormSubmission, User
    
    if not args:
        return {'display_text': '❌ Usage: `/contact <email|id>`', 'card': None}
    
    query = args.strip()
    results = []
    
    # Check if it's an ID
    try:
        contact_id = int(query)
        contact = ContactFormSubmission.query.get(contact_id)
        if contact:
            results.append({
                'type': 'contact',
                'id': contact.id,
                'name': f"{contact.first_name} {contact.last_name}",
                'email': contact.email,
                'source': 'Contact Form'
            })
    except ValueError:
        # Search by email
        contacts = ContactFormSubmission.query.filter(
            ContactFormSubmission.email.ilike(f'%{query}%')
        ).limit(5).all()
        
        for c in contacts:
            results.append({
                'type': 'contact',
                'id': c.id,
                'name': f"{c.first_name} {c.last_name}",
                'email': c.email,
                'source': 'Contact Form'
            })
        
        # Also search users
        users = User.query.filter(User.email.ilike(f'%{query}%')).limit(5).all()
        for u in users:
            results.append({
                'type': 'user',
                'id': u.id,
                'name': u.username,
                'email': u.email,
                'source': 'User'
            })
    
    if not results:
        return {'display_text': f'❌ No contacts found for "{query}"', 'card': None}
    
    # Build display
    lines = [f"🔍 **Found {len(results)} result(s) for \"{query}\":**"]
    for r in results[:5]:
        lines.append(f"• [{r['source']}] {r['name']} - {r['email']}")
    
    card = {
        'type': 'search_results',
        'query': query,
        'results': results
    }
    
    return {'display_text': '\n'.join(lines), 'card': card}


@register_command('ticket', 'Display support ticket details', '/ticket <id>')
def cmd_ticket(args: str, user, channel_id: int) -> Dict[str, Any]:
    """Look up and display support ticket information."""
    from app.models import SupportTicket
    
    if not args:
        return {'display_text': '❌ Usage: `/ticket <id>`', 'card': None}
    
    try:
        ticket_id = int(args.strip())
    except ValueError:
        return {'display_text': f'❌ Invalid ticket ID: {args}', 'card': None}
    
    ticket = SupportTicket.query.get(ticket_id)
    if not ticket:
        return {'display_text': f'❌ Ticket #{ticket_id} not found', 'card': None}
    
    card = {
        'type': 'ticket',
        'id': ticket.id,
        'title': ticket.subject,
        'status': ticket.status,
        'priority': getattr(ticket, 'priority', 'normal'),
        'customer_email': ticket.email,
        'created_at': ticket.created_at.strftime('%Y-%m-%d %H:%M') if ticket.created_at else None,
        'url': url_for('support.admin_ticket_detail', ticket_id=ticket.id, _external=True)
    }
    
    display = f"🎫 **Ticket #{ticket.id}** | {ticket.subject[:50]} | {ticket.status}"
    
    return {'display_text': display, 'card': card}


def is_slash_command(content: str) -> bool:
    """Check if message content is a slash command."""
    if not content:
        return False
    return content.strip().startswith('/') and len(content) > 1


def get_available_commands() -> Dict[str, Dict[str, str]]:
    """Get list of available commands with descriptions."""
    return {
        name: {'description': cmd['description'], 'usage': cmd['usage']}
        for name, cmd in COMMANDS.items()
    }
