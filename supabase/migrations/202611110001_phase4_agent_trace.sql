-- Phase 4 extension: preserve bounded investigation routing steps and review flags.
-- Apply after 202611100001_phase4_5_operations.sql.
-- No secrets, payment actions, or new data access grants.

alter table public.agent_runs
  add column if not exists workflow_steps jsonb not null default '[]'::jsonb,
  add column if not exists review_flags jsonb not null default '[]'::jsonb;

do $migration$
begin
  if not exists (select 1 from pg_constraint
    where conname = 'agent_runs_workflow_steps_array'
      and conrelid = 'public.agent_runs'::regclass) then
    alter table public.agent_runs
      add constraint agent_runs_workflow_steps_array
      check (jsonb_typeof(workflow_steps) = 'array'
        and jsonb_array_length(workflow_steps) <= 24);
  end if;
  if not exists (select 1 from pg_constraint
    where conname = 'agent_runs_review_flags_array'
      and conrelid = 'public.agent_runs'::regclass) then
    alter table public.agent_runs
      add constraint agent_runs_review_flags_array
      check (jsonb_typeof(review_flags) = 'array'
        and jsonb_array_length(review_flags) <= 16);
  end if;
end;
$migration$;
