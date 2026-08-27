create extension if not exists pgcrypto;

create table if not exists public.briefs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  reference text not null unique,
  payload jsonb not null,
  file_paths text[] not null default '{}',
  status text not null default 'received' check (status in ('received','reviewing','contacted','archived')),
  created_at timestamptz not null default now()
);

create table if not exists public.text_revisions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  project_identifier text not null,
  reference text not null unique,
  payload jsonb not null,
  status text not null default 'received' check (status in ('received','reviewing','applied','archived')),
  created_at timestamptz not null default now()
);

create index if not exists briefs_user_id_idx on public.briefs(user_id);
create index if not exists text_revisions_user_id_idx on public.text_revisions(user_id);

alter table public.briefs enable row level security;
alter table public.text_revisions enable row level security;
revoke all on public.briefs, public.text_revisions from anon;
revoke all on public.briefs, public.text_revisions from authenticated;
grant select, insert, update on public.briefs, public.text_revisions to authenticated;

create policy "briefs_select_own" on public.briefs for select to authenticated using ((select auth.uid()) = user_id);
create policy "briefs_insert_own" on public.briefs for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "briefs_update_own" on public.briefs for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "text_revisions_select_own" on public.text_revisions for select to authenticated using ((select auth.uid()) = user_id);
create policy "text_revisions_insert_own" on public.text_revisions for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "text_revisions_update_own" on public.text_revisions for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

insert into storage.buckets (id, name, public, file_size_limit)
values ('brief-files', 'brief-files', false, 10485760)
on conflict (id) do update set public = excluded.public, file_size_limit = excluded.file_size_limit;

create policy "brief_files_insert_own" on storage.objects for insert to authenticated
with check (bucket_id = 'brief-files' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "brief_files_select_own" on storage.objects for select to authenticated
using (bucket_id = 'brief-files' and (storage.foldername(name))[1] = (select auth.uid())::text);

