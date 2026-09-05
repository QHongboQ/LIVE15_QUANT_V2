# Ingress Boundary

## Responsibility

This Market Ingress child owns LIVE15 interpretation of provider facts. It is a sibling of Kalshi Gateway, Market Stream, and Reference Stream.

It owns:

- `Live15MarketScopeConfig` as the sole exact nine-asset asset/series authority;
- `MarketScopePort` / `MarketScopeBinding`;
- UTC 15-minute `MarketWindow` mechanics;
- interpretation of official bounded discovery supplied through `MarketDiscoveryPort`;
- fail-closed verification and verifier-issued `VerifiedMarketIdentity`;
- candidate/shadow diagnostics that can never authorize truth;
- `MarketIdentityResolver` and its output interface.

It does not own SDK transport, authentication, WebSocket reconnect/resubscribe, persistence, Data Truth, trading, or runtime lifecycle.

## Public interface

Callers import the stable LIVE15 semantic surface from:

`live15_quant_v2.data.market_ingress.ingress_boundary`

Ingress Boundary depends only on its narrow `MarketDiscoveryPort`, never on a concrete `KalshiGateway`. The Market Ingress parent composes the Gateway's provider capability with the Boundary's public resolver factory. The public parent composition always instantiates the sole `Live15MarketScopeConfig`; callers do not inject an alternate scope into that authoritative path.

## Provider DTO containment

`MarketDiscoveryPort` speaks the pinned SDK `kalshi.models.Market` DTO only at the provider-discovery seam. `OfficialMarketDiscovery` immediately translates that DTO into the LIVE15-owned `DiscoveredMarket` / `OfficialStrike` domain facts before verification. The SDK DTO is therefore a contained upstream adapter dependency, not LIVE15 market-identity authority and not a downstream public truth model.

## Scope authority

The approved universe is exactly BTC, ETH, GOLD, SILVER, XRP, SOL, HYPE, DOGE, and BNB. WTI is absent. The concrete series bindings were read-only verified against current official Kalshi Get Series data on 2026-09-04, each with `fifteen_min` frequency.

## Verification authority

A market is promoted to `VerifiedMarketIdentity` only through exact official-series, exact-window, structured-strike, and non-empty official identity checks. The verified identity carries verifier-issued provenance; a merely type-correct caller-constructed instance is not accepted by Market Stream.
