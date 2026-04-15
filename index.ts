import express from "express";
import type { Request, Response } from "express";

const app = express();
const PORT = 3000;

app.get("/ping", (_req: Request, res: Response) => {
  res.status(200).json({ pong: true });
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`API listening on port ${PORT}`);
});
