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
- Engineering Foundation = COMPLETE.
- Market Ingress is FINAL CLOSED; its authoritative child details are owned
  under `docs/project-brain/data/market-ingress/`.
- Storage Shared `CaptureFact` Contract = FINAL CLOSED. Hot Store = FINAL
  CLOSED under that contract: a provider-neutral interface and QuestDB adapter
  with explicit 500-row write batches and sealed native physical
  transport-idempotency using `WAL DEDUP UPSERT KEYS(received_timestamp,
  capture_id)` for new tables. Capture Boundary = FINAL CLOSED.
- QuestDB Runtime Platform = FINAL CLOSED. The canonical official QuestDB
  `10.0.1` runtime is operational; independent review, PR #20, hosted CI,
  merge, post-merge CI, and final local seal passed.
- Data Truth contract authority, implementation-plan authority, and engineering
  implementation are FINAL CLOSED. Slice 1 is FINAL CLOSED; the QuestDB
  reconciliation POC gate is FINAL CLOSED / PASS / ACCEPTED; and Slice 2
  Persistent History is FINAL CLOSED following PR #38 merge
  `abc4bdbd52150ab33ec60c0c6902235042d199f6`. The implemented persistent
  TruthDecision history is limited to the approved single-writer constraint;
  concurrent `decide()` and multi-process/multi-writer authority are not
  supported. Canonical TruthDecision-table creation and canonical runtime
  activation remain NOT AUTHORIZED / NOT PERFORMED. Replay & As-Of contract
  authority is a DRAFT CANDIDATE pending independent review; its implementation
  is NOT IMPLEMENTED. Canonical Dataset, Model, Trading, and broad Operations
  functionality remain unimplemented.

Durable Persistence contract authority = FINAL CLOSED. Durable Persistence
implementation = FINAL CLOSED. Its code, contract, tests, and failure-mode
acceptance are sealed; canonical table materialization, canonical DEDUP runtime
activation, and SF activation remain separate unauthorized runtime actions.

Current NEXT: **Data System → Replay & As-Of contract independent review**.
The candidate contract defines a strict two-dimensional As-Of authority but
does not authorize Replay implementation, runtime deployment, Canonical
Dataset work, Model/training work, or Trading work. After contract closure, the
next gate is Replay & As-Of implementation-plan / availability-mechanism fit
preparation only; code remains unauthorized. Canonical runtime activation
remains unauthorized.
