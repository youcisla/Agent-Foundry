---
name: sql-migration-trio
description: "Every SQL migration = three files: up (forward DDL), down (reverse DDL), and schema.sql sync. Apply, drift-check, and rollback procedure. Use for any database migration in a Supabase or Postgres project."
version: 0.1.0
license: MIT
provenance:
  author: Youcisla
  source: operational methodology
  inspired: true
---

# SQL Migration Trio

Every migration = three files (up .sql, down .sql, schema.sql sync). Runs both directions.

## When to Use

- Creating or reviewing any SQL migration
- Running advisors after DDL changes
- Investigating migration drift between repo and production

## Procedure

### 1 — Scaffold the trio

```bash
TIMESTAMP=$(date +%Y%m%d%H%M%S)
NAME="descriptive_name"
touch "supabase/migrations/${TIMESTAMP}_${NAME}.sql"
touch "supabase/migrations/${TIMESTAMP}_${NAME}.down.sql"
```

- Up: `begin; -- your DDL here; commit;`
- Down: `begin; -- your REVERSE DDL here; commit;`

### 2 — Sync schema.sql

Update the project's `schema.sql` (or equivalent) to match the migration. CI should check this.

### 3 — Drift check

```sql
-- Applied in prod but NOT in repo
select version, name from supabase_migrations.schema_migrations
where version not in (
  select regexp_replace(f.name, '.down.sql$', ''),
         regexp_replace(f.name, '.sql$', '')
  from pg_catalog.pg_ls_dir('supabase/migrations') f(name)
);

-- Repo files not in applied list
select version, name from supabase_migrations.schema_migrations
  outer join ...
```

Also check reverse: repo files that are not in the applied list.

### 4 — Apply + run advisors

Run database advisors (security + performance) after every DDL change.

### 5 — Rollback plan

Document before deploying: run the .down.sql, PITR snapshot taken before applying.

## Verification Checklist

- [ ] Three files: up + down + schema.sql update
- [ ] CI lint passes locally
- [ ] Drift check run — no unexpected ghost migrations
- [ ] Advisors run post-DDL — zero new errors
- [ ] Down file actually reverses the up (test in preview)

## Anti-patterns

- Creating the up file without planning the down first
- Forgetting to sync schema.sql (CI linter should catch this)
- Applying without a drift check first
- Not testing the down file before deploying
