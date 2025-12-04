# Verso-Backend Enterprise Enhancement Plan (Nov 30, 2025)

## Current Signal
- Python/Flask monolith with blueprints for auth (`app/routes/auth.py`), admin (`app/routes/admin.py`), scheduling (`app/routes/main_routes.py`), and CMS/blog (`app/routes/blog.py`).
- Data layer: SQLAlchemy models for users/roles, appointments, services, posts, and business config (`app/models.py`).
- Features: RBAC via decorators, basic email + password auth, appointment booking with business-hour config, blog with CKEditor + image BLOBs, sitemap generator.
- Gaps for enterprise-readiness: no MFA/SSO, limited session security, no audit/event trail, minimal input validation on phone/email reuse, no structured logging/metrics, no privacy workflows (DSAR/retention), few tests, no CI controls.

## Enhancement Themes & Recommended Work

### 1) Identity, Access, and Session Security
- Add MFA (TOTP + WebAuthn fallback) and step-up auth for admin/blog actions; enforce password rotation, length, breach checks (HaveIBeenPwned API with k‑anonymity).
- Integrate SSO (OIDC + SAML) for enterprise IdPs (Okta/Azure AD); map IdP groups to local roles in a centralized policy map (e.g., `app/modules/authz_policy.py`).
- Harden session cookies: `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE=strict`, short `REMEMBER_COOKIE_DURATION`, server-side session store (Redis) to enable revocation and device logouts.
- Implement account lockout/backoff on `auth.login` failures and IP/device fingerprinting alerts.

### 2) Compliance & Data Governance
- PII inventory and data-classification matrix for `User`, `Appointment`, `ContactFormSubmission`; tag fields and document processing purposes.
- Add consent + ToS attestation records (already tracks `tos_accepted`; extend with versioning and IP/timestamp tables).
- Build audit log pipeline: append-only `audit_events` table with hashing, plus export to SIEM (Splunk/Elastic) via syslog/OTLP; capture auth, role changes, content changes, and data exports.
- Data subject rights flows: endpoints + admin UI for access/erasure/export; soft-delete with tombstones and purge jobs.
- Retention policies: configurable TTL for contact/appointment data; scheduled purge job (Celery/RQ) with reporting.
- Encryption posture: mandate TLS everywhere, move secrets to a vault (HashiCorp Vault/AWS Secrets Manager), use envelope encryption for stored images and phone numbers (PGP/pgcrypto), and rotate keys.

### 3) Observability, QA, and Risk Controls
- Structured JSON logging (request/response IDs, user ID, role, tenant) and log sampling; propagate trace IDs.
- Metrics & tracing via OpenTelemetry (Flask/SQLAlchemy instrumentation) -> Prometheus/OTLP; define SLIs/SLOs for p95 latency on auth, booking, blog fetch.
- Health endpoints: `/healthz` (process/db), `/readyz` (migrations applied, cache reachable) for load balancers.
- Security testing: Bandit, pip-audit, safety, and secret scanning; DAST (OWASP ZAP) in CI; dependency pinning with Renovate.
- Unit/integration tests for forms, RBAC decorators, booking overlap logic; seed fixtures for roles/services.

### 4) Reliability, Performance, and Data Architecture
- Rate limiting per IP/user/route (Flask-Limiter) on login, booking, contact forms; CAPTCHA for anonymous forms.
- Background jobs for email, sitemap submission, and media processing (Redis + RQ/Celery) to keep request latency low.
- Caching: Redis for session store, CSRF tokens, and computed availability slots; CDN for static assets; move blog images to object storage with signed URLs.
- Database: migrations discipline, read replicas for reporting, query budgets, and indexes on booking time (`Appointment.preferred_date_time`) and `ContactFormSubmission.submitted_at`.
- Resilience: graceful shutdown for workers, circuit breakers on external calls (email, Bing), retry + idempotency keys for form submissions.

### 5) Product & Domain Features
- Multi-tenant option (schema-per-tenant or row-level with `tenant_id`) for agencies/resellers; isolate media buckets per tenant.
- Scheduling upgrades: recurring availability calendars, double-booking prevention window, customer notifications (email/SMS), iCal/Google sync with OAuth.
- CMS enhancements: draft/preview workflow, scheduled publishing, version history, content diffing, and role-based publishing gates.
- Admin UX: audit log viewer, role/permission matrix, configuration UI for retention windows and cookie/session policies.

## Phased Roadmap (sequence + acceptance)

**Phase 0 — Hardening (1–2 weeks)**
- Enable secure cookie flags, helmet-style headers, and rate limits on auth/contact.
- Add JSON structured logging and trace IDs; create `/healthz` & `/readyz` endpoints.
- Minimum test harness with pytest + coverage for auth routes and booking slot generation.

**Phase 1 — Identity & Compliance (weeks 3–6)**
- Ship MFA + lockout + password policy; add SSO adapters and group-to-role mapping table.
- Implement audit event model and emit for auth, RBAC changes, and content CRUD.
- ToS/Privacy versioning table; capture consent with IP/timestamp; admin export.

**Phase 2 — Data Governance & Observability (weeks 7–10)**
- PII catalog and retention configs; background purge jobs with reports.
- OTEL metrics/traces + dashboards (auth latency, booking success rate, blog render p95).
- Backup/restore runbook with quarterly disaster-recovery drill; document RPO/RTO targets.

**Phase 3 — Reliability & Scale (weeks 11–14)**
- Redis for sessions/rate limits/cache; move heavy tasks to workers; idempotent email + sitemap jobs.
- Object storage for media with signed URLs; CDN fronting static assets.
- Performance passes on booking queries and blog pagination; add request budgets.

**Phase 4 — Product Depth (weeks 15–18)**
- Multi-tenant isolation path; tenant-aware RBAC.
- CMS workflow (draft/review/publish, scheduled posts) and scheduling improvements (calendar sync, reminders).
- SIEM integration and SOC-ready dashboards; finalize compliance evidence pack (policies, diagrams, test results).

## Quick Wins (can be done immediately)
- Enforce secure cookie settings and CSRF on JSON endpoints (currently `@csrf.exempt` on some routes).
- Add index on `Appointment.preferred_date_time` and `ContactFormSubmission.submitted_at` for admin views.
- Turn on request logging with unique IDs; log authentication failures with IP/UA for anomaly detection.
- Add Bandit + pip-audit to CI and pin dependency versions in `requirements.txt`.

## Artifacts to Produce Along the Way
- Architecture & data-flow diagrams, PII inventory, threat model (STRIDE/LINDDUN) for appointments/contact/blog flows.
- Runbooks: incident response, backup/restore, key rotation, vulnerability management, change control.
- Compliance traceability matrix mapping controls to code/config (PCI/GDPR/CCPA/SOC2 lite).

## Ownership & RACI (suggested)
- **Identity & Security:** Lead engineer + security partner.
- **Data Governance:** Data/infra engineer + legal/compliance reviewer.
- **Observability & SRE:** Platform engineer.
- **Product Enhancements:** App lead + design.

## Definition of Done (enterprise-ready slice)
- SSO + MFA enforced, RBAC mapped from IdP groups, session hijack protections in place.
- Audit trail immutable and exported; retention + DSAR flows implemented and tested.
- Observability stack live with SLOs and alerting; backup/restore tested; rate limits enforced.
- CI gates for security, linting, tests; release checklist includes migrations and runbook updates.
