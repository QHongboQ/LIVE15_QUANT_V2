# Replay & As-Of

## Status and responsibility

**Contract authority:** FINAL CLOSED.
**Implementation-plan authority:** FINAL CLOSED.
**Implementation:** IN PROGRESS / PARTIALLY IMPLEMENTED.
**Slice 1 — Pure Replay Core:** FINAL CLOSED.
**Slice 2 — Availability Support:** FINAL CLOSED.
**Slice 3 — QuestDB Replay Source:** FINAL CLOSED.
**Slice 4 — Recorder Composition:** NOT IMPLEMENTED / CURRENT NEXT.
**Availability-mechanism fit preparation:** COMPLETED.
**Availability Support engineering implementation:** FINAL CLOSED.
**Canonical availability activation:** NOT AUTHORIZED / NOT PERFORMED.
**Canonical Replay activation:** NOT AUTHORIZED.
**Recorder production composition:** NOT IMPLEMENTED.
**Production `CLOCK_SAFETY` operational gate:** NOT AUTHORIZED / NOT CLOSED.
**Planning candidate:** ACCEPTED FOR IMPLEMENTATION-PLAN DESIGN; its physical
DDL and production activation remain undecided and unauthorized. The candidate
direction is Replay-owned availability support observed and recorded from upper
Data System composition through sealed public Storage/Data Truth seams.
**Canonical activation:** NOT AUTHORIZED.

**Closure evidence:** PR #40 first reviewed head
`77fa8264f48994fe6ab2158184651c4b9c0823e2` required changes; corrected head
`a838ebfd6d0bd9cc427e0ec90ce08c952d794d61` passed ChatGPT re-audit and
exact-head CI. Normal merge `528815ef2883b3757515b9b9d8e3dcadc92981b6` and
its Ubuntu, Windows, and CI Gate checks passed; the local docs seal passed. No
runtime, code, or data change occurred.

**Implementation-plan closure evidence:** PR #44's first reviewed head
`86d51d89f02f7c3bc5e5c15a2260848c8f5d4dfb` received ChatGPT
`CHANGES_REQUIRED`; corrected head
`af87756b1a948aee41253b9507c552f31df93bfc` passed ChatGPT exact-head
re-audit and exact-head CI. Normal merge
`13af6e1cea4c087c547bfc9f6a25311ab6690b6b` has parents
`752c57e3c262e006ff127f1436e435d40376d7ee` and
`af87756b1a948aee41253b9507c552f31df93bfc`; its merge-SHA CI and local docs
seal passed. No source, runtime, table, or data change occurred.

**Slice 1 closure evidence:** PR #46's initial reviewed head
`e2e0426628e5999733ee678729c350f6a582899f` received ChatGPT
`CHANGES_REQUIRED`. Corrected approved head
`9779c99ef79f1815ee5c4d51cad225599a94d120` passed ChatGPT exact-head
re-audit and Ubuntu, Windows, and CI Gate checks. PR #46 merged normally as
`62f8c2f672ca3627d9690727ff47b80d805266d5` with parents
`fe097c1a5d112619f3949a92a341604f1760072b` and
`9779c99ef79f1815ee5c4d51cad225599a94d120`; its merge-SHA CI and exact-merge
technical seal passed. No QuestDB, runtime, table, or data change occurred.

**Slice 2 closure evidence:** PR #48's initial reviewed head
`f2361333d8c3b231a53feca3128e64119f12e814` received ChatGPT
`CHANGES_REQUIRED`; final approved head
`5119271b71450fa83a15de4b709fb07034a837e4` passed the exact-head re-audit and
Ubuntu, Windows, and CI Gate checks. PR #48 merged normally as
`a78b731a8c24879b0da41ec4d6f28bb43ebe2daf` with parents
`cd456aaba643a201809bdd360fc4fec31d1efe24` and
`5119271b71450fa83a15de4b709fb07034a837e4`; merge-SHA CI, exact-merge
technical seal, and task-owned QuestDB teardown passed. No canonical runtime,
table, or data change occurred.

**Slice 3 closure evidence:** PR #50's initial reviewed head
`ced4d6820f8335a255251c2e15a97533cac8be01` received ChatGPT
`CHANGES_REQUIRED`; identity-corrected head
`725c6cdd8673d13528183776c7772f60a26178f6` received a second
`CHANGES_REQUIRED`; acceptance-corrected head
`6c9c61df5c3ec381cac987a3aa87d3487cde34c9` was followed by final approved
head `d98d5798004c48aae735fef6fb6236982bb67d34`, which passed the final
ChatGPT exact-head re-audit and Ubuntu, Windows, and CI Gate checks. PR #50
merged normally as `4a1809d72aa0451cf357a3845451da294ea33a5a` with parents
`08b87512d9ae6e266a549f055ed19c33bc7dc7c0` and
`d98d5798004c48aae735fef6fb6236982bb67d34`; merge-SHA CI, the exact-merge
technical seal, task-owned real QuestDB acceptance, and teardown passed. No
canonical runtime, table, or production-data change occurred.

**Accepted Slice 3 engineering result:** `QuestDBReplaySource` is a
Replay-owned, read-only physical adapter with explicit evidence, TruthDecision,
and availability tables and no canonical defaults. It validates sealed physical
schemas and models without creation, migration, or repair; reconstructs direct
sealed `CaptureFact` and `TruthDecision` values for the exact requested policy;
keeps every valid TruthDecision category replayable; and fails closed for
malformed/duplicate evidence and authority. Availability markers use sealed
`AvailabilityRecord` validation and logical EVIDENCE/AUTHORITY proof identities,
while composite source identities bind logical identity, table, and schema
provenance only. The source is connection-string-independent, restart-stable,
deterministic, free of source-side semantic pagination and `OFFSET`, preserves
EVENT_TIME-null candidates for ReplayAsOf, and supports keyset continuation,
configuration/source drift failure, future-cutoff stability, and fail-closed
backdated membership drift.

**Accepted Slice 2 engineering result:** immutable semantic availability
records under `replay-availability-proof/v1`; a narrow provider-neutral
recording port and one ordered writer; post-proof monotonic wall projection,
strict committed-floor/last-issued advancement, and monotonic-regression
fail-closed behavior; exact immutable `IN_DOUBT` reconciliation with no blind
reappend; bounded append outcomes; and a disposable explicit-table QuestDB
adapter using WAL, no DEDUP, no UPSERT, physical `written_at_ns` separate from
semantic `available_at_ns`, exact verification, duplicate-key fail-closed, and
incompatible-schema no-repair fail-closed behavior. Clock engineering tests
passed, but `LAST_MARKER_FLOOR_ALONE_INSUFFICIENT` remains explicit and the
canonical `CLOCK_SAFETY` operational gate remains NOT AUTHORIZED / NOT CLOSED.

**Accepted Slice 1 engineering result:** provider-neutral immutable request and
view models; the complete FINAL CLOSED error vocabulary; deterministic request
and source-snapshot identities; independent selection and ordering; ARRIVAL /
EVENT semantics and deterministic ARRIVAL / STRICT_EVENT ordering; bounded
two-dimensional availability qualification and deterministic exclusions; a
request-bounded `ReplayCandidateScope` and narrow `ReplaySource`; in-memory
support; strict Cursor V1 structural validation with distinct request/snapshot
failures; lexicographic keyset pagination without `OFFSET`; and
`COMPLETENESS_STATE = NOT_ASSERTED`. The reviewed corrections established the
request-bounded source seam, strict cursor schema, deterministic exclusions,
and empty-availability-reference fail-closed behavior.

## Snapshot-membership POC gate

**Gate:** FINAL CLOSED.
**Technical result:** `PASS_WITH_FAIL_CLOSED_DRIFT`.
**Clock result:** `LAST_MARKER_FLOOR_ALONE_INSUFFICIENT`.

**Evidence:** PR #42's first head
`48f56d7751ef02e886bac5fdf1554ad722e6461d` required changes; corrected
reviewed head `cb1d285a46abb6ba725eaf0a3287a339f85ae76c` passed the ChatGPT
exact-head re-audit and hosted CI. Normal merge
`b76d10b0bc480a7f84a0cd6e97dd896a2f24d124`, its merge-SHA CI, and an
exact-merged-main real disposable POC all passed. The POC left no task
Java-process, listener-port, or root residue and made no canonical runtime,
service, table, or data change.

**Accepted planning candidate:** deterministic canonical membership
serialization plus a cryptographic fingerprint of source authority identities
and fixed request/cutoff semantics; recompute it after reader or task-server
restart and fail closed if membership drifts. This is sufficient input to
implementation-plan design only. It does not implement a production snapshot
mechanism or select production physical DDL.

**Accepted findings:** conservative proof time need not claim earliest
visibility; evidence proof is exact public immutable `CaptureFact` read-back,
not `PersistenceStatus` alone; authority proof is successful
`DataTruth.decide(fact)` return after sealed same-authority verification; and
the semantic availability keys are `capture_id` and
`(policy_version, subject_capture_id)`. Late recovery records a fresh later
proof time and never backdates it. V1 planning assumes one ordered availability
writer, with neither distributed coordination nor last-write-wins history.
All valid recorded `TruthDecision` categories are Replay authority, while
Canonical Dataset filtering remains future/out of scope. Selection and ordering
remain independent.

Replay & As-Of is a direct Data System child. It owns a research-facing,
read-only projection of already persisted immutable evidence and already
recorded `TruthDecision` authority. Its bounded responsibilities are:

1. historical replay of persisted immutable evidence for research;
2. replay/read projection of an already-recorded `TruthDecision`;
3. strict bounded historical-knowledge As-Of views;
4. deterministic ordering;
5. bounded provenance; and
6. explicit nonclaims about completeness.

It does not own or perform provider transport replay/resend, QuestDB SF
transport replay/resend, Hot Store physical replay/idempotency, ingress
recovery/reconnect/redownload/gap repair, Data Truth adjudication or
re-adjudication, features, labels, Canonical Dataset construction, models,
training, or trading.

The following terms are intentionally distinct:

| Term | Meaning in this contract |
| --- | --- |
| **TRANSPORT REPLAY** | Re-sending provider transport or QuestDB SF transport material. Out of scope. |
| **PHYSICAL REPLAY** | Replaying Hot Store physical frames, idempotency, or recovery mechanics. Out of scope. |
| **HISTORICAL EVIDENCE REPLAY** | Reading approved persisted immutable `CaptureFact` evidence. In scope. |
| **AUTHORITY REPLAY** | Reading the recorded decision authority paired to that evidence. In scope. |
| **AS-OF VIEW** | A bounded replay/read projection qualified by the two recorded availability dimensions below. In scope. |

`sid` and `seq` remain transport evidence only. They are not chronology,
identity, a cross-session tie-breaker, or evidence of completeness.

## Strict two-dimensional As-Of semantics

The contract names these facts without changing the existing `CaptureFact`,
`HotStore` protocol, `CaptureRange`, `TruthDecision`, `TruthDecisionHistory`,
or Data Truth contracts:

| Name | Meaning | Explicit non-meaning |
| --- | --- | --- |
| `EVENT_TIME` | `CaptureFact.provider_timestamp` when non-null. | Provider evidence is not availability evidence. |
| `ARRIVAL_TIME` | `CaptureFact.received_timestamp`. | Capture Boundary receipt is not persistence or query-visibility evidence. |
| `EVIDENCE_AVAILABLE_TIME` | Recorded physical-availability evidence proving the `CaptureFact` was usable from an approved persisted-evidence authority. | It is not inferred from event or arrival time. |
| `AUTHORITY_AVAILABLE_TIME` | Recorded availability evidence proving the recorded `TruthDecision` was authoritative and query-visible. | It is not inferred from a physical write. |
| `AS_OF_CUTOFF` | The upper bound on system knowledge for a view. | It is not a provider-time or receipt-time filter alone. |

A paired record qualifies for an As-Of view only when both conditions hold:

```text
evidence_available_at <= as_of_cutoff_ns
authority_available_at <= as_of_cutoff_ns
```

Neither `provider_timestamp <= cutoff` nor `received_timestamp <= cutoff` is
sufficient. A raw capture whose evidence is available by the cutoff but whose
recorded authority is not available by the cutoff is not an
`AuthoritativeReplayRecord`; a bounded `AUTHORITY_NOT_AVAILABLE_BY_CUTOFF`
exclusion may describe it.

### Recorded authority-policy binding

`AsOfRequest.authority_policy_version` is mandatory. Current V1 accepts only
the approved Data Truth authority policy:

```text
authority_policy_version = "data-truth/v1"
```

Every paired recorded `TruthDecision` must exactly match the requested
`authority_policy_version`. Its authority-availability evidence must identify
the sealed authority key `(policy_version, subject_capture_id)`. A request
never chooses a latest policy or infers a policy from whichever row happens to
be returned first. Different policy versions are neither duplicate authority
rows nor an `AUTHORITY_CONFLICT` by themselves.

### Existing-evidence boundary

`STRICT_AS_OF_EXISTING_EVIDENCE = INSUFFICIENT FOR EXACT HISTORICAL
SYSTEM-KNOWLEDGE RECONSTRUCTION`.

This is a deliberate fail-closed limit, not an implementation gap that this
draft fills. Existing `received_timestamp` proves receipt rather than database
visibility; current hot rows have no availability timestamp; Data Truth's
`physical_written_at` precedes acknowledgement, WAL visibility, and the same
authority verification; and persisted history records no availability event.
Those fields must not be reinterpreted as either availability dimension.

A future, separately authorized fit decision must select a provider-neutral
availability-evidence mechanism. Whatever physical representation is chosen
(for example a ledger, composition metadata, or another immutable audited
record) must preserve immutable, auditable evidence, avoid changing sealed
contracts, and permit exact pairwise cutoff qualification. This draft makes no
storage selection and authorizes no availability implementation.

## Selection, ordering, and pagination

Every request has a required selection window:

```text
SelectionAxis = ARRIVAL_TIME | EVENT_TIME
SelectionWindow(axis, start_ns, end_ns)  # [start_ns, end_ns); start_ns < end_ns
```

Selection is independent of output ordering. For example, a request can select
event time from 10:00 through 10:15, use a 10:16 cutoff, and order by event
time; it returns only selected paired records whose evidence and authority were
both available by 10:16.

For `EVENT_TIME` selection, the reader first applies the availability cutoff,
requested authority policy, asset filters, and channel filters. If any
candidate in that qualified scope has a null `provider_timestamp`, the read
fails closed with `UNSUPPORTED_EVENT_TIME` before evaluating the event-time
window. It must not silently exclude that candidate, substitute
`received_timestamp`, invent event time from `sid`/`seq`, or claim the event
window is complete. `ARRIVAL_TIME` selection remains valid for a
null-provider-time record.

V1 permits only these deterministic ordering rules:

```text
ARRIVAL:      (received_timestamp ASC, capture_id ASC)
STRICT_EVENT: (provider_timestamp ASC, received_timestamp ASC, capture_id ASC)
```

`capture_id` is the sufficient final tie-breaker; this contract introduces no
availability sequence. `STRICT_EVENT` fails closed with
`UNSUPPORTED_EVENT_TIME` if any selected candidate has a null
`provider_timestamp`; it must not silently fall back to arrival ordering.

Pagination is included in the V1 contract. The first page binds a provider-
neutral, immutable `SOURCE_SNAPSHOT_IDENTITY`: the fixed source-membership
boundary for one paged As-Of view. It is included in view provenance and in the
next cursor. Subsequent pages must use that same identity; an identity change
or mismatch fails with `CURSOR_MISMATCH`. If a source cannot honor the bound
identity, it fails with `SOURCE_UNAVAILABLE`. No snapshot mechanism, global
sequence, snapshot database, table, or custom query framework is selected by
this contract.

A cursor binds at minimum the As-Of contract version,
`authority_policy_version`, `as_of_cutoff_ns`, selection axis and window,
asset/channel filters, ordering-rule version, `SOURCE_SNAPSHOT_IDENTITY`, and
last deterministic ordering key. Reuse with a different bound value fails with
`CURSOR_MISMATCH`; malformed cursors fail with `INVALID_CURSOR`. Pagination
does not use unstable `OFFSET` semantics.

Availability evidence that arrives or is backfilled after a source snapshot is
bound must not retroactively mutate the membership represented by that
`SOURCE_SNAPSHOT_IDENTITY`. This is a contract invariant only. A later
implementation-plan / upstream-fit gate must prove how a provider supplies the
identity and preserves this invariant; otherwise pagination remains
unimplemented rather than weakening this contract.

## Public read contract

The public surface is read-only and conceptual until an implementation plan is
authorized:

```text
AsOfRequest(
    as_of_cutoff_ns,
    authority_policy_version,
    selection_window,
    ordering,
    assets,
    channels,
    page_size,
    cursor,
)

ReplayAsOf.read(request) -> AsOfReplayView
```

There is no CRUD surface, no raw-only public mode, and no public operation that
recreates historical decisions through `DataTruth.decide()`. The adapter may
depend only on public physical/read authorities; the contract remains
provider-neutral.

The V1 output is always paired:

```text
AuthoritativeReplayRecord:
  CaptureFact
  recorded TruthDecision
  evidence availability evidence/reference
  authority availability evidence/reference

AsOfReplayView:
  immutable record tuple/page
  request identity
  authority policy version
  cutoff semantics/version
  selection window
  ordering rule/version
  source snapshot identity
  completeness = NOT_ASSERTED
  explicit exclusions/anomalies
  provenance
  next cursor
```

The contract-level error taxonomy is: `INVALID_REQUEST`, `INVALID_CURSOR`,
`SOURCE_UNAVAILABLE`, `MALFORMED_EVIDENCE`, `MALFORMED_AUTHORITY`,
`AUTHORITY_CONFLICT`, `AVAILABILITY_EVIDENCE_MISSING`,
`UNSUPPORTED_EVENT_TIME`, and `CURSOR_MISMATCH`. None implies a completeness
claim.

## Completeness, anomalies, and provenance

V1 exposes no `require_complete` switch. Every result declares
`COMPLETENESS_STATE = NOT_ASSERTED`. It may surface known exclusions and
anomalies, but it never claims complete coverage, a gap-free stream, or the
latest world state.

It must not fabricate a baseline, silently fill gaps, redownload evidence, or
silently exclude quarantined material. Known malformed, conflicting, or
unavailable evidence fails closed when required for a requested paired record;
known exclusions are recorded in provenance. Absence cannot support a clean
claim, and unknown completeness remains `NOT_ASSERTED`. A future strict
completeness claim requires separately authorized Gap/Coverage authority.

Required bounded provenance includes the As-Of contract version, request
parameters, `authority_policy_version`, cutoff, selection window, ordering
rule, assets, channels, source authority identity, `SOURCE_SNAPSHOT_IDENTITY`,
capture IDs, decision subject and policy, both availability references,
completeness state, explicit exclusions/anomalies, and cursor identity. Any
future COLD extension may add manifest, chunk, and checksum provenance only; it
does not authorize COLD mechanics, Parquet, ZSTD, or a new dependency in V1.

## Integration seams and next gate

QuestDB may supply generic strong filters, binds, ordering, joins, WAL
primitives, and possibly SQL `ASOF` as a primitive. None supplies the semantic
contract above by itself, and this document selects no query engine or new
dependency.

Replay & As-Of must remain independently removable from Storage, Data Truth,
and Market Ingress. Its composition adapter depends on their public physical
read authorities, while its contract remains provider-neutral. Canonical
Dataset is a future consumer, not an owner or prerequisite.

## Current next

**Current NEXT:** a separately reviewed Slice 4 — Data System Recorder
Composition implementation task.
`SAFE_TO_BEGIN_REPLAY_AS_OF_SLICE_4_IMPLEMENTATION = YES` because Slices 1–3
engineering prerequisites are FINAL CLOSED. This status record does not begin
Slice 4.

Slice 4 is owned by the upper Data System composition layer, not by a new Replay
leaf. Its planned files are `src/live15_quant_v2/data/recorder_composition.py`,
`tests/test_replay_as_of_recorder_composition.py`, and
`tests/test_questdb_replay_as_of_end_to_end.py`. It composes sealed public seams
without widening CaptureFact, Capture Boundary, Durable Persistence, HotStore,
CaptureRange, DataTruth, TruthDecision, TruthDecisionHistory, AvailabilityStore,
AvailabilityWriter, ReplaySource, or ReplayAsOf, and must not use sibling
private helpers or own SQL, QuestDB sender/WAL mechanics, clocks, cursor logic,
retry/disk queues, leases, schedulers, or distributed infrastructure.

The sealed sequence is Market Ingress → Capture Boundary → Durable Persistence
→ exact Hot Store read-back proof → EVIDENCE marker attempt →
`DataTruth.decide()` → AUTHORITY marker attempt. `LOCAL_PERSISTENCE_FAILED` or
`DEFINITELY_REJECTED` creates no evidence marker and performs no Data Truth;
`PERSISTED_PENDING`, `ACKNOWLEDGED_OK`, and `IN_DOUBT` are not proof without an
exact immutable read-back. A marker failure or `IN_DOUBT` after successful proof
does not invalidate evidence, block Data Truth, roll back authority, or permit
blind reappend; fresh public proof/reconciliation is required.

Slice 4 acceptance must cover the persistence and read-back status matrix,
marker definite/ambiguous failure isolation, Data Truth failure/re-entry,
Replay exclusion while markers are unavailable, and no rollback of lower
authority. Its real end-to-end path is task-owned disposable infrastructure only:
Capture Boundary → Durable Persistence → read-back → markers → Data Truth →
markers → ReplayAsOf. It excludes canonical tables/runtime/service activation,
production Recorder deployment, canonical availability/TruthDecision/Replay
activation, production `CLOCK_SAFETY` closure, Canonical Dataset, Model/training,
Trading, and Operations expansion. `LAST_MARKER_FLOOR_ALONE_INSUFFICIENT` and
the canonical `CLOCK_SAFETY` gate remain preserved and open.
