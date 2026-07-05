# Budget Pilot — Frontend (fresh rebuild)

A minimal, mobile-first React app wired to the FastAPI backend. Nothing here
talks to Supabase directly except authentication (sign in / sign up) — every
piece of budget data goes through the API, which is where all the rules
(fixed categories, archive-not-delete, account deletion) actually live.

## Design

- Quiet neutral palette (`paper`/`ink`/`line`) with a single accent (`pine`,
  a muted teal-green) for primary actions and "on track" states. Amber for
  "spending faster than the month is passing," clay-red reserved only for
  "over budget" — so red actually means something when it shows up.
- The **ledger rail** (`src/components/LedgerRail.jsx`) is the one signature
  visual: a thin ruled bar per category, filled to actual spend, with a small
  tick marking how far into the month you are. If the fill passes the tick,
  you're outpacing the calendar — no chart or extra number needed to explain it.
- `Fraunces` (display) + `Inter` (body) + `IBM Plex Mono` (money figures, so
  amounts always align).

## Setup

```bash
npm install
cp .env.example .env
```

Fill in `.env`:
- `VITE_SUPABASE_URL` / `VITE_SUPABASE_PUBLISHABLE_KEY` — same Supabase project as the backend, Settings -> API Keys (the `sb_publishable_...` one, safe for the browser)
- `VITE_API_BASE_URL` — your FastAPI backend, e.g. `http://localhost:8000/api/v1` locally, or your Render URL in production

```bash
npm run dev       # http://localhost:5173
npm run build     # production build, verified working (see below)
```

## What's here

- `src/pages/Login.jsx` — sign in / sign up via Supabase Auth
- `src/pages/Dashboard.jsx` — month switcher, category ledger rails, inline
  planned-amount editing, add/archive categories, log/delete purchases
- `src/pages/Settings.jsx` — the account-deletion danger zone: type your
  email exactly to enable the delete button, calls `DELETE /account`
- `src/lib/api.js` — every backend call, always attaching the current
  Supabase session's JWT
- `src/lib/auth.jsx` — session state via React context

## Verified

`npm run build` completes cleanly with zero errors (73 modules, ~130KB gzipped).
Not yet verified: a live run against your actual Supabase project + deployed
backend, since that needs your real credentials.

## Not yet built

- Reference-items UI (the "what's inside Food bucket" line items) — the
  backend endpoints exist (`/reference-items`), just not wired into a screen yet
- Charts/rolling-average view (`GET` endpoint exists in `budget_calc.py`, no UI yet)
