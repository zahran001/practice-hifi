import { Router } from "express";
import type { Request, Response } from "express";
import { TransferRequestBody } from "@/types";
import { pool } from "@/db";
import { providerTransfer, providerEvents } from "@/provider";

const router = Router();

router.post(
  "/",
  async (req: Request<{}, {}, TransferRequestBody>, res: Response) => {
    try {
      const {
        transactionId,
        sourceUserId,
        destinationUserId,
        sourceCurrency,
        sourceAmount,
        destinationCurrency,
      } = req.body;

      if (
        !transactionId ||
        !sourceUserId ||
        !destinationUserId ||
        !sourceCurrency ||
        sourceAmount == null ||
        !destinationCurrency
      ) {
        return res.status(400).json({
          error:
            "transactionId, sourceUserId, destinationUserId, sourceCurrency, sourceAmount, and destinationCurrency are required",
        });
      }

      // TODO: validate sourceCurrency and destinationCurrency are supported values

      // TODO: validate sourceAmount is a positive number

      // TODO: check for a duplicate transactionId and return early (idempotency)

      // TODO: verify sourceUserId and destinationUserId exist in the users table

      // TODO: verify the source user has sufficient balance in sourceCurrency

      // TODO: deduct sourceAmount from the source user's balance
      //       and record the transaction — do this atomically

      // TODO: call providerTransfer(opts) to submit to the provider.
      //       Listen on providerEvents for "received", "transferred", and "failed"
      //       events keyed by transactionId, and update your transaction record
      //       accordingly. On "failed", remember to restore the source balance.

      return res.status(200).json({ ok: true });
    } catch (error) {
      console.error(error);
      return res.status(500).json({ error: "server error" });
    }
  },
);

export default router;
