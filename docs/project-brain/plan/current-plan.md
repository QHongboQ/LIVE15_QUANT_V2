# Current V2 Plan

This document records only approved V2 direction. It is not a V1 roadmap.

- V2 is a clean rebuild; V1 is frozen legacy/reference material, not a future runtime.
- The exact V2 asset universe is BTC, ETH, Gold, Silver, XRP, SOL, HYPE, DOGE, and BNB. WTI does not exist: no compatibility, skip, tombstone, or retired-WTI behavior.
- Initial external market-data direction is Kalshi-only: Kalshi prediction-market data; CF Benchmarks for BTC/ETH/XRP/SOL/HYPE/DOGE/BNB; Kalshi-hosted `pyth_value` for Gold/Silver.
- The current upstream `kalshi-sdk` supports CF Benchmarks natively. Kalshi exposes Gold/Silver `pyth_value`, but the current upstream SDK lacks complete native `pyth_value` helper support.
- Do not reintroduce direct Pyth, Coinbase, Binance, or Hyperliquid clients at this stage.
- The development foundation is Python 3.12, uv, a project-local `.venv`, `kalshi-sdk`, pytest, ruff, mypy, and the complete current `mattpocock/skills` set. Business implementation has not started.
- The modular CI Router foundation now exists: declarative scope discovery, dependency-aware routing, one `foundation` leaf, and a thin GitHub Actions orchestrator with a stable CI Gate.

Next: continue blueprint/foundation discussion after foundation review, before implementing the first business module. No later phases are approved here.
