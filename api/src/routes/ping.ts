import { Router } from "express";
import type { Request, Response } from "express";

const router = Router();

router.get("/ping", (_req: Request, res: Response) => {
  res.status(200).json({ pong: true });
});

export default router;
