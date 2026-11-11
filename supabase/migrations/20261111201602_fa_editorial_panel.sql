create schema fa_panel_private;
revoke all on schema fa_panel_private from public, anon, authenticated;
grant usage on schema fa_panel_private to authenticated;

create table public.fa_panel_members (
  user_id uuid primary key references auth.users (id) on delete cascade,
  email text not null unique check (email = lower(btrim(email)) and char_length(email) between 3 and 254),
  role text not null check (role in ('author', 'editor', 'admin'))
);

create table public.fa_panel_stories (
  id uuid primary key default gen_random_uuid(),
  author_id uuid default auth.uid() references auth.users (id) on delete set null,
  title text not null default '' check (char_length(title) <= 160),
  topic text not null default '' check (char_length(topic) <= 120),
  summary text not null default '' check (char_length(summary) <= 600),
  body text not null default '' check (char_length(body) <= 30000),
  source text not null default '' check (char_length(source) <= 160),
  url text not null default '' check (char_length(url) <= 1500),
  image text not null default '' check (char_length(image) <= 1500),
  alt text not null default '' check (char_length(alt) <= 200),
  status text not null default 'draft' check (status in ('draft', 'review', 'approved')),
  reviewed_by uuid references auth.users (id) on delete set null,
  reviewed_at timestamptz,
  updated_at timestamptz not null default now(),
  revision integer not null default 1,
  constraint fa_panel_review_content check (
    status = 'draft' or (
      title ~ '[^[:space:]]' and summary ~ '[^[:space:]]'
      and body ~ '[^[:space:]]' and source ~ '[^[:space:]]'
      and url ~ '^https://[^/?#@[:space:]]+([/?#][^[:space:]]*)?$'
      and strpos(url, chr(92)) = 0
      and (image = '' or (
        image ~ '^https://[^/?#@[:space:]]+([/?#][^[:space:]]*)?$'
        and strpos(image, chr(92)) = 0 and alt ~ '[^[:space:]]'
      ))
    )
  ),
  constraint fa_panel_review_audit check (
    (status = 'approved' and reviewed_at is not null)
    or (status <> 'approved' and reviewed_at is null and reviewed_by is null)
  )
);

create index fa_panel_stories_author_order on public.fa_panel_stories (author_id, updated_at desc, id);
create index fa_panel_stories_order on public.fa_panel_stories (updated_at desc, id);
create index fa_panel_stories_reviewer on public.fa_panel_stories (reviewed_by) where reviewed_by is not null;

create table public.fa_panel_layout (
  id smallint primary key check (id = 1),
  sections text[] not null check (
    cardinality(sections) = 4
    and sections @> array['Karşılama', 'Son Haberler', 'FA’yı keşfet', 'Topluluk']::text[]
  ),
  updated_at timestamptz not null default now(),
  revision integer not null default 1
);

insert into public.fa_panel_layout (id, sections)
values (1, array['Karşılama', 'Son Haberler', 'FA’yı keşfet', 'Topluluk']);

alter table public.fa_panel_members enable row level security;
alter table public.fa_panel_stories enable row level security;
alter table public.fa_panel_layout enable row level security;

revoke all on public.fa_panel_members, public.fa_panel_stories, public.fa_panel_layout from public, anon, authenticated;
grant select, delete on public.fa_panel_members to authenticated;
grant select on public.fa_panel_stories, public.fa_panel_layout to authenticated;
grant insert (id, title, topic, summary, body, source, url, image, alt, status)
  on public.fa_panel_stories to authenticated;
grant update (title, topic, summary, body, source, url, image, alt, status)
  on public.fa_panel_stories to authenticated;
grant update (sections) on public.fa_panel_layout to authenticated;

create function fa_panel_private.member_role()
returns text
language sql stable security definer
set search_path = ''
as $$
  select membership.role
  from public.fa_panel_members as membership
  join auth.users as auth_user on auth_user.id = membership.user_id
  where membership.user_id = (select auth.uid())
    and lower(auth_user.email) = membership.email
    and auth_user.email_confirmed_at is not null
    and not coalesce(auth_user.is_anonymous, false);
$$;
revoke all on function fa_panel_private.member_role() from public, anon, authenticated, service_role;
grant execute on function fa_panel_private.member_role() to authenticated;

create policy fa_panel_read_members on public.fa_panel_members for select to authenticated
using (
  (select fa_panel_private.member_role()) = 'admin'
  or (user_id = (select auth.uid()) and (select fa_panel_private.member_role()) is not null)
);

create policy fa_panel_revoke_member on public.fa_panel_members for delete to authenticated
using ((select fa_panel_private.member_role()) = 'admin' and role in ('author', 'editor'));

create policy fa_panel_read_stories on public.fa_panel_stories for select to authenticated
using (
  (select fa_panel_private.member_role()) in ('editor', 'admin')
  or ((select fa_panel_private.member_role()) = 'author' and author_id = (select auth.uid()))
);

create policy fa_panel_create_story on public.fa_panel_stories for insert to authenticated
with check (
  (select fa_panel_private.member_role()) is not null
  and author_id = (select auth.uid())
  and status in ('draft', 'review')
);

create policy fa_panel_update_story on public.fa_panel_stories for update to authenticated
using (
  ((select fa_panel_private.member_role()) is not null and author_id = (select auth.uid()) and status = 'draft')
  or ((select fa_panel_private.member_role()) in ('editor', 'admin') and status = 'review')
)
with check (
  ((select fa_panel_private.member_role()) is not null and author_id = (select auth.uid()) and status in ('draft', 'review'))
  or ((select fa_panel_private.member_role()) in ('editor', 'admin') and status in ('draft', 'approved'))
);

create policy fa_panel_read_layout on public.fa_panel_layout for select to authenticated
using ((select fa_panel_private.member_role()) in ('editor', 'admin'));

create policy fa_panel_update_layout on public.fa_panel_layout for update to authenticated
using ((select fa_panel_private.member_role()) in ('editor', 'admin'))
with check ((select fa_panel_private.member_role()) in ('editor', 'admin'));

create function fa_panel_private.record_source_review()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if old.status = 'review' then
    if (new.title, new.topic, new.summary, new.body, new.source, new.url, new.image, new.alt)
      is distinct from (old.title, old.topic, old.summary, old.body, old.source, old.url, old.image, old.alt) then
      raise insufficient_privilege using message = 'Return the story for editing before changing its content.';
    end if;

    if new.status = 'approved' then
      new.reviewed_by = auth.uid();
      new.reviewed_at = now();
    end if;
  end if;
  return new;
end;
$$;

create function fa_panel_private.advance_revision()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  new.revision = old.revision + 1;
  return new;
end;
$$;

revoke all on function fa_panel_private.record_source_review() from public, anon, authenticated, service_role;
revoke all on function fa_panel_private.advance_revision() from public, anon, authenticated, service_role;

create trigger fa_panel_story_review before update on public.fa_panel_stories
for each row execute function fa_panel_private.record_source_review();

create trigger fa_panel_story_revision before update on public.fa_panel_stories
for each row execute function fa_panel_private.advance_revision();

create trigger fa_panel_layout_revision before update on public.fa_panel_layout
for each row execute function fa_panel_private.advance_revision();

create function fa_panel_private.set_member_role(target_email text, assigned_role text)
returns uuid
language plpgsql security definer
set search_path = ''
as $$
declare
  normalized_email text := lower(btrim(target_email));
  target_user uuid;
  saved_user uuid;
begin
  if auth.uid() is null or fa_panel_private.member_role() is distinct from 'admin' then
    raise insufficient_privilege using message = 'Panel administration is required.';
  end if;

  if assigned_role is null or assigned_role not in ('author', 'editor')
    or normalized_email is null or char_length(normalized_email) > 254
    or normalized_email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' then
    raise invalid_parameter_value using message = 'An email address and author or editor role are required.';
  end if;

  begin
    select id into strict target_user
    from auth.users
    where lower(email) = normalized_email
      and (email_confirmed_at is not null or invited_at is not null)
      and not coalesce(is_anonymous, false);
  exception
    when no_data_found then return null;
  end;

  insert into public.fa_panel_members as member (user_id, email, role)
  values (target_user, normalized_email, assigned_role)
  on conflict (user_id) do update set email = excluded.email, role = excluded.role
  where member.role in ('author', 'editor')
  returning user_id into saved_user;

  if saved_user is null then
    raise insufficient_privilege using message = 'Administrator roles are managed by the project owner.';
  end if;
  return saved_user;
end;
$$;

create function public.fa_panel_set_member_role(target_email text, assigned_role text)
returns uuid
language sql security invoker
set search_path = ''
as $$
  select fa_panel_private.set_member_role(target_email, assigned_role);
$$;

revoke all on function fa_panel_private.set_member_role(text, text) from public, anon, authenticated, service_role;
revoke all on function public.fa_panel_set_member_role(text, text) from public, anon, authenticated, service_role;
grant execute on function fa_panel_private.set_member_role(text, text) to authenticated;
grant execute on function public.fa_panel_set_member_role(text, text) to authenticated;
