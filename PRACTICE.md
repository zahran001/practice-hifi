# HiFi Transfer API — Practice Notes

## Architecture

```
Python test client (make client)
        |
        | POST /transfer  (every 2s)
        v
Express API — localhost:3333          [api/src/index.ts]
        |
        |— pool.query() ————————————> PostgreSQL — localhost:5432
        |                               users table (pre-seeded)
        |                               transactions table (you create)
        |
        |— providerTransfer() ———————> Provider Simulator — ws://provider-sim:4000
                                        (fire-and-forget, results come back async)
                                        |
                                        | providerEvents.emit("received" | "transferred" | "failed")
                                        v
                                    Your event listeners (in transfer.ts)
```

### Key files

| File | Role |
|---|---|
| [api/src/routes/transfer.ts](api/src/routes/transfer.ts) | **Your entire implementation** |
| [api/src/provider.ts](api/src/provider.ts) | `providerTransfer()` + `providerEvents` — do not modify |
| [api/src/db.ts](api/src/db.ts) | `pool` — import this anywhere |
| [api/src/types.ts](api/src/types.ts) | `Currency`, `TransferRequestBody` |
| [api/src/index.ts](api/src/index.ts) | Server entry, WS broadcast — do not modify |
| [postgres/init/001_init.sql](postgres/init/001_init.sql) | Add your `transactions` table here |
| [config/transactions.json](config/transactions.json) | 31 test cases with expected outcomes |

### Users table (pre-seeded, read-only)

```sql
users (userid UUID PK, username, usdc NUMERIC(20,8), usdt NUMERIC(20,8), pyusd NUMERIC(20,8))
```

| User  | userid ending in | USDC  | USDT | PYUSD |
|-------|-----------------|-------|------|-------|
| Alice | ...0001         | 100   | 50   | 25    |
| Bob   | ...0002         | 10.5  | 0    | 5.25  |
| Carol | ...0003         | 0     | 75   | 12    |

### Provider events

```typescript
providerTransfer(opts)                         // fire-and-forget, call after reserving funds
providerEvents.on("received",    ({ transactionId }) => { ... })
providerEvents.on("transferred", ({ transactionId }) => { ... })
providerEvents.on("failed",      ({ transactionId, reason }) => { ... })
```

Events are **global** — multiple transfers can be in-flight at once. Always match by `transactionId`.

### DB transaction pattern

```typescript
const client = await pool.connect();
try {
  await client.query("BEGIN");
  // atomic queries here
  await client.query("COMMIT");
} catch (err) {
  await client.query("ROLLBACK");
  throw err;
} finally {
  client.release();
}
```

### Dev commands

```bash
make up      # start all services (hot-reload on save)
make client  # run test client, prints [PASS]/[FAIL] audit at end
make reset   # restore seed balances, clear transactions table
make down    # tear everything down
```

pgAdmin: http://localhost:5050 — `user@hifi.com` / `pass`

---

## Implementation Tasks

### 0. Create the transactions table

Add to [postgres/init/001_init.sql](postgres/init/001_init.sql).

Minimum columns needed:
- `transaction_id UUID PRIMARY KEY`
- `source_user_id UUID`
- `destination_user_id UUID`
- `source_currency TEXT`
- `source_amount NUMERIC(20,8)`
- `destination_currency TEXT`
- `status TEXT` — values: `received`, `transferred`, `failed`
- `created_at TIMESTAMPTZ DEFAULT now()`

Run `make reset` (or `make down && make up`) to apply.

---

### 1. Validate the request body

Location: top of the handler in [api/src/routes/transfer.ts](api/src/routes/transfer.ts), after the existing missing-field check.

- `sourceCurrency` and `destinationCurrency` must be one of `"usdc" | "usdt" | "pyusd"` — return `400`
- `sourceAmount` must be a number greater than `0` — return `400`

No DB calls yet. Pure input validation.

---

### 2. Idempotency check

Query the `transactions` table for the incoming `transactionId`.

- If a row exists: return `200` immediately, no re-processing
- If not: continue to the next step

---

### 3. Verify both users exist

Query the `users` table for `sourceUserId` and `destinationUserId`.

- If either is missing: return `404`

---

### 4. Check source balance

Query the source user's balance in `sourceCurrency`.

- If `balance < sourceAmount`: return `400` (insufficient funds)

---

### 5. Atomically reserve funds + record transaction

This must be a single DB transaction (BEGIN/COMMIT) to be race-condition-free.

Inside the transaction:
1. `SELECT ... FOR UPDATE` on the source user row to lock it
2. Re-check balance (the pre-lock check in step 4 can race — this is the real guard)
3. `UPDATE users SET <sourceCurrency> = <sourceCurrency> - sourceAmount WHERE userid = sourceUserId`
4. `INSERT INTO transactions (...) VALUES (...) ON CONFLICT DO NOTHING` with status `'received'`

Return `200` to the HTTP caller after this commit — do not wait for the provider.

---

### 6. Submit to provider + handle async events

After the HTTP response is sent, call `providerTransfer(opts)`.

Register listeners on `providerEvents` **before** calling `providerTransfer` to avoid a race:

```typescript
providerEvents.once("transferred", async ({ transactionId: tid }) => {
  if (tid !== transactionId) return;
  // credit destination user + update status to "transferred"
});

providerEvents.once("failed", async ({ transactionId: tid, reason }) => {
  if (tid !== transactionId) return;
  // restore source balance + update status to "failed"
});

providerTransfer(opts);
```

Use `once` not `on` to avoid accumulating listeners across requests.

---

### 7. Settle: transferred

On `"transferred"` event:

```sql
UPDATE users SET <destinationCurrency> = <destinationCurrency> + sourceAmount
WHERE userid = destinationUserId;

UPDATE transactions SET status = 'transferred' WHERE transaction_id = transactionId;
```

---

### 8. Settle: failed

On `"failed"` event:

```sql
UPDATE users SET <sourceCurrency> = <sourceCurrency> + sourceAmount
WHERE userid = sourceUserId;

UPDATE transactions SET status = 'failed' WHERE transaction_id = transactionId;
```

---

## Grading checklist

- [ ] All three users have correct final balances (`[PASS]`)
- [ ] Invalid currency / negative amount → `400` before any DB/provider call
- [ ] Unknown user → `404`
- [ ] Duplicate `transactionId` applied exactly once
- [ ] No race conditions under concurrent requests (row-level lock in step 5)
- [ ] Provider failure restores source balance correctly
- [ ] Audit completes quickly after last request (no hanging listeners)
