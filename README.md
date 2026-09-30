# Trusted Neighbourhood Network — API

Backend for TNN: a neighbourhood utility platform (community notices/issues + a
trusted home-services marketplace). Initial market: Hyderabad, India.

## Architecture

Three strict layers, enforced by convention (see `/db/functions` for the actual rules):

```
/db/migrations   -> schema DDL (tables, enums, indexes), tracked in schema_migrations
                     (lives one level above this folder — see repo root)
/db/functions    -> ALL business logic: PL/pgSQL stored functions, grouped by domain.
                     Validation, state machines, permission checks, SLA/commission
                     calculations, idempotency, audit-log writes — all live here.
/db/seed         -> demo data matching the resident-app prototype (Jasmine Meadows)
/models          -> Pydantic request bodies. One file per domain.
/modules         -> FastAPI routers. One file per domain. Each endpoint:
                     authenticate -> authorize (coarse role gate) -> validate (Pydantic)
                     -> call exactly ONE DB function -> wrap in the response envelope.
/database        -> db.py — the asyncpg pool + call_fn/call_fn_one/call_fn_jsonb helpers.
/adapters        -> external vendors (SMS gateway, payment gateway) behind interfaces,
                     swappable without touching any module or DB function.
/config_file     -> webconfig.ini (gitignored, local DB credentials).
```

Every endpoint returns:

```json
{ "success": true, "data": {}, "error": null }
```

or on failure:

```json
{ "success": false, "data": null, "error": { "code": "...", "message": "...", "details": {}, "correlation_id": "..." } }
```

All routes are versioned under `/api/v1`. All timestamps are UTC. Money is always
integer minor units (paise), never floating point.

## Stack

- **API**: Python 3.13, FastAPI, asyncpg (async Postgres driver), Pydantic v2, python-jose (JWT)
- **DB**: PostgreSQL 17/18, business logic in PL/pgSQL — `Neighbourhood_APP` database
- **Auth**: passwordless OTP login, short-lived JWT access tokens + DB-backed refresh token rotation
- **Payments**: Razorpay adapter behind `PaymentGatewayAdapter`-style interface (no live keys required in dev)
- **SMS/OTP**: 99smsservice.com gateway adapter (falls back to console logging in dev if unconfigured)

## Setup

1. **Database** — create the app role + database (already done for local dev; see below for a fresh machine):
   ```sql
   CREATE ROLE tnn_app WITH LOGIN PASSWORD 'change_me';
   CREATE DATABASE "Neighbourhood_APP" OWNER tnn_app;
   ```
2. **Env** — copy `.env.example` to `.env` and fill in `DATABASE_URL`, `MIGRATION_DATABASE_URL`
   (a superuser/owner role — migrations run as this role so table/function ownership stays
   separate from the runtime `tnn_app` role, which is what makes the `audit_log` immutability
   grant actually bind), `JWT_ACCESS_SECRET`, and the SMS/Razorpay credentials.
3. **Python env**:
   ```bash
   python -m venv .venv
   .venv/Scripts/pip install -r requirements.txt   # Windows
   ```
4. **Run migrations + install DB functions + seed demo data** (script lives in the
   sibling `db/` folder, alongside the migrations/functions/seed it runs):
   ```bash
   .venv/Scripts/python ../db/scripts/run_migrations.py
   ```
   Re-running is safe: schema migrations are tracked by filename in `schema_migrations`
   and only new ones apply; DB functions (`CREATE OR REPLACE`) and seed data
   (`ON CONFLICT ...`) are idempotent and always re-applied.
5. **Run the API**:
   ```bash
   .venv/Scripts/uvicorn main:app --reload --port 4000
   ```
6. **Export the OpenAPI spec** (keeps `openapi/openapi.json` current with the actual routes):
   ```bash
   .venv/Scripts/python ../db/scripts/export_openapi.py
   ```

## Demo credentials (seeded)

- Resident (matches the clickable prototype — "Ananya Reddy", Jasmine Meadows, Tower 4, Unit 401):
  phone `+919848012345`. Log in with `/auth/otp/send`, then check the API response's
  `dev_otp` field (only present when `DEV_EXPOSE_OTP=true`) or the server console log.
- Community admin: phone `+919999900001`
- Platform admin: phone `+919999900000`
- Verified demo provider: "Ravi Electricals" (electrician, 4.8★, 214 jobs)

## Security notes

- Every DB function re-validates authorization itself (`fn__has_capability`,
  `fn__actor_owns_provider`, role checks) — the FastAPI-layer `require_role` is a
  coarse, fail-fast gate only, never the source of truth.
- `audit_log` is insert-only: the runtime role (`tnn_app`) has `UPDATE`/`DELETE`
  revoked at the grant level (`db/migrations/002_grants.sql`), not just by convention.
- OTPs are never stored in plaintext (SHA-256 hash + phone salt); rate-limited to
  5 sends per 10 minutes and 5 verify attempts per code.
- No raw card data ever touches this service — Razorpay Checkout handles card entry.

## What's implemented vs. scaffolded

Fully implemented: auth (OTP + refresh rotation), resident onboarding + community
matching, directory (privacy-by-default), notices, issues (full state machine +
reopen + SLA), polls/events, marketplace browse/rank/profile/favourites, full booking
lifecycle, reviews, payments (Pending→Paid webhook reconciliation + settlement
ledger), provider portal (onboarding, documents, dashboard, staff, availability,
support tickets), admin (community setup, bulk import, membership queue, committee
roles, provider verification, curated providers, reports, moderation), platform admin
(categories, commission/SLA config, feature flags, audit log viewer, KPIs), and
notification dispatch across push/SMS/WhatsApp/email (push/WhatsApp/email are logging
stubs behind the same adapter interface — swap in FCM/Twilio/SES by implementing
`NotificationAdapter`).

Intentionally scaffolded, not implemented (Phase 2 per the product spec):
`modules/ai.py` — community assistant Q&A and AI-personalized provider recommendations.
The interfaces exist and fall back to the plain marketplace ranking so nothing breaks;
implementing them is future work, and they must never be wired to refunds,
suspensions, or dispute decisions per the product guardrails.

## Tests

`tests/` holds pytest scaffolding for integration tests against a real test database
(point `DATABASE_URL`/`MIGRATION_DATABASE_URL` at a disposable DB, e.g.
`Neighbourhood_APP_test`, before running `pytest`). Priority coverage per the spec:
permission/state-machine unit tests in the DB layer, cross-community and
cross-provider authorization tests (must fail closed), and end-to-end tests for the
onboarding → issue and booking → payment → review journeys.
