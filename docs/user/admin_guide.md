# Administrator Guide

This guide provides comprehensive instructions for administrators managing a Verso-Backend installation.

## Table of Contents

- [Getting Started](#getting-started)
- [Dashboard Overview](#dashboard-overview)
- [User Management](#user-management)
- [Content Management](#content-management)
- [E-commerce Administration](#e-commerce-administration)
- [Analytics & Reports](#analytics--reports)
- [System Configuration](#system-configuration)
- [Maintenance Tasks](#maintenance-tasks)

---

## Getting Started

### Accessing the Admin Panel

1. Navigate to `https://your-domain.com/admin`
2. Log in with an administrator account
3. You'll be directed to the admin dashboard

### First-Time Setup

After installation, complete these initial setup tasks:

1. **Configure Business Settings**
   - Go to **Settings → Business Configuration**
   - Set your business name, address, and contact information
   - Configure timezone and working hours

2. **Set Up Email**
   - Go to **Settings → Email Configuration**
   - Configure SMTP settings for transactional emails
   - Send a test email to verify

3. **Create Staff Accounts**
   - Go to **Users → Add User**
   - Create accounts for your team
   - Assign appropriate roles

4. **Configure Payments**
   - Go to **Settings → Payment Configuration**
   - Enter your Stripe API keys
   - Configure webhook endpoint

---

## Dashboard Overview

The admin dashboard provides an at-a-glance view of your business:

### Key Metrics Cards

| Metric | Description |
|--------|-------------|
| **Revenue Today** | Total sales for the current day |
| **Orders Pending** | Orders awaiting processing |
| **Appointments Today** | Scheduled appointments for today |
| **New Leads** | Contact form submissions |

### Quick Actions

- **Add Product** - Create a new product
- **View Orders** - Jump to order management
- **Check Calendar** - View today's schedule
- **View Analytics** - Open analytics dashboard

### Recent Activity

Shows the latest system events:
- New orders
- User registrations
- Appointment bookings
- Form submissions

---

## User Management

### Viewing Users

Navigate to **Users → All Users** to see all registered users.

**Available Actions:**
- **Search** - Find users by name or email
- **Filter** - Filter by role or status
- **Export** - Download user list as CSV

### User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full system access |
| **User** | Standard customer access |
| **Commercial** | Sales and CRM access |
| **Blogger** | Content creation access |
| **Employee** | Employee portal access |

### Creating a User

1. Go to **Users → Add User**
2. Fill in the required fields:
   - Username (unique)
   - Email address
   - Password
   - First/Last name
3. Assign roles
4. Click **Create User**

### Editing User Details

1. Click on a user's name or **Edit** button
2. Modify user information
3. Enable/disable account
4. Reset password if needed
5. Click **Save Changes**

### Deactivating vs. Deleting

- **Deactivate**: User can't log in but data is preserved
- **Delete**: Permanently removes user (may affect order history)

> ⚠️ **Warning**: Deleting users with orders may cause data integrity issues. Prefer deactivation.

---

## Content Management

### Blog Posts

#### Creating a Post

1. Go to **Content → Blog → New Post**
2. Enter post details:
   - **Title** - The post headline
   - **Content** - Use the rich text editor
   - **Excerpt** - Short description for listings
   - **Featured Image** - Upload a cover image
3. Configure SEO settings (optional)
4. Set publication status:
   - **Draft** - Not visible
   - **Published** - Visible to all
   - **Scheduled** - Will publish at set time

#### Managing Posts

- **Edit** - Modify existing posts
- **Preview** - See how post will appear
- **Duplicate** - Create a copy for similar content
- **Archive** - Hide without deleting

### Pages

#### Creating a Static Page

1. Go to **Content → Pages → New Page**
2. Enter page content
3. Set URL slug
4. Publish

### Categories

Organize content with categories:

1. Go to **Content → Categories**
2. Click **Add Category**
3. Enter name and optional parent category
4. Save

### Media Library

Upload and manage files:

1. Go to **Content → Media**
2. Upload files via drag-and-drop
3. Browse and search existing media
4. Get URLs for embedding

---

## E-commerce Administration

### Products

#### Adding a Product

1. Go to **Shop → Products → Add Product**
2. Fill in basic information:
   - Name
   - Description
   - Price (in cents)
   - SKU
3. Add images
4. Configure variants (if applicable)
5. Set inventory
6. Publish

#### Product Variants

For products with options (size, color):

1. Click **Add Variant**
2. Enter variant name (e.g., "Large - Blue")
3. Set SKU and price adjustment
4. Set inventory for this variant
5. Repeat for all combinations

#### Inventory Management

- View inventory levels in product list
- Filter by "Low Stock" to see items needing reorder
- Bulk update inventory via CSV import

### Orders

#### Order Statuses

| Status | Description |
|--------|-------------|
| **Pending** | Awaiting payment |
| **Paid** | Payment received |
| **Processing** | Being prepared |
| **Shipped** | Sent to customer |
| **Delivered** | Received by customer |
| **Cancelled** | Order cancelled |
| **Refunded** | Payment refunded |

#### Processing an Order

1. Go to **Shop → Orders**
2. Click on order number to view details
3. Verify order items and shipping address
4. Update status to **Processing**
5. When shipped, update to **Shipped** and enter tracking number
6. Customer receives notification

#### Refunding an Order

1. Open order details
2. Click **Refund**
3. Select full or partial refund
4. Enter reason
5. Confirm refund (processes through Stripe)

### Discounts

#### Creating a Discount

1. Go to **Shop → Discounts → Add Discount**
2. Configure:
   - **Code** - Customer enters this at checkout
   - **Type** - Percentage or fixed amount
   - **Value** - Discount value
   - **Minimum Order** - Optional minimum cart value
   - **Usage Limit** - Maximum total uses
3. Set date range (optional)
4. Save

### Gift Cards

#### Issuing a Gift Card

1. Go to **Shop → Gift Cards → Issue**
2. Enter amount
3. Optional: Add recipient details for email delivery
4. Save

#### Checking Balance

Search gift cards by code to view balance and transaction history.

---

## Analytics & Reports

### Traffic Analytics

View visitor statistics:

1. Go to **Analytics → Dashboard**
2. Select date range
3. Review metrics:
   - Page views
   - Unique visitors
   - Session duration
   - Bounce rate
   - Traffic sources

### Revenue Reports

1. Go to **Reports → Revenue**
2. Select period (daily, weekly, monthly)
3. View charts and tables
4. Export to CSV or PDF

### Product Performance

See which products sell best:

1. Go to **Reports → Products**
2. Sort by revenue or units sold
3. Identify top performers and underperformers

### Customer Analytics

Understand your customers:

1. Go to **Reports → Customers**
2. View metrics:
   - Customer lifetime value
   - Repeat purchase rate
   - Average order value
   - Customer acquisition

---

## System Configuration

### Business Settings

**Settings → Business Configuration**

- Business name
- Address and contact info
- Timezone
- Operating hours
- Logo

### Email Configuration

**Settings → Email**

- SMTP server settings
- Default sender address
- Email templates

### Payment Settings

**Settings → Payments**

- Stripe API keys
- Currency
- Tax settings

### Appearance

**Settings → Theme**

- Color scheme
- Logo upload
- Custom CSS

---

## Maintenance Tasks

### Database Backup

1. Go to **System → Backups**
2. Click **Create Backup**
3. Download backup file
4. Store securely off-server

### Scheduled Backups

Configure automatic backups:

1. Go to **System → Backups → Settings**
2. Set schedule (daily, weekly)
3. Configure retention period
4. Optional: Configure remote storage

### Clearing Cache

If you notice stale data:

1. Go to **System → Cache**
2. Click **Clear All Cache**

### Viewing Logs

For troubleshooting:

1. Go to **System → Logs**
2. Filter by level (Error, Warning, Info)
3. Search for specific messages

### System Health

Monitor system status:

1. Go to **System → Health**
2. Check:
   - Database connection
   - Email connectivity
   - Background worker status
   - Disk space

---

## Security Best Practices

### For Administrators

1. **Use Strong Passwords**: Minimum 12 characters with mixed case, numbers, symbols
2. **Enable MFA**: Go to your profile → Security → Enable Two-Factor Authentication
3. **Review Access Regularly**: Audit who has admin access
4. **Monitor Login Activity**: Check for suspicious logins
5. **Keep Software Updated**: Apply updates promptly

### Session Management

If you suspect unauthorized access:

1. Go to **Security → Active Sessions**
2. Review all active sessions
3. Click **Revoke** on suspicious sessions
4. Change your password

---

## Getting Help

### In-App Help

- Click the **?** icon for contextual help
- Hover over **ⓘ** icons for tooltips
- Check **Help → Documentation** for guides

### Support

- **Technical Issues**: Contact your development team
- **Billing Questions**: Contact support@your-company.com
- **Feature Requests**: Submit through the feedback form

---

*Last Updated: December 2024*
