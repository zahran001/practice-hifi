import http from "http";
import express from "express";
import { WebSocketServer, WebSocket } from "ws";
import utilRouter from "@/routes/utils";
import usersRouter from "@/routes/users";
import transferRouter from "@/routes/transfer";
import { providerEvents } from "@/provider";

const app = express();
const PORT = 3000;

app.use(express.json());
app.use("/", utilRouter);
app.use("/users", usersRouter);
app.use("/transfer", transferRouter);

// ---------------------------------------------------------------------------
// /events  — WebSocket stream of all provider lifecycle events.
// Clients (e.g. the test worker) connect here to watch transfers in real time.
// Each message is JSON: { event, transactionId, reason? }
// ---------------------------------------------------------------------------

const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: "/events" });
const listeners = new Set<WebSocket>();

wss.on("connection", (ws) => {
  listeners.add(ws);
  ws.on("close", () => listeners.delete(ws));
});

function broadcast(payload: object) {
  const msg = JSON.stringify(payload);
  for (const ws of listeners) {
    if (ws.readyState === WebSocket.OPEN) ws.send(msg);
  }
}

providerEvents.on("received",    (d) => broadcast({ event: "received",    ...d }));
providerEvents.on("transferred", (d) => broadcast({ event: "transferred", ...d }));
providerEvents.on("failed",      (d) => broadcast({ event: "failed",      ...d }));

server.listen(PORT, "0.0.0.0", () => {
  console.log(`API listening on port ${PORT}`);
});
