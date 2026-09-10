-- Applied atomically by the maintenance owner after schema/role migrations.
-- The app may present an opaque browser token; only the authority can mint it.
CREATE SCHEMA IF NOT EXISTS milkyway_private;
REVOKE ALL ON SCHEMA milkyway_private FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO milkyway_authority;
GRANT USAGE ON SCHEMA milkyway_private TO milkyway_app, milkyway_paper, milkyway_backtest;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles r ON r.oid=m.member
        WHERE r.rolname IN ('milkyway_app','milkyway_paper','milkyway_backtest','milkyway_scheduler','milkyway_authority')
    ) THEN
        RAISE EXCEPTION 'Runtime roles must not inherit or SET ROLE to other roles';
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_catalog.pg_roles
        WHERE rolname IN ('milkyway_app', 'milkyway_paper', 'milkyway_backtest', 'milkyway_scheduler', 'milkyway_authority')
          AND (rolsuper OR rolbypassrls OR rolcreaterole)
    ) THEN
        RAISE EXCEPTION 'Runtime roles must not bypass row security or create roles';
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_roles r ON r.oid = c.relowner
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND r.rolname IN ('milkyway_app', 'milkyway_paper', 'milkyway_backtest', 'milkyway_scheduler', 'milkyway_authority')
    ) THEN
        RAISE EXCEPTION 'Runtime roles must not own application objects';
    END IF;
END $$;

CREATE OR REPLACE FUNCTION milkyway_private.member_id()
RETURNS text LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
    SELECT s.user_id::text
    FROM public.authority_sessions s JOIN public.users u ON u.id = s.user_id
    WHERE s.token_hash = pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
        pg_catalog.current_setting('milkyway.auth_token', true), 'UTF8')), 'hex')
      AND pg_catalog.length(pg_catalog.current_setting('milkyway.auth_token', true)) = 43
      AND s.expires_at > pg_catalog.statement_timestamp() AND u.active
$$;

CREATE OR REPLACE FUNCTION milkyway_private.principal()
RETURNS TABLE (user_id text, email text, display_name text, role text, csrf text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public
AS $$
    SELECT u.id::text, u.email::text, u.display_name::text, u.role::text, s.csrf::text
    FROM public.authority_sessions s JOIN public.users u ON u.id = s.user_id
    WHERE s.token_hash = pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
        pg_catalog.current_setting('milkyway.auth_token', true), 'UTF8')), 'hex')
      AND pg_catalog.length(pg_catalog.current_setting('milkyway.auth_token', true)) = 43
      AND s.expires_at > pg_catalog.statement_timestamp() AND u.active
$$;

CREATE OR REPLACE FUNCTION milkyway_private.current_claim()
RETURNS SETOF public.work_claims LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
    SELECT c.token_hash,c.service,c.user_id,coalesce(r.resource_id,c.resource_id),
           coalesce(r.strategy_id,c.strategy_id),coalesce(r.tickers_json,c.tickers_json),
           c.credential_version,c.slot,c.expires_at,c.quotes_consumed_at,c.completed_at,c.created_at
    FROM public.work_claims c JOIN public.users u ON u.id = c.user_id
    LEFT JOIN public.work_resources r ON r.claim_hash=c.token_hash
    WHERE c.token_hash = pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
        pg_catalog.current_setting('milkyway.claim_token', true), 'UTF8')), 'hex')
      AND pg_catalog.length(pg_catalog.current_setting('milkyway.claim_token', true)) = 43
      AND c.service = CASE session_user WHEN 'milkyway_paper' THEN 'paper'
                                       WHEN 'milkyway_backtest' THEN 'backtest' ELSE '' END
      AND c.expires_at > pg_catalog.statement_timestamp()
      AND c.completed_at IS NULL AND u.active
$$;

REVOKE ALL ON ALL FUNCTIONS IN SCHEMA milkyway_private FROM PUBLIC;
GRANT EXECUTE ON FUNCTION milkyway_private.member_id(), milkyway_private.principal() TO milkyway_app;
GRANT EXECUTE ON FUNCTION milkyway_private.current_claim() TO milkyway_paper, milkyway_backtest;

-- The public app cannot read password hashes or issue/revoke identities itself.
REVOKE ALL ON users, browser_sessions, authority_sessions, operation_permits, work_claims,
    invitations, login_throttles, ai_connections, market_data_connections, member_quotes, admitted_tickers, work_resources
    FROM milkyway_app, milkyway_paper, milkyway_backtest, milkyway_scheduler;
REVOKE UPDATE (password_hash) ON users FROM milkyway_app;
REVOKE UPDATE (redeemed_at, redeemed_by) ON invitations FROM milkyway_app;
REVOKE ALL ON quotes FROM milkyway_paper;
GRANT SELECT ON quotes TO milkyway_paper;
GRANT SELECT (user_id, provider, environment, key_hint, secret_hint, verified_at, created_at, updated_at)
    ON market_data_connections TO milkyway_app;
GRANT SELECT ON member_quotes TO milkyway_app, milkyway_paper;
-- Ciphertext is also restricted to the authority; workers receive quote results.
REVOKE SELECT ON market_data_connections FROM milkyway_paper;
GRANT SELECT (user_id, provider, environment, key_hint, secret_hint, verified_at, created_at, updated_at)
    ON market_data_connections TO milkyway_paper;

GRANT SELECT, INSERT, UPDATE, DELETE ON users, authority_sessions, operation_permits,
    work_claims, invitations, login_throttles, market_data_connections, member_quotes,
    quotes, runtime_heartbeats, work_cursors, backtest_jobs TO milkyway_authority;
GRANT SELECT, INSERT, UPDATE, DELETE ON admitted_tickers, work_resources TO milkyway_authority;
GRANT UPDATE (status) ON paper_accounts TO milkyway_authority;
GRANT SELECT ON strategies, paper_accounts, paper_positions, paper_fills, equity_points TO milkyway_authority;

DO $$
DECLARE target text;
BEGIN
    FOREACH target IN ARRAY ARRAY['users','strategies','backtest_jobs','paper_accounts',
        'paper_positions','paper_fills','equity_points','market_data_connections',
        'member_quotes','runtime_heartbeats','leases','work_cursors'] LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', target);
        EXECUTE format('DROP POLICY IF EXISTS authority_access ON public.%I', target);
        EXECUTE format('CREATE POLICY authority_access ON public.%I TO milkyway_authority USING (true) WITH CHECK (true)', target);
        EXECUTE format('DROP POLICY IF EXISTS backup_access ON public.%I', target);
        EXECUTE format('CREATE POLICY backup_access ON public.%I FOR SELECT TO milkyway_backup USING (true)', target);
    END LOOP;
    FOREACH target IN ARRAY ARRAY['strategies','backtest_jobs','paper_accounts','market_data_connections','member_quotes'] LOOP
        EXECUTE format('DROP POLICY IF EXISTS app_member ON public.%I', target);
        EXECUTE format('CREATE POLICY app_member ON public.%I TO milkyway_app USING (user_id = milkyway_private.member_id()) WITH CHECK (user_id = milkyway_private.member_id())', target);
    END LOOP;
    FOREACH target IN ARRAY ARRAY['paper_positions','paper_fills','equity_points'] LOOP
        EXECUTE format('DROP POLICY IF EXISTS app_member ON public.%I', target);
        EXECUTE format('CREATE POLICY app_member ON public.%I FOR SELECT TO milkyway_app USING (EXISTS (SELECT 1 FROM public.paper_accounts a WHERE a.id = account_id AND a.user_id = milkyway_private.member_id()))', target);
    END LOOP;
END $$;

DROP POLICY IF EXISTS worker_claim ON public.strategies;
CREATE POLICY worker_claim ON public.strategies FOR SELECT TO milkyway_paper, milkyway_backtest
USING (EXISTS (SELECT 1 FROM milkyway_private.current_claim() c WHERE c.strategy_id = strategies.id AND c.user_id = strategies.user_id));

DROP POLICY IF EXISTS worker_claim ON public.backtest_jobs;
CREATE POLICY worker_claim ON public.backtest_jobs TO milkyway_backtest
USING (EXISTS (SELECT 1 FROM milkyway_private.current_claim() c WHERE c.resource_id = backtest_jobs.id AND c.user_id = backtest_jobs.user_id))
WITH CHECK (EXISTS (SELECT 1 FROM milkyway_private.current_claim() c WHERE c.resource_id = backtest_jobs.id AND c.user_id = backtest_jobs.user_id));

DROP POLICY IF EXISTS worker_claim ON public.paper_accounts;
CREATE POLICY worker_claim ON public.paper_accounts TO milkyway_paper
USING (EXISTS (SELECT 1 FROM milkyway_private.current_claim() c WHERE c.resource_id = paper_accounts.id AND c.user_id = paper_accounts.user_id))
WITH CHECK (EXISTS (SELECT 1 FROM milkyway_private.current_claim() c WHERE c.resource_id = paper_accounts.id AND c.user_id = paper_accounts.user_id));

DROP POLICY IF EXISTS worker_claim ON public.paper_positions;
CREATE POLICY worker_claim ON public.paper_positions TO milkyway_paper
USING (EXISTS (SELECT 1 FROM milkyway_private.current_claim() c WHERE c.resource_id = account_id))
WITH CHECK (EXISTS (SELECT 1 FROM milkyway_private.current_claim() c WHERE c.resource_id = account_id AND c.tickers_json::jsonb ? ticker));

DROP POLICY IF EXISTS worker_claim ON public.paper_fills;
CREATE POLICY worker_claim ON public.paper_fills TO milkyway_paper
USING (EXISTS (SELECT 1 FROM milkyway_private.current_claim() c WHERE c.resource_id = account_id))
WITH CHECK (left(dedupe_key,length(account_id)+1) = account_id || ':'
    AND EXISTS (SELECT 1 FROM milkyway_private.current_claim() c WHERE c.resource_id = account_id AND c.tickers_json::jsonb ? ticker));

DROP POLICY IF EXISTS worker_claim ON public.equity_points;
CREATE POLICY worker_claim ON public.equity_points TO milkyway_paper
USING (EXISTS (SELECT 1 FROM milkyway_private.current_claim() c WHERE c.resource_id = account_id))
WITH CHECK (EXISTS (SELECT 1 FROM milkyway_private.current_claim() c WHERE c.resource_id = account_id));

DROP POLICY IF EXISTS worker_claim ON public.member_quotes;
CREATE POLICY worker_claim ON public.member_quotes FOR SELECT TO milkyway_paper
USING (EXISTS (SELECT 1 FROM milkyway_private.current_claim() c WHERE c.user_id = member_quotes.user_id AND c.tickers_json::jsonb ? ticker));

DROP POLICY IF EXISTS worker_claim ON public.market_data_connections;
CREATE POLICY worker_claim ON public.market_data_connections FOR SELECT TO milkyway_paper
USING (EXISTS (SELECT 1 FROM milkyway_private.current_claim() c WHERE c.user_id = market_data_connections.user_id));

DROP POLICY IF EXISTS app_health ON public.runtime_heartbeats;
CREATE POLICY app_health ON public.runtime_heartbeats FOR SELECT TO milkyway_app USING (true);
DROP POLICY IF EXISTS service_heartbeat ON public.runtime_heartbeats;
CREATE POLICY service_heartbeat ON public.runtime_heartbeats TO milkyway_paper, milkyway_backtest, milkyway_scheduler
USING (component = CASE current_user WHEN 'milkyway_paper' THEN 'paper-worker' WHEN 'milkyway_backtest' THEN 'backtest-worker' WHEN 'milkyway_scheduler' THEN 'data-scheduler' END)
WITH CHECK (component = CASE current_user WHEN 'milkyway_paper' THEN 'paper-worker' WHEN 'milkyway_backtest' THEN 'backtest-worker' WHEN 'milkyway_scheduler' THEN 'data-scheduler' END);

DROP POLICY IF EXISTS service_lease ON public.leases;
CREATE POLICY service_lease ON public.leases TO milkyway_paper, milkyway_scheduler
USING (name = CASE current_user WHEN 'milkyway_paper' THEN 'paper-engine' WHEN 'milkyway_scheduler' THEN 'daily-data-refresh' END)
WITH CHECK (name = CASE current_user WHEN 'milkyway_paper' THEN 'paper-engine' WHEN 'milkyway_scheduler' THEN 'daily-data-refresh' END);

DROP POLICY IF EXISTS service_cursor ON public.work_cursors;
CREATE POLICY service_cursor ON public.work_cursors TO milkyway_paper, milkyway_backtest
USING ((current_user = 'milkyway_paper' AND name = 'shared-quote-worklist') OR (current_user = 'milkyway_backtest' AND name = 'backtest-owner'))
WITH CHECK ((current_user = 'milkyway_paper' AND name = 'shared-quote-worklist') OR (current_user = 'milkyway_backtest' AND name = 'backtest-owner'));

-- RLS hides other members from normal counts. Global admission therefore runs
-- inside an owner function and reads limits unavailable to runtime writers.
CREATE TABLE IF NOT EXISTS milkyway_private.limits (name text PRIMARY KEY, value bigint NOT NULL CHECK (value > 0));
REVOKE ALL ON milkyway_private.limits FROM PUBLIC, milkyway_app, milkyway_paper, milkyway_backtest, milkyway_scheduler, milkyway_authority;
INSERT INTO milkyway_private.limits(name,value) VALUES
 ('max_strategies_per_user',10),('max_accounts_per_user',3),('max_backtests_per_user_day',20),
 ('max_outstanding_backtests_per_user',2),('max_outstanding_backtests_total',40),('max_backtest_result_bytes',1048576)
 ON CONFLICT(name) DO NOTHING;

CREATE OR REPLACE FUNCTION milkyway_private.limit_value(key text)
RETURNS bigint LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public
AS $$ SELECT value FROM milkyway_private.limits WHERE name=key $$;
REVOKE ALL ON FUNCTION milkyway_private.limit_value(text) FROM PUBLIC;

CREATE OR REPLACE FUNCTION milkyway_private.enforce_admission()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public
AS $$
DECLARE total bigint;
BEGIN
    IF TG_TABLE_NAME = 'backtest_jobs' AND TG_OP='UPDATE' THEN
        IF octet_length(coalesce(NEW.result_json,'')) > milkyway_private.limit_value('max_backtest_result_bytes')
           OR octet_length(coalesce(NEW.error,'')) > 8000 THEN
            RAISE EXCEPTION 'Backtest result exceeds retention limit' USING ERRCODE='23514';
        END IF;
        RETURN NEW;
    END IF;
    IF session_user <> 'milkyway_app' THEN RETURN NEW; END IF;
    IF NEW.user_id IS DISTINCT FROM milkyway_private.member_id() THEN
        RAISE EXCEPTION 'A live member identity is required' USING ERRCODE='42501';
    END IF;
    PERFORM pg_catalog.pg_advisory_xact_lock(778459201);
    NEW.created_at := statement_timestamp();
    IF TG_TABLE_NAME = 'strategies' THEN
        SELECT count(*) INTO total FROM public.strategies WHERE user_id=NEW.user_id;
        IF total >= milkyway_private.limit_value('max_strategies_per_user') OR octet_length(NEW.spec_json)>32768
           OR octet_length(NEW.original_prompt)>12000 THEN
            RAISE EXCEPTION 'Strategy admission limit reached' USING ERRCODE='23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'paper_accounts' THEN
        SELECT count(*) INTO total FROM public.paper_accounts WHERE user_id=NEW.user_id;
        IF total >= milkyway_private.limit_value('max_accounts_per_user') THEN
            RAISE EXCEPTION 'Paper account admission limit reached' USING ERRCODE='23514';
        END IF;
        NEW.status := 'active';
    ELSIF TG_TABLE_NAME = 'backtest_jobs' THEN
        SELECT count(*) INTO total FROM public.backtest_jobs WHERE user_id=NEW.user_id
            AND created_at >= date_trunc('day',statement_timestamp() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC';
        IF total >= milkyway_private.limit_value('max_backtests_per_user_day') THEN
            RAISE EXCEPTION 'Daily backtest admission limit reached' USING ERRCODE='23514';
        END IF;
        SELECT count(*) INTO total FROM public.backtest_jobs WHERE user_id=NEW.user_id AND status IN ('queued','running');
        IF total >= milkyway_private.limit_value('max_outstanding_backtests_per_user') THEN
            RAISE EXCEPTION 'Member backtest queue is full' USING ERRCODE='23514';
        END IF;
        SELECT count(*) INTO total FROM public.backtest_jobs WHERE status IN ('queued','running');
        IF total >= milkyway_private.limit_value('max_outstanding_backtests_total') THEN
            RAISE EXCEPTION 'Global backtest queue is full' USING ERRCODE='23514';
        END IF;
        NEW.status := 'queued'; NEW.progress := 0; NEW.result_json := NULL; NEW.error := NULL;
        NEW.started_at := NULL; NEW.finished_at := NULL; NEW.worker_id := NULL;
    END IF;
    RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION milkyway_private.enforce_admission() FROM PUBLIC;
DROP TRIGGER IF EXISTS enforce_admission ON strategies;
CREATE TRIGGER enforce_admission BEFORE INSERT ON strategies FOR EACH ROW EXECUTE FUNCTION milkyway_private.enforce_admission();
DROP TRIGGER IF EXISTS enforce_admission ON paper_accounts;
CREATE TRIGGER enforce_admission BEFORE INSERT ON paper_accounts FOR EACH ROW EXECUTE FUNCTION milkyway_private.enforce_admission();
DROP TRIGGER IF EXISTS enforce_admission ON backtest_jobs;
CREATE TRIGGER enforce_admission BEFORE INSERT OR UPDATE ON backtest_jobs FOR EACH ROW EXECUTE FUNCTION milkyway_private.enforce_admission();
