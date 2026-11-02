# ResolveOps AI Agent

A practical AI support operations starter built with **FastAPI**, **LangChain**, **Gemini**, and **Next.js**. Phase 1 uses **fictional orders** and a clearly marked deterministic demo mode so the entire request flow is testable without credentials.

> **Phase 1 only.** No authentication, production database, real refunds, payment actions, or live customer integrations are implemented. Do not deploy with real customer data.

## Features

- Order lookup using safe, read-only tools (`1001`, `1002`, `1003`).
- FastAPI health, orders, and chat endpoints with input validation.
- LangChain `create_agent` with a Gemini tool-calling path, enabled explicitly.
- Credential-free, deterministic demo mode for local testing.
- Next.js App Router support dashboard with interactive chat.
- Offline tests and an automated GitHub Actions backend test job.

## Run locally (Windows PowerShell)

Clone the repository, open the `resolveops-ai-agent` folder in VS Code, then open two terminals.

```powershell
git clone https://github.com/Ali-Khoso/resolveops-ai-agent.git
cd resolveops-ai-agent
code .
```

**Terminal 1 — backend**

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

If `py -3.11` is unavailable, use `py -3.12` or `py -3.13`. FastAPI Swagger: http://127.0.0.1:8000/docs . Test with `python -m pytest` from `backend`.

**Terminal 2 — frontend**

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000. Use Node.js **20.9+**.

## Enable the actual AI agent

1. Create a Gemini API key in Google AI Studio.
2. Edit **only** `backend/.env`:

```dotenv
AGENT_MODE=ai
GOOGLE_API_KEY=your_actual_key
GEMINI_MODEL=gemini-2.5-flash-lite
```

3. Restart FastAPI. **Never commit your `.env` or publish API keys.** Gemini API quotas and pricing depend on your account. Without a key, keep `AGENT_MODE=demo`.

## Useful endpoints

- `GET /health` — service health and active mode.
- `GET /api/v1/orders` — fictional sample orders.
- `GET /api/v1/orders/1001` — one order.
- `POST /api/v1/agent/chat` — JSON `{"message": "Where is order 1001?"}`.

The demo agent intentionally does **not** process refunds, update orders, or claim to know live shipment status.

## Phase 2 onward

Supabase authentication and per-customer authorization, PostgreSQL orders/tickets, RAG over policies, LangGraph approvals and audit logs. See `docs/ROADMAP.md` and `docs/ARCHITECTURE.md`.

## Security note

API routes expose **fictional demo data only**. Production features require access control, authenticated customer ownership checks, rate limiting, request tracing, and explicit approval for sensitive actions.
