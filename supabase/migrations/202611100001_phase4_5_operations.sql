-- ResolveOps Phases 4/5: account-private agent runs, approvals and audit events.
-- Apply after the existing Phase 2 and Phase 3 migrations.
create table if not exists public.agent_runs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  ticket_id uuid not null,
  intent text not null check(intent in ('order','policy','refund','escalation','general')),
  question text not null check(char_length(question) between 3 and 1500),
  response text not null check(char_length(response) between 1 and 10000),
  order_snapshot jsonb not null default '{}'::jsonb,
  sources jsonb not null default '[]'::jsonb,
  requires_approval boolean not null default false,
  status text not null default 'completed' check(status in ('completed','pending_approval','failed')),
  duration_ms integer not null default 0 check(duration_ms between 0 and 3600000),
  created_at timestamptz not null default now(),
  constraint runs_owned_ticket foreign key(ticket_id,owner_id)
    references public.tickets(id,owner_id) on delete cascade,
  constraint runs_id_ticket_owner_key unique(id,ticket_id,owner_id)
);

create table if not exists public.approval_requests (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  ticket_id uuid not null,
  run_id uuid,
  action_type text not null check(action_type in ('send_reply','resolve_ticket','refund_review')),
  draft_reply text not null check(char_length(draft_reply) between 1 and 4000),
  reason text not null check(char_length(reason) between 3 and 1000),
  status text not null default 'pending' check(status in ('pending','approved','rejected')),
  decision_note text check(char_length(decision_note) <= 1000),
  decided_by uuid references auth.users(id),
  decided_at timestamptz,
  created_at timestamptz not null default now(),
  constraint approval_owned_ticket foreign key(ticket_id,owner_id)
    references public.tickets(id,owner_id) on delete cascade,
  constraint approval_owned_run foreign key(run_id,ticket_id,owner_id)
    references public.agent_runs(id,ticket_id,owner_id) on delete cascade,
  constraint approval_id_owner_unique unique(id,owner_id),
  constraint one_approval_per_run unique(run_id)
);

alter table public.ticket_messages add column if not exists approval_id
  uuid unique references public.approval_requests(id) on delete set null;

create table if not exists public.operation_audit_events (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  approval_id uuid not null,
  action_type text not null,
  decision text not null check(decision in ('approved','rejected')),
  actor_id uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  foreign key(approval_id,owner_id) references public.approval_requests(id,owner_id) on delete cascade
);

create index if not exists runs_owner_created_idx on public.agent_runs(owner_id,created_at desc);
create index if not exists approvals_owner_status_idx on public.approval_requests(owner_id,status,created_at desc);
create index if not exists audit_owner_created_idx on public.operation_audit_events(owner_id,created_at desc);

alter table public.agent_runs enable row level security;
alter table public.approval_requests enable row level security;
alter table public.operation_audit_events enable row level security;

revoke all on public.agent_runs,public.approval_requests,public.operation_audit_events from anon,authenticated;
grant select,insert on public.agent_runs to authenticated;
grant select,insert on public.approval_requests to authenticated;
grant select on public.operation_audit_events to authenticated;

create policy "runs_read_own" on public.agent_runs for select to authenticated using ((select auth.uid())=owner_id);
create policy "runs_insert_own" on public.agent_runs for insert to authenticated with check((select auth.uid())=owner_id);
create policy "approvals_read_own" on public.approval_requests for select to authenticated using ((select auth.uid())=owner_id);
create policy "approvals_insert_own" on public.approval_requests for insert to authenticated
  with check((select auth.uid())=owner_id and status='pending'
             and decided_at is null and decided_by is null);
create policy "audit_read_own" on public.operation_audit_events for select to authenticated
  using ((select auth.uid())=owner_id);

-- Atomic, owner-checked action approval; executes NO real payments or customer emails.
create or replace function public.decide_approval(p_approval_id uuid,p_decision text,p_note text default null)
returns setof public.approval_requests
language plpgsql security definer set search_path=''
as $$
declare a public.approval_requests%rowtype;
begin
  if auth.uid() is null then raise exception 'Authentication required'; end if;
  if p_decision not in ('approved','rejected') then raise exception 'Invalid decision'; end if;
  if p_note is not null and char_length(p_note)>1000 then raise exception 'Note too long'; end if;

  select * into a from public.approval_requests
  where id=p_approval_id and owner_id=auth.uid() for update;
  if not found then return; end if;
  if a.status<>'pending' then return next a; return; end if;

  update public.approval_requests
  set status=p_decision,decided_by=auth.uid(),decided_at=now(),decision_note=p_note
  where id=a.id returning * into a;

  insert into public.operation_audit_events(owner_id,approval_id,action_type,decision,actor_id)
  values(a.owner_id,a.id,a.action_type,p_decision,auth.uid());

  if p_decision='approved' and a.action_type='send_reply' then
    -- Store internally only. No outbound email or chatbot message is sent.
    insert into public.ticket_messages(owner_id,ticket_id,author_id,sender_type,content,approval_id)
    values(a.owner_id,a.ticket_id,auth.uid(),'agent',a.draft_reply,a.id)
    on conflict(approval_id) do nothing;
  elsif p_decision='approved' and a.action_type='resolve_ticket' then
    update public.tickets set status='resolved'
    where id=a.ticket_id and owner_id=a.owner_id;
  end if;
  return next a;
end $$;

revoke all on function public.decide_approval(uuid,text,text) from public,anon;
grant execute on function public.decide_approval(uuid,text,text) to authenticated;
