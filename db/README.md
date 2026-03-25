## DB Bootstrap

Postgres bootstrap SQL for Phase 3 persistence lives in:

- `db/bootstrap/001_phase3_persistence.sql`

Apply it to either:

- local Docker/Supabase Postgres
- Supabase Cloud Postgres

Recommended workflow:

1. Apply in local first.
2. Validate API run creation, approval, and approval-history reads.
3. Apply the same SQL to Supabase Cloud to keep schema parity.
