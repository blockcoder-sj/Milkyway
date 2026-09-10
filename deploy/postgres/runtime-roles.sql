REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM milkyway_app, milkyway_paper, milkyway_backtest, milkyway_scheduler;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM milkyway_app, milkyway_paper, milkyway_backtest, milkyway_scheduler;

-- Table REVOKE does not remove older column grants. Clear those on upgrades.
DO $$
DECLARE target record; role_name text;
BEGIN
    FOR target IN
        SELECT c.relname, string_agg(quote_ident(a.attname), ', ' ORDER BY a.attnum) AS columns
        FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid
        WHERE n.nspname='public' AND c.relkind IN ('r','p') AND a.attnum>0 AND NOT a.attisdropped
        GROUP BY c.relname
    LOOP
        FOREACH role_name IN ARRAY ARRAY['milkyway_app','milkyway_paper','milkyway_backtest','milkyway_scheduler'] LOOP
            EXECUTE format('REVOKE ALL (%s) ON TABLE public.%I FROM %I', target.columns, target.relname, role_name);
        END LOOP;
    END LOOP;
END $$;

DO $$
DECLARE owner_name text;
BEGIN
    FOR owner_name IN
        SELECT DISTINCT r.rolname FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        JOIN pg_catalog.pg_roles r ON r.oid=c.relowner WHERE n.nspname='public'
        UNION SELECT current_user
    LOOP
        EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I REVOKE ALL ON TABLES FROM PUBLIC, milkyway_app, milkyway_paper, milkyway_backtest, milkyway_scheduler', owner_name);
        EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public REVOKE ALL ON TABLES FROM PUBLIC, milkyway_app, milkyway_paper, milkyway_backtest, milkyway_scheduler', owner_name);
        EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I REVOKE ALL ON SEQUENCES FROM PUBLIC, milkyway_app, milkyway_paper, milkyway_backtest, milkyway_scheduler', owner_name);
        EXECUTE format('ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public REVOKE ALL ON SEQUENCES FROM PUBLIC, milkyway_app, milkyway_paper, milkyway_backtest, milkyway_scheduler', owner_name);
    END LOOP;
END $$;

GRANT USAGE ON SCHEMA public TO milkyway_app, milkyway_paper, milkyway_backtest, milkyway_scheduler, milkyway_backup;

GRANT SELECT, INSERT ON users TO milkyway_app;
GRANT UPDATE (password_hash) ON users TO milkyway_app;
GRANT SELECT, INSERT, DELETE ON browser_sessions TO milkyway_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON login_throttles TO milkyway_app;
GRANT SELECT ON invitations TO milkyway_app;
GRANT UPDATE (redeemed_at, redeemed_by) ON invitations TO milkyway_app;
GRANT SELECT, INSERT ON strategies TO milkyway_app;
GRANT SELECT, INSERT ON backtest_jobs TO milkyway_app;
GRANT SELECT, INSERT ON paper_accounts TO milkyway_app;
GRANT UPDATE (status) ON paper_accounts TO milkyway_app;
GRANT SELECT ON paper_positions, paper_fills, quotes, runtime_heartbeats TO milkyway_app;
GRANT SELECT ON equity_points TO milkyway_app;

GRANT SELECT ON strategies TO milkyway_paper;
GRANT SELECT ON paper_accounts TO milkyway_paper;
GRANT UPDATE (cash, status, last_rebalanced_on) ON paper_accounts TO milkyway_paper;
GRANT SELECT, INSERT, DELETE ON paper_positions TO milkyway_paper;
GRANT UPDATE (shares, avg_price, last_price, updated_at) ON paper_positions TO milkyway_paper;
GRANT SELECT, INSERT ON paper_fills, equity_points TO milkyway_paper;
GRANT SELECT, INSERT, UPDATE ON quotes, runtime_heartbeats, leases TO milkyway_paper;
GRANT SELECT, INSERT, UPDATE ON work_cursors TO milkyway_paper;

GRANT SELECT ON strategies TO milkyway_backtest;
GRANT SELECT, DELETE ON backtest_jobs TO milkyway_backtest;
GRANT UPDATE (status, progress, result_json, error, worker_id, started_at, finished_at) ON backtest_jobs TO milkyway_backtest;
GRANT SELECT, INSERT, UPDATE ON runtime_heartbeats TO milkyway_backtest;
GRANT SELECT, INSERT, UPDATE ON work_cursors TO milkyway_backtest;

GRANT SELECT, INSERT, UPDATE ON leases, runtime_heartbeats TO milkyway_scheduler;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO milkyway_backup;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO milkyway_backup;
