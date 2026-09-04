# Kalshi Gateway

## Responsibility

This Market Ingress child owns bounded official Kalshi market discovery and
fail-closed market identity verification. It has no storage or trading side
effects.

## Public interface

Callers may import `KalshiGateway`, `MarketScopePort`, `MarketScopeBinding`,
`MarketWindow`, `MarketIdentityResolver`, `MarketIdentityResolution`, and
`VerifiedMarketIdentity` from `live15_quant_v2.data.market_ingress.kalshi_gateway`.

## Composition flow

`MarketScopePort -> MarketWindow -> Candidate heuristic -> official bounded
series discovery -> verification -> shadow result`. Candidate/shadow results
are diagnostic only; `verification.verified` and its `VerifiedMarketIdentity`
are authoritative.

## How to use

```python
from kalshi import KalshiClient
from live15_quant_v2.data.market_ingress.kalshi_gateway import KalshiGateway, MarketIdentityResolver
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.candidate import CandidateTickerPredictor
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.discovery import OfficialMarketDiscovery
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.shadow import ShadowValidator
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.verification import OfficialMarketVerifier
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.window import current

client = KalshiClient()  # caller owns and closes this SDK client
resolver = MarketIdentityResolver(scope, CandidateTickerPredictor(), OfficialMarketDiscovery(KalshiGateway.from_sdk(client)), OfficialMarketVerifier(), ShadowValidator())
resolution = resolver.resolve(asset_id, current(now))
if resolution.verification.verified:
    identity = resolution.verification.identity
client.close()
```

Official discovery uses documented `series_ticker`, `min_close_ts`, and
`max_close_ts` with no status filter; its query provenance is compared to the
expected binding. Ticker strings are not used as series-membership truth.

## Next extension

A future concrete `MarketScopeConfig` implements `MarketScopePort` and owns
`asset_id <-> approved series_ticker` exactly once. Adding the nine-asset map
must not edit gateway, windows, candidate, discovery, verification, or shadow.