import { Router } from "express";
import type { Request, Response } from "express";
import { pool } from "../db";

const router = Router();

type UserParams = {
  userid: string;
};

router.get("/:userid", async (
  req: Request<UserParams>,
  res: Response
) => {
  try {
    const { userid } = req.params;

    const result = await pool.query(
      `
      SELECT userid, usdc, usdt, pyusd
      FROM users
      WHERE userid = $1
      `,
      [userid]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        error: "user not found"
      });
    }

    return res.status(200).json(result.rows[0]);

  } catch (error) {
    console.error(error);

    return res.status(500).json({
      error: "server error"
    });
  }
});

export default router;
