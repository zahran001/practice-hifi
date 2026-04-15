import asyncio
import json
import os
import time
import aiohttp

BASE_URL     = os.getenv("TARGET_URL",   "http://api:3000")
PROVIDER_URL = os.getenv("PROVIDER_URL", "http://provider-sim:4000")
CONFIG_PATH  = os.getenv("CONFIG_PATH",  "/config/transactions.json")
TRANSFER_URL = BASE_URL + "/transfer"
EVENTS_URL   = BASE_URL.replace("http", "ws") + "/events"

SEND_INTERVAL_SEC = 2  # gap between each outgoing request

# ---------------------------------------------------------------------------
# Initial balances (must match postgres/init/001_init.sql)
# ---------------------------------------------------------------------------

INITIAL_BALANCES: dict[str, dict[str, float]] = {
    "00000000-0000-0000-0000-000000000001": {"usdc": 100.0,  "usdt": 50.0,  "pyusd": 25.0},
    "00000000-0000-0000-0000-000000000002": {"usdc": 10.5,   "usdt": 0.0,   "pyusd": 5.25},
    "00000000-0000-0000-0000-000000000003": {"usdc": 0.0,    "usdt": 75.0,  "pyusd": 12.0},
}

# ---------------------------------------------------------------------------
# Load transaction config
# ---------------------------------------------------------------------------

def load_transactions() -> list[dict]:
    with open(CONFIG_PATH) as f:
        return json.load(f)["transactions"]

# ---------------------------------------------------------------------------
# Compute expected final balances from the config.
# Only "transferred" outcomes change balances.
# Duplicate txIds (same ID appearing more than once) are only counted once —
# that is what correct idempotency implementation should produce.
# ---------------------------------------------------------------------------

def compute_expected_balances(transactions: list[dict]) -> dict[str, dict[str, float]]:
    balances = {uid: dict(currencies) for uid, currencies in INITIAL_BALANCES.items()}
    seen: set[str] = set()

    for tx in transactions:
        tx_id = tx["transactionId"]
        if tx_id in seen:
            continue  # idempotent — only apply once per unique txId
        seen.add(tx_id)

        if tx["outcome"] != "transferred":
            continue

        src = tx["sourceUserId"]
        dst = tx["destinationUserId"]
        src_c = tx["sourceCurrency"]
        dst_c = tx["destinationCurrency"]
        amt = tx["sourceAmount"]

        balances[src][src_c] -= amt
        balances[dst][dst_c] += amt

    return balances

# ---------------------------------------------------------------------------
# WebSocket event listener
# ---------------------------------------------------------------------------

async def listen_for_events(session: aiohttp.ClientSession) -> None:
    try:
        async with session.ws_connect(EVENTS_URL) as ws:
            print(f"[ws] connected to {EVENTS_URL}", flush=True)
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    print(f"[ws] {msg.data}", flush=True)
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        print(f"[ws] error: {exc}", flush=True)

# ---------------------------------------------------------------------------
# HTTP transfer sender
# ---------------------------------------------------------------------------

async def call_transfer(session: aiohttp.ClientSession, tx: dict, count: int) -> None:
    payload = {
        "transactionId":      tx["transactionId"],
        "sourceUserId":       tx["sourceUserId"],
        "destinationUserId":  tx["destinationUserId"],
        "sourceCurrency":     tx["sourceCurrency"],
        "sourceAmount":       tx["sourceAmount"],
        "destinationCurrency": tx["destinationCurrency"],
    }
    try:
        async with session.post(
            TRANSFER_URL,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=5),
        ) as response:
            data = await response.json()
            print(f"[http] request {count:02d}: status={response.status} body={data}", flush=True)
    except Exception as exc:
        print(f"[http] request {count:02d}: failed -> {exc}", flush=True)

# ---------------------------------------------------------------------------
# Completion detection — poll provider stats until all sent transfers settled
# ---------------------------------------------------------------------------

async def wait_until_settled(session: aiohttp.ClientSession, timeout: float = 60.0) -> float:
    deadline = time.monotonic() + timeout
    prev_line = ""

    while time.monotonic() < deadline:
        await asyncio.sleep(0.5)
        try:
            async with session.get(f"{PROVIDER_URL}/stats") as resp:
                s = await resp.json()
        except Exception:
            continue

        received     = s.get("received", 0)
        transferred  = s.get("transferred", 0)
        failed       = s.get("failed", 0)
        settled      = transferred + failed
        line = f"provider — received={received}  transferred={transferred}  failed={failed}"

        if line != prev_line:
            print(f"[audit] {line}", flush=True)
            prev_line = line

        if received > 0 and received == settled:
            return time.monotonic()

    print("[audit] timeout waiting for provider to settle", flush=True)
    return time.monotonic()

# ---------------------------------------------------------------------------
# Balance audit
# ---------------------------------------------------------------------------

async def audit_balances(
    session: aiohttp.ClientSession,
    expected: dict[str, dict[str, float]],
) -> None:
    print("\n[audit] ── Balance Check ──────────────────────────────", flush=True)
    all_pass = True

    for user_id, exp_currencies in expected.items():
        try:
            async with session.get(f"{BASE_URL}/users/{user_id}") as resp:
                actual = await resp.json()
        except Exception as exc:
            print(f"[audit] could not fetch user {user_id}: {exc}", flush=True)
            all_pass = False
            continue

        short = user_id[-4:]
        for currency in ("usdc", "usdt", "pyusd"):
            exp = exp_currencies[currency]
            act = float(actual.get(currency, -1))
            ok  = abs(exp - act) < 0.000001
            if not ok:
                all_pass = False
            mark = "PASS" if ok else "FAIL"
            print(
                f"  [{mark}] user ...{short} {currency.upper():>5}  "
                f"expected={exp:.8f}  actual={act:.8f}",
                flush=True,
            )

    verdict = "ALL BALANCES CORRECT" if all_pass else "BALANCE MISMATCH DETECTED"
    print(f"\n[audit] {verdict}", flush=True)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    transactions = load_transactions()
    expected_balances = compute_expected_balances(transactions)

    await asyncio.sleep(5)  # wait for API to be ready

    async with aiohttp.ClientSession() as session:
        event_task = asyncio.create_task(listen_for_events(session))
        await asyncio.sleep(0.5)  # let WS connect before first request

        for count, tx in enumerate(transactions, start=1):
            asyncio.create_task(call_transfer(session, tx, count))
            await asyncio.sleep(SEND_INTERVAL_SEC)

        last_sent_at = time.monotonic()
        print(f"\n[worker] all {len(transactions)} requests sent — waiting for settlement...\n", flush=True)

        settled_at = await wait_until_settled(session)
        lag = settled_at - last_sent_at
        print(f"[audit] provider fully settled {lag:.2f}s after last request was sent", flush=True)

        # Small buffer for API to finish any DB writes after the final provider event
        await asyncio.sleep(2)

        await audit_balances(session, expected_balances)

        event_task.cancel()

    print("\n[worker] done", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
