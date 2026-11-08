# ResolveOps — AI Support & Order Resolution Platform

Production-minded portfolio application for a support operations team: FastAPI, LangChain/Gemini, Next.js, Supabase Auth + Postgres + RLS, and testable API workflows.

**Status:** Phase 1 demo and Phase 2 authenticated-workspace implementation are in the repository. Phase 3 (company-policy RAG) and subsequent LangGraph workflows are not implemented.

## What you can do

- **Public Phase 1 demo (`/`):** ask about three fictional orders in offline demo mode, or optionally enable LangChain/Gemini tool calling with a private key.
- **Private Phase 2 workspace (`/login` → `/workspace`):** email/password signup and login through Supabase; create and review customers, orders and support tickets; change ticket status; write internal notes.
- **REST APIs:** token verification against Supabase Auth, user-scoped PostgREST access, request validation, pagination and RLS.
- **PostgreSQL migration:** `supabase/migrations/202611070001_phase2_workspaces.sql` creates tables, profile signup trigger, composite ownership checks and RLS policies.
- **Tests:** backend checks work without cloud credentials; GitHub Actions runs `pytest` in demo mode.

## Quick start

Read **[docs/PHASE2_SETUP.md](docs/PHASE2_SETUP.md)** for exact URLs, key locations, database migration, VS Code commands and API routes.

```powershell
git clone https://github.com/Ali-Khoso/resolveops-ai-agent.git
cd resolveops-ai-agent
code .
```

Backend (terminal 1):

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m pytest -q
python -m uvicorn app.main:app --reload
```

Frontend (terminal 2):

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

For Supabase functionality add the URL and publishable key to **both** `.env` files and run the migration. Without credentials, the Phase 1 demo still works; `/workspace` does not silently bypass authentication.

## Security boundaries

- Phase 2 backend accepts an **end-user token** and validates it through Supabase Auth, then forwards the token to PostgREST so RLS can enforce row ownership.
- The secret/service-role key is **not needed** and must not be added to this project.
- Each user can see only their own records. Cross-user/cross-customer relationships are prohibited by composite FKs.
- Ticket messages are internal agent notes; AI cannot issue refunds, write messages or modify real orders yet.
- User-created records require authentication; public Phase 1 endpoints return **only synthetic** orders.
- These are portfolio/demo safeguards, not a complete production security review.

## Folder layout

- `backend/app/api/` — FastAPI public demo and authenticated workspace routes
- `backend/app/core/supabase.py` — token verification + configuration
- `backend/app/services/postgrest.py` — user-token database transport
- `backend/app/models/workspace.py` — strict request schemas
- `backend/app/agents/` and `backend/app/tools/` — LangChain demo agent and order tool
- `frontend/src/app/login/` and `frontend/src/app/workspace/` — Phase 2 UI
- `supabase/migrations/` — SQL schema, roles and RLS
- `docs/` — setup, architecture, and roadmap

## Upcoming phases

1. Foundation and demo tool-calling — ✅ implemented
2. Supabase database, authentication, customer/order/ticket CRUD — ✅ code implemented; needs your Supabase project setup
3. Knowledge base and grounded RAG — planned
4. LangGraph agent workflows — planned
5. Human approval and ticket automation — planned
6. Professional dashboard refinements and advanced UX — planned
7. Monitoring, deployment, security hardening and evaluations — planned

**License:** MIT. Do not use personal or live business data until the remaining authorization, security and compliance work is complete.

## Phase 3 — private company-policy RAG

- Authenticated **Knowledge Base** at `/knowledge`.
- PDF (text-based), Markdown and TXT upload; LangChain chunking with PDF page citations.
- Gemini `gemini-embedding-001` (768-dimensional vectors) with Supabase pgvector.
- Per-user Postgres RLS and **SECURITY INVOKER** semantic search RPC.
- LangChain/Gemini answers with retrieved source excerpts, citation checks and abstention.
- Full setup and test guide: [Phase 3 setup](docs/PHASE3_SETUP.md).

Run `supabase/migrations/202611090001_phase3_knowledge_rag.sql` after the Phase 2 migration. Then add your **private** `GOOGLE_API_KEY` to `backend/.env`. Do not commit your credentials. Live Google/Supabase checks require your configured project.
