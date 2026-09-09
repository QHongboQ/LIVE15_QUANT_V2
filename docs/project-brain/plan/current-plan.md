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
  `62f8c2f672ca3627d9690727ff47b80d805266d5`; overall Replay implementation is
  IN PROGRESS. Slice 2 Availability Support, Slice 3 QuestDB Replay Source,
  Slice 4 Recorder Composition, availability production implementation, and
  recorder production composition remain NOT IMPLEMENTED; canonical activation
  remains NOT AUTHORIZED. Canonical Dataset, Model, Trading, and broad
  Operations functionality remain unimplemented.

Durable Persistence contract authority = FINAL CLOSED. Durable Persistence
implementation = FINAL CLOSED. Its code, contract, tests, and failure-mode
acceptance are sealed; canonical table materialization, canonical DEDUP runtime
activation, and SF activation remain separate unauthorized runtime actions.

Current NEXT: **Data System → Replay & As-Of → Slice 2 — Availability Support
implementation**. `SLICE_1_PURE_REPLAY_CORE = FINAL CLOSED` at merge
`62f8c2f672ca3627d9690727ff47b80d805266d5`.
`SAFE_TO_BEGIN_REPLAY_AS_OF_SLICE_2_IMPLEMENTATION = YES` because the Slice 1
prerequisite plus Replay contract and implementation-plan authorities are
closed. Slice 2 still requires its own separately reviewed implementation task.

Slice 2 owns `AvailabilityKind` / `AvailabilityRecord`, semantic availability
keys, a provider-neutral recording port (`find`, `read_committed_floor`, and
`append`), conservative post-proof timing, process-lifetime monotonic wall
projection, committed-floor startup behavior, one ordered writer, append-only
semantics, definite-prepublication failure, `IN_DOUBT`,
`INVARIANT_CONFLICT`, exact-key reconciliation, no blind reappend, a disposable
QuestDB availability adapter, and `CLOCK_SAFETY` acceptance. Its planned
production files are `src/live15_quant_v2/data/replay_as_of/availability.py`
and `src/live15_quant_v2/data/replay_as_of/questdb_availability.py`; its
planned tests are `tests/test_replay_as_of_availability.py` and
`tests/test_questdb_replay_as_of_availability_integration.py`.

`LAST_MARKER_FLOOR_ALONE_INSUFFICIENT` remains preserved. Slice 2 must prove
post-trigger proof sampling, in-process rollback safety and monotonic
projection, committed-floor startup and strict advancement or fail-closed
behavior, restart below the committed floor, non-decreasing timestamps, no
backdating, and no claim of arbitrary distributed clock correctness.

Slice 2 excludes `questdb_source.py`, `recorder_composition.py`, canonical
availability-table or runtime activation, Slices 3–4, Canonical Dataset,
Model/training, and Trading.
