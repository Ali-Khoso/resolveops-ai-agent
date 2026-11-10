# ResolveOps Phase 4–7 setup and security checklist

This extends the existing Phase 2 and Phase 3 guides. No private keys,
production database records or live customer credentials are stored in Git.

## Credentials
- Supabase URL and publishable key from https://supabase.com/dashboard
- Gemini key from https://aistudio.google.com/apikey (for policy RAG)
- Backend: copy backend/.env.example to backend/.env. Set SUPABASE_URL,
  SUPABASE_PUBLISHABLE_KEY, GOOGLE_API_KEY, FRONTEND_ORIGIN, AGENT_MODE.
- Frontend: copy frontend/.env.example to frontend/.env.local. Set
  NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
  NEXT_PUBLIC_API_URL=http://127.0.0.1:8000.
- Do NOT expose a Supabase service-role key in the frontend.

## Database setup
Run these migrations in the Supabase SQL Editor, in order:
1. supabase/migrations/202611070001_phase2_workspaces.sql
2. supabase/migrations/202611090001_phase3_knowledge_rag.sql
3. supabase/migrations/202611100001_phase4_5_operations.sql

The last migration creates per-user investigations, approval requests, audit
records and an atomic approval-decision function. No real refunds are executed.

## Run locally
Backend: install backend/requirements.txt in a Python 3.11+ venv, run
python -m pytest -q from backend, then:
  python -m uvicorn app.main:app --reload
API documentation: http://127.0.0.1:8000/docs

Frontend: use Node 22+, npm install, npm run lint, npm run build, npm run dev.
Pages: http://localhost:3000/login, /workspace, /knowledge, /operations, /analytics.

Test the full flow using synthetic data: create customer, order and ticket;
upload a policy; investigate the ticket; request approval; approve/reject;
check the decision in the audit history.

## Docker (local development only)
Copy .env.compose.example to the repository-root .env and supply public
Supabase build values. Configure backend/.env with server-side settings.
Run docker compose up --build.

## Important limitations
- Agent execution uses a LangGraph request workflow. Saved result records are
  durable, but mid-run checkpoint/resume is not implemented.
- Reply approvals create internal ticket notes, not outgoing customer emails.
- Refund review is only a recorded decision; it does NOT refund money.
- Deploying for real customers requires production security review, rate
  limiting, TLS, logging redaction, separate reviewer permissions, backups,
  action idempotency, load tests and live integration verification.
