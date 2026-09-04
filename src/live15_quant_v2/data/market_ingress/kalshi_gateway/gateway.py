"""Thin read-only boundary over installed kalshi-sdk public APIs."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, cast

from kalshi import AsyncKalshiClient, KalshiClient
from kalshi.models import Market
from kalshi.ws import KalshiWebSocket


class _MarketsResource(Protocol):
    def get(self, ticker: str) -> Market: ...

    def list_all(
        self,
        *,
        series_ticker: str,
        min_close_ts: int,
        max_close_ts: int,
    ) -> Iterable[Market]: ...


class _KalshiRestClient(Protocol):
    markets: _MarketsResource


class KalshiGateway:
    def __init__(self, client: _KalshiRestClient) -> None:
        self._client = client

    @classmethod
    def from_sdk(cls, client: KalshiClient) -> KalshiGateway:
        return cls(cast(_KalshiRestClient, client))

    def fetch_market(self, ticker: str) -> Market:
        return self._client.markets.get(ticker)

    def discover_markets(
        self,
        *,
        series_ticker: str,
        min_close_ts: int,
        max_close_ts: int,
    ) -> tuple[Market, ...]:
        return tuple(
            self._client.markets.list_all(
                series_ticker=series_ticker,
                min_close_ts=min_close_ts,
                max_close_ts=max_close_ts,
            )
        )

    @staticmethod
    def subscription_access(client: AsyncKalshiClient) -> KalshiWebSocket:
        return client.ws
