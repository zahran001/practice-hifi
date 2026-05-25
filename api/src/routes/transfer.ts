import { Router } from "express";
import type { Request, Response } from "express";
import { TransferRequestBody } from "@/types";
import { pool } from "@/db";
import { providerTransfer, providerEvents } from "@/provider";

const router = Router();

const VALID_CURRENCIES = ["usdc", "usdt", "pyusd"];

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

      /*
       * Research what the transaction flow should look like
       * Start with the HTTP request body — what comes in:
       * transactionId, sourceUserId, destinationUserId, sourceCurrency, sourceAmount, destinationCurrency
       * Then, determine what does the system add to support this flow: status (lifecycle statuses: received, transferred, failed), createdAt (audit trail)
       */

      /*
       * sourceAmount uses == null instead of !sourceAmount
       * !sourceAmount evaluates to true for null, undefined, AND 0.
       * Sending sourceAmount: 0 should fail with "must be > 0", not "field missing".
       */


      // TODO: validate sourceCurrency and destinationCurrency are supported values
      if(!VALID_CURRENCIES.includes(sourceCurrency)){
        return res.status(400).json({ error: "unsupported sourceCurrency" });
      }

      if(!VALID_CURRENCIES.includes(destinationCurrency)){
        return res.status(400).json({ error: "unsupported destinationCurrency" });
      }

      // TODO: validate sourceAmount is a positive number
      if(sourceAmount <= 0){
        return res.status(400).json({ error: "sourceAmount must be greater than 0" });
      }

      // TODO: check for a duplicate transactionId and return early (idempotency)

      // have to check if the transactionId exists in the transactions table
      // using pool.query() directly - parameterized query
      const result = await pool.query(
        "SELECT transactionid FROM transactions WHERE transactionid=$1", [transactionId]
      );

      if(result.rows.length !== 0){
        // idempotent - same input, same output
        return res.status(200).json({ok: true}); // already processed this
      }

      // TODO: verify sourceUserId and destinationUserId exist in the users table
      const check = await pool.query(
        "SELECT userid FROM users WHERE userid=ANY($1)", [[sourceUserId, destinationUserId]]
      );
      
      // return error when they're missing
      // one row for sourceUserId, one row for destinationUserId
      if(check.rows.length < 2){
        return res.status(404).json({error: "user not found"}); // 404 Not Found
      }

      // TODO: verify the source user has sufficient balance in sourceCurrency
      // we already know the specific sourceCurrency

      const getBalanceFromSourceUser = await pool.query(
        `SELECT ${sourceCurrency} FROM users WHERE userid=$1`, [sourceUserId]
      );
      
      // parse the response
      const balance = parseFloat(getBalanceFromSourceUser.rows[0][sourceCurrency])
      if(balance < sourceAmount){
        return res.status(400).json({error: "insufficient funds"}); // bad request
      }

      // TODO: deduct sourceAmount from the source user's balance
      //       and record the transaction — do this atomically

      /*
       * The deduction must happen inside the atomic BEGIN/COMMIT transaction (Step 5), not as a standalone query.
       * A plain pool.query() here has a race condition — two concurrent requests can both read the balance, both pass the check, and both deduct.
       * Recording means inserting a row into the transactions table to track that this transfer happened.
       */

      
      let client;

      try {
        client = await pool.connect();
        await client.query("BEGIN"); // why use await here before all the client.query usages

        // lock the row so no other request can read/write it until we commit
        const locked = await client.query(
          `SELECT ${sourceCurrency} FROM users WHERE userid=$1 FOR UPDATE`, [sourceUserId]
        );

        // RE-CHECK balance after lock (the pre-lock check above can race)
        const lockedBalance = parseFloat(locked.rows[0][sourceCurrency]);
        if(lockedBalance < sourceAmount){
          await client.query("ROLLBACK");
          return res.status(400).json({error: "insufficient funds"});
        }
        
        // deduct (negation)
        await client.query(
          `UPDATE users SET ${sourceCurrency} = ${sourceCurrency} - $1 WHERE userid = $2`, [sourceAmount, sourceUserId]
        );
        
        // record

        // The idempotency check earlier (SELECT transactionid FROM transactions) has a tiny race window:
        // two identical requests could both pass it at almost the same time before either has inserted a row.
        await client.query(
          `INSERT INTO transactions (transactionid, sourceuserid, destinationuserid, sourcecurrency, sourceamount, destinationcurrency, status)
          VALUES ($1, $2, $3, $4, $5, $6, 'received')
          ON CONFLICT DO NOTHING`,
          [transactionId, sourceUserId, destinationUserId, sourceCurrency, sourceAmount, destinationCurrency]
        );

        await client.query("COMMIT"); // permanent

        } catch (err) {
          if(client){
            await client.query("ROLLBACK");
          }
            
          throw err;
        } finally {
          if(client){
            client.release();
          }
        }

      // TODO: call providerTransfer(opts) to submit to the provider.
      //       Listen on providerEvents for "received", "transferred", and "failed"
      //       events keyed by transactionId, and update your transaction record
      //       accordingly. On "failed", remember to restore the source balance.

      // register listeners BEFORE calling providerTransfer to avoid a race
      
      // Listen for the transferred event ONE TIME
      providerEvents.once("transferred", async ({transactionId : tid}) => {
        // may have MANY transfers happening simultaneously - need to filter others
        if(tid !== transactionId) return;

        await pool.query(
          `UPDATE users SET ${destinationCurrency} = ${destinationCurrency} + $1 WHERE userid = $2`, 
          [sourceAmount, destinationUserId]
        );

        await pool.query(
          "UPDATE transactions SET status = 'transferred' WHERE transactionid = $1", [transactionId]
        );

        
      });

      providerEvents.once("failed", async ({transactionId: tid}) => {
        if(tid !== transactionId) return;

        // opposit of deduction - addition
        await pool.query(
          `UPDATE users SET ${sourceCurrency} = ${sourceCurrency} + $1 WHERE userid = $2`,
          [sourceAmount, sourceUserId]
        );

        await pool.query(
          "UPDATE transactions SET status = 'failed' WHERE transactionid = $1", [transactionId]
        );

      });


      providerTransfer({
        transactionId,
        sourceUserId,
        destinationUserId,
        sourceCurrency,
        sourceAmount,
        destinationCurrency,
      });
      
      return res.status(200).json({ ok: true });
    } catch (error) {
      console.error(error);
      return res.status(500).json({ error: "server error" });
    }
  },
);

export default router;
