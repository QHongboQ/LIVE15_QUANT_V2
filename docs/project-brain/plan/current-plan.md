# Current V2 Plan

This document records only approved V2 direction. It is not a V1 roadmap.

- V2 is a clean rebuild; V1 is frozen legacy/reference material, not a runtime.
- The exact V2 asset universe is BTC, ETH, Gold, Silver, XRP, SOL, HYPE, DOGE,
  and BNB. WTI does not exist.
- Initial external market-data direction is Kalshi-only:
  - Kalshi prediction-market data;
  - Kalshi-hosted CF Benchmarks for BTC, ETH, XRP, SOL, HYPE, DOGE, and BNB;
  - Kalshi-hosted `pyth_value` for Gold and Silver.
- The pinned `kalshi-sdk==13.0.0` supports CF Benchmarks natively. Kalshi exposes
  Gold/Silver `pyth_value`, but the pinned SDK lacks a native typed `pyth_value`
  helper. LIVE15 bridges that upstream SDK gap through its isolated,
  version-guarded compatibility leaf; direct Pyth/Hermes is not used.
- Do not reintroduce direct Pyth, Coinbase, Binance, or Hyperliquid clients at
  this stage.
- Engineering Foundation is complete.
- Market Ingress is complete: Kalshi Gateway, Ingress Boundary, Market Stream,
  and Reference Stream are complete; Reference Stream is merged.
- Kalshi Gateway and Ingress Boundary are physical sibling packages with no direct sibling dependency. The Market Ingress parent composes the Gateway's provider capability with the Boundary's public semantic interface; they do not share one implementation subtree.
- Market Ingress currently has four responsibilities: Kalshi Gateway exposes
  provider capability from `kalshi-sdk`; Ingress Boundary turns provider
  discovery capability into `VerifiedMarketIdentity`; Market Stream turns
  verified identities plus SDK streaming capability into typed SDK async
  iterators; and Reference Stream selects the fixed nine-asset Kalshi-hosted CF/Pyth scope into typed SDK iterators. Storage, Data Truth, Replay,
  Dataset, Model, Trading, and Operations implementation have not begun.

Next implementation stage: Storage. Storage requires separate explicit user
authorization; this closeout cleanup does not begin Storage.
