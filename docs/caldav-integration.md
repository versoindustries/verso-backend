# CalDAV Integration Research

## Overview

CalDAV (Calendaring Extensions to WebDAV) is a standard protocol for calendar synchronization. This document outlines the integration path for Verso's calendar system with external calendar providers.

## Current State

Verso currently provides:
- **ICS Feed Export** (Read-only): `/calendar/ics/<estimator_id>.ics`
  - Standard iCalendar format
  - Subscribable in Google Calendar, Outlook, Apple Calendar
  - One-way sync (Verso → External)

## CalDAV Integration Options

### Option 1: CalDAV Server Integration (Recommended)

Use an existing CalDAV server like **Radicale** or **DAViCal** alongside Verso.

**Architecture:**
```
                    ┌─────────────────┐
                    │  External       │
                    │  Calendar Apps  │
                    └────────┬────────┘
                             │ CalDAV
                             ▼
                    ┌─────────────────┐
                    │  Radicale       │
                    │  CalDAV Server  │
                    └────────┬────────┘
                             │ Webhooks/Sync
                             ▼
                    ┌─────────────────┐
                    │  Verso Backend  │
                    └─────────────────┘
```

**Implementation Steps:**
1. Deploy Radicale alongside Verso (Docker or same server)
2. Create sync daemon that:
   - Pushes Verso appointments to Radicale calendar
   - Polls Radicale for external changes
   - Reconciles conflicts with priority rules
3. Authenticate users via Verso credentials

**Pros:**
- Full two-way sync
- Standard protocol support
- Works with all CalDAV clients

**Cons:**
- Additional service to maintain
- Sync delay between systems
- Potential for conflicts

### Option 2: Direct Provider APIs

Integrate directly with calendar providers via their APIs.

**Google Calendar:**
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# OAuth2 flow for user authorization
# Push events to user's Google Calendar
service = build('calendar', 'v3', credentials=creds)
event = service.events().insert(calendarId='primary', body=event_body).execute()
```

**Microsoft Outlook (Graph API):**
```python
import msal
import requests

# MSAL authentication
# POST to /me/events
```

**Pros:**
- Native integration
- Real-time updates possible
- Rich feature support

**Cons:**
- Provider-specific code
- OAuth complexity
- Requires user authorization per provider

### Option 3: Hybrid Approach

Combine ICS feed with selective push updates.

**Implementation:**
1. Keep ICS feed for basic read access
2. Add webhook endpoints for external calendar changes
3. Use provider APIs only for critical updates (reschedules, cancellations)

## Recommended Implementation Path

### Phase 1: Enhanced ICS (Current)
- ✅ Basic ICS export implemented
- Add refresh interval header: `X-WR-REFRESH: 15min`
- Add VALARM reminders for appointments

### Phase 2: Google Calendar Push (Future)
1. Create Google Cloud project
2. Implement OAuth2 consent flow
3. Add "Connect Google Calendar" button to estimator profile
4. Sync appointments on create/update/delete

### Phase 3: Full CalDAV (Long-term)
1. Evaluate Radicale deployment
2. Build sync daemon
3. Test with multiple clients

## Security Considerations

- **OAuth Tokens**: Store refresh tokens encrypted, use short-lived access tokens
- **Webhook Validation**: Verify signatures on incoming webhooks
- **Scopes**: Request minimal calendar permissions
- **User Consent**: Clear disclosure of calendar access

## Resources

- [CalDAV RFC 4791](https://tools.ietf.org/html/rfc4791)
- [Radicale Documentation](https://radicale.org/v3.html)
- [Google Calendar API](https://developers.google.com/calendar/api)
- [Microsoft Graph Calendar API](https://docs.microsoft.com/en-us/graph/api/resources/calendar)
- [icalendar Python Library](https://icalendar.readthedocs.io/)

## Decision Matrix

| Approach | Complexity | Two-Way Sync | Sovereignty | Maintenance |
|----------|------------|--------------|-------------|-------------|
| ICS Only | Low | ❌ | ✅ High | ✅ Low |
| Radicale | Medium | ✅ | ✅ High | ⚠️ Medium |
| Provider APIs | High | ✅ | ⚠️ Medium | ⚠️ Medium |
| Hybrid | Medium | Partial | ✅ High | ⚠️ Medium |

## Conclusion

For Verso's "sovereignty-first" philosophy, the **Radicale hybrid approach** offers the best balance:

1. Self-hosted CalDAV maintains data control
2. Two-way sync for power users who need it
3. ICS feed continues to work for basic cases
4. No dependency on third-party APIs

Implementation estimate: 2-3 weeks for initial CalDAV integration, 1 week per provider API.
