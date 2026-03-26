## DB Bootstrap

Postgres bootstrap SQL for Phase 3 persistence lives in:

- `db/bootstrap/001_phase3_persistence.sql`
- `db/bootstrap/002_transfer_ownership_to_erp_app.sql` (optional role-ownership migration)

Apply it to either:

- local Docker/Supabase Postgres
- Supabase Cloud Postgres

Recommended workflow:

1. Apply in local first.
2. Validate API run creation, approval, and approval-history reads.
3. Optionally apply ownership migration so app role (`erp_app`) owns only the ecommerceERP objects.
   Use this on local or self-managed Postgres. For Supabase Cloud, use grants instead of ownership transfer.
4. Apply the same SQL to Supabase Cloud to keep schema parity.
