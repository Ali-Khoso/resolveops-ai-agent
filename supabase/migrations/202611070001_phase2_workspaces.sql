-- ResolveOps Phase 2 — secure, user-owned demo workspaces.
-- Run once in Supabase SQL Editor, or deploy with Supabase CLI migrations.
-- Each authenticated agent currently owns an isolated workspace (one user = one workspace).
-- Roles are reserved for later team/multi-tenant RBAC; nobody can self-promote to admin.

create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null default '' check (char_length(display_name) <= 120),
  role text not null default 'agent' check (role in ('agent', 'admin')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.customers (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  full_name text not null check (char_length(full_name) between 2 and 120),
  email text not null check (char_length(email) <= 254),
  phone text check (char_length(phone) <= 32),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint customers_id_owner_unique unique(id, owner_id)
);

create table if not exists public.orders (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  customer_id uuid not null,
  item text not null check (char_length(item) between 2 and 200),
  status text not null default 'processing' check(status in ('processing','shipped','delivered','cancelled')),
  tracking_number text check (char_length(tracking_number) <= 80),
  estimated_delivery date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint orders_customer_owned foreign key (customer_id, owner_id)
    references public.customers(id, owner_id) on delete restrict,
  constraint orders_id_owner_unique unique(id, owner_id),
  constraint orders_id_owner_customer_unique unique(id, owner_id, customer_id)
);

create table if not exists public.tickets (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  customer_id uuid not null,
  order_id uuid,
  subject text not null check(char_length(subject) between 3 and 200),
  description text not null check(char_length(description) between 3 and 4000),
  status text not null default 'open' check(status in ('open','in_progress','resolved','closed')),
  priority text not null default 'normal' check(priority in ('low','normal','high','urgent')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint tickets_customer_owned foreign key(customer_id, owner_id)
    references public.customers(id, owner_id) on delete restrict,
  constraint tickets_order_and_customer_owned foreign key(order_id, owner_id, customer_id)
    references public.orders(id, owner_id, customer_id) on delete restrict,
  constraint tickets_id_owner_unique unique(id, owner_id)
);

create table if not exists public.ticket_messages (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  ticket_id uuid not null,
  author_id uuid not null references auth.users(id) on delete cascade,
  sender_type text not null default 'agent' check (sender_type = 'agent'),
  content text not null check(char_length(content) between 1 and 4000),
  created_at timestamptz not null default now(),
  constraint messages_ticket_owned foreign key(ticket_id, owner_id)
    references public.tickets(id, owner_id) on delete cascade
);

create index if not exists customers_owner_created_idx on public.customers(owner_id, created_at desc);
create index if not exists orders_owner_created_idx on public.orders(owner_id, created_at desc);
create index if not exists tickets_owner_status_idx on public.tickets(owner_id, status);
create index if not exists tickets_owner_created_idx on public.tickets(owner_id, created_at desc);
create index if not exists messages_owner_ticket_created_idx on public.ticket_messages(owner_id, ticket_id, created_at);

create or replace function public.update_timestamp() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create trigger profiles_timestamp before update on public.profiles
  for each row execute function public.update_timestamp();
create trigger customers_timestamp before update on public.customers
  for each row execute function public.update_timestamp();
create trigger orders_timestamp before update on public.orders
  for each row execute function public.update_timestamp();
create trigger tickets_timestamp before update on public.tickets
  for each row execute function public.update_timestamp();

-- Runs as the migration owner on signup (no user-controlled privilege fields).
create or replace function public.create_user_profile() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles(id, display_name)
  values (new.id, left(coalesce(nullif(trim(new.raw_user_meta_data->>'full_name'), ''), split_part(coalesce(new.email,''), '@', 1), 'Support Agent'), 120))
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.create_user_profile();

-- If people registered before this migration, give them a profile too.
insert into public.profiles(id, display_name)
select id, left(coalesce(nullif(trim(raw_user_meta_data->>'full_name'), ''), split_part(coalesce(email,''), '@', 1), 'Support Agent'), 120)
from auth.users on conflict (id) do nothing;

alter table public.profiles enable row level security;
alter table public.customers enable row level security;
alter table public.orders enable row level security;
alter table public.tickets enable row level security;
alter table public.ticket_messages enable row level security;

-- Explicit database privileges; anon receives no rights to the user tables.
revoke all on public.profiles, public.customers, public.orders, public.tickets, public.ticket_messages from anon, authenticated;
grant select on public.profiles to authenticated;
grant update(display_name) on public.profiles to authenticated;
grant select, insert, update, delete on public.customers, public.orders, public.tickets to authenticated;
grant select, insert on public.ticket_messages to authenticated;

create policy "Read own profile" on public.profiles for select to authenticated
using ((select auth.uid()) = id);
create policy "Edit own profile name" on public.profiles for update to authenticated
using ((select auth.uid()) = id) with check ((select auth.uid()) = id);

create policy "Read own customers" on public.customers for select to authenticated
using ((select auth.uid()) = owner_id);
create policy "Create own customers" on public.customers for insert to authenticated
with check ((select auth.uid()) = owner_id);
create policy "Edit own customers" on public.customers for update to authenticated
using ((select auth.uid()) = owner_id) with check ((select auth.uid()) = owner_id);
create policy "Delete own customers" on public.customers for delete to authenticated
using ((select auth.uid()) = owner_id);

create policy "Read own orders" on public.orders for select to authenticated
using ((select auth.uid()) = owner_id);
create policy "Create own orders" on public.orders for insert to authenticated
with check ((select auth.uid()) = owner_id);
create policy "Edit own orders" on public.orders for update to authenticated
using ((select auth.uid()) = owner_id) with check ((select auth.uid()) = owner_id);
create policy "Delete own orders" on public.orders for delete to authenticated
using ((select auth.uid()) = owner_id);

create policy "Read own tickets" on public.tickets for select to authenticated
using ((select auth.uid()) = owner_id);
create policy "Create own tickets" on public.tickets for insert to authenticated
with check ((select auth.uid()) = owner_id);
create policy "Edit own tickets" on public.tickets for update to authenticated
using ((select auth.uid()) = owner_id) with check ((select auth.uid()) = owner_id);
create policy "Delete own tickets" on public.tickets for delete to authenticated
using ((select auth.uid()) = owner_id);

create policy "Read own messages" on public.ticket_messages for select to authenticated
using ((select auth.uid()) = owner_id);
create policy "Write agent messages only" on public.ticket_messages for insert to authenticated
with check ((select auth.uid()) = owner_id
  and (select auth.uid()) = author_id and sender_type = 'agent');

-- Security audit: do not add permissive anon policies or expose service_role keys.
