from uuid import UUID, uuid4
from typing import TypedDict, List
from enum import Enum


class Currency(Enum):
    usdc = "usdc"
    usdt = "usdt"
    pyusd = "pyusd"


class TransferRequestBody(TypedDict):
    transactionId: UUID
    sourceUserId: UUID
    destinationUserId: UUID
    sourceCurrency: Currency
    sourceAmount: float
    destinationCurrency: Currency


transfer_requests = [
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "sourceCurrency": Currency.usdc,
        "sourceAmount": 10.0,
        "destinationCurrency": Currency.usdt,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "sourceCurrency": Currency.usdt,
        "sourceAmount": 25.5,
        "destinationCurrency": Currency.pyusd,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "sourceCurrency": Currency.pyusd,
        "sourceAmount": 3.25,
        "destinationCurrency": Currency.usdc,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa4"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "sourceCurrency": Currency.usdc,
        "sourceAmount": 999.99,
        "destinationCurrency": Currency.usdt,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa5"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "sourceCurrency": Currency.usdt,
        "sourceAmount": 0.01,
        "destinationCurrency": Currency.pyusd,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa6"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "sourceCurrency": Currency.pyusd,
        "sourceAmount": 150.0,
        "destinationCurrency": Currency.usdc,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa7"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "sourceCurrency": Currency.usdc,
        "sourceAmount": 1.0,
        "destinationCurrency": Currency.pyusd,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa8"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "sourceCurrency": Currency.usdt,
        "sourceAmount": 5000.0,
        "destinationCurrency": Currency.usdc,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa9"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "sourceCurrency": Currency.pyusd,
        "sourceAmount": 42.42,
        "destinationCurrency": Currency.usdt,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa10"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "sourceCurrency": Currency.usdc,
        "sourceAmount": 7.77,
        "destinationCurrency": Currency.usdt,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa11"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000099"),
        "sourceCurrency": Currency.usdc,
        "sourceAmount": 12.0,
        "destinationCurrency": Currency.usdt,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa12"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000099"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "sourceCurrency": Currency.usdt,
        "sourceAmount": 8.0,
        "destinationCurrency": Currency.pyusd,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa13"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "sourceCurrency": "eur",
        "sourceAmount": 10.0,
        "destinationCurrency": Currency.usdc,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa14"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "sourceCurrency": Currency.pyusd,
        "sourceAmount": 10.0,
        "destinationCurrency": "btc",
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa15"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "sourceCurrency": Currency.usdc,
        "sourceAmount": -5.0,
        "destinationCurrency": Currency.usdt,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa16"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "sourceCurrency": Currency.usdt,
        "sourceAmount": -0.01,
        "destinationCurrency": Currency.pyusd,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa17"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "sourceCurrency": Currency.pyusd,
        "sourceAmount": 0.0,
        "destinationCurrency": Currency.usdc,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa18"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "sourceCurrency": Currency.usdc,
        "sourceAmount": 1000000.0,
        "destinationCurrency": Currency.usdt,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa19"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "sourceCurrency": Currency.usdt,
        "sourceAmount": 250000.75,
        "destinationCurrency": Currency.pyusd,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa20"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "sourceCurrency": Currency.pyusd,
        "sourceAmount": 0.0001,
        "destinationCurrency": Currency.usdc,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa21"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "sourceCurrency": Currency.usdc,
        "sourceAmount": 63.0,
        "destinationCurrency": Currency.usdt,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa22"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "sourceCurrency": Currency.usdt,
        "sourceAmount": 88.88,
        "destinationCurrency": Currency.usdc,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa23"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "sourceCurrency": Currency.pyusd,
        "sourceAmount": 17.0,
        "destinationCurrency": Currency.usdt,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa24"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "sourceCurrency": Currency.usdc,
        "sourceAmount": 2.5,
        "destinationCurrency": Currency.pyusd,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa25"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "sourceCurrency": Currency.usdt,
        "sourceAmount": 31.25,
        "destinationCurrency": Currency.pyusd,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa05"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "sourceCurrency": Currency.usdt,
        "sourceAmount": 0.01,
        "destinationCurrency": Currency.pyusd,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa11"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000099"),
        "sourceCurrency": Currency.usdc,
        "sourceAmount": 12.0,
        "destinationCurrency": Currency.usdt,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa15"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000002"),
        "sourceCurrency": Currency.usdc,
        "sourceAmount": -5.0,
        "destinationCurrency": Currency.usdt,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa26"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000098"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000097"),
        "sourceCurrency": Currency.usdc,
        "sourceAmount": 55.0,
        "destinationCurrency": Currency.usdt,
    },
    {
        "transactionId": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaa03"),
        "sourceUserId": UUID("00000000-0000-0000-0000-000000000003"),
        "destinationUserId": UUID("00000000-0000-0000-0000-000000000001"),
        "sourceCurrency": Currency.pyusd,
        "sourceAmount": 3.25,
        "destinationCurrency": Currency.usdc,
    },
]
