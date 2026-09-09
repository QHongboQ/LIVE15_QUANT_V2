# Replay & As-Of

## Status and responsibility

**Contract authority:** DRAFT CANDIDATE / PENDING INDEPENDENT REVIEW.
**Implementation:** NOT IMPLEMENTED.
**Implementation plan:** NOT YET AUTHORIZED; the next gate after contract
closure is implementation-plan / availability-mechanism fit preparation.
**Canonical activation:** NOT AUTHORIZED.

Replay & As-Of is a direct Data System child. It owns a research-facing,
read-only projection of already persisted immutable evidence and already
recorded `TruthDecision` authority. Its bounded responsibilities are:

1. historical replay of persisted immutable evidence for research;
2. replay/read projection of an already-recorded `TruthDecision`;
3. strict bounded historical-knowledge As-Of views;
4. deterministic ordering;
5. bounded provenance; and
6. explicit nonclaims about completeness.

It does not own or perform StreamFeed transport replay/resend, physical
transport idempotency, ingress recovery/reconnect/redownload/gap repair,
Data Truth adjudication or re-adjudication, features, labels, Canonical
Dataset construction, models, training, or trading.

The following terms are intentionally distinct:

| Term | Meaning in this contract |
| --- | --- |
| **TRANSPORT REPLAY** | Re-sending provider/StreamFeed transport material. Out of scope. |
| **PHYSICAL REPLAY** | Replaying storage/transport frames or recovery mechanics. Out of scope. |
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

V1 permits only these deterministic ordering rules:

```text
ARRIVAL:      (received_timestamp ASC, capture_id ASC)
STRICT_EVENT: (provider_timestamp ASC, received_timestamp ASC, capture_id ASC)
```

`capture_id` is the sufficient final tie-breaker; this contract introduces no
availability sequence. `STRICT_EVENT` fails closed with
`UNSUPPORTED_EVENT_TIME` if any selected candidate has a null
`provider_timestamp`; it must not silently fall back to arrival ordering.

Pagination is included in the V1 contract. A cursor binds the exact request
identity, cutoff, selection axis and window, ordering-rule version, and last
deterministic key. Reuse with a different bound value fails with
`CURSOR_MISMATCH`; malformed cursors fail with `INVALID_CURSOR`. Pagination
does not use unstable `OFFSET` semantics.

## Public read contract

The public surface is read-only and conceptual until an implementation plan is
authorized:

```text
AsOfRequest(
    as_of_cutoff_ns,
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
  cutoff semantics/version
  selection window
  ordering rule/version
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
parameters, cutoff, selection window, ordering rule, assets, channels, source
authority identity, capture IDs, decision subject and policy, both availability
references, completeness state, explicit exclusions/anomalies, and cursor
identity. Any future COLD extension may add manifest, chunk, and checksum
provenance only; it does not authorize COLD mechanics, Parquet, ZSTD, or a new
dependency in V1.

## Integration seams and next gate

QuestDB may supply generic strong filters, binds, ordering, joins, WAL
primitives, and possibly SQL `ASOF` as a primitive. None supplies the semantic
contract above by itself, and this document selects no query engine or new
dependency.

Replay & As-Of must remain independently removable from Storage, Data Truth,
and Market Ingress. Its composition adapter depends on their public physical
read authorities, while its contract remains provider-neutral. Canonical
Dataset is a future consumer, not an owner or prerequisite.

After independent contract review and closure, the only authorized next
activity is implementation-plan / availability-mechanism fit preparation.
Implementation code, availability storage, canonical runtime or table
activation, and canonical dataset work require separate authorization.
