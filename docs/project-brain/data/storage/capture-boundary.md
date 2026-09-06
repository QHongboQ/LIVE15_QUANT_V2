# Capture Boundary

## Status

Capture Boundary = FINAL CLOSED.

## Closure evidence

- Implementation candidate: `713d9afefef0d6001c6c3e5c1f8ca2c06a17c1ea`
- Review fix: `914084164f8e617e5c578dd6ccf73101fbee3312`
- PR #16 merged as `2d00ad1fcc13456e801e9335c5ccc3c10a7399c1`
- Final independent re-review, PR Windows / Ubuntu / CI Gate, and post-merge
  Windows / Ubuntu / CI Gate passed.
- Local Ruff, pytest (84 passed, 1 expected live-QuestDB skip), MyPy, and
  `git diff --check` passed on local main equal to `origin/main` at the merge
  SHA. The merged feature branch was removed, no task residue remained, and
  QuestDB was not started.

## Responsibility

Capture Boundary synchronously accepts one approved typed Market Ingress
data-plane message, samples a received timestamp, freezes it through Pydantic
`model_dump_json()`, applies the minimal LIVE15 capture semantics, and returns
one immutable shared `CaptureFact`.

It accepts verifier-issued `VerifiedMarketIdentity` for prediction-market data
and resolves reference data only through `Live15ReferenceScopeConfig`. It owns
no second ticker, event, or reference mapping table.

## Inputs and output

Prediction-market data-plane inputs are exact SDK types:

- `OrderbookSnapshotMessage` and `OrderbookDeltaMessage`
- `TickerMessage` and `TradeMessage`
- `MarketLifecycleMessage` and `EventFeeUpdateMessage`

Reference data-plane inputs are `CFBenchmarksValueMessage` and the isolated
typed `PythValueMessage` compatibility contract. The output is always a shared
`CaptureFact`; no Hot Store write occurs here.

`CFBenchmarksIndexListMessage` and `PythUnderlyingListMessage` are
control-plane responses and fail closed. Unknown types, subclasses, invalid
authority, source mismatches, and incompatible discriminators also fail closed.

## Mechanics and policy

Upstream-owned mechanics are `kalshi-sdk` typed models and Pydantic
`model_dump_json()` serialization. Python standard-library `time.time_ns`,
`uuid.uuid4`, and exact integer datetime arithmetic provide the default clock,
identifier, and legacy-delta timestamp mechanics. Clock and identifier factory
are injectable for deterministic tests.

LIVE15 policy persists provider `kalshi`, schema `market-ingress/v1`, exact
subscription-family channels, exact top-level message discriminators, nullable
provider timestamps, and `event_subtype` only for market lifecycle events. The
payload is opaque UTF-8 JSON text frozen synchronously before this boundary
returns; it is not parsed, normalized, or canonicalized here.

## Non-responsibilities

This leaf has no I/O, async runtime, queue, retry, WAL, network, database, Hot
Store integration, reconnect, persistence, Data Truth, gap or freshness policy,
replay, archive, retention, quarantine, model, or training behavior. Capture
Boundary is not a Recorder.
