# ResolveOps Phase 4 — LangGraph investigation workflow

## What the workflow does

The Phase 4 agent performs an authenticated, **read-only** investigation and
creates an internal response draft. It does not execute payments, ship orders,
send customer messages, or approve its own recommendations.

```text
POST /api/v1/workspace/operations/investigations
  -> verify Supabase bearer JWT and ticket ownership
  -> classify request conservatively
  -> retrieve the owned ticket and optionally its owned order
  -> conditional route:
       order / escalation -> directly draft
       refund / policy / general -> Gemini-backed policy retrieval -> draft
  -> assess deterministic human review flags
  -> store draft, evidence, workflow_steps and review_flags in agent_runs
  -> support team reviews any proposed action via separate approval queue
```

## Intent and security

Intent is detected by deterministic rules in `backend/app/agents/intent.py`.
Refund and reimbursement requests receive priority over order tracking. The
classification determines **which evidence to inspect**, not permission to
execute account actions. Every database lookup uses the verified end-user JWT
plus an owner filter, with database RLS as a second enforcement layer.

Documents retrieved by RAG are untrusted input. The policy-answer component
requires citation tokens and returns an ungrounded response if the evidence is
missing. Refund requests require human review regardless of citations.

## Safety and failure handling

- Ticket and order labels are bounded and stripped of hidden control characters.
- A missing linked order is flagged for human verification.
- A policy answer without evidence is flagged `policy_not_verified`.
- Provider failures (502/503/504) degrade to a human-review draft.
- Authentication/authorization, invalid input and rate-limit failures are
  **not** silently converted into successful investigations.
- `GRAPH_TIMEOUT_SECONDS` defaults to 30 seconds and is constrained to 5–120.
- No mid-graph checkpoint/resume is implemented. Final results are persisted only
  after the request graph completes.
- Approved `refund_review` records are *not* payment refunds.
- Approved reply records are internal ticket notes, not outgoing messages.

## Deployment and migration

Apply the migrations in order:

1. `202611070001_phase2_workspaces.sql`
2. `202611090001_phase3_knowledge_rag.sql`
3. `202611100001_phase4_5_operations.sql`
4. `202611110001_phase4_agent_trace.sql` (**new**)

The fourth migration adds `workflow_steps` and `review_flags` JSON arrays to
`agent_runs`. Until it has been applied, investigation persistence will fail:
**apply it before testing the updated Phase 4 endpoint**. Existing records
receive empty arrays; they are not retroactively reconstructed.

The backend requires `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY`. A
`GOOGLE_API_KEY` is only needed for live policy retrieval. Keep all secrets in
`backend/.env` (never commit it). The frontend needs its public Supabase
configuration as explained in `PHASE4_7_SETUP.md`.

## Testing checklist

From `backend/`: `python -m pytest -q`. The tests include classification,
policy-routing decisions, user-scoped lookups, sanitized draft fields,
risk flags, persistence payloads, and timeout handling. GitHub Actions runs
the backend suite on push. Frontend CI runs lint and production build.

These offline tests **do not replace** live Supabase/RLS integration tests
with two separate test accounts, or a live Gemini RAG evaluation. Complete
those checks before any production deployment.
