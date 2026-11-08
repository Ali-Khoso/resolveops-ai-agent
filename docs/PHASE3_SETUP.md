# Phase 3 — Policy RAG: setup and validation

Phase 3 adds a private knowledge base with PDF/TXT/Markdown ingestion, Gemini embeddings, pgvector retrieval and source-cited answers. No refund automation is enabled.

## Requirements
- Apply Phase 2 first: `supabase/migrations/202611070001_phase2_workspaces.sql`.
- Supabase project URL and **publishable** key from your own Supabase dashboard.
- A **private** Google Gemini API key for embeddings and response generation, regardless of `AGENT_MODE=demo`. Do not share or commit credentials.
- Python 3.11+ and Node 20.9+.

## 1. Apply the migration
In Supabase > SQL Editor, run the entire `supabase/migrations/202611090001_phase3_knowledge_rag.sql` file. It creates `knowledge_documents`, `knowledge_chunks`, per-user ownership RLS, a cosine vector index, and the authenticated `match_policy_chunks` RPC (security invoker). It must run **after** Phase 2.

## 2. Backend environment
In `backend/.env` (copy `.env.example`), configure:

```dotenv
AGENT_MODE=demo
GOOGLE_API_KEY=YOUR_PRIVATE_GEMINI_KEY
GEMINI_MODEL=gemini-2.5-flash-lite
RAG_SIMILARITY_THRESHOLD=0.35
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_PUBLISHABLE_KEY=YOUR_PUBLISHABLE_KEY
```

The embedding model is fixed to **gemini-embedding-001**, output size **768**, matching `extensions.vector(768)`. Never mix model versions; re-embed and migrate when switching.

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app.main:app --reload
```

## 3. Frontend environment
Configure `frontend/.env.local` with:

```dotenv
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=YOUR_PUBLISHABLE_KEY
```

```powershell
cd frontend
npm install
npm run lint
npm run build
npm run dev
```

Visit `http://localhost:3000/login`, sign in, then open `/workspace` > Knowledge Base, or `/knowledge`.

## 4. Real integration checklist
1. Upload `docs/samples/returns-policy.md` and `docs/samples/shipping-policy.md`.
2. Verify both documents show **ready** and at least one indexed chunk.
3. Ask “What is the return window?” → answer cites the return policy and says 30 days.
4. Ask “How are tracking numbers delivered?” → answer cites the shipping policy.
5. Ask an unrelated question (“Who won the World Cup?”) → should abstain, not invent policy.
6. Delete a policy; verify its chunks no longer appear in retrieval.
7. Sign in as a **second Supabase user** and verify the first user's documents are inaccessible through the API *and* direct PostgREST. This requires two real accounts and is not covered by offline mock tests.
8. Optionally run `RAG_TEST_JWT=YOUR_TEMPORARY_TOKEN python -m scripts.evaluate_policy_rag` from backend; never commit or log the JWT.

## Authorized endpoints
All routes require `Authorization: Bearer <Supabase access token>`.

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/v1/workspace/knowledge/documents` | List user documents |
| POST | `/api/v1/workspace/knowledge/documents` | Multipart upload: `file`, `title` |
| DELETE | `/api/v1/workspace/knowledge/documents/{uuid}` | Delete a document and chunks |
| POST | `/api/v1/workspace/knowledge/ask` | JSON `{"question":"...","top_k":5}` |

## Limits, privacy and caveats
- PDF must contain selectable text; no OCR. TXT and Markdown must be UTF-8.
- Max 2MB raw file, 40 PDF pages, 180k extracted characters, 200 chunks, 8 retrieved passages.
- Only extracted chunks and vectors are persisted; original file bytes are **not stored**.
- Gemini APIs receive document text; do not upload confidential data without a privacy review.
- Retrieval supports abstention and citations but cannot guarantee correctness; manually review consequential policy statements. The model never executes policy text as an instruction.
- SQL uses per-user RLS and composite foreign keys; JWT is forwarded, not a service-role key. The app still needs rate limiting, async background jobs, operational timeouts and malware scanning before production use.
- LangGraph agents are planned for Phase 4; refund approvals and ticket actions for Phase 5.
