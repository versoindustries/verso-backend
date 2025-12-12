# Verso-Backend Documentation

> **Sovereign Business Operating System** — Complete documentation for the no-rent Flask monolith.

## Quick Navigation

| Getting Started | Developer Guide | Administrator Guide |
|-----------------|-----------------|---------------------|
| [First-Time Setup](first_time_setup.md) | [Architecture](architecture.md) | [Admin Guide](user/admin_guide.md) |
| [Troubleshooting](troubleshooting.md) | [Database Schema](database_schema.md) | [Deployment](deployment.md) |
| [FAQ](user/faq.md) | [Testing Guide](testing.md) | [Compliance](compliance/) |

---

## 📖 Documentation Index

### For New Users

| Document | Description |
|----------|-------------|
| [First-Time Setup](first_time_setup.md) | Complete local development environment setup |
| [User Quickstart](user/quickstart.md) | Getting started with Verso features |
| [FAQ](user/faq.md) | Frequently asked questions |

### For Developers

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System overview, tech stack, design decisions |
| [Database Schema](database_schema.md) | All 80+ models with ER diagrams |
| [API Reference](api_reference.md) | REST API endpoints and authentication |
| [OpenAPI Spec](openapi.yaml) | Machine-readable API specification |
| [How to Extend](how_to_extend.md) | Adding routes, models, and features |
| [Testing Guide](testing.md) | pytest configuration, fixtures, best practices |
| [Developer Conventions](developer/CONVENTIONS.md) | Code style and contribution guidelines |
| [React Islands](developer/REACT_ISLANDS.md) | Frontend architecture and component patterns |
| [Module Reference](developer/MODULES.md) | Helper modules in `app/modules/` |

### For Administrators

| Document | Description |
|----------|-------------|
| [Admin Guide](user/admin_guide.md) | Complete administrator walkthrough |
| [Deployment](deployment.md) | Production deployment options |
| [How to Deploy](how_to_deploy.md) | Quick deployment checklist |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |

### Integration Guides

| Document | Description |
|----------|-------------|
| [Integrations Overview](integrations/integrations.md) | Third-party integration options |
| [Zapier Integration](integrations/zapier-integration.md) | Connect Verso to 5000+ apps |
| [CalDAV Integration](caldav-integration.md) | Calendar sync setup |

### Compliance & Security

| Document | Description |
|----------|-------------|
| [OWASP Checklist](compliance/owasp_checklist.md) | Web application security |
| [GDPR Checklist](compliance/gdpr_checklist.md) | Data protection compliance |
| [Accessibility Checklist](compliance/accessibility_checklist.md) | WCAG 2.1 compliance |
| [License Compliance](compliance/license_compliance.md) | Open source license audit |

---

## 🏗️ Repository Structure

```
verso-backend/
├── app/                    # Main application
│   ├── routes/             # 47 Flask blueprints
│   ├── models.py           # 136 SQLAlchemy models
│   ├── modules/            # 35 helper modules
│   ├── templates/          # Jinja2 templates
│   └── static/src/         # React/TypeScript source
├── docs/                   # Documentation (you are here)
├── migrations/             # Database migrations
├── scripts/                # Utility scripts
└── tests/                  # Test suite
```

---

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/versoindustries/verso-backend.git
cd verso-backend
./scripts/setup_local.sh

# Configure environment
nano .env

# Start development
./scripts/setup_local.sh --run
```

Visit http://localhost:5000 — See [First-Time Setup](first_time_setup.md) for details.

---

## 📊 Documentation Health

| Category | Status | Coverage |
|----------|--------|----------|
| Architecture | ✅ Complete | Full system overview |
| Database | ✅ Complete | All 80+ models documented |
| API | ✅ Complete | All endpoints with examples |
| Testing | ✅ Complete | Full pytest guide |
| Deployment | ✅ Complete | Multiple deployment options |
| Admin | ✅ Complete | Full administrator guide |
| Compliance | ✅ Complete | OWASP, GDPR, Accessibility |

---

## 📚 External Resources

- **Repository**: [github.com/versoindustries/verso-backend](https://github.com/versoindustries/verso-backend)
- **Issues**: [GitHub Issues](https://github.com/versoindustries/verso-backend/issues)
- **Changelog**: [CHANGELOG.md](../CHANGELOG.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 💡 Documentation Conventions

All documentation follows these standards:

- **Markdown** with GitHub Flavored extensions
- **Mermaid** diagrams for architecture and flows
- **Code examples** with syntax highlighting
- **Tables** for structured information
- **Last Updated** footer on each document

---

*Last Updated: December 2024*
