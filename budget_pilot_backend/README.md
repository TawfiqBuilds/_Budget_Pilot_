# Budget Pilot — Backend (Phase 1: schema + FastAPI scaffold)

Implements Section 1–4 of `Budget_Pilot_Rearchitecture_Plan.md`: categories are
permanent and archive instead of delete, per-month data lives in its own table
that never gets wiped, and the 8 fixed categories are protected server-side.

## What's in this phase

- `app/models/` — the 4 tables (`categories`, `category_months`, `purchases`, `reference_items`)
- `app/crud/category.py` — the actual fix: `archive_category()` soft-deletes and
  refuses to touch the 8 fixed categories; `hard_delete_category()` is a separate,
  explicit action that requires `?cascade=true` if history exists
- `app/api/v1/` — categories, months, and account-deletion endpoints
- `app/core/security.py` — verifies the Supabase JWT on every request (using PyJWT)
- `alembic/versions/0001_initial_schema.py` — creates the new tables *alongside*
  your existing `ledger_data` table (nothing old is touched or dropped)

**Fresh start:** no data migration from the old `ledger_data` blob table —
this is a clean rebuild, old data is not carried over.

Not yet built (later phases, per the plan doc): purchases/reference-items routers,
`budget_calc.py` aggregation service, and the frontend rewrite.

## Setup

```bash
cd budget_pilot_backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in DATABASE_URL, SUPABASE_URL, SUPABASE_JWT_SECRET, SUPABASE_SERVICE_ROLE_KEY
# (all four are in your Supabase dashboard under Project Settings -> API / Database)
#
# IMPORTANT: for DATABASE_URL, use the "Transaction pooler" connection string, not
# "Direct connection". The direct host (db.<ref>.supabase.co) is IPv6-only and will
# fail with "could not translate host name" on most Windows/home networks. The
# pooler host (aws-0-<region>.pooler.supabase.com) works over IPv4 everywhere.
# Find it at: Project Settings -> Database -> Connection string -> Transaction pooler.

alembic upgrade head      # creates the 4 new tables in your existing Supabase Postgres

uvicorn app.main:app --reload
# -> http://localhost:8000/docs for interactive API docs
```

## Seeding your 8 fixed categories

After a user's first login, call:

```python
from app.crud.category import seed_default_categories
seed_default_categories(db, user_id)
```

This is idempotent — safe to call every login, it only seeds once per user.

## Deploying (free tier)

- **Render** → New Web Service → connect this repo → build command
  `pip install -r requirements.txt`, start command
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
  Add the same env vars from `.env` in Render's dashboard.
- Free tier cold-starts after 15 min idle (30–60s first request) — fine for personal use.

## Next steps

See `Budget_Pilot_Rearchitecture_Plan.md`, Section 8, Phases 2–7.
