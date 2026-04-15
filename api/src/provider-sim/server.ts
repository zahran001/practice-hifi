import express from "express";
import http from "http";
import { readFileSync } from "fs";
import { WebSocketServer, WebSocket } from "ws";

const app = express();
app.use(express.json());

// ---------------------------------------------------------------------------
// Transaction config — loaded once at startup from the shared config file.
// Outcomes that reach the provider: "transferred" | "provider_failed"
// All other outcomes (insufficient_funds, invalid_input, etc.) should be
// rejected by the API before they ever arrive here.
// ---------------------------------------------------------------------------

type Outcome =
  | "transferred"
  | "provider_failed"
  | "insufficient_funds"
  | "invalid_input"
  | "user_not_found";

type TxConfig = {
  transactionId: string;
  outcome: Outcome;
};

const CONFIG_PATH = process.env.CONFIG_PATH ?? "/config/transactions.json";

function loadOutcomes(): Map<string, Outcome> {
  const map = new Map<string, Outcome>();
  try {
    const raw = readFileSync(CONFIG_PATH, "utf-8");
    const parsed = JSON.parse(raw) as { transactions: TxConfig[] };
    for (const tx of parsed.transactions) {
      map.set(tx.transactionId, tx.outcome);
    }
    console.log(`[provider-sim] loaded ${map.size} transaction outcomes from ${CONFIG_PATH}`);
  } catch (err) {
    console.warn(`[provider-sim] could not load config (${CONFIG_PATH}): ${(err as Error).message}`);
    console.warn("[provider-sim] falling back to random outcomes based on failureRate");
  }
  return map;
}

const outcomeMap = loadOutcomes();

// ---------------------------------------------------------------------------
// Control plane — tweak timing and fallback failure rate at runtime
// ---------------------------------------------------------------------------

type Config = {
  failureRate: number; // used only for transactions NOT in the config map
  minDelayMs: number;
  maxDelayMs: number;
  paused: boolean;
};

const config: Config = {
  failureRate: 0,    // deterministic by default; crank via POST /control to stress-test unknowns
  minDelayMs: 300,
  maxDelayMs: 1500,  // keep under SEND_INTERVAL_SEC (2s) to preserve sequential ordering
  paused: false,
};

const stats = {
  received: 0,
  transferred: 0,
  failed: 0,
  startedAt: new Date().toISOString(),
};

app.get("/control", (_req, res) => { res.json(config); });

app.post("/control", (req, res) => {
  const { failureRate, minDelayMs, maxDelayMs, paused } = req.body as Partial<Config>;
  if (failureRate !== undefined) config.failureRate = Math.max(0, Math.min(1, failureRate));
  if (minDelayMs !== undefined) config.minDelayMs = Math.max(0, minDelayMs);
  if (maxDelayMs !== undefined) config.maxDelayMs = Math.max(config.minDelayMs, maxDelayMs);
  if (paused !== undefined) config.paused = paused;
  console.log("[provider-sim] config updated:", config);
  res.json(config);
});

app.get("/stats", (_req, res) => { res.json(stats); });

// ---------------------------------------------------------------------------
// WebSocket server
// ---------------------------------------------------------------------------

const server = http.createServer(app);
const wss = new WebSocketServer({ server });

wss.on("connection", (ws) => {
  console.log("[provider-sim] API connected");

  ws.on("message", (raw) => {
    let payload: { transactionId?: string } & Record<string, unknown>;
    try {
      payload = JSON.parse(raw.toString());
    } catch {
      ws.send(JSON.stringify({ event: "error", reason: "invalid JSON" }));
      return;
    }

    const { transactionId } = payload;
    if (!transactionId) {
      ws.send(JSON.stringify({ event: "error", reason: "missing transactionId" }));
      return;
    }

    stats.received++;
    console.log(`[provider-sim] received  ${transactionId}`);
    safeSend(ws, { event: "received", transactionId });

    if (config.paused) {
      console.log(`[provider-sim] paused — ${transactionId} will not resolve`);
      return;
    }

    // Determine outcome.
    // "transferred" is the only outcome where the provider succeeds.
    // All other configured outcomes (insufficient_funds, user_not_found,
    // invalid_input, provider_failed) result in a provider failure — a real
    // provider would also reject transfers for accounts with no funds, unknown
    // users, or bad input. Transactions not in the config fall back to failureRate.
    const configuredOutcome = outcomeMap.get(transactionId);
    const willFail =
      configuredOutcome === "transferred"
        ? false
        : configuredOutcome !== undefined
        ? true
        : Math.random() < config.failureRate;

    const delay =
      Math.random() * (config.maxDelayMs - config.minDelayMs) + config.minDelayMs;

    setTimeout(() => {
      if (ws.readyState !== WebSocket.OPEN) return;

      if (willFail) {
        stats.failed++;
        console.log(`[provider-sim] failed      ${transactionId} (+${Math.round(delay)}ms)`);
        safeSend(ws, { event: "failed", transactionId, reason: "provider error" });
      } else {
        stats.transferred++;
        console.log(`[provider-sim] transferred ${transactionId} (+${Math.round(delay)}ms)`);
        safeSend(ws, { event: "transferred", transactionId });
      }
    }, delay);
  });

  ws.on("close", () => console.log("[provider-sim] API disconnected"));
  ws.on("error", (err) => console.error("[provider-sim] ws error:", err.message));
});

function safeSend(ws: WebSocket, data: object) {
  if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(data));
}

const PORT = 4000;
server.listen(PORT, "0.0.0.0", () => {
  console.log(`[provider-sim] listening on port ${PORT}`);
  console.log(`  WS:      ws://0.0.0.0:${PORT}`);
  console.log(`  Control: http://0.0.0.0:${PORT}/control`);
  console.log(`  Stats:   http://0.0.0.0:${PORT}/stats`);
});
