# ResolveOps Engineering Roadmap

## Phase 1 — Local working MVP (this repo)
- [x] Python FastAPI REST application
- [x] Isolated fictional sample order tool
- [x] LangChain tool calling with Gemini AI mode
- [x] Credential-free explicit demo mode
- [x] Next.js dashboard with support chat
- [x] Input validation, error states and automated API tests
- [x] GitHub Actions backend CI
- [ ] Test live Gemini flow with **your own** local API key
- [ ] Run frontend build on your VS Code machine

## Phase 2 — Persistence and identity
- Supabase PostgreSQL schema: organizations, profiles, customers, orders, tickets, messages.
- Auth and role-based access control; test cross-customer isolation and RLS policies.
- Ticket CRUD, pagination, ownership validations and audit logs.

## Phase 3 — Retrieval and evaluation
- Policy uploads; safe parsing and chunking.
- Embeddings in pgvector; metadata filtering and citation-backed answers.
- Evaluation set containing grounded, conflicting and missing-policy cases.

## Phase 4 — Agent orchestration
- LangGraph nodes for intent, order lookup, policy search, outcome drafting.
- Durable state, retries, timeouts and human approval before refunds.
- Idempotency keys and irreversible-action safeguards.

## Phase 5 — SaaS interface
- Authenticated inbox, ticket detail, document manager and approval queue.
- Responsive dashboards with accessible forms and loading states.

## Phase 6 — Quality and deployment
- LangSmith traces, privacy-safe logs, regression evaluation and cost metrics.
- Docker, CI/CD, security review and public demo using synthetic data.
