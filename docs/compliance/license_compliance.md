# License Compliance Report

This document tracks the licenses of all dependencies used in Verso-Backend and their compatibility with the project's AGPL-3.0 license.

## Project License

**Verso-Backend** is licensed under **AGPL-3.0** (GNU Affero General Public License v3.0).

This license:
- Allows commercial use, modification, and distribution
- Requires source code disclosure for network use
- Requires derivative works to use the same license
- Is compatible with most permissive licenses

---

## Dependency License Summary

| License Type | Count | Status |
|--------------|-------|--------|
| MIT | 15+ | ✅ Compatible |
| BSD (2/3-Clause) | 8+ | ✅ Compatible |
| Apache 2.0 | 5+ | ✅ Compatible |
| PSF (Python) | 3+ | ✅ Compatible |
| LGPL | 2+ | ✅ Compatible |
| Other Permissive | 5+ | ✅ Compatible |
| Unknown | 0 | ⚠️ Review needed |

---

## Core Dependencies

### Web Framework

| Package | Version | License | Compatible |
|---------|---------|---------|------------|
| Flask | 2.3+ | BSD-3-Clause | ✅ Yes |
| Werkzeug | 2.3+ | BSD-3-Clause | ✅ Yes |
| Jinja2 | 3.1+ | BSD-3-Clause | ✅ Yes |
| MarkupSafe | 2.1+ | BSD-3-Clause | ✅ Yes |
| itsdangerous | 2.1+ | BSD-3-Clause | ✅ Yes |
| click | 8.1+ | BSD-3-Clause | ✅ Yes |

### Database

| Package | Version | License | Compatible |
|---------|---------|---------|------------|
| SQLAlchemy | 2.0+ | MIT | ✅ Yes |
| Flask-SQLAlchemy | 3.0+ | BSD-3-Clause | ✅ Yes |
| Flask-Migrate | 4.0+ | MIT | ✅ Yes |
| Alembic | 1.12+ | MIT | ✅ Yes |
| psycopg2-binary | 2.9+ | LGPL-3.0 | ✅ Yes |

### Authentication & Security

| Package | Version | License | Compatible |
|---------|---------|---------|------------|
| Flask-Login | 0.6+ | MIT | ✅ Yes |
| Flask-Bcrypt | 1.0+ | BSD-3-Clause | ✅ Yes |
| Flask-WTF | 1.2+ | BSD-3-Clause | ✅ Yes |
| WTForms | 3.1+ | BSD-3-Clause | ✅ Yes |
| PyOTP | 2.9+ | MIT | ✅ Yes |
| PyJWT | 2.8+ | MIT | ✅ Yes |

### Email

| Package | Version | License | Compatible |
|---------|---------|---------|------------|
| Flask-Mail | 0.9+ | BSD-3-Clause | ✅ Yes |

### Caching

| Package | Version | License | Compatible |
|---------|---------|---------|------------|
| Flask-Caching | 2.1+ | BSD-3-Clause | ✅ Yes |
| redis | 5.0+ | MIT | ✅ Yes |

### Internationalization

| Package | Version | License | Compatible |
|---------|---------|---------|------------|
| Flask-Babel | 4.0+ | BSD-3-Clause | ✅ Yes |
| Babel | 2.14+ | BSD-3-Clause | ✅ Yes |

### Content & Media

| Package | Version | License | Compatible |
|---------|---------|---------|------------|
| Pillow | 10.1+ | HPND | ✅ Yes |
| bleach | 6.1+ | Apache-2.0 | ✅ Yes |
| python-dotenv | 1.0+ | BSD-3-Clause | ✅ Yes |

### API & HTTP

| Package | Version | License | Compatible |
|---------|---------|---------|------------|
| requests | 2.31+ | Apache-2.0 | ✅ Yes |
| gunicorn | 21.2+ | MIT | ✅ Yes |

### Payments

| Package | Version | License | Compatible |
|---------|---------|---------|------------|
| stripe | 7.0+ | MIT | ✅ Yes |

### Utilities

| Package | Version | License | Compatible |
|---------|---------|---------|------------|
| python-dateutil | 2.8+ | Apache-2.0 / BSD | ✅ Yes |
| pytz | 2023+ | MIT | ✅ Yes |
| qrcode | 7.4+ | BSD-3-Clause | ✅ Yes |

---

## Development Dependencies

| Package | License | Purpose | Compatible |
|---------|---------|---------|------------|
| pytest | MIT | Testing | ✅ Yes |
| pytest-cov | MIT | Coverage | ✅ Yes |
| pytest-flask | MIT | Flask testing | ✅ Yes |
| black | MIT | Formatting | ✅ Yes |
| isort | MIT | Import sorting | ✅ Yes |
| flake8 | MIT | Linting | ✅ Yes |
| bandit | Apache-2.0 | Security | ✅ Yes |
| pip-audit | Apache-2.0 | Vulnerabilities | ✅ Yes |

---

## Frontend Dependencies

| Package | License | Compatible |
|---------|---------|------------|
| React | MIT | ✅ Yes |
| TypeScript | Apache-2.0 | ✅ Yes |
| Vite | MIT | ✅ Yes |
| Recharts | MIT | ✅ Yes |

---

## License Compatibility Matrix

```
AGPL-3.0 (Project License)
    │
    ├── ✅ MIT - Compatible (permissive)
    │
    ├── ✅ BSD-2-Clause - Compatible (permissive)
    │
    ├── ✅ BSD-3-Clause - Compatible (permissive)
    │
    ├── ✅ Apache-2.0 - Compatible (permissive)
    │
    ├── ✅ ISC - Compatible (permissive)
    │
    ├── ✅ PSF - Compatible (permissive)
    │
    ├── ✅ LGPL-2.1/3.0 - Compatible (weak copyleft)
    │
    ├── ✅ MPL-2.0 - Compatible (file-level copyleft)
    │
    └── ⚠️ GPL-2.0-only - May have compatibility issues
```

---

## Attribution Requirements

### Packages Requiring Attribution

The following licenses require attribution in documentation or about pages:

**MIT License Attribution:**
```
This software includes packages licensed under the MIT License.
See individual package LICENSE files for details.
```

**Apache 2.0 Attribution:**
```
This software includes packages licensed under the Apache License 2.0.
A copy of the license is available at http://www.apache.org/licenses/LICENSE-2.0
```

**BSD-3-Clause Attribution:**
```
This software includes packages licensed under the BSD 3-Clause License.
See individual package LICENSE files for details.
```

---

## LGPL Considerations

The following packages use LGPL licensing:

- **psycopg2-binary** (LGPL-3.0)

**Compliance Requirements:**
1. ✅ Using as a library (not modifying)
2. ✅ Not statically linking
3. ✅ Project source available
4. ✅ Users can replace the library

**No action required** - LGPL permits use as a dependency without license propagation when used as a library.

---

## Compliance Verification

### Automated Check Script

```bash
# Run license check
pip install pip-licenses
pip-licenses --format=markdown --with-urls

# Or use our audit script
python scripts/audit/dependency_audit.py
```

### Manual Review Checklist

- [ ] All dependencies have identified licenses
- [ ] No GPL-2.0-only dependencies (incompatible)
- [ ] No proprietary/closed-source dependencies
- [ ] Attribution requirements documented
- [ ] NOTICE file updated if required

---

## Adding New Dependencies

When adding new packages:

1. **Check License**
   ```bash
   pip show <package> | grep License
   ```

2. **Verify Compatibility**
   - MIT, BSD, Apache-2.0: ✅ Always OK
   - LGPL: ✅ OK for library use
   - GPL-3.0: ⚠️ OK but review implications
   - GPL-2.0-only: ❌ Not compatible
   - Proprietary: ❌ Not allowed

3. **Update This Document**
   - Add to appropriate table
   - Note any special requirements

4. **Update NOTICE File** (if attribution required)

---

## NOTICE File

A NOTICE file should be included with the following content:

```
Verso-Backend
Copyright 2024 Verso Industries

This product includes software developed by the Flask team (https://palletsprojects.com/).
This product includes software developed by SQLAlchemy authors (https://www.sqlalchemy.org/).

For a complete list of dependencies and their licenses, see:
docs/compliance/license_compliance.md
```

---

*Last Updated: December 2024*
*License scan performed by: pip-licenses, pip-audit*
