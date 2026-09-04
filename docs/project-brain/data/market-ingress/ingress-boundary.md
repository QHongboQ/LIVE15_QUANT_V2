# Ingress Boundary

## Responsibility

This Market Ingress child owns LIVE15 interpretation of provider facts. It is a sibling of Kalshi Gateway, Market Stream, and Reference Stream.

It owns:

- `Live15MarketScopeConfig` as the sole exact nine-asset asset/series authority;
- `MarketScopePort` / `MarketScopeBinding`;
- UTC 15-minute `MarketWindow` mechanics;
- official bounded discovery composition through `KalshiGateway`;
- fail-closed verification and `VerifiedMarketIdentity`;
- candidate/shadow diagnostics that can never authorize truth;
- `MarketIdentityResolver` and its output interface.

It does not own SDK transport, authentication, WebSocket reconnect/resubscribe, persistence, Data Truth, trading, or runtime lifecycle.

## Public interface

Callers import the stable LIVE15 semantic surface from:

`live15_quant_v2.data.market_ingress.ingress_boundary`

The provider gateway is injected into `OfficialMarketDiscovery`; therefore dependency flows one way from Ingress Boundary to Kalshi Gateway. Kalshi Gateway must never import this package.

## Scope authority

The approved universe is exactly BTC, ETH, GOLD, SILVER, XRP, SOL, HYPE, DOGE, and BNB. WTI is absent. The concrete series bindings were read-only verified against current official Kalshi Get Series data on 2026-09-04, each with `fifteen_min` frequency.
