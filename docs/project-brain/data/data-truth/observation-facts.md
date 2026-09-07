# Data Truth — Observation Facts

## Status and ownership

This child authority is a candidate pending independent review and merge. It
owns observation/state acceptance semantics only. It receives immutable shared
`CaptureFact` evidence through the Data Truth parent and produces a conceptual
append-only `TruthDecision`; it owns no event identity, storage, transport,
runtime, or public parent contract.

## V1 approved scope

The currently approved Observation Fact families are:

- OrderbookSnapshot
- OrderbookDelta
- Ticker
- MarketLifecycle
- EventFeeUpdate
- CFBenchmarksValue
- PythValue

A valid immutable CaptureFact in this scope may be accepted as the auditable
fact: **this provider reported this observation, state, or value for this
source.** This is useful provider-evidence truth without asserting a globally
unique logical business event.

Observations do not require a logical event identity. Equal values, similar
payloads, equal timestamps, or similar sequence/session metadata do not cause
event-style semantic duplicate collapse. Multiple observations may remain
multiple valid observations.

## Explicit non-claims

Observation acceptance does not claim global uniqueness, market completeness,
freshness, latest state, semantic ordering, correction relation, source
precedence, or world-state truth. Provider and received timestamps remain
preserved evidence, not a global time or watermark authority.

## Exclusions and removability

Observation Facts does not own Event Facts, logical event identity, event-style
semantic deduplication, database DEDUP, physical replay handling, watermarks,
late-data engines, completeness, storage, replay, Canonical Dataset shaping,
model/trading behavior, or canonical runtime activation.

It has no dependency on Event Facts. Removing it leaves Event Facts and every
sealed upstream authority unchanged; only parent routing/composition may
change.
