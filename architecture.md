# Architecture

## The full picture

Three separate programs talk to each other, all started by `make up`:

```
[Test Client]  →→→  [Your Express API]  →→→  [Provider Simulator]
   Python                Node.js                  Node.js
  (worker.py)         (transfer.ts)            (provider-sim/)
                            ↕
                       [PostgreSQL]
                        (database)
```

---

## What each piece does

### Test Client (`client/worker.py`)

A Python script that pretends to be a customer app. It reads the 31 test cases
from `config/transactions.json` and fires them one by one at the Express API.
At the end it audits the final balances and prints `[PASS]` / `[FAIL]`.

**The 2-second interval** — from `worker.py:13` and `worker.py:191`:

```python
SEND_INTERVAL_SEC = 2

for count, tx in enumerate(transactions, start=1):
    asyncio.create_task(call_transfer(session, tx, count))  # fire-and-forget
    await asyncio.sleep(SEND_INTERVAL_SEC)                  # wait 2s, then next
```

`asyncio.create_task()` launches each HTTP call as a background task without
waiting for it to finish. So requests go out every 2 seconds regardless of
whether the previous transfer has settled with the provider yet. This means
multiple transfers can be in-flight simultaneously.

---

### Your Express API (`api/src/routes/transfer.ts`)

A normal web server. It receives HTTP POST requests and must:
1. Validate them
2. Read/write to PostgreSQL
3. Forward the transfer to the Provider Simulator
4. Respond to the HTTP caller immediately (do not wait for provider settlement)
5. Handle provider events in the background

---

### PostgreSQL + `pool.query()`

PostgreSQL is the database — it stores user balances and transaction state.
`pool` (from `api/src/db.ts`) is the connection your Node.js code uses to talk
to it. It keeps several connections open and reuses them.

```typescript
import { pool } from "@/db";
const result = await pool.query(
  "SELECT usdc FROM users WHERE userid = $1",
  [userId]
);
```

For operations that must be atomic (deduct + record in one step), you acquire a
client and use BEGIN/COMMIT:

```typescript
const client = await pool.connect();
try {
  await client.query("BEGIN");
  // multiple queries here
  await client.query("COMMIT");
} catch (err) {
  await client.query("ROLLBACK");
  throw err;
} finally {
  client.release();
}
```

---

### Provider Simulator (`api/src/provider-sim/server.ts`)

Simulates an external payment company (like Stripe, but for stablecoins).
It is a black box — you interact with it only through `api/src/provider.ts`.

It communicates over **WebSocket** (a persistent two-way socket), not HTTP.
You send it a transfer and it responds asynchronously some time later with
`"transferred"` or `"failed"`. This is why there are events instead of a
return value.

```typescript
// register listeners BEFORE calling providerTransfer to avoid a race
providerEvents.once("transferred", ({ transactionId }) => { /* credit dst */ });
providerEvents.once("failed",      ({ transactionId, reason }) => { /* refund src */ });

providerTransfer(opts);  // fire-and-forget
```

Events are **global** — always match by `transactionId`.

---

## Full request flow, step by step

```
1. Test client sends:  POST /transfer { transactionId, sourceUserId, ... }

2. Your API receives it and:
   a. Validates input
   b. Checks DB: do both users exist?
   c. Checks DB: does source user have enough balance?
   d. DB transaction (atomic):
        SELECT ... FOR UPDATE  ← locks the row against concurrent requests
        UPDATE users SET balance = balance - amount
        INSERT INTO transactions (status = 'received')
   e. Returns HTTP 200 to the test client  ← response ends HERE

3. After the response — in the background:
   Your API calls providerTransfer(opts)
   → sends a message over WebSocket to the Provider Simulator

4. Provider Simulator processes it (takes a variable amount of time)
   → sends back: "transferred" or "failed"

5. Your API receives the event via providerEvents.on(...)
   → "transferred": credit destination user, set status = 'transferred'
   → "failed":      refund source user,      set status = 'failed'
```

Steps 3–5 happen **in the background** while the test client has already moved
on and may be sending the next request 2 seconds later.

---

## Why concurrency matters

Because requests fire every 2 seconds without waiting for settlement, you can
have 5–10 transfers in-flight simultaneously. If two requests both try to
deduct from the same user's balance at the same time, without locking:

```
Request A reads balance = 100, deducts 10, writes 90
Request B reads balance = 100, deducts 10, writes 90  ← lost one deduction
```

The `SELECT ... FOR UPDATE` in step 2d locks the user row so Request B waits
until Request A has committed before it reads the balance. This makes the
deduction race-condition-free.
