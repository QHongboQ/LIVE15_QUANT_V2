# Canonical Dataset

## Status and responsibility

**Contract authority:** FINAL CLOSED.
**Engineering implementation:** NOT IMPLEMENTED / NOT AUTHORIZED.
**Implementation plan:** CURRENT NEXT / NOT STARTED.
**Canonical physical materialization:** NOT AUTHORIZED / NOT PERFORMED.
**Model/training:** NOT STARTED / NOT AUTHORIZED.
**Trading:** NOT STARTED / NOT AUTHORIZED.

Canonical Dataset is one direct Data System child. It turns one strictly
bounded authoritative Replay view into an immutable, deterministic, versioned
dataset snapshot: the controlled handoff from Data System to a future Research
& Model System.

```text
ReplayAsOf
→ bounded authoritative Replay snapshot
→ Canonical Dataset admissibility policy
→ immutable CanonicalDatasetSnapshot
→ future Research & Model System
```

Its responsibility is authoritative membership, a deterministic materialization
boundary, and provenance. It is not a model pipeline, a truth-adjudication
system, an archive implementation, or a mutable "current data" service.

## Sealed upstream authority

Canonical Dataset consumes authority only through the FINAL CLOSED Replay public
boundary:

```text
ReplayAsOf.read(AsOfRequest)
→ complete paginated sequence of AsOfReplayView
→ AuthoritativeReplayRecord
```

`AsOfRequest`, `AsOfReplayView`, `AuthoritativeReplayRecord`, `ReplayAsOf`,
`TruthDecision`, `TruthDecisionCategory`, and `CaptureFact` retain their sealed
upstream meanings. Data Truth authority arrives inside each
`AuthoritativeReplayRecord` as its immutable `TruthDecision`; Canonical Dataset
does not re-adjudicate it.

Canonical Dataset must not independently call `DataTruth.decide()`,
`TruthDecisionHistory`, `QuestDBTruthDecisionHistory`, `HotStore`,
`QuestDBHotStore`, `QuestDBReplaySource`, `AvailabilityStore`,
`AvailabilityWriter`, or Market Ingress. It neither reads physical SQL nor
creates a second authority path.

## Complete bounded Replay request

One Canonical Dataset build corresponds to one complete semantic Replay request,
not to one delivered page. It consumes pages until `next_cursor = None`:

```text
page 1 → next_cursor → page 2 → … → next_cursor = None
```

Every page must preserve the same `request_identity`,
`source_snapshot_identity`, `authority_policy_version`, As-Of cutoff,
selection window and axis, ordering and ordering-rule version, and completeness
state, including the same canonical asset and channel filters bound by the
request. Replay exclusions returned on subsequent pages must be semantically
identical after deterministic canonicalization. A difference is a malformed or
inconsistent Replay view and fails the entire dataset build. A Replay cursor
failure, source-unavailable result, or snapshot drift also fails the build.
There is no partial Canonical Dataset snapshot and no mixed-source recovery to
"latest."

`page_size` is delivery mechanics only. The same Replay semantic request,
source snapshot, and authoritative records must describe the same Canonical
Dataset regardless of a page size such as 10 or 1000. Page size is not part of
dataset identity, dataset policy version, or canonical membership policy.

## V1 admissibility policy

The semantic policy version is `canonical-dataset/v1`. It owns admissibility,
dataset-identity semantics, manifest semantics, and deterministic rebuild
rules. It is the single Canonical Dataset semantic/identity/manifest version in
V1; there is no separate `dataset_contract_version`. Any later incompatible
semantic change requires a new policy version.

| Recorded `TruthDecisionCategory` | Canonical row membership | Manifest treatment |
| --- | --- | --- |
| `ACCEPTED` | Included | Included authoritative membership |
| `DUPLICATE` | Excluded | Canonical category exclusion |
| `CONFLICT` | Excluded | Canonical category exclusion |
| `NOT_ACCEPTED` | Excluded | Canonical category exclusion |

Replay legitimately returns every valid recorded category because it owns
historical authority replay. Canonical Dataset owns the narrower decision of
which authoritative records are admissible as canonical research/training
source rows. It does not change Replay or Data Truth semantics to perform this
filtering.

Each included row is lossless with respect to its accepted authoritative input:
it preserves the immutable `CaptureFact`, its immutable `TruthDecision`, and
the Replay availability references/provenance needed for audit. It does not
rewrite `CaptureFact.payload`, timestamps, `capture_id`, `TruthDecision`, or
`EventIdentity`, and it creates no second truth representation.

Data Truth already owns Event Fact identity and duplicate/conflict
adjudication. Canonical Dataset must not add a generic deduplication engine.
In particular, it must not deduplicate accepted Observation Facts by payload
hash, timestamp, asset, source, `sid`, `seq`, value equality, nearest timestamp,
or physical/database row order. Every accepted authoritative replay record is
independently admissible under V1. `EventIdentity` is optional: Observation
Facts may have `EventIdentity = None` and remain valid canonical rows; no
universal logical event key may be fabricated.

## CanonicalDatasetSnapshot and identity

`CanonicalDatasetSnapshot` is a conceptual immutable value, not a Python or
storage implementation. Its semantic metadata includes at least:

- `dataset_identity` and `dataset_policy_version`;
- Replay `request_identity` and `source_snapshot_identity`;
- `authority_policy_version`, As-Of cutoff, selection axis/window, ordering,
  and ordering-rule version;
- canonical asset and channel filters from the bounded request;
- ordered included-record membership and semantic digests;
- deterministic Replay and Canonical Dataset exclusion provenance; and
- `completeness = NOT_ASSERTED`.

First define a deterministic `semantic_manifest_core`. Then derive
`dataset_identity = SHA-256(canonical JSON(semantic_manifest_core))`. The final
manifest may expose `dataset_identity`, but the core never contains its own
identity and therefore has no circular hash definition. At minimum the core
binds:

- `dataset_policy_version` (`canonical-dataset/v1`);
- Replay request and source-snapshot identities;
- authority policy and completeness state;
- ordered included authoritative-record semantic digests;
- deterministic Canonical Dataset category-exclusion provenance; and
- deterministic Replay-exclusion provenance.

One authoritative-record semantic digest applies to every
`AuthoritativeReplayRecord`, whether it is included or category-excluded. It
binds all immutable `CaptureFact` content, all immutable `TruthDecision`
content (including decision policy, subject, category, contributing capture
IDs, reason, and optional EventIdentity), and both opaque Replay provenance
values: `evidence_availability_reference` and
`authority_availability_reference`. Canonical Dataset does not decode,
reinterpret, or infer availability from those references.

For `ACCEPTED` records, the core binds the ordered authoritative-record digests.
For `DUPLICATE`, `CONFLICT`, and `NOT_ACCEPTED`, the core binds deterministic
category-exclusion provenance: `capture_id`, decision category,
authoritative-record semantic digest, and the canonical exclusion disposition.
For a Replay exclusion, the core binds exactly the public `capture_id` and
`ReplayExclusionCode`, canonicalized deterministically; it does not invent
missing `CaptureFact` or `TruthDecision` data. Thus a change to either
availability reference, either exclusion layer, or an excluded authoritative
record's meaning produces a new identity.

Python `hash()`, random UUIDs, wall-clock build time, physical row number,
database order, paths, file modification times, machine identity, connection
strings, page size, and cursors are never semantic identity inputs.

Canonical Dataset preserves the explicit Replay order from the request:
`ARRIVAL` or `STRICT_EVENT`. It must not silently re-sort by provider timestamp,
received timestamp, capture ID, or database order. The ordered included-record
sequence is bound into dataset identity.

## Strict As-Of, completeness, and revision

Canonical Dataset relies on Replay's strict qualification: an included record
was qualified only when its evidence and authority availability were both at or
before the bound As-Of cutoff. It must never infer availability from provider
timestamp, received timestamp, `sid`, `seq`, file creation time, or physical
write time, and it must not independently re-run that qualification.

A snapshot contains only authority Replay qualified at its bounded cutoff. It
exposes cutoff and request provenance so future Research & Model code can make
chronological choices, but it does not claim that a dataset alone guarantees
every future model is free of leakage. Future sample construction must still
select valid historical cutoffs.

Replay's `COMPLETENESS = NOT_ASSERTED` is preserved as Canonical Dataset
`NOT_ASSERTED`. Counts and provenance may be reported without claims of full
market coverage, all events, no gaps, or 100% coverage.

A snapshot is immutable once identified. There is no update-current, replace
latest, silent append, or last-write-wins dataset behavior. The same complete
`semantic_manifest_core` produces the same identity, ordered membership, and
exclusion provenance across process restarts, page sizes, and materialization
runs. Conversely, the same identity means the same complete semantic/audit
manifest core. A different Replay request or source snapshot, authority or
dataset policy, completeness state, included authoritative content, included
availability reference, Canonical Dataset category-exclusion provenance, or
Replay-exclusion provenance yields a new identity. Old snapshots remain
immutable historical artifacts.

If Replay cannot reproduce the bound source snapshot while paging, the build
fails closed. It must not merge records from snapshots, restart from latest,
discard a cursor, or return a partial dataset.

## Manifest, exclusions, and failure boundary

A deterministic build manifest is required conceptually, without choosing a
file or database format. Its `semantic_manifest_core` records dataset policy;
Replay request and source-snapshot identities; authority policy; completeness;
ordered included authoritative-record digests; deterministic Replay exclusions;
and deterministic Canonical Dataset category exclusions. The final manifest
adds its derived dataset identity plus redundant audit fields such as cutoff,
selection, ordering, assets, channels, included count, and ordered membership.

Exclusion provenance must deterministically answer which capture was excluded
and why. It includes both Replay-produced exclusions (the public capture ID and
code, such as evidence or authority unavailable by cutoff) and Canonical Dataset
exclusions for `DUPLICATE`, `CONFLICT`, and `NOT_ACCEPTED` with their
authoritative-record digest and disposition. Non-accepted authority cannot
silently disappear.

The bounded fail-closed classes are invalid dataset request/policy, Replay
source unavailable, Replay cursor/snapshot drift, malformed or inconsistent
Replay view, and dataset identity/invariant conflict. There is no partial
success. Where Replay supplies a precise public error, its meaning is
preserved rather than replaced by a competing Canonical Dataset interpretation.

## Explicit non-ownership

Canonical Dataset does not own features, indicators, returns, rolling windows,
normalization, embeddings, labels, future-return targets, train/validation/test
splits, walk-forward folds, model tensors, hyperparameters, or model training.
Those are future Research & Model responsibilities.

It does not reclassify decisions, resolve conflicts, choose duplicate
authority, correct provider values, fill/interpolate/forward-fill/back-fill
observations, invent baseline state, or claim latest state. It consumes Data
Truth and Replay authority; it does not create market truth.

This contract selects no physical format, archive, database, object store, or
dependency: not Parquet, ZSTD, Arrow, DuckDB, QuestDB, SQLite, S3, or MinIO.
V1 Research Data Authority is reference evidence for deterministic controlled
research inputs and provenance. V1 Parquet+ZSTD and verified COLD → RDA →
isolated-runner paths are bounded offline implementation references only; a
future implementation plan must revalidate any physical choice against a small
read-only V2 fixture before adoption.

"Canonical Dataset" does not mean one mutable `canonical.csv`, one current
table, or one latest rowset. Many immutable snapshots may exist for different
bounded requests, cutoffs, and policies. Any future latest convenience pointer
would be non-authoritative.

## Asset boundary and next gate

Canonical Dataset inherits the Data System `AssetId` authority: BTC, ETH, GOLD,
SILVER, XRP, SOL, HYPE, DOGE, and BNB. WTI does not exist. It creates no second
asset registry; bounded Replay request filters remain snapshot provenance.

The contract authority is FINAL CLOSED. The current next task is
implementation-plan design only; it does not authorize source code, physical
dataset materialization, Canonical Dataset activation, canonical
Replay/availability/TruthDecision activation, production Recorder deployment,
`CLOCK_SAFETY` closure, Model/training, or Trading.

### Contract review and closure evidence

This contract requires provenance sufficient to reconstruct included authority;
page-size-independent identity; no mixed or partial build on source drift; no
silent duplicate/conflict inclusion; no accepted-observation hash deduplication;
no invented EventIdentity; no completeness claim; no physical metadata in
semantic identity; no in-place snapshot mutation; and no research bypass of
bounded Replay authority while calling the result canonical. It also requires:
a changed evidence availability reference, Replay exclusion code, or excluded
category/disposition produces a new identity; page-size-only and restart-only
changes preserve identity when the complete semantic manifest core is unchanged.

The initial PR #55 head `5a48b8e0ae1c2b2e99590b0f7bb1b088772abf13` received
`CHANGES_REQUIRED`. The corrected approved head
`72238313b16d30e340d4390cabd0e8db19a07215` received ChatGPT exact-head `PASS`
and passed exact-head Ubuntu, Windows, and CI Gate checks. PR #55 then merged
through a guarded normal merge as
`3d61a4d8dac4a35c91dec314b5eaeb2098878a6d` with parents
`49c9c53b6b0027b6e4088df45e841c9d4a031c29` and
`72238313b16d30e340d4390cabd0e8db19a07215`; its merge-SHA Ubuntu, Windows,
and CI Gate checks and postmerge seal passed. No implementation, runtime,
physical data, or production activation occurred.

PR #56 approved head `c4319f9d62f83f5d59bbd35617e72e0465412f54` received
ChatGPT exact-head closure-review `PASS` and merged normally as
`0b1f5788aa09859aaa24b499a452ce7acfc02c3f` with parents
`3d61a4d8dac4a35c91dec314b5eaeb2098878a6d` and
`c4319f9d62f83f5d59bbd35617e72e0465412f54`. Its merge-SHA Ubuntu, Windows,
and CI Gate checks passed. Canonical Dataset contract authority is FINAL CLOSED
at this PR #56 status-closure merge; PR #55 remains the accepted
contract-content merge. Neither merge authorized implementation, runtime,
materialization, Model/training, or Trading.
