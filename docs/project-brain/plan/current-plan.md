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
  authority = FINAL CLOSED following PR #40 normal merge
  `528815ef2883b3757515b9b9d8e3dcadc92981b6`. Its snapshot-membership POC
  gate is FINAL CLOSED / `PASS_WITH_FAIL_CLOSED_DRIFT` following PR #42 normal
  merge `b76d10b0bc480a7f84a0cd6e97dd896a2f24d124`.
  Availability-mechanism fit preparation is COMPLETED. Replay implementation
  plan authority is FINAL CLOSED following PR #44 normal merge
  `13af6e1cea4c087c547bfc9f6a25311ab6690b6b`. Slice 1 Pure Replay Core is
  FINAL CLOSED following PR #46 normal merge
  `62f8c2f672ca3627d9690727ff47b80d805266d5`. Slice 2 Availability Support is
  FINAL CLOSED following PR #48 normal merge
  `a78b731a8c24879b0da41ec4d6f28bb43ebe2daf`. Slice 3 QuestDB Replay Source is
  FINAL CLOSED following PR #50 normal merge
  `4a1809d72aa0451cf357a3845451da294ea33a5a`. Slice 4 Recorder Composition and
  overall Replay & As-Of engineering implementation are FINAL CLOSED following
  PR #52 normal merge `306924cae59dc5a2ec9f5737e7c4103a0c5e7227`. Production
  Recorder deployment, canonical availability activation, and canonical Replay
  activation remain NOT AUTHORIZED / NOT PERFORMED. Canonical Dataset contract
  authority is FINAL CLOSED; its implementation-plan design is CURRENT NEXT /
  NOT STARTED, while implementation remains NOT AUTHORIZED. Model, Trading,
  and broad Operations functionality remain unimplemented.

Durable Persistence contract authority = FINAL CLOSED. Durable Persistence
implementation = FINAL CLOSED. Its code, contract, tests, and failure-mode
acceptance are sealed; canonical table materialization, canonical DEDUP runtime
activation, and SF activation remain separate unauthorized runtime actions.

Current NEXT: **Data System → Canonical Dataset → Implementation-plan design**.
`REPLAY_AS_OF_ENGINEERING_IMPLEMENTATION = FINAL CLOSED` at merge
`306924cae59dc5a2ec9f5737e7c4103a0c5e7227`.
`CANONICAL_DATASET_CONTRACT = FINAL CLOSED` at merge
`3d61a4d8dac4a35c91dec314b5eaeb2098878a6d`.
`CANONICAL_DATASET_IMPLEMENTATION_PLAN = CURRENT NEXT / NOT STARTED`.
`SAFE_TO_BEGIN_CANONICAL_DATASET_IMPLEMENTATION_PLAN_DESIGN = YES`.
`CANONICAL_DATASET_IMPLEMENTATION = NOT IMPLEMENTED / NOT AUTHORIZED`.
`CANONICAL_DATASET_PHYSICAL_MATERIALIZATION = NOT AUTHORIZED / NOT PERFORMED`.

The bounded next task is implementation-plan design only. It may plan a future
implementation against the FINAL CLOSED contract, but does not authorize
Canonical Dataset source implementation, a physical backend or format,
materialization, canonical Replay/runtime activation, Model/training, or
Trading.

`LOCAL_REPLAY_TEST_HYGIENE = PASS_WITH_HYGIENE`.
`EMPTY_TASK_PYTEST_BASE_RESIDUES = 2`.
`RUNTIME_CORRECTNESS_BLOCKER = NO`.
`ACL_REPAIR_AUTHORIZED = NO`.

Canonical physical materialization, canonical availability/TruthDecision/Replay
activation, production Recorder deployment, configuration/runtime changes, and
production `CLOCK_SAFETY` closure remain NOT AUTHORIZED / NOT PERFORMED.
`LAST_MARKER_FLOOR_ALONE_INSUFFICIENT` remains preserved; the canonical
`CLOCK_SAFETY` operational gate is NOT AUTHORIZED / NOT CLOSED.
