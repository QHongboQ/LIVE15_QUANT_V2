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
  Gold/Silver `pyth_value`, but complete native `pyth_value` helper support is
  not available in the pinned SDK and remains a separate ingress gap.
- Do not reintroduce direct Pyth, Coinbase, Binance, or Hyperliquid clients at
  this stage.
- Engineering Foundation is complete.
- Market Ingress child #1 Kalshi Gateway is complete and owns provider access only.
- Market Ingress child #4 Ingress Boundary is complete and owns LIVE15 market identity semantics and the concrete immutable nine-asset scope.
- Kalshi Gateway and Ingress Boundary are physical sibling packages with one-way dependency `Ingress Boundary -> Kalshi Gateway`; they must not share one implementation subtree.
- Market Stream and Reference Stream have not started. Storage, Data Truth, Replay, Dataset, Model, Trading, and Operations implementation have not begun.

Next approved implementation target after the sibling-separation closeout and review: Market Stream, unless user priority changes.
