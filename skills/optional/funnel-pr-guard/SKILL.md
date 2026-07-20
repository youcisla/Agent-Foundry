---
name: funnel-pr-guard
description: "Every PR that touches the front door must state which funnel step it changes and by how much. PR review discipline for landing, auth, onboarding, and signup flows. Use whenever a diff touches conversion-critical paths."
version: 0.1.0
license: MIT
provenance:
  author: Youcisla
  source: operational methodology
  inspired: true
---

# Funnel PR Guard

Every PR that touches the front door must state which funnel step it changes and by how much.

## When to Use

- Diff touching landing, auth, onboarding, invite, or loading screens
- Adding funnel/tracking events
- Any PR that could affect signup → activation conversion

## Procedure

### 1 — Identify the funnel step affected

Generic funnel steps for any web app:

```
visitor → signup_started → signed_up → activated → core_engagement → retention
```

State in the PR body which step(s) the change affects.

### 2 — Ensure tracking table exists

```sql
create table public.funnel_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  event text not null,
  meta jsonb,
  created_at timestamptz not null default now()
);
alter table public.funnel_events enable row level security;
create policy "insert own" on public.funnel_events for insert to authenticated
  with check (auth.uid() = user_id);
```

### 3 — Fire-and-forget, no sensitive content

```typescript
supabase.from('funnel_events').insert({
  user_id: session.user.id,
  event: 'event_name',
  meta: { version: 'v2' }
}).then().catch(() => {})
```

Rule: `meta` must never contain user content, PII, or proprietary data. IDs and event names only.

### 4 — Weekly funnel query

```sql
select event, count(*) as total, count(distinct user_id) as unique_users,
  min(created_at) as first_seen, max(created_at) as last_seen
from public.funnel_events
where created_at > now() - interval '7 days'
group by 1 order by 2 desc;
```

### 5 — Gate check before merging

Before merging, confirm:
- Funnel step stated in PR body with expected direction
- funnel_events table exists (or migration created it)
- No user content in event meta
- Rollback: feature flag (env var or toggle)
- Data shows the expected change after N users flow through

## Anti-patterns

- Merging a funnel change without stating the metric you expect to move
- Including free-text content in event metadata
- Changing the UI without adding tracking and rollback plan
