# Phase 2 — From GitHub to a working Supabase workspace

Phase 2 includes a working code path for **email/password Supabase Auth**, **PostgreSQL** via Supabase PostgREST, ownership-based **RLS**, customers, orders, tickets, and internal ticket messages. It does **not** include payments, refunds, live shipping APIs, or RAG.

## 1. Requirements

- Python 3.11+ / Node.js 20.9+
- A Supabase account and **one** Supabase project.
- Project URL + Publishable key only. **No service role key.**
- Gemini is optional, only for the existing Phase 1 `AGENT_MODE=ai` feature.

## 2. Supabase setup

1. In the [Supabase dashboard](https://supabase.com/dashboard), create a project and wait for the database to provision.
2. Open **SQL Editor** and paste the migration from `supabase/migrations/202611070001_phase2_workspaces.sql`; run it once.
3. Under **Authentication → Providers**, check that email sign-in is enabled. Decide whether to require email confirmations for the demo.
4. Under **Authentication → URL Configuration**, set Site URL to `http://localhost:3000` and add `http://localhost:3000/**` to Redirect URLs.
5. Copy **Project URL** and **Publishable key** from Project Settings → API Keys or the project's Connect screen (menu names may vary).

## 3. Create .env files

Backend: from `backend/`, copy `.env.example` to `.env`, and set

```env
AGENT_MODE=demo
SUPABASE_URL=https://PROJECT_ID.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_REPLACE_ME
```

Frontend: from `frontend/`, copy `.env.example` to `.env.local`, and set

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SUPABASE_URL=https://PROJECT_ID.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_REPLACE_ME
```

The publishable key may appear in the browser; it must not grant database access without a valid user session. **Do not use a secret key in any `NEXT_PUBLIC_` variable.**

## 4. Start servers (Windows PowerShell)

Terminal 1:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app.main:app --reload
```

Terminal 2:

```powershell
cd frontend
npm install
npm run build
npm run dev
```

Visit `http://localhost:3000/login`. Create an account (confirm via email if enabled), sign in, and open `http://localhost:3000/workspace`.

## 5. Test workflow

1. Create a fictional customer with an example email.
2. Create an order for that customer.
3. Open a support ticket, optionally linked to the order.
4. Choose a ticket, add an internal agent note, then change its status.
5. Sign out and create a second account. Its lists should be empty (RLS isolation).
6. Confirm the public `/api/v1/orders` still only returns 3 fabricated Phase 1 records and never the private data.

## 6. API overview

All `/api/v1/workspace/**` endpoints **require** `Authorization: Bearer <Supabase access_token>`.

| Method | Route | Action |
| --- | --- | --- |
| GET / PATCH | `/api/v1/workspace/me` | Own profile |
| GET / POST | `/api/v1/workspace/customers` | List/create customers |
| GET / PATCH / DELETE | `/api/v1/workspace/customers/{uuid}` | Customer record |
| GET / POST | `/api/v1/workspace/orders` | List/create orders |
| GET / PATCH | `/api/v1/workspace/orders/{uuid}` | Order detail/status |
| GET / POST | `/api/v1/workspace/tickets` | List/create tickets |
| GET / PATCH | `/api/v1/workspace/tickets/{uuid}` | Ticket detail/status |
| GET / POST | `/api/v1/workspace/tickets/{uuid}/messages` | Internal messages |

Use Swagger at `http://127.0.0.1:8000/docs`. API endpoints are not operational until the SQL migration and environmental values have been applied.

## 7. Important limitations

- Phase 2 is scoped to **one private workspace per user**, not shared-team/multi-tenant roles.
- The initial `profiles.role` is `agent` and cannot be escalated by end users. Admin features are future scope.
- Database policies are written but **cross-account live database tests still need running on your Supabase project**.
- Python tests mock Auth/PostgREST; no live database, email-delivery, or browser end-to-end tests were performed in the development environment.
- The frontend requires npm packages before build verification, and the Gemini mode requires your own private key.
- Avoid uploading real customer data until production hardening and privacy review.
