# ResolveOps Phase 5 — Internal approval workflows

## Scope and safety

Phase 5 implements account-scoped internal human-review requests for:

| Action | Internal outcome after approval |
| --- | --- |
| `send_reply` | An internal ticket message (nothing sent to the customer) |
| `resolve_ticket` | Changes the owned ticket to `resolved` |
| `refund_review` | Records a review decision only; **never** issues a payment refund |

There is **no Stripe, PayPal, shipping-service, or outbound email integration**.
This prototype is **one account = one workspace**. The requesting account can also
review its own requests. It is NOT an independent two-person approval system.
Before production use, implement role-separated reviewer permissions, risk
assessments, live RLS tests with multiple accounts, and security review.

## Setup

Use [Phase 4–7 setup](PHASE4_7_SETUP.md) for your private Supabase project
URL, publishable key, authentication, Gemini key and local startup commands.

Run all five SQL migrations in order, including:

`supabase/migrations/202611120001_phase5_approval_guardrails.sql`

This migration hardens **both** direct PostgREST creation and SQL decisions,
so bypassing FastAPI does not bypass the core business constraints.
It also replaces `decide_approval` with an owner-checked row-locking version.
Do not run the operations UI against an outdated database schema.

## Review rules

- A closed ticket cannot receive any new approval request.
- A resolved ticket cannot be resolved again.
- A refund review requires a matching, pending refund investigation.
- A refund investigation cannot be resolved using a different action.
- An escalation investigation cannot be resolved without response review.
- Rejections require a written reason (enforced in Pydantic and Postgres).
- An **approved** refund review requires written rationale (enforced in SQL).
- Identical decision retries are idempotent; contrary retries return HTTP 409.
- Decisions and their actor are recorded in the immutable, owner-scoped audit
  table. Audit rows are read-only for normal authenticated users.

## API reference (requires Supabase access token)

Use `Authorization: Bearer <user-access-token>` on the authenticated routes.
Never store this token in a repository or terminal screenshot.

| Route | Purpose |
| --- | --- |
| `POST /api/v1/workspace/operations/approvals` | Create an internal review request |
| `GET /api/v1/workspace/operations/approvals?status=pending&limit=20&offset=0` | Filter and paginate your approvals |
| `GET /api/v1/workspace/operations/approvals/{id}` | Read one owned approval |
| `POST /api/v1/workspace/operations/approvals/{id}/decision` | Approve/reject with optional or required note |
| `GET /api/v1/workspace/operations/audit?approval_id={id}&limit=20&offset=0` | Filter and paginate decision audit |
| `GET /api/v1/workspace/operations/analytics` | Review internal metrics |

Example rejection body:

```json
{"decision": "rejected", "note": "Refund request lacks supporting evidence."}
```

Example refund-review approval body (records only a decision):

```json
{"decision": "approved", "note": "Policy and order status independently checked; approved for manual follow-up."}
```

## Testing

Within `backend/`, run `python -m pytest -q`. The Phase 5 regression suite
tests approval state rules, HTTP ownership filters, note validation, conflict
translation, and static SQL safety contracts.

In your real Supabase project, use **two distinct accounts** to confirm one
cannot list, create against, or decide on another account's approvals. Test
repeat decisions and conflicting decisions. Check that internal notes are
written at most once and that no external email or payment events occur.
Offline tests cannot replace these integration checks.

## Production limitations

No independent reviewer RBAC, no reviewer assignment, no notification service,
no automatic email, no real refund gateway, and no production-grade audit
retention policy. The database migration must be applied manually.
