# Current V2 Plan

This document records only approved V2 direction. It is not a V1 roadmap.

- V2 is a clean rebuild; V1 is frozen legacy/reference material, not a runtime.
- The exact V2 asset universe is BTC, ETH, GOLD, SILVER, XRP, SOL, HYPE, DOGE,
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
- Market Ingress is complete and hardened; its authoritative child details are
  owned under `docs/project-brain/data/market-ingress/`.
- Storage owns the shared `CaptureFact` contract and has begun only its Hot
  Store leaf: a provider-neutral interface and QuestDB adapter with explicit
  500-row write batches. Capture Boundary and all other Storage responsibilities
  remain unimplemented.
- Data Truth, Replay, Dataset, Model, Trading, and Operations implementation have
  not begun.

Next implementation stage: independent review of the bounded shared Storage
capture-contract migration before any Capture Boundary implementation.
