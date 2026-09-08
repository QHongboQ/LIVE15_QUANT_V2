# Data Truth — Event Facts

## Status and ownership

**Contract authority:** FINAL CLOSED.

**Implementation:** NOT IMPLEMENTED.

This child owns event-specific semantic adjudication only. It receives immutable
shared `CaptureFact` evidence through the Data Truth parent and produces a
conceptual append-only `TruthDecision`; it owns no storage, transport, runtime,
or public parent contract.

## V1 approved scope

Trade is the only currently approved Event Fact family. Its logical identity is
provider-scoped:

```text
provider + source_id + message_type + provider-owned trade_id
```

The provider-owned `trade_id` is read as evidence from the sealed frozen trade
payload. The resulting identity is not global across providers, sources, or
message families.

This child may classify an approved event identity as accepted, duplicate, or
conflicting when the same approved identity has incompatible immutable
evidence. Adjudication must be deterministic under an approved policy version.

## Fail-closed identity boundary

Missing or invalid explicit event identity is not repaired. This child must
fail closed rather than synthesize a fallback from `capture_id`, either
timestamp, payload hashing, database order, sequence/session metadata, or any
other convenient physical property.

Hot Store physical replay idempotency remains separate. It collapses exact
transport replay by `(received_timestamp, capture_id)` and does not decide
logical event duplication.

## Exclusions

Event Facts does not own Observation Facts, database DEDUP, transport replay,
global event time, watermarks, late-data mechanics, semantic completeness,
source precedence, correction/supersession semantics, storage, replay, Canonical
Dataset shaping, model/trading behavior, or canonical runtime activation.

It has no dependency on Observation Facts. Removing it leaves Observation Facts
and every sealed upstream authority unchanged; only parent routing/composition
may change.
