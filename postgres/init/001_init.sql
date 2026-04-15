CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- TODO (candidate): create any additional tables you need here.
--
-- The transfer provider emits the following lifecycle statuses for each transaction:
--   received    – provider has acknowledged the request
--   transferred – provider completed the transfer successfully
--   failed      – provider could not complete the transfer

CREATE TABLE IF NOT EXISTS users (
  userid UUID PRIMARY KEY,
  username VARCHAR(50) UNIQUE,
  usdc NUMERIC(20,8) NOT NULL DEFAULT 0,
  usdt NUMERIC(20,8) NOT NULL DEFAULT 0,
  pyusd NUMERIC(20,8) NOT NULL DEFAULT 0
);

INSERT INTO users (userid, username, usdc, usdt, pyusd)
VALUES
(
  '00000000-0000-0000-0000-000000000001',
  'Alice', 
  100.00000000, 
  50.00000000, 
  25.00000000
),
(
  '00000000-0000-0000-0000-000000000002',
  'Bob', 
  10.50000000, 
  0.00000000, 
  5.25000000
),
(
  '00000000-0000-0000-0000-000000000003',
  'Carol', 
  0.00000000, 
  75.00000000, 
  12.00000000
);
