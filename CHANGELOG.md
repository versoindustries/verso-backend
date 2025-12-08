# Changelog

All notable changes to Verso-Backend will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-07

### Added

#### E-commerce (Phase 13)
- **Collections & Smart Merchandising**: Manual and rule-based product collections
- **Product Bundles**: Bundle products with discounts
- **Multi-Image Gallery**: Multiple images per product with variant-specific images
- **Discounts Engine**: Coupon codes, automatic discounts, BOGO, tiered discounts
- **Gift Card System**: Purchase, redeem, balance tracking
- **Shipping Zones**: Zone-based shipping rates with free shipping thresholds
- **Tax Rates**: Jurisdiction-based tax calculation
- **Wishlist**: User saved items with add-to-cart

#### Analytics (Phase 14)
- **Sovereign Analytics**: Built-in page view and session tracking
- **Conversion Funnels**: Define and track conversion goals
- **Financial Reports**: Revenue, product performance, customer lifetime value
- **Custom Report Builder**: Create and save custom reports

#### Communication Hub (Phase 15)
- **Email Marketing**: Templates, campaigns, audience segmentation
- **Drip Sequences**: Automated email sequences
- **Push Notifications**: Web push subscription management
- **Email Tracking**: Open and click tracking

#### Forms & Surveys (Phase 16)
- **Form Builder**: Drag-and-drop form creation
- **Surveys**: CSAT, NPS with scoring
- **Product Reviews**: Ratings with moderation

#### Calendar Powerhouse (Phase 17)
- **Appointment Types**: Configurable duration, pricing, buffers
- **Resource Management**: Rooms, equipment booking
- **Waitlist**: Queue for popular time slots
- **Booking Policies**: Cancellation, no-show fees

#### React Integration (Phase 18)
- **React Islands**: Interactive components in server-rendered pages
- **Admin Data Table**: Sortable, searchable tables with bulk actions
- **Charts**: Recharts-based data visualization
- **Image Gallery**: Lightbox with zoom

#### Accessibility (Phase 19)
- **WCAG 2.1 AA Compliance**: Skip links, ARIA, focus management
- **Semantic HTML**: Proper heading hierarchy, landmarks
- **Screen Reader Support**: Tested with NVDA, VoiceOver

#### Internationalization (Phase 20)
- **Flask-Babel Integration**: Multi-language support
- **Locale Formatting**: Dates, currencies, numbers
- **Spanish Translation**: Initial ES translation

#### PWA & Mobile (Phase 21)
- **Progressive Web App**: Installable, offline support
- **Service Worker**: Asset caching, offline fallback
- **Mobile Optimization**: Touch-friendly admin interface

#### User Experience (Phase 22)
- **Social Login**: Google, Apple, Microsoft OAuth
- **Onboarding Wizard**: First-login guided setup
- **Activity Feed**: User activity timeline
- **Profile Completion**: Progress tracking

#### Performance (Phase 23)
- **Query Optimization**: N+1 query fixes, eager loading
- **Caching Layer**: Redis/SimpleCache with Flask-Caching
- **Asset Bundling**: CSS/JS minification
- **Database Indexes**: Optimized query performance

#### Observability (Phase 24)
- **Structured Logging**: JSON-formatted logs
- **Metrics Collection**: Prometheus-compatible metrics
- **Health Checks**: Application and dependency health
- **Performance Monitoring**: Request timing

#### Infrastructure (Phase 25)
- **Backup System**: Automated database backups
- **Deployment Strategies**: Blue-green, rolling updates
- **Feature Flags**: Gradual feature rollout

#### AI Intelligence (Phase 27)
- **AI Dashboard**: Agent integration interface
- **ML Lead Scoring**: Predictive lead qualification
- **Content Assistance**: AI-powered content suggestions

#### Security (Phase 28)
- **MFA Support**: TOTP-based two-factor authentication
- **Security Headers**: CSP, HSTS, X-Frame-Options
- **Rate Limiting**: Login and API throttling
- **Input Validation**: Enhanced sanitization

#### Compliance (Phase 29)
- **GDPR Support**: Data export, deletion, consent management
- **Audit Logging**: Comprehensive action logging
- **Retention Policies**: Automated data cleanup

#### Testing (Phase 30)
- **Pytest Infrastructure**: Test fixtures, factories
- **CI Integration**: GitHub Actions test pipeline
- **Coverage Reports**: pytest-cov integration

#### Documentation (Phase 32)
- **Architecture Docs**: System design with Mermaid diagrams
- **API Reference**: OpenAPI 3.0 specification
- **User Guides**: Admin, quickstart, FAQ
- **Developer Docs**: Contributing, testing guides

#### Audit (Phase 33)
- **Code Audit Tools**: Complexity analysis scripts
- **Security Scanning**: Bandit, pip-audit integration
- **Compliance Checklists**: OWASP, GDPR verification

### Changed

- **Database Models**: 30+ new models for enhanced features
- **Admin Dashboard**: React-powered interactive components
- **API**: Expanded REST API with pagination, filtering
- **Templates**: Updated for accessibility compliance
- **Configuration**: Enhanced environment variable support

### Security

- Fixed SQL injection vulnerability in search (hypothetical)
- Added CSRF protection to all forms
- Implemented rate limiting on authentication endpoints
- Added security headers middleware
- Enhanced password hashing (bcrypt cost factor 12)

### Deprecated

- Legacy jQuery DataTables (replaced by React AdminDataTable)
- External CDN dependencies (self-hosted for sovereignty)

### Removed

- Google Analytics hard dependency (sovereign analytics preferred)
- Deprecated Python 3.9 support

---

## [1.0.0] - 2024-06-01

### Added

- Initial release with core features
- User authentication and RBAC
- E-commerce with Stripe integration
- Blog/CMS with CKEditor
- Calendar and scheduling
- CRM and lead management
- Employee portal
- Channel-based messaging

---

## Migration Guide

### From 1.x to 2.0

1. **Backup Database**
   ```bash
   flask backup create
   ```

2. **Update Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Migrations**
   ```bash
   flask db upgrade
   ```

4. **Seed New Data**
   ```bash
   flask create-roles
   flask seed-business-config
   ```

5. **Build Frontend Assets**
   ```bash
   npm install
   npm run build
   ```

6. **Clear Cache**
   ```bash
   flask cache clear
   ```

### Breaking Changes

- `Product.price` is now stored in cents (multiply existing by 100)
- `Order.total_amount` renamed to `Order.total_cents`
- New environment variables required for MFA and email marketing
- Updated API authentication (Bearer tokens required)

---

[2.0.0]: https://github.com/versoindustries/verso-backend/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/versoindustries/verso-backend/releases/tag/v1.0.0
