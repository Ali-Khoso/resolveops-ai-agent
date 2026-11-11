-- Phase 5 guardrails. Apply after 202611110001_phase4_agent_trace.sql.
-- These checks apply to direct PostgREST inserts as well as FastAPI.
-- This is an internal human-review demo, NOT multi-person authorization.
create or replace function public.guard_phase5_approval_insert()
returns trigger language plpgsql security definer set search_path = ''
as $guard$
declare
  ticket_status text;
  linked_run public.agent_runs%rowtype;
begin
  if auth.uid() is null or new.owner_id is distinct from auth.uid() then
    raise sqlstate 'PT403' using message = 'Approval owner is not authenticated';
  end if;
  select t.status into ticket_status
    from public.tickets t where t.id = new.ticket_id and t.owner_id = new.owner_id;
  if not found then
    raise sqlstate 'PT404' using message = 'Ticket not found';
  end if;
  if ticket_status = 'closed' then
    raise sqlstate 'PT409' using message = 'Closed ticket cannot receive approval';
  end if;
  if new.action_type = 'resolve_ticket' and ticket_status = 'resolved' then
    raise sqlstate 'PT409' using message = 'Ticket already resolved';
  end if;
  if new.status <> 'pending' or new.decided_at is not null or new.decided_by is not null then
    raise sqlstate 'PT422' using message = 'Only pending approvals may be created';
  end if;
  if new.run_id is not null then
    select r.* into linked_run from public.agent_runs r
      where r.id = new.run_id and r.ticket_id = new.ticket_id and r.owner_id = new.owner_id;
    if not found then
      raise sqlstate 'PT404' using message = 'Linked investigation not found';
    end if;
    if linked_run.requires_approval is not true then
      raise sqlstate 'PT422' using message = 'Investigation is not reviewable';
    end if;
    if linked_run.status <> 'pending_approval' then
      raise sqlstate 'PT409' using message = 'Investigation not awaiting approval';
    end if;
    if linked_run.intent = 'refund' and new.action_type <> 'refund_review' then
      raise sqlstate 'PT422' using message = 'Refund investigation requires refund review';
    end if;
    if linked_run.intent = 'escalation' and new.action_type = 'resolve_ticket' then
      raise sqlstate 'PT422' using message = 'Escalated ticket requires response review';
    end if;
  end if;
  if new.action_type = 'refund_review'
    and (new.run_id is null or linked_run.intent is distinct from 'refund') then
    raise sqlstate 'PT422' using message = 'Refund review needs a refund investigation';
  end if;
  return new;
end
$guard$;

revoke all on function public.guard_phase5_approval_insert() from public, anon, authenticated;
drop trigger if exists guard_phase5_approval_insert on public.approval_requests;
create trigger guard_phase5_approval_insert before insert on public.approval_requests
for each row execute function public.guard_phase5_approval_insert();

-- Owner-checked atomic decisions; same-decision retry returns existing row without
-- another audit entry. Conflicting retries return HTTP 409.
create or replace function public.decide_approval(p_approval_id uuid,p_decision text,p_note text default null)
returns setof public.approval_requests
language plpgsql security definer set search_path = ''
as $decide$
declare a public.approval_requests%rowtype;
begin
  if auth.uid() is null then
    raise sqlstate 'PT401' using message = 'Authentication required';
  end if;
  if p_decision not in ('approved', 'rejected') then
    raise sqlstate 'PT422' using message = 'Invalid decision';
  end if;
  if p_note is not null and char_length(p_note) > 1000 then
    raise sqlstate 'PT422' using message = 'Decision note too long';
  end if;
  select * into a from public.approval_requests
    where id=p_approval_id and owner_id=auth.uid() for update;
  if not found then return; end if;
  if a.status <> 'pending' then
    if a.status = p_decision then
      return next a;
      return;
    end if;
    raise sqlstate 'PT409' using message = 'Approval already finalized';
  end if;
  if p_decision = 'rejected' and nullif(btrim(p_note), '') is null then
    raise sqlstate 'PT422' using message = 'Rejection reason required';
  end if;
  if a.action_type = 'refund_review' and p_decision = 'approved'
    and nullif(btrim(p_note), '') is null then
    raise sqlstate 'PT422' using message = 'Refund review requires written rationale';
  end if;

  update public.approval_requests
    set status=p_decision, decided_by=auth.uid(), decided_at=now(),
        decision_note=nullif(btrim(p_note), '')
    where id=a.id returning * into a;

  insert into public.operation_audit_events(owner_id,approval_id,action_type,decision,actor_id)
    values(a.owner_id,a.id,a.action_type,p_decision,auth.uid());

  if p_decision='approved' and a.action_type='send_reply' then
    -- Internal record only; NO outbound email.
    insert into public.ticket_messages(owner_id,ticket_id,author_id,sender_type,content,approval_id)
      values(a.owner_id,a.ticket_id,auth.uid(),'agent',a.draft_reply,a.id)
      on conflict(approval_id) do nothing;
  elsif p_decision='approved' and a.action_type='resolve_ticket' then
    update public.tickets set status='resolved'
      where id=a.ticket_id and owner_id=a.owner_id and status <> 'closed';
  end if;
  return next a;
end
$decide$;

revoke all on function public.decide_approval(uuid,text,text) from public,anon;
grant execute on function public.decide_approval(uuid,text,text) to authenticated;
