"""Thin read-only boundary over the installed Kalshi Python SDK."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, cast

from kalshi import AsyncKalshiClient, KalshiClient
from kalshi.models import Market


class _MarketsResource(Protocol):
    def get(self, ticker: str) -> Market: ...

    def list_all(self, *, series_ticker: str, **kwargs: object) -> Iterable[Market]: ...


class _KalshiRestClient(Protocol):
    markets: _MarketsResource


class KalshiGateway:
    """Expose only V2's current read-only Kalshi market seams.

    Transport, authentication, pagination, WebSocket lifecycle, subscriptions,
    SID routing, reconnect, and resubscribe remain owned by ``kalshi-sdk``.
    """

    def __init__(self, client: _KalshiRestClient) -> None:
        self._client = client

    @classmethod
    def from_sdk(cls, client: KalshiClient) -> KalshiGateway:
        """Bind a real public ``KalshiClient`` without recreating its transport."""
        return cls(cast(_KalshiRestClient, client))

    def fetch_market(self, ticker: str) -> Market:
        """Fetch one official market through ``KalshiClient.markets.get``."""
        return self._client.markets.get(ticker)

    def discover_markets(self, series_ticker: str) -> tuple[Market, ...]:
        """Use SDK-owned pagination for an exact series-ticker discovery."""
        return tuple(self._client.markets.list_all(series_ticker=series_ticker))

    @staticmethod
    def subscription_access(client: AsyncKalshiClient) -> object:
        """Return the SDK's future subscription surface; do not implement it here."""
        return client.ws