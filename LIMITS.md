# HookRelay — current limits

## What this system does today

HookRelay accepts events via an unauthenticated `POST /events` endpoint,
stores each event and its per-endpoint delivery work durably in PostgreSQL,
and delivers signed webhooks to a single configured receiver. A worker
claims a due delivery with `FOR UPDATE SKIP LOCKED`, assigns a lease and
attempt row, sends an HMAC-signed request with bounded time and byte caps,
and finalizes the attempt and delivery conditionally on the lease still
matching. The full local slice works end to end and is covered by tests.

## What it does not do yet

- **One-attempt budget; failures are terminal.** A transient receiver
  error (503, timeout, brief outage) permanently marks the delivery as
  `failure` with no retry. The delivery is dead even though a retry
  would likely succeed. Addressed in D15 (retry policy).

- **No lease recovery.** If a worker crashes between claiming and
  finalizing, the delivery stays `in_progress` with an expired lease
  and an unfinished attempt row. No other worker can claim it, and it
  is effectively lost from the queue. Addressed in D16 (reaper).

- **No authentication or tenant isolation.** The API hardcodes
  `tenant_id = "local-tenant"`. Any caller can write to that tenant.
  No API keys, no per-tenant authorization, no rate limiting. The
  system is intended for local use only. Addressed in D23, D24, D33.

- **Receiver effects are not deduplicated.** The receiver verifies
  signatures and records receipts, but has no transactional dedup on
  the delivery ID. Once retries exist (D15), a retry could apply the
  receiver's side effect twice. Addressed in D19 (transactional
  receiver dedup).

- **No operational visibility.** Logs are unstructured; no metrics,
  no health checks beyond `/health`, no alerting. Addressed in D26
  (structured logs) and D37 (metrics).

## Deliberately out of scope

- **Arbitrary destination URLs.** Users cannot register their own
  receivers. This is a security decision, not an unfinished feature:
  arbitrary URLs introduce SSRF risk that is its own project.
  See the roadmap's SSRF extension if this is ever pursued.