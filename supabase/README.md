# Supabase Phase 2 setup

1. Create a Supabase project and wait for the database to become ready.
2. Open **SQL Editor** and run `migrations/202611070001_phase2_workspaces.sql` once. Or apply it with the Supabase CLI in a fresh project.
3. Open **Authentication → Providers → Email** and enable email/password auth. For local testing, set your allowed redirect URL to `http://localhost:3000/**` and site URL to `http://localhost:3000` under **Authentication → URL Configuration**.
4. Copy **Project URL** and **Publishable key** from your Supabase project dashboard to `backend/.env` and `frontend/.env.local`. Don't copy the secret/service-role key.
5. Restart both development servers, register on `/login`, and confirm the email if confirmation is enabled. Your profile is created automatically by a database trigger.

The app uses **single-user-owned workspaces** in Phase 2. Each authenticated user sees only their own customers, orders, tickets, and messages. This is *not yet* team collaboration or multi-tenant organization-level RBAC; that is a later phase.

For safer development, use fake names/emails and synthetic orders. The demo endpoints under `/api/v1/orders` remain separate and public and never return the private Supabase records.

## Required variables

Backend `backend/.env`:

```dotenv
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_example
AGENT_MODE=demo
```

Frontend `frontend/.env.local`:

```dotenv
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_example
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Email/password sign-up from an unconfirmed address might not immediately return a session; follow the confirmation link and sign in.

## Security caveats

- No service-role or secret key is required; backend forwards a *validated user access token* to PostgREST.
- Ownership RLS is enabled on all exposed workspace tables.
- Composite foreign keys prevent orders and tickets from referencing another user's records, including an order belonging to another customer.
- User cannot edit `profiles.role`, and `admin` is not automatically granted.
- Registering does not send a customer notification or process refunds.
- For production, add rate limiting, audit logs, email delivery settings, deployment secrets, and full cross-user RLS integration tests.
