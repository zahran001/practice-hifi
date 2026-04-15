import { Router } from "express";
import pingRouter from "./ping";
import testRouter from "./test";

const router = Router();
router.use("/", pingRouter);
router.use("/", testRouter);

export default router;
