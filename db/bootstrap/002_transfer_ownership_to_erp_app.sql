BEGIN;

-- Intended for local or self-managed Postgres.
-- Supabase Cloud commonly blocks ownership changes even when grants succeed.

-- Optional but recommended if ownership transfer fails with "must be able to SET ROLE".
-- Run separately as a sufficiently privileged role:
-- GRANT erp_app TO postgres;

-- Transfer ownership only for ecommerceERP persistence objects.
ALTER TABLE IF EXISTS public.runs OWNER TO erp_app;
ALTER TABLE IF EXISTS public.approval_events OWNER TO erp_app;
ALTER SEQUENCE IF EXISTS public.approval_events_id_seq OWNER TO erp_app;

-- Keep runtime permissions explicit.
GRANT USAGE ON SCHEMA public TO erp_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.runs TO erp_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.approval_events TO erp_app;
GRANT USAGE, SELECT ON SEQUENCE public.approval_events_id_seq TO erp_app;

COMMIT;
