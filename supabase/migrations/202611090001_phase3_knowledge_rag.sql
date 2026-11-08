-- ResolveOps Phase 3: private policy RAG. Apply after Phase 2.
create extension if not exists vector with schema extensions;

create table if not exists public.knowledge_documents (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  title text not null check(char_length(title) between 1 and 160),
  filename text not null check(char_length(filename) between 1 and 180),
  content_type text not null check(content_type in ('application/pdf', 'text/plain', 'text/markdown')),
  content_sha256 text not null check(content_sha256 ~ '^[a-f0-9]{64}$'),
  embedding_model text not null default 'gemini-embedding-001' check (embedding_model = 'gemini-embedding-001'),
  status text not null default 'processing' check (status in ('processing','ready','failed')),
  chunk_count integer not null default 0 check(chunk_count between 0 and 200),
  error_message text check(char_length(error_message) <= 300),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint documents_id_owner_unique unique(id, owner_id),
  constraint documents_owner_content_unique unique(owner_id, content_sha256)
);

create table if not exists public.knowledge_chunks (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  document_id uuid not null,
  chunk_index integer not null check(chunk_index between 0 and 199),
  page_number integer check(page_number between 1 and 40),
  content text not null check(char_length(content) between 1 and 3500),
  embedding extensions.vector(768) not null,
  created_at timestamptz not null default now(),
  constraint chunks_document_owner_fk foreign key(document_id, owner_id)
    references public.knowledge_documents(id, owner_id) on delete cascade,
  constraint chunks_document_index_unique unique(document_id, chunk_index)
);

create index if not exists kb_docs_owner_created_idx on public.knowledge_documents(owner_id, created_at desc);
create index if not exists kb_chunks_owner_doc_idx on public.knowledge_chunks(owner_id, document_id);
create index if not exists kb_chunks_embedding_idx on public.knowledge_chunks using hnsw (embedding vector_cosine_ops);
create trigger kb_docs_timestamp before update on public.knowledge_documents for each row execute function public.update_timestamp();

alter table public.knowledge_documents enable row level security;
alter table public.knowledge_chunks enable row level security;
revoke all on public.knowledge_documents, public.knowledge_chunks from anon, authenticated;
grant select, insert, update, delete on public.knowledge_documents to authenticated;
grant select, insert, delete on public.knowledge_chunks to authenticated;

create policy "Read own policy documents" on public.knowledge_documents for select to authenticated using ((select auth.uid()) = owner_id);
create policy "Create own policy documents" on public.knowledge_documents for insert to authenticated with check ((select auth.uid()) = owner_id);
create policy "Update own policy documents" on public.knowledge_documents for update to authenticated
 using ((select auth.uid()) = owner_id) with check ((select auth.uid()) = owner_id);
create policy "Delete own policy documents" on public.knowledge_documents for delete to authenticated using ((select auth.uid()) = owner_id);
create policy "Read own policy chunks" on public.knowledge_chunks for select to authenticated using ((select auth.uid()) = owner_id);
create policy "Insert own policy chunks" on public.knowledge_chunks for insert to authenticated with check ((select auth.uid()) = owner_id);
create policy "Delete own policy chunks" on public.knowledge_chunks for delete to authenticated using ((select auth.uid()) = owner_id);

-- SECURITY INVOKER means the RPC cannot bypass RLS.
create or replace function public.match_policy_chunks(
  query_embedding extensions.vector(768),
  match_threshold double precision default 0.35,
  match_count integer default 5
)
returns table (id uuid, document_id uuid, title text, filename text, page_number integer,
  chunk_index integer, content text, similarity double precision)
language sql stable security invoker
set search_path = public, extensions
as $$
 select c.id, c.document_id, d.title, d.filename, c.page_number, c.chunk_index, c.content,
 (1 - (c.embedding <=> query_embedding))::double precision as similarity
 from public.knowledge_chunks c join public.knowledge_documents d
 on d.id = c.document_id and d.owner_id = c.owner_id
 where c.owner_id = (select auth.uid()) and d.owner_id = (select auth.uid())
 and d.status = 'ready'
 and (1 - (c.embedding <=> query_embedding)) >= greatest(0.0, least(1.0, match_threshold))
 order by c.embedding <=> query_embedding asc
 limit least(greatest(match_count,1),8)
$$;
revoke all on function public.match_policy_chunks(extensions.vector(768), double precision, integer) from public, anon;
grant execute on function public.match_policy_chunks(extensions.vector(768), double precision, integer) to authenticated;
