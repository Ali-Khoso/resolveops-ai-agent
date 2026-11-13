# Phase 6 — Dashboard and UX setup guide

## 1. Run the synthetic showcase (no credentials)

1. From `frontend/`, run `npm install && npm run dev`.
2. Open `http://localhost:3000/showcase` for the overview.
3. Open `http://localhost:3000/showcase/tickets` to search, filter, sort, paginate and open a ticket detail drawer.
4. Open `http://localhost:3000/showcase/insights` to view synthetic charts.
5. Compare the visuals with `docs/screenshots/README.md`. The images were captured from a deterministic static HTML mock with **synthetic sample data**.

This is a public, safe portfolio preview. It does not read Supabase or run an agent. The preview screenshot images are reference mock captures, not evidence of a live backend.

## 2. Configure the authenticated workspace

Follow `docs/PHASE4_7_SETUP.md` and `docs/PHASE5_APPROVALS.md`.

- Backend: copy `backend/.env.example` to `backend/.env`.
- Frontend: copy `frontend/.env.example` to `frontend/.env.local`.
- Set Supabase project URL and publishable key on both sides; set Gemini key **only** in the backend.
- Apply all five migration files under `supabase/migrations/`, in file-name order.
- Create two test accounts for cross-account RLS verification.
- Run `python -m pytest -q` in `backend/`, and `npm run phase6:check && npm run lint && npm run build` in `frontend/`.

## 3. Test the real signed-in journey

1. Sign in at `/login`.
2. Add a fictional customer, order and ticket at `/workspace`.
3. Visit `/dashboard` and verify the new support KPIs.
4. Visit `/tickets`: search by subject/customer, filter and sort, click the ticket to inspect its details.
5. Upload a synthetic return-policy document in `/knowledge`.
6. Investigate the ticket in `/operations`; review citations, flags and workflow trace.
7. Create an approval; approve or reject with written notes.
8. Inspect `/activity` and `/insights` for recorded events and current counts.
9. Log in as another test user and confirm there is no cross-account data leakage.

## 4. Remaining work (Phase 7)

Production security and authorization review; independent reviewer roles;
server-side search/pagination and durable aggregated analytics;
LangGraph checkpointing and background workers; rate limits; observability,
tracing, alerts, incident logging, backup/restore procedures, performance tests,
multi-account integration tests, accessibility audits and deployment.

No real emails or refunds are issued by this demo. No real user data should
be uploaded until these controls are implemented and independently reviewed.
