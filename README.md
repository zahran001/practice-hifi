# HiFi Transfer API Technical Interview

## Overview

You are building the core of a stablecoin transfer API. A client will send transfer requests to your Express server. Your server must validate them, manage user balances in Postgres, submit transfers to an external payment provider, and handle the provider's async responses correctly.

The client, the payment provider, and the test harness are all already running. **Your job is to implement `api/src/routes/transfer.ts`** and create whatever database tables you need.

---

## Getting Started

```bash
make up
```

This builds all images and starts four background services:

| Service | What it does |
|---|---|
| `api` | Your Express server — the code you edit (`localhost:3333`) |
| `postgres` | PostgreSQL database (`localhost:5432`) |
| `pgadmin` | Database admin UI (`localhost:5050`) |
| `provider-sim` | Simulated payment provider — **do not modify** |

The server hot-reloads on save via `tsx watch`, so you don't need to restart Docker while working.

### Running the test client

When you're ready to test your implementation, run the client in a separate terminal:

```bash
make client
```

The client sends transfer requests every 2 seconds, then automatically runs a balance audit and prints `[PASS]` / `[FAIL]` results.

### Resetting the database

To restore all user balances to their starting values and clear the transactions table:

```bash
make reset
```

### Tearing down

```bash
make down
```

Stops all containers, removes volumes, and cleans up any orphaned containers.

---

## Database

### pgAdmin

Open `http://localhost:5050` in your browser.

| Field | Value |
|---|---|
| Email | `user@hifi.com` |
| Password | `pass` |

The server is pre-configured. Click **Servers → hifi** to connect. From there you can inspect tables, run queries, and create new tables.

### Connecting in code

A connection pool is already set up in `api/src/db.ts`. Import and use it anywhere in the API:

```typescript
import { pool } from "@/db";

const result = await pool.query(
  "SELECT usdc FROM users WHERE userid = $1",
  [userId]
);
```

For transactions that must be atomic, acquire a client from the pool:

```typescript
const client = await pool.connect();
try {
  await client.query("BEGIN");
  // ... multiple queries ...
  await client.query("COMMIT");
} catch (err) {
  await client.query("ROLLBACK");
  throw err;
} finally {
  client.release();
}
```

### Existing schema

```sql
users (
  userid UUID PRIMARY KEY,
  username VARCHAR(50),
  usdc NUMERIC(20,8),
  usdt NUMERIC(20,8),
  pyusd NUMERIC(20,8)
)
```

Three users are seeded:

| Name | userid | USDC | USDT | PYUSD |
|---|---|---|---|---|
| Alice | `00000000-0000-0000-0000-000000000001` | 100 | 50 | 25 |
| Bob | `00000000-0000-0000-0000-000000000002` | 10.5 | 0 | 5.25 |
| Carol | `00000000-0000-0000-0000-000000000003` | 0 | 75 | 12 |

You will need to **create a transactions table** to track transfer state. You can do this in pgAdmin, in an init SQL file, or programmatically — your choice. The possible statuses a transaction moves through are documented in `postgres/init/001_init.sql`.

---

## Payment Provider

The provider is a black box. You interact with it through two exports in `api/src/provider.ts` — **do not modify this file**.

### Submitting a transfer

```typescript
import { providerTransfer, providerEvents } from "@/provider";

providerTransfer({
  transactionId,
  sourceUserId,
  destinationUserId,
  sourceCurrency,
  sourceAmount,
  destinationCurrency,
});
```

This is **fire-and-forget**. The function returns nothing. The result arrives asynchronously via `providerEvents`.

### Listening for results

```typescript
providerEvents.on("received", ({ transactionId }) => {
  // provider acknowledged the request
});

providerEvents.on("transferred", ({ transactionId }) => {
  // provider completed the transfer — credit the destination user
});

providerEvents.on("failed", ({ transactionId, reason }) => {
  // provider could not complete the transfer — restore the source balance
});
```

Events are emitted globally. Use `transactionId` to match events back to the right transfer. Transfers take a variable amount of time — multiple may be in-flight simultaneously.

---

## What to Implement

All your work goes in `api/src/routes/transfer.ts`. The route receives a `POST /transfer` with this body:

```typescript
{
  transactionId: string      // UUID — used for idempotency
  sourceUserId: string       // UUID
  destinationUserId: string  // UUID
  sourceCurrency: string     // "usdc" | "usdt" | "pyusd"
  sourceAmount: number       // must be > 0
  destinationCurrency: string
}
```

The TODO comments in the file outline the steps. At a high level:

0. **Create a transactions table** — you need somewhere to record each transfer and its status. The possible statuses are documented in `postgres/init/001_init.sql`. You can create the table in pgAdmin, in a new init SQL file, or programmatically — your choice.
1. **Validate** the request — reject bad currencies, negative/zero amounts, missing fields
2. **Idempotency** — if this `transactionId` was already processed, return the same result without re-running the transfer
3. **User validation** — verify both users exist
4. **Balance check** — verify the source user has enough funds
5. **Reserve funds** — atomically deduct from the source and record the transaction
6. **Submit to provider** — call `providerTransfer` and handle the async events
7. **Settle** — on `"transferred"`, credit the destination; on `"failed"`, restore the source

---

## Grading

When the client finishes sending all requests it will automatically run a balance audit and print the results. We will evaluate your submission on:

| Criteria | What we look at |
|---|---|
| **Correctness** | Do all three users end up with the right final balances? |
| **Validation** | Are bad requests (invalid currency, negative amount, unknown user) rejected with the right status code before touching the DB or provider? |
| **Idempotency** | Does sending the same `transactionId` twice apply the transfer exactly once? |
| **Concurrency** | Are balance updates race-condition-free under concurrent requests? |
| **Failure recovery** | When the provider fails a transfer, is the source balance correctly restored? |
| **Settlement lag** | How quickly after the last request does everything finish processing? |

The audit output will show `[PASS]` or `[FAIL]` per user per currency, plus timing. A correct implementation passes all checks.

<img width="5760" height="2160" alt="image" src="https://github.com/user-attachments/assets/4a949e14-9bdf-41da-9f23-52a99e32930f" />

