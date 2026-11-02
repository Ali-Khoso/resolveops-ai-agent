# Architecture — Phase 1

```text
Browser / Next.js :3000
    | GET /health, GET /api/v1/orders, POST /api/v1/agent/chat
    v
FastAPI :8000
    |-- core/config.py   (AGENT_MODE demo | ai)
    |-- api/routes.py    (validated REST endpoints)
    |-- tools/orders.py  (isolated, read-only fictional data)
    +-- agents/support_agent.py
          |-- demo: deterministic local response
          +-- ai: LangChain create_agent -> Gemini -> lookup_order tool
```

## Safety boundaries

- The agent only has a read-only fictional order tool.
- No credentials are ever exposed to the frontend.
- No payment or refund actions exist in Phase 1.
- The API returns a `mode` value so users can tell demo from LLM output.
- Order data is not private or authenticated: **do not replace sample records with live data** until Phase 2 authorization exists.

## Future additions

Phase 2: Supabase Auth, scoped PostgreSQL customer records, tickets, service layer. Phase 3: embeddings and policy RAG. Phase 4: LangGraph state machine, gated actions, approvals and audit logs.
