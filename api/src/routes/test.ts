
import { Router } from "express";
import type { Request, Response } from "express";

const router = Router();

router.get("/test", (_req: Request, res: Response) => {
  res.status(200).json({ test: "test"});
});

export default router;
