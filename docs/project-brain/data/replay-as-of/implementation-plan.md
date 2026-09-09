# Replay & As-Of Implementation Plan

## Status and authority

**Implementation-plan authority:** DRAFT CANDIDATE / PENDING INDEPENDENT
REVIEW.
**Implementation:** NOT IMPLEMENTED.
**Canonical activation:** NOT AUTHORIZED.

The FINAL CLOSED Replay & As-Of contract outranks this plan. If an
implementation convenience conflicts with the contract, implementation must
change; the contract must not be silently weakened. This plan is the next
planning gate, not authorization for a source change, a production table, a
runtime change, Canonical Dataset work, Model/training, or Trading.

## Scope, ownership, and seams

Replay & As-Of remains one direct Data System child. Its smallest useful
internal mechanical split is:

```text
Replay public read service
├── internal availability support
└── Replay-owned physical source adapter

Data System recorder composition (upper composition owner)
```

Availability support is not a top-level semantic system; fingerprinting,
cursor encoding, and clock handling are mechanics within these bounded
modules, not services of their own. Storage continues to own immutable
CaptureFact physical persistence; Data Truth continues to own TruthDecision
authority; Replay does not own ingress, transport retry, persistence retry, or
adjudication.

The existing `src/live15_quant_v2/data/__init__.py` deliberately has no
composition seam. The planned upper owner is
`src/live15_quant_v2/data/recorder_composition.py`. It is the only planned
place to sequence public Capture Boundary, Durable Persistence, Replay support,
and Data Truth calls. It is not a Replay child and remains unimplemented in
this plan.

The plan preserves, without widening, `CaptureFact`, `HotStore`,
`CaptureRange`, `TruthDecision`, `TruthDecisionHistory`, and `DataTruth`.
There is no availability field in CaptureFact or TruthDecision, Replay range
method in TruthDecisionHistory, generic pagination in HotStore, or
`DataTruth.decide()` on the Replay read path. Direct physical access beyond
those semantic ports belongs only to the dedicated Replay source adapter.

## Public read contract

The V1 public shape remains conceptual until implementation is separately
authorized:

```text
AsOfRequest
ReplayAsOf.read(request) -> AsOfReplayView
```

`AsOfRequest` contains:

- `as_of_cutoff_ns`: an integer nanosecond cutoff;
- `authority_policy_version`: exactly `data-truth/v1` in V1;
- `SelectionWindow(axis, start_ns, end_ns)`, half-open with `start_ns < end_ns`;
- ordering: `ARRIVAL` or `STRICT_EVENT`;
- approved `AssetId` values and bounded configured/exact channel strings;
- positive `page_size`, capped by an implementation-configured resource bound;
  and
- an absent or contract-versioned cursor.

The page-size ceiling is a resource bound, not a semantic data-truth rule and
is unrelated to Hot Store's 500-row write batch limit. Validation deterministically
rejects invalid integer/window/page-size/policy/assets/channels/cursor inputs.
Selection and ordering are independently bound request fields:

```text
ARRIVAL_TIME selection = CaptureFact.received_timestamp
EVENT_TIME selection   = CaptureFact.provider_timestamp

ARRIVAL order      = (received_timestamp, capture_id)
STRICT_EVENT order = (provider_timestamp, received_timestamp, capture_id)
```

After availability, policy, asset, and channel qualification, EVENT_TIME with
any qualified null provider timestamp fails `UNSUPPORTED_EVENT_TIME` before
window selection. STRICT_EVENT with any selected null provider timestamp also
fails that way. Neither case falls back to receipt time, `sid`, `seq`, provider
row order, or database row order.

Every public record remains paired:

```text
AuthoritativeReplayRecord =
    CaptureFact + recorded TruthDecision + evidence availability reference
    + authority availability reference

AsOfReplayView = immutable records/page + request/provenance + next cursor
```

The view includes the authority policy, cutoff semantics/version, selection
window, ordering rule/version, source snapshot identity, bounded
exclusions/anomalies, and `COMPLETENESS_STATE = NOT_ASSERTED`. There is no
raw-only public authority mode. `ACCEPTED`, `DUPLICATE`, `CONFLICT`, and
`NOT_ACCEPTED` are all valid recorded Replay authority; Canonical Dataset
filtering is a future, out-of-scope policy.

## Replay-owned availability support

One provider-neutral immutable model is sufficient:

```text
AvailabilityKind = EVIDENCE | AUTHORITY

AvailabilityRecord(
    kind,
    capture_id,
    policy_version: str | None,
    available_at_ns,
    proof_schema_version,
    source_authority_identity,
)
```

`proof_reference` is intentionally omitted: the immutable semantic key,
proof schema version, and configured source identity are sufficient for V1
reconciliation and provenance; adding a reference without a concrete audit
operation would widen the record needlessly.

Semantic keys are `capture_id` for EVIDENCE and
`(policy_version, subject_capture_id)` for AUTHORITY. An EVIDENCE record must
have no policy version; an AUTHORITY record must have one. `capture_id` names
the subject in both cases. The internal recording port is deliberately small:

```text
find(key) -> AvailabilityRecord | None
append(record) -> AvailabilityRecord
```

It has no update, delete, arbitrary CRUD, semantic UPSERT, last-write-wins
replacement, or public range API. Bulk marker lookup, when needed to rebuild a
snapshot, stays in the physical source adapter.

`available_at_ns` is conservative proven availability, not mathematically
earliest database visibility. Evidence proof occurs only when the configured
public evidence authority's `HotStore.read_capture(capture_id)` returns the
exact expected immutable CaptureFact. `PersistenceStatus`, including
`ACKNOWLEDGED_OK`, is not evidence proof; `PERSISTED_PENDING` and `IN_DOUBT`
may later be proved by exact read-back. Authority proof occurs only after
successful `DataTruth.decide(fact)` returns, because that sealed composition
has persisted and exact same-authority verified the decision.

### Recording and reconciliation

V1 assumes one ordered availability writer. Append is append-only and creates
one authoritative immutable record per semantic key. Before an append, lookup
the exact key; exact existing content reconciles, while a mismatch fails
closed. There is no blind retry after ambiguous publication and no semantic
replacement.

After ambiguous/in-doubt publication, lookup the exact semantic key:

1. one exact row reconciles;
2. multiple or mismatched rows fail closed; and
3. zero rows remains IN_DOUBT.

A later independent re-proof may use a newly established proof time to append
a new candidate only when the earlier ambiguous publication was positively
absent. It never reuses an earlier failed proof time merely for convenience.
V1 may conservatively leave an unresolved key unavailable indefinitely:
`NOT_ASSERTED` completeness and fail-closed membership are safer than
fabricating historical availability.

### Recorder composition and failure isolation

The future upper composition sequence is:

```text
typed Market Ingress message
→ Capture Boundary → immutable CaptureFact
→ approved Durable Persistence path
→ exact public HotStore read-back
→ evidence AvailabilityRecord
→ DataTruth.decide(fact)
→ authority AvailabilityRecord
```

The chosen policy is decoupling: availability-support failure does not block
the sealed Data Truth core. The composition records an explicit Replay-support
IN_DOUBT/absent outcome, continues Data Truth processing through its public
seam, and schedules no blind marker write retry. A later exact evidence
read-back or independent authority re-proof performs the reconciliation rules
above. Thus the affected record remains unavailable to an As-Of cutoff until a
fresh, immutable marker is proven; no single-dimensional shortcut can admit it.

## Disposable QuestDB availability adapter

This is a future disposable implementation shape only; this plan creates no
table. A UUID-named disposable WAL table is expected to have:

```text
kind VARCHAR,
capture_id VARCHAR,
policy_version VARCHAR,
available_at_ns TIMESTAMP_NS,
proof_schema_version VARCHAR,
source_authority_identity VARCHAR,
written_at_ns TIMESTAMP_NS
TIMESTAMP(written_at_ns) PARTITION BY DAY WAL
```

It has **NO DEDUP** and **NO UPSERT**. `written_at_ns` is physical
diagnostic/mechanical time, not availability semantics. Adapter validation
checks all required columns/types, a null policy only for EVIDENCE, a present
policy only for AUTHORITY, exactly one row per semantic key, and immutable
identity agreement. It uses existing `questdb==5.0.0` mechanisms
`sender.row`, `auto_flush=False`, `flush_and_get_fsn`, `await_acked_fsn`,
structured rejection diagnostics, and `wait_wal_table`; it does not copy
private sibling adapter code.

## Bounded clock strategy and gate

`LAST_MARKER_FLOOR_ALONE_INSUFFICIENT` is an accepted POC result.
`max(time.time_ns(), last_available_at + 1)` alone cannot prevent rollback
backdating. The V1 direction is process-lifetime monotonic wall projection:

```text
anchor_wall_ns = time.time_ns()
anchor_mono_ns = time.monotonic_ns()
proof_now = anchor_wall_ns + (time.monotonic_ns() - anchor_mono_ns)
```

Apply the highest committed availability proof floor only as an additional
forward-only lower bound. At process startup, load that floor before accepting
new writes; if projected startup time is behind it, clamp forward or fail
closed, never emit an earlier proof time. This prevents an in-process rollback
from backdating markers, but does not claim arbitrary distributed-clock or
cross-restart correctness: a long proof-free interval followed by host clock
regression cannot be reconstructed from the last marker alone.

Before canonical activation, a separately authorized `CLOCK_SAFETY` gate must
prove process-lifetime rollback handling, restart below the persisted floor,
non-decreasing proof timestamps, no backdating, bound fingerprint drift
detection, and the host UTC/NTP operational assumption. A clock-unsafe state
must clamp safely or fail closed. No distributed clock service or dependency is
planned.

## Snapshot, cursor, and physical source

`SOURCE_SNAPSHOT_IDENTITY` is a stdlib cryptographic digest of canonical
serialization containing at least the snapshot scheme version, configured
evidence/truth/availability authority identities, authority policy, cutoff,
selection axis/window, asset/channel filters, ordering mode/version, and
sorted eligible semantic membership keys. Python `hash()` is forbidden. This
fingerprint is not a database transaction snapshot:

```text
first page: rebuild membership and bind digest
later page: rebuild the same membership
same digest: continue by keyset
different/unreproducible: no mixed continuation
```

Cursor data is deterministic, versioned, and code-readable—canonical JSON with
URL-safe encoding is sufficient. It binds contract/cursor version, request ID,
policy, cutoff, selection axis/window, filters, ordering/version, snapshot
identity, and last ordering key. No HMAC is planned because this cursor is not
currently a security boundary; malformed or internally inconsistent values are
`INVALID_CURSOR`. Different valid bound request values are
`CURSOR_MISMATCH`; a same valid request whose physical authorities cannot
reproduce membership is `SOURCE_UNAVAILABLE`. No OFFSET is used.

Keyset predicates are lexicographic:

```text
ARRIVAL: received > last_received
      OR (received = last_received AND capture_id > last_capture_id)

STRICT_EVENT: provider > last_provider
      OR (provider = last_provider AND received > last_received)
      OR (provider = last_provider AND received = last_received
          AND capture_id > last_capture_id)
```

The planned Replay-owned `QuestDBReplaySource` directly reads configured
evidence, TruthDecision, and availability authority tables. It verifies
configured source identity (logical identity, table identity, expected physical
schema/version; never credentials/connection strings), uses parameter binds,
decodes existing immutable CaptureFact and TruthDecision models, and returns
Replay-owned provider-neutral internal paired rows. A source configuration
change changes the snapshot identity.

Before serving, it validates required physical schemas. It fails
`SOURCE_UNAVAILABLE` rather than adapting or mutating a missing/wrong evidence,
truth, or availability table. It validates one physical authority row per
`(policy_version, subject_capture_id)`, marker uniqueness, all-null or
all-present EventIdentity, valid category/reason decoding, and all pairing
invariants. Semantic `TruthDecisionCategory.CONFLICT` remains valid; multiple
physical rows are malformed ambiguous authority and fail closed.

For a paired record, capture ID equals decision subject, decision policy equals
the request policy, marker keys match their evidence/authority keys, and both
availability times are at or before cutoff. Evidence/authority asymmetry,
future/missing markers, malformed records, ambiguity, and permanently absent
markers become bounded exclusions only where the contract permits; otherwise
the read fails closed. Completeness remains `NOT_ASSERTED`.

## Proposed module tree

The minimum planned Replay package is:

```text
src/live15_quant_v2/data/replay_as_of/
├── __init__.py                 # provider-neutral public exports
├── models.py                   # request/view/errors/internal immutable values
├── service.py                  # validation, selection, ordering, cursor, digest
├── source.py                   # narrow Replay source protocol and in-memory test source
├── availability.py             # record/key/recording port and clock policy
├── questdb_source.py           # direct configured physical read adapter
└── questdb_availability.py     # append-only disposable availability adapter
```

No `snapshot.py`, cursor/clock/pagination service, generic repository, or
cross-child adapter is justified. The future parent composition file is
`src/live15_quant_v2/data/recorder_composition.py`; it is not included in the
Replay package.

## Implementation slices and gates

| Slice | Planned files and tests | Dependencies / gates | Still unauthorized after merge |
| --- | --- | --- | --- |
| 1 — Pure Replay Core | `models.py`, `service.py`, `source.py`, exports; `tests/test_replay_as_of.py` for request validation, paired records, selection/order, cursor/digest/keyset with an in-memory source; `tests/test_replay_as_of_architecture.py` for public-seam and no-widening checks | FINAL CLOSED contract; independent remote review before merge | QuestDB, availability persistence, recorder composition, canonical activation |
| 2 — Availability Support | `availability.py`, `questdb_availability.py`; `tests/test_replay_as_of_availability.py` for keys, proof, reconciliation, and clock policy; `tests/test_questdb_replay_as_of_availability_integration.py` for disposable append/read-back/in-doubt acceptance | existing QuestDB 5.0.0; `CLOCK_SAFETY` gate and independent review | canonical availability table/runtime, Replay physical reads, recorder composition |
| 3 — Replay QuestDB Source | `questdb_source.py`; `tests/test_questdb_replay_as_of_source_integration.py` for disposable schema, pairing, qualification, fingerprint recomputation, keyset, drift, and restart | accepted PR #42 POC is evidence only; independent review and disposable acceptance | recorder composition and all canonical activation |
| 4 — Data System Recorder Composition | `data/recorder_composition.py`; `tests/test_replay_as_of_recorder_composition.py` for decoupled failure/isolation; `tests/test_questdb_replay_as_of_end_to_end.py` for disposable Capture Boundary → Durable Persistence → read-back → markers → Data Truth → markers → Replay | public sealed Storage/Data Truth seams; separate review, with Slice 3/4 retained separately for ownership and review blast radius | canonical tables, runtime/service activation, Canonical Dataset, Model/training, Trading |

No new dependency is planned: V1 uses stdlib, existing models/contracts, and
the existing pinned `questdb==5.0.0` client. SQLAlchemy, Kafka, Redis, Arrow,
DuckDB, Polars, a crypto package, and distributed coordination are unjustified.

## Acceptance matrix

| Area | Required acceptance |
| --- | --- |
| Request/core | invalid window/page size/policy, asset/channel binding, selection independent of ordering, cursor request mismatch |
| Availability | read-back-only evidence proof; ACK-not-proof; verified DataTruth-return authority proof; exact keys; conservative time; no backdating; definite and in-doubt publication; reconciliation; duplicate/mismatch failure; fresh re-proof; single-writer assumption |
| Clock | in-process rollback, monotonic projection, restart below floor, non-decreasing timestamps, no claim that floor alone suffices, clock-unsafe fail-closed/clamp behavior, documented UTC/NTP assumption |
| As-Of/categories | both availability dimensions, asymmetric/future markers, exact policy, half-open windows, EVENT null failure, ARRIVAL null validity, and every valid TruthDecision category replayable |
| Ordering/cursor | equal receipt/provider timestamps, capture-ID tie-break, no sid/seq chronology, canonical digest, page 1/2, policy/filter/order/source binding, altered request mismatch, malformed cursor, no OFFSET |
| Snapshot/restarts | late append and recovery after cutoff unchanged, reader and task-owned server restart, membership drift as `SOURCE_UNAVAILABLE` before mixed page |
| Physical/boundary | missing/wrong schema, malformed CaptureFact/TruthDecision, partial EventIdentity, multiple authority/marker rows, config drift, no Replay `DataTruth.decide`, no HotStore/history/CaptureFact/TruthDecision widening, no canonical runtime mutation |

## Production boundary

Implementation-plan authority may close before canonical activation, and
disposable QuestDB slices may prove engineering behavior before canonical
activation. Production acceptance remains separately authorized and requires
canonical evidence, TruthDecision, and availability authorities/tables;
verified production schemas; Recorder composition; runtime configuration;
clock-safety operational assumptions; canonical service/runtime activation;
and health/restart/recovery acceptance.

Replay output remains evidence/authority replay. It does not choose a training
universe, feature/label shape, sample inclusion, conflict/duplicate filtering,
or model-ready rows; those are future Canonical Dataset and Research concerns.
