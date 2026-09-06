"""Canonical LIVE15 Data System asset identifiers."""

from enum import StrEnum


class AssetId(StrEnum):
    """The exact durable LIVE15 asset universe."""

    BTC = "BTC"
    ETH = "ETH"
    GOLD = "GOLD"
    SILVER = "SILVER"
    XRP = "XRP"
    SOL = "SOL"
    HYPE = "HYPE"
    DOGE = "DOGE"
    BNB = "BNB"
