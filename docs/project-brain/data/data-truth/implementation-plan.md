# Data Truth Implementation Plan

## Status

**Contract authority:** FINAL CLOSED.

**Implementation-plan authority:** FINAL CLOSED.

**Implementation:** NOT IMPLEMENTED. Slice 1 is FINAL CLOSED. The required
QuestDB TruthDecision-history reconciliation POC is FINAL CLOSED, PASS /
ACCEPTED. Slice 2 remains NOT AUTHORIZED and requires separate explicit
authorization.

Replay & As-Of, Canonical Dataset, Model, and Trading remain UNIMPLEMENTED.
Canonical runtime activation remains UNAUTHORIZED. This plan creates neither
source, tests, schema, table, runtime process, database, dependency, nor
canonical activation.

## Scope and shape

The implementation goal is:

```text
immutable CaptureFact
→ deterministic Data Truth adjudication
→ persistent append-only TruthDecision authority
```

The sealed `CaptureFact` is sufficient and unchanged. `capture_id` is immutable
evidence identity, not logical Trade identity; the frozen Trade payload retains
the provider-owned `trade_id`. No new semantic child is created. The semantic
tree remains exactly Event Facts and Observation Facts. Models, the history
seam, composition, and the QuestDB adapter are implementation-support
mechanics, not semantic children.

## TruthDecision and identity

The minimum immutable implementation model is:

- `subject_capture_id`;
- decision category: `ACCEPTED`, `DUPLICATE`, `CONFLICT`, or `NOT_ACCEPTED`;
- policy version;
- immutable contributing CaptureFact-reference tuple;
- bounded reason code; and
- optional EventIdentity.

EventIdentity is exactly:

```text
(provider, source_id, message_type, trade_id)
```

`subject_capture_id` identifies the CaptureFact being adjudicated; it is not
logical event identity. SubjectDecisionKey is exactly
`(policy_version, subject_capture_id)` and supports audit, already-decided
lookup, retry reconciliation, and in-doubt handling. This is an implementation
clarification within the sealed immutable-reference contract, not a contract
reopening.

## Semantic decisions

Observation Facts is stateless. One shared policy covers OrderbookSnapshot,
OrderbookDelta, Ticker, MarketLifecycle, EventFeeUpdate, CFBenchmarksValue,
and PythValue. A valid fact means only that its provider reported that
observation, state, or value for that source. These seven approved families
already carry sufficient provider/source/message evidence through the sealed
CaptureFact contract for this provider-observation meaning; no CaptureFact
field is requested. There is no observation semantic deduplication,
latest-state machinery, watermark, completeness assertion, source precedence,
or correction chain.

Event Facts remains Trade only. Its identity has no fallback from capture ID,
timestamps, `sid`, `seq`, payload hash, database order, or WAL order.

For the current supported Trade, the V1 compatibility rule is exact:

1. Parse the frozen payload with pinned `kalshi-sdk==13.0.0` `TradeMessage`.
2. Require `market-ingress/v1`, provider `kalshi`, Trade message type, and
   provider/source/message/trade identity consistency.
3. Canonicalize through the typed JSON-mode representation and structurally
   compare provider semantic `msg` content.
4. Exclude `trade_id` and `market_ticker` from that projection because they are
   separately validated identity fields.

`capture_id`, `received_timestamp`, `sid`, `seq`, outer
`provider_timestamp`, database/WAL order, and raw JSON formatting are excluded
from compatibility. Provider-semantic `msg.ts` and `msg.ts_ms` remain evidence.

A new valid EventIdentity is `ACCEPTED`; an equal projection is `DUPLICATE`;
and a different valid projection is `CONFLICT`. Invalid evidence is
`NOT_ACCEPTED` with only `INVALID_TRADE_EVIDENCE`,
`TRADE_IDENTITY_MISMATCH`, or `UNSUPPORTED_TRADE_SCHEMA` as V1 Trade reasons.
An existing SubjectDecisionKey returns or reconciles its exact decision.

## History and authoritative return

Event Facts receives a resolved EventAnchor containing EventIdentity, the
accepted TruthDecision reference/value, and its immutable accepted
CaptureFact. It does not depend directly on QuestDB, SQL, HotStore adapters,
or table names.

The provider-neutral history seam has exactly three methods:

```text
find_subject_decision(policy_version, capture_id)
find_accepted_event(event_identity)
append(decision)
```

There is no generic CRUD, update, delete, arbitrary query layer, repository
framework, or public evidence-resolver interface. A concrete history adapter
internally composes the sealed provider-neutral
`HotStore.read_capture(capture_id)` to resolve accepted evidence.

Initial authority permits one ordered DataTruth writer for one
TruthDecisionHistory. Concurrent `decide()` and multi-process writers are not
supported. This is an API, composition, and deployment precondition; no
distributed lock, lease, Kafka, consensus, scheduler, daemon, or new service
is authorized.

The parent remains conceptually:

```text
DataTruth(history).decide(fact: CaptureFact) -> TruthDecision
```

It owns routing, shared invariants, policy version, subject reconciliation,
persistence success, and composition—not Trade projection, observation policy,
QuestDB mechanics, SQL, replay, Canonical Dataset, Model, or Trading.

A returned TruthDecision is authoritative only after deterministic computation,
append to authoritative history, approved persistence success, and a
same-authority SubjectDecisionKey lookup verifies the exact persisted decision.
The history outcomes are success, definite failure/rejection, and in-doubt;
`decide()` exposes bounded exceptions rather than a generic result wrapper.

Blind retry is forbidden. After in-doubt, look up SubjectDecisionKey: reconcile
an identical persisted decision, fail closed on conflict, and remain in-doubt
when absence cannot prove that an ambiguous append did not commit. Semantic
Event `DUPLICATE` is never physical retry reconciliation. TruthDecision-history
DEDUP is disabled: QuestDB last-write-wins replacement is incompatible with
append-only authority.

## QuestDB and persistence planning

Persistence classification is **B**: a deterministic semantic library is a
valid first slice, but Data Truth cannot be FINAL CLOSED before persistent
append-only TruthDecision authority is independently accepted.

QuestDB Server `10.0.1` with existing `questdb==5.0.0` is the preferred
generic persistence/query mechanism. TruthDecision-history
persistence/reconciliation fit is **PROVEN UNDER THE APPROVED SINGLE-WRITER
CONSTRAINT** by the accepted disposable POC: direct append acknowledgement,
committed-but-no-caller-ACK reconciliation, ambiguous-write/in-doubt handling,
exact subject-key lookup/read visibility, no blind reappend, fail-closed
conflicting/multiple authority, and append-only operation without DEDUP or
UPSERT. The POC did not use canonical tables, alter `server.conf`, or enable
canonical SF or DEDUP.

That accepted mechanical result does not implement Slice 2, a production
`questdb_history.py`, production `find_accepted_event` behavior, Hot Store
evidence resolution, multi-writer safety, concurrent `decide()`, a canonical
TruthDecision table, or canonical runtime activation. Slice 2 remains NOT
AUTHORIZED pending separate explicit authorization.

One conceptual append-only TruthDecision-history table may be needed. It keeps
the subject key, policy version, category, contributing CaptureFact IDs,
bounded reason, optional EventIdentity, and only physical persistence/order
metadata needed by generic storage. Storage timestamp is not semantic event
time. No DDL is decided here and no new database is required.

## Planned modules and slices

```text
src/live15_quant_v2/data/data_truth/
├── __init__.py
├── models.py
├── history.py
├── composition.py
├── event_facts.py
├── observation_facts.py
└── questdb_history.py
```

This is six substantive modules plus exports. Event and Observation modules do
not import one another. `questdb_history.py` is the explicit adapter and owns
no semantic policy; `__init__.py` exports only provider-neutral supported
types.

There are exactly two production slices:

1. **Slice 1 — Semantic Library Candidate:** models, history protocol/errors,
   parent composition, Trade Event Facts, stateless Observation Facts,
   test-only in-memory history, and unit/architecture tests. It contains no
   QuestDB adapter, persistent authority, canonical table, runtime activation,
   Replay & As-Of, or Canonical Dataset. It cannot close Data Truth
   implementation.
2. **Slice 2 — Persistent History Candidate:** only after the POC passes;
   QuestDB adapter, persistent append-only authority, subject/Event lookup,
   sealed HotStore evidence resolution, and disposable integration tests. It
   does not activate canonical runtime and still requires review, PR, CI,
   merge, validation, and local seal before FINAL CLOSED status.

## Required future validation

Future tests must cover first valid Trade acceptance; equal and changed Trade
projections; differing `sid`/`seq`; JSON-format independence; invalid identity
and schema; no fallback identity; every approved Observation family; distinct
equal observations; subject reconciliation; definite and in-doubt append
failure; sibling isolation; unchanged CaptureFact; no semantic-leaf QuestDB
dependency; and no multi-writer safety claim.

## Exclusions

This plan does not include Replay & As-Of, Canonical Dataset, features, labels,
models, prediction, signals, positions, orders, PnL, strategy, transport gaps,
Market Ingress mechanics, Capture Boundary mechanics, QuestDB Runtime
lifecycle, or canonical runtime activation.
