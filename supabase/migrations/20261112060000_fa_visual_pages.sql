-- The published projection contains only explicitly published page content.
create table public.fa_panel_page_drafts (
  page_path text primary key check (page_path ~ '^[a-z0-9][a-z0-9-]*\.html$'),
  settings jsonb not null check (
    jsonb_typeof(settings) = 'object'
    and settings @> '{"version":1}'
    and coalesce(jsonb_typeof(settings -> 'fields') = 'object', false)
    and coalesce(jsonb_typeof(settings -> 'order') = 'object', false)
    and octet_length(settings::text) <= 262144
  ),
  revision integer not null default 1,
  updated_at timestamptz not null default now()
);

create table public.fa_panel_published_pages (
  page_path text primary key references public.fa_panel_page_drafts (page_path),
  settings jsonb not null,
  revision integer not null,
  published_at timestamptz not null default now()
);

alter table public.fa_panel_page_drafts enable row level security;
alter table public.fa_panel_published_pages enable row level security;

revoke all on public.fa_panel_page_drafts, public.fa_panel_published_pages from public, anon, authenticated;
grant select, insert (page_path, settings), update (settings) on public.fa_panel_page_drafts to authenticated;
grant select on public.fa_panel_published_pages to anon, authenticated;

create policy fa_page_draft_read on public.fa_panel_page_drafts for select to authenticated
using ((select fa_panel_private.member_role()) in ('editor', 'admin'));

create policy fa_page_draft_create on public.fa_panel_page_drafts for insert to authenticated
with check ((select fa_panel_private.member_role()) in ('editor', 'admin'));

create policy fa_page_draft_update on public.fa_panel_page_drafts for update to authenticated
using ((select fa_panel_private.member_role()) in ('editor', 'admin'))
with check ((select fa_panel_private.member_role()) in ('editor', 'admin'));

create policy fa_published_page_read on public.fa_panel_published_pages for select to anon, authenticated
using (true);

create trigger fa_page_draft_revision before update on public.fa_panel_page_drafts
for each row execute function fa_panel_private.advance_revision();

create function fa_panel_private.publish_page(target_path text, expected_revision integer)
returns integer
language plpgsql security definer
set search_path = ''
as $$
declare
  draft public.fa_panel_page_drafts%rowtype;
begin
  if coalesce(fa_panel_private.member_role(), '') not in ('editor', 'admin') then
    raise insufficient_privilege using message = 'Page editing is required.';
  end if;

  select * into draft from public.fa_panel_page_drafts
  where page_path = target_path
  for update;

  if not found or draft.revision is distinct from expected_revision then
    raise sqlstate '40001' using message = 'The page draft has changed.';
  end if;

  insert into public.fa_panel_published_pages as published (page_path, settings, revision)
  values (draft.page_path, draft.settings, draft.revision)
  on conflict (page_path) do update
  set settings = excluded.settings, revision = excluded.revision, published_at = now()
  where published.revision < excluded.revision;

  return draft.revision;
end;
$$;

create function public.fa_panel_publish_page(target_path text, expected_revision integer)
returns integer
language sql security invoker
set search_path = ''
as $$
  select fa_panel_private.publish_page(target_path, expected_revision);
$$;

revoke all on function fa_panel_private.publish_page(text, integer) from public, anon, authenticated, service_role;
revoke all on function public.fa_panel_publish_page(text, integer) from public, anon, authenticated, service_role;
grant execute on function fa_panel_private.publish_page(text, integer) to authenticated;
grant execute on function public.fa_panel_publish_page(text, integer) to authenticated;
