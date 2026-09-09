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

### Deterministic request identity

`REQUEST_IDENTITY` is a deterministic cryptographic digest of canonical JSON
for the request's contract-bound semantic fields. It is not an `AsOfRequest`
field, random UUID, caller-chosen opaque identifier, or database identity. Its
canonical input contains the contract/request version,
`authority_policy_version`, `as_of_cutoff_ns`, selection axis and half-open
window, canonicalized approved asset set, canonicalized channel set, and
ordering mode/version. Asset and channel filters are unordered sets at the
public boundary and are sorted by their canonical serialized values before
digesting. A request without filters canonically represents the approved
unfiltered value, not an arbitrary empty-list spelling.

`page_size` is deliberately excluded: it is a bounded delivery/resource
parameter and does not alter As-Of source membership. It remains validated and
cursor-delivery compatible, but it is not part of semantic source-membership
identity. Cursor contents and view provenance bind `REQUEST_IDENTITY`; the
separate `SOURCE_SNAPSHOT_IDENTITY` binds the rebuilt eligible membership for
that request.

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
read_committed_floor() -> int | None
append(record) -> AvailabilityRecord
```

`read_committed_floor()` returns only the greatest verified committed
`available_at_ns` known to this provider-neutral availability authority. It is
for `CLOCK_SAFETY` startup only, not membership reconstruction or generic
querying. The port has no update, delete, arbitrary CRUD, semantic UPSERT,
last-write-wins replacement, or public range API. Bulk marker lookup, when
needed to rebuild a snapshot, stays in the physical source adapter.

`available_at_ns` is conservative proven availability, not mathematically
earliest database visibility. `available_at_ns` is sampled only after its
proof trigger succeeds—never before a possibly slow or failing proof call.
For EVIDENCE, the configured public evidence authority's
`HotStore.read_capture(capture_id)` must first return the exact expected
immutable CaptureFact, then the proof time is sampled. For AUTHORITY,
`DataTruth.decide(fact)` must first return its verified authority, then the
proof time is sampled. `PersistenceStatus`, including `ACKNOWLEDGED_OK`, is
not evidence proof; `PERSISTED_PENDING` and `IN_DOUBT` may later be proved by
exact read-back.

The only V1-supported proof schema version is
`replay-availability-proof/v1`. Qualification fails closed if
`proof_schema_version` is unsupported. It also requires exact source binding:

```text
EVIDENCE  source_authority_identity == configured evidence authority identity
AUTHORITY source_authority_identity == configured TruthDecision authority identity
```

These identities are semantic proof inputs, not decorative provenance. An old
or differently configured source's marker cannot qualify a same-key fact or
decision from the new source. The future recorder composition obtains and binds
the same logical evidence authority identity from its configuration for the
Durable Persistence target, the HotStore read-back proof, and the resulting
EVIDENCE record; it adds no field to sealed Durable Persistence or HotStore
protocols.

### Recording and reconciliation

V1 assumes one ordered availability writer. Append is append-only and creates
one authoritative immutable record per semantic key. `append(record)` returns
an `AvailabilityRecord` only after verified successful publication and exact
semantic-key visibility/reconciliation. Its bounded typed non-success outcomes
are `DEFINITE_PREPUBLICATION_FAILURE`, `IN_DOUBT`, and
`INVARIANT_CONFLICT` (names are planned public-internal error values, not
generic CRUD results).

The executable append state machine is:

1. Exact semantic-key prelookup: one exact existing record reconciles and is
   returned; multiple or mismatched content is `INVARIANT_CONFLICT` and fails
   closed; only an absent key continues.
2. Append one immutable candidate with the pinned QuestDB mechanism.
3. Interpret flush/publication result, FSN when available, completion timeout,
   structured rejection, and diagnostic loss. A known rejection before any
   publication attempt is `DEFINITE_PREPUBLICATION_FAILURE`; an ambiguous
   outcome is `IN_DOUBT`.
4. When publication may have succeeded, use `wait_wal_table` and the approved
   visibility barrier, then perform exact semantic-key verification.
5. Exactly one same record is success and may be returned; multiple/mismatched
   rows are `INVARIANT_CONFLICT`; no row after ambiguous publication remains
   `IN_DOUBT`.

Zero rows after ambiguous publication is not proof that no row was published.
It must not trigger a blind reappend. A later fresh proof may create a new
candidate only after `DEFINITE_PREPUBLICATION_FAILURE` or another explicitly
proven non-publication condition supplied by the pinned upstream—not an
invented “positive absence” test. An unresolved key may conservatively remain
unavailable indefinitely: `NOT_ASSERTED` completeness and fail-closed
membership are safer than fabricating historical availability.

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

The V1 status boundary is exact:

| Durable Persistence outcome / next proof | This iteration's Data Truth progression | Replay recovery |
| --- | --- | --- |
| `LOCAL_PERSISTENCE_FAILED` or `DEFINITELY_REJECTED` | Do not claim evidence availability, create no evidence marker, and do not call Data Truth for this attempt. | A future independently accepted ingestion attempt is required. |
| `PERSISTED_PENDING`, `ACKNOWLEDGED_OK`, or `IN_DOUBT`, before exact read-back | Status is not evidence proof. Attempt exact `HotStore.read_capture`; until it succeeds, do not claim evidence availability, create no evidence marker, or advance the fact through normal Data Truth composition in this iteration. | Fresh exact evidence read-back proof may later establish evidence. |
| Exact evidence read-back succeeds; EVIDENCE marker records/reconciles | Proceed through the sealed Data Truth public seam. | Normal paired proof path. |
| Exact evidence read-back succeeds; EVIDENCE marker is `IN_DOUBT` or fails | Replay evidence availability remains absent/in-doubt, but this Replay-support publication failure does not block Data Truth core. No blind marker retry. | Fresh exact read-back proof may reconcile/record later. |
| Successful `DataTruth.decide(fact)`; AUTHORITY marker is `IN_DOUBT` or fails | Do not roll back Data Truth. Replay authority availability remains absent/in-doubt. | Upper Recorder/Data System composition may re-enter the approved Data Truth public path for the exact fact so its existing exact-subject decision can be returned and re-proved; Replay READ never calls `DataTruth.decide()`. |

Thus only marker-publication failure after its corresponding exact proof is
decoupled. Persistence failure and evidence-proof failure are not generic
“availability-support failures” and cannot advance normal Data Truth flow.
No custom retry queue is planned. An affected record stays unavailable to an
As-Of cutoff until a fresh immutable marker is proven; no one-dimensional
shortcut can admit it.

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
forward-only lower bound. At process startup, call
`read_committed_floor()` before accepting new writes. For a newly established
proof, sample `candidate = projected_proof_now` after its proof trigger; if
`candidate <= committed_floor`, emit `committed_floor + 1` or fail closed. It
must never emit a time equal to or before the committed floor merely because a
startup clamp is needed. This prevents an in-process rollback from backdating
markers, but does not claim arbitrary distributed-clock or cross-restart
correctness: a long proof-free interval followed by host clock regression
cannot be reconstructed from the last marker alone.

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
URL-safe encoding is sufficient. It binds contract/cursor version,
`REQUEST_IDENTITY`, `SOURCE_SNAPSHOT_IDENTITY`, and the last ordering key. The
identity already binds policy, cutoff, selection axis/window, canonical
filters, and ordering/version; no random or caller-supplied request ID exists.
No HMAC is planned because this cursor is not currently a security boundary;
malformed or internally inconsistent values are `INVALID_CURSOR`. Different
valid bound request identity values are `CURSOR_MISMATCH`; a same valid request
whose physical authorities cannot reproduce membership is
`SOURCE_UNAVAILABLE`. No OFFSET is used.

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
physical rows are malformed ambiguous authority and fail closed. Physical
evidence that cannot decode/validate as sealed `CaptureFact` is
`MALFORMED_EVIDENCE`; malformed TruthDecision category/reason/EventIdentity or
row shape is `MALFORMED_AUTHORITY`; and conflicting/multiple physical authority
rows for the same `(policy_version, subject_capture_id)` with no single
authoritative row is `AUTHORITY_CONFLICT`. Different policy versions alone are
not `AUTHORITY_CONFLICT`.

For a paired record, capture ID equals decision subject, decision policy equals
the request policy, marker keys match their evidence/authority keys, and both
availability times are at or before cutoff. Evidence/authority asymmetry,
future/missing markers, unsupported proof schema, source-identity mismatch,
malformed records, ambiguity, and permanently absent markers become bounded
exclusions only where the contract permits; otherwise the read fails closed.
Required marker absence is `AVAILABILITY_EVIDENCE_MISSING`, not a generic
source failure. Completeness remains `NOT_ASSERTED`.

## FINAL CLOSED error taxonomy mapping

The service preserves the sealed contract taxonomy rather than laundering
domain/data defects into `SOURCE_UNAVAILABLE`:

| Error | Planned mapping |
| --- | --- |
| `INVALID_REQUEST` | Invalid semantic request input: cutoff/window/page size, policy, filter value, or unsupported selection/ordering value. |
| `INVALID_CURSOR` | Malformed, undecodable, wrong-shape, or internally inconsistent cursor. |
| `CURSOR_MISMATCH` | A valid cursor is reused with a different bound `REQUEST_IDENTITY` (including its semantic filters/order/cutoff). |
| `SOURCE_UNAVAILABLE` | Configured source/table/schema is unavailable, or same-request bound membership cannot be reproduced because authority/configuration changed. |
| `MALFORMED_EVIDENCE` | A physical evidence row exists but cannot decode/validate as the sealed `CaptureFact`. |
| `MALFORMED_AUTHORITY` | A physical TruthDecision row has malformed category/reason/EventIdentity or violates its row shape. |
| `AUTHORITY_CONFLICT` | Same-policy, same-subject physical authority has conflicting/multiple rows and no single authoritative row can be established. Different policy versions alone are valid and are not this error. |
| `AVAILABILITY_EVIDENCE_MISSING` | A required evidence or authority availability proof/qualifying marker is absent, unusable, future, source-mismatched, or uses an unsupported proof schema for a requested paired record. |
| `UNSUPPORTED_EVENT_TIME` | The FINAL CLOSED qualified/selected null-provider-time rule is reached for EVENT_TIME or STRICT_EVENT. |

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
| 1 — Pure Replay Core | `models.py`, `service.py`, `source.py`, exports; `tests/test_replay_as_of.py` for deterministic `REQUEST_IDENTITY`, filter canonicalization, request validation, paired records, selection/order, cursor/digest/keyset with an in-memory source; `tests/test_replay_as_of_architecture.py` for public-seam and no-widening checks | FINAL CLOSED contract; independent remote review before merge | QuestDB, availability persistence, recorder composition, canonical activation |
| 2 — Availability Support | `availability.py`, `questdb_availability.py`; `tests/test_replay_as_of_availability.py` for keys, supported proof schema/source identity, post-proof sampling, committed-floor strict advancement, reconciliation, and clock policy; `tests/test_questdb_replay_as_of_availability_integration.py` for disposable definite-failure/ambiguous-zero/no-reappend behavior and append/read-back acceptance | existing QuestDB 5.0.0; `CLOCK_SAFETY` gate and independent review | canonical availability table/runtime, Replay physical reads, recorder composition |
| 3 — Replay QuestDB Source | `questdb_source.py`; `tests/test_questdb_replay_as_of_source_integration.py` for disposable schema, pairing, qualification, all contract error mappings, fingerprint recomputation, source reconfiguration drift, keyset, and restart | accepted PR #42 POC is evidence only; independent review and disposable acceptance | recorder composition and all canonical activation |
| 4 — Data System Recorder Composition | `data/recorder_composition.py`; `tests/test_replay_as_of_recorder_composition.py` for durable-status matrix, no Data Truth before exact evidence proof, and decoupled marker failure/isolation; `tests/test_questdb_replay_as_of_end_to_end.py` for disposable Capture Boundary → Durable Persistence → read-back → markers → Data Truth → markers → Replay | public sealed Storage/Data Truth seams; separate review, with Slice 3/4 retained separately for ownership and review blast radius | canonical tables, runtime/service activation, Canonical Dataset, Model/training, Trading |

No new dependency is planned: V1 uses stdlib, existing models/contracts, and
the existing pinned `questdb==5.0.0` client. SQLAlchemy, Kafka, Redis, Arrow,
DuckDB, Polars, a crypto package, and distributed coordination are unjustified.

## Acceptance matrix

| Area | Required acceptance |
| --- | --- |
| Request/core | deterministic `REQUEST_IDENTITY`; filter canonicalization; invalid window/page size/policy; asset/channel binding; selection independent of ordering; `page_size` excluded from source-membership identity; cursor request mismatch |
| Availability | read-back-only evidence proof; ACK-not-proof; verified DataTruth-return authority proof; exact keys; evidence/authority marker source mismatch; unsupported proof schema; post-proof timestamp sampling; definite and in-doubt publication; reconciliation; duplicate/mismatch failure; no blind reappend; single-writer assumption |
| Clock | `read_committed_floor`; in-process rollback; monotonic projection; startup floor strict advancement; restart below floor; non-decreasing timestamps; no claim that floor alone suffices; clock-unsafe fail-closed/clamp behavior; documented UTC/NTP assumption |
| As-Of/categories | both availability dimensions, asymmetric/future markers, exact policy, half-open windows, EVENT null failure, ARRIVAL null validity, and every valid TruthDecision category replayable |
| Ordering/cursor | equal receipt/provider timestamps, capture-ID tie-break, no sid/seq chronology, canonical digest, page 1/2, request-identity/filter/order/source binding, altered request mismatch, malformed cursor, no OFFSET |
| Snapshot/restarts | late append and recovery after cutoff unchanged, reader and task-owned server restart, source reconfiguration invalidates old snapshot identity, membership drift as `SOURCE_UNAVAILABLE` before mixed page |
| Physical/boundary | missing/wrong schema; full FINAL CLOSED error taxonomy; malformed CaptureFact/TruthDecision; partial EventIdentity; multiple authority/marker rows; config drift; durable-persistence status matrix; no Data Truth before exact evidence proof; evidence marker failure does not block Data Truth; authority marker failure does not roll back Data Truth; no Replay `DataTruth.decide`; no HotStore/history/CaptureFact/TruthDecision widening; no canonical runtime mutation |

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
