import WebSocket from "ws";
import { EventEmitter } from "events";
import { TransferRequestBody } from "./types";

// ---------------------------------------------------------------------------
// providerTransfer — submit a transfer to the external provider
//
// Call this once per transaction after you have reserved the funds.
// The function is fire-and-forget; the result arrives asynchronously
// via providerEvents (see below).
//
// providerEvents emits three event types, each with { transactionId: string }:
//
//   "received"    – provider acknowledged the request; update your record
//   "transferred" – provider completed the transfer successfully
//   "failed"      – provider could not complete the transfer;
//                   also includes { reason: string }
//
// Example:
//   providerEvents.on("transferred", ({ transactionId }) => { ... });
//   providerEvents.on("failed",      ({ transactionId, reason }) => { ... });
//   providerTransfer(opts);
// ---------------------------------------------------------------------------

export type ProviderEvent =
  | { event: "received"; transactionId: string }
  | { event: "transferred"; transactionId: string }
  | { event: "failed"; transactionId: string; reason: string };

export const providerEvents = new EventEmitter();

export function providerTransfer(opts: TransferRequestBody): void {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    // Emit failure immediately if the provider is not reachable
    setImmediate(() =>
      providerEvents.emit("failed", {
        transactionId: opts.transactionId,
        reason: "provider not connected",
      })
    );
    return;
  }
  ws.send(JSON.stringify(opts));
}

// ---------------------------------------------------------------------------
// Internal — persistent WS connection to the provider simulator
// ---------------------------------------------------------------------------

const WS_URL = process.env.PROVIDER_WS_URL ?? "ws://provider-sim:4000";

let ws: WebSocket;
let reconnectDelay = 500;

function connect() {
  ws = new WebSocket(WS_URL);

  ws.on("open", () => {
    console.log("[provider] connected to provider-sim");
    reconnectDelay = 500;
  });

  ws.on("message", (raw) => {
    let msg: ProviderEvent;
    try {
      msg = JSON.parse(raw.toString());
    } catch {
      return;
    }

    const { event, transactionId, reason } = msg;

    if (event === "received") {
      providerEvents.emit("received", { transactionId });
    } else if (event === "transferred") {
      providerEvents.emit("transferred", { transactionId });
    } else if (event === "failed") {
      providerEvents.emit("failed", { transactionId, reason });
    }
  });

  ws.on("close", () => {
    console.log(`[provider] disconnected — reconnecting in ${reconnectDelay}ms`);
    setTimeout(connect, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 5000);
  });

  ws.on("error", (err) => {
    console.error("[provider] error:", err.message);
    // 'close' fires after 'error', reconnect is handled there
  });
}

connect();
