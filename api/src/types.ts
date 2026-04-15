export type UUID = string;

export type Currency = "usdc" | "usdt" | "pyusd";

export type TransferRequestBody = {
  transactionId: UUID;
  sourceUserId: UUID;
  destinationUserId: UUID;
  sourceCurrency: Currency;
  sourceAmount: number;
  destinationCurrency: Currency;
};
