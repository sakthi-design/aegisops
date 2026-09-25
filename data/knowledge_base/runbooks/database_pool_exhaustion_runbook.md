# Runbook: Aurora PostgreSQL Connection Pool Exhaustion & High Latency

## Symptoms
- HTTP 503 / 504 errors on `/api/v1/payments/charge`
- HikariCP pool saturation alert: `ActiveConnections > 85%` for > 60s
- Slow query logs: Queries on `transactions` table with sequential scans exceeding 12,000ms

## Diagnostic Steps
1. Verify active connection count on primary database:
   `SELECT count(*), state FROM pg_stat_activity GROUP BY state;`
2. Identify long-running queries holding locks:
   `SELECT pid, now() - query_start as duration, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC LIMIT 5;`
3. Inspect recent deployment history on `payment-processor` and database migration jobs.

## Immediate Mitigation
1. If unindexed query is flooding connections:
   - Terminate offending queries: `SELECT pg_terminate_backend(pid);`
   - Apply hotfix migration adding missing btree index on foreign key or filter column:
     `CREATE INDEX CONCURRENTLY idx_transactions_user_created ON transactions(user_id, created_at DESC);`
2. If connection leak suspected:
   - Perform graceful rolling restart of `payment-processor` pods.
   - Adjust HikariCP `maximumPoolSize` up to DB max limit temporarily.
