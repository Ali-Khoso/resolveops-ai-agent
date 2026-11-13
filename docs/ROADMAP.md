# ResolveOps development roadmap

The repository now contains the **coded implementation for Phases 1–6**.
Live Supabase integration, Gemini policy RAG, cross-account authorization,
and production readiness must still be validated with real test accounts.

- [x] **Phase 1 — Foundations:** FastAPI, Next.js, LangChain demo agent, offline sample orders
- [x] **Phase 2 — Customer operations:** Supabase Auth, PostgreSQL row-level security, customer/order/ticket CRUD
- [x] **Phase 3 — Knowledge retrieval:** PDF/text policy ingestion, pgvector semantic search, source-cited Q&A
- [x] **Phase 4 — LangGraph:** classified investigation workflow, owned order lookup, policy evidence, bounded traces
- [x] **Phase 5 — Human review:** approval-request validation, auditable internal decisions, queue UI, SQL safeguards
- [x] **Phase 6 — UX:** responsive dashboard, accessible shell, searchable/filterable tickets, details, analytics, activity, public synthetic previews, screenshot gallery
- [ ] **Phase 7 — Production hardening:** full E2E tests with connected accounts, role-separated reviewer permissions, rate limits, resilient background jobs and checkpoints, observability/alerts, deployment security, backups, performance and accessibility audit

## Known limitations before production

1. One user owns a private workspace; independent second-person approval and team RBAC are not implemented.
2. SQL migrations must be applied manually in order; no production migrations have been verified.
3. Agent runs store finished results but do not support checkpoint/resume mid-run.
4. Real refund processing, sending customer emails, and external order/shipping integrations are not enabled.
5. Frontend ticket explorer filters the records returned by the existing bounded list API; it is not global server-side searching.
6. Analytics summarize capped API responses, not a complete, historical data warehouse.
7. Demo screenshots use synthetic data, not live Supabase customer records.
8. Production deployment requires TLS, secrets management, audit retention, monitoring, rate limiting and independent security evaluation.

See [Phase 6 guide](PHASE6_SETUP.md), [Phase 5 approval guide](PHASE5_APPROVALS.md), and [screenshot walkthrough](screenshots/README.md).
