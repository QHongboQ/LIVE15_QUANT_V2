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
- Data Truth contract authority = FINAL CLOSED. Implementation-plan authority
  = FINAL CLOSED. Overall implementation remains NOT IMPLEMENTED. The Slice 1
  semantic library is FINAL CLOSED after PR #33 merge
  `f80c786307fe5e2c2092a0f2955f62ca03c9c7bb`, merge-SHA hosted CI PASS, and
  final local seal PASS. It provides no persistent TruthDecision authority.
  QuestDB TruthDecision-history persistence/reconciliation fit is PROVEN under
  the approved single-writer constraint: POC PR #36 merged as
  `249144de204247bd7a0589d8ba67116c48b8dcc7`, its ChatGPT remote review PASS,
  merge-SHA hosted CI PASS, and merge-SHA local opt-in POC A-L PASS (12
  passed). The POC gate is FINAL CLOSED / PASS / accepted. Persistent
  TruthDecision authority remains NOT IMPLEMENTED; Slice 2 remains NOT
  AUTHORIZED. Replay & As-Of, Canonical Dataset, Model, Trading, and broad
  Operations functionality remain unimplemented. Canonical runtime activation
  remains unauthorized.

Durable Persistence contract authority = FINAL CLOSED. Durable Persistence
implementation = FINAL CLOSED. Its code, contract, tests, and failure-mode
acceptance are sealed; canonical table materialization, canonical DEDUP runtime
activation, and SF activation remain separate unauthorized runtime actions.

Current NEXT: **Data System → Data Truth Slice 2 authorization preparation**.
Slice 1 and the QuestDB reconciliation POC gate are FINAL CLOSED. Overall Data
Truth implementation and persistent TruthDecision authority remain NOT
IMPLEMENTED. Slice 2 remains NOT AUTHORIZED. Replay & As-Of and Canonical
Dataset remain unimplemented; canonical runtime activation remains unauthorized.
