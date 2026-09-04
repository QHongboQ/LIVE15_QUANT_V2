# Current V2 Plan

This document records only approved V2 direction. It is not a V1 roadmap.

- V2 is a clean rebuild; V1 is frozen legacy/reference material, not a runtime.
- The exact V2 asset universe is BTC, ETH, Gold, Silver, XRP, SOL, HYPE, DOGE,
  and BNB. WTI does not exist.
- Initial external market-data direction is Kalshi-only. Do not reintroduce
  direct Pyth, Coinbase, Binance, or Hyperliquid clients at this stage.
- Engineering Foundation is complete. Data System implementation has started
  with Data System -> Market Ingress -> Kalshi Gateway framework in PR #4.
- PR #4 deliberately does not contain the concrete nine-asset Market Scope
  Config. Storage, Data Truth, Replay, Dataset, Model, Trading, and Operations
  implementation have not begun from this task.

Next approved implementation step after PR #4 review and merge authorization:
Concrete LIVE15 Market Scope Config.