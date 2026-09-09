# Canonical Dataset

## Status and responsibility

**Contract status:** CANDIDATE / PENDING INDEPENDENT REVIEW.
**Engineering implementation:** NOT IMPLEMENTED.
**Implementation plan:** NOT STARTED.
**Canonical physical materialization:** NOT AUTHORIZED / NOT PERFORMED.
**Model/training:** NOT STARTED.
**Trading:** NOT STARTED.

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
state. Replay exclusion provenance must also be consistent for the shared
snapshot. A Replay cursor failure, source-unavailable result, snapshot drift,
or malformed/inconsistent page fails the entire dataset build. There is no
partial Canonical Dataset snapshot and no mixed-source recovery to "latest."

`page_size` is delivery mechanics only. The same Replay semantic request,
source snapshot, and authoritative records must describe the same Canonical
Dataset regardless of a page size such as 10 or 1000. Page size is not part of
dataset identity, dataset policy version, or canonical membership policy.

## V1 admissibility policy

The semantic policy version is `canonical-dataset/v1`. It owns admissibility,
dataset-identity semantics, manifest semantics, and deterministic rebuild
rules. Any later change to category-admissibility semantics requires a new
policy version.

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

Its identity is deterministic and cryptographic, conceptually:

```text
SHA-256(canonical JSON({
  dataset_contract_version,
  dataset_policy_version,
  replay_request_identity,
  replay_source_snapshot_identity,
  authority_policy_version,
  ordered_included_record_semantic_digests,
}))
```

Each included record's semantic digest binds more than `capture_id`: it binds
the immutable `CaptureFact` content and immutable `TruthDecision` content,
including decision policy, subject, category, contributing capture IDs, reason,
and optional EventIdentity. Replay availability proofs and source provenance
remain in snapshot provenance. Python `hash()`, random UUIDs, wall-clock build
time, physical row number, database order, paths, file modification times,
machine identity, and connection strings are never semantic identity inputs.

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
latest, silent append, or last-write-wins dataset behavior. With the same
contract version, dataset policy, Replay request identity, Replay source
snapshot identity, and authoritative record content, rebuilds across process
restarts, page sizes, and materialization runs yield the exact same identity and
ordered membership. A different cutoff, selection, asset/channel filter,
ordering, Replay source snapshot, Data Truth policy, dataset policy, or
included authoritative content yields a new dataset identity. Old snapshots
remain immutable historical artifacts.

If Replay cannot reproduce the bound source snapshot while paging, the build
fails closed. It must not merge records from snapshots, restart from latest,
discard a cursor, or return a partial dataset.

## Manifest, exclusions, and failure boundary

A deterministic build manifest is required conceptually, without choosing a
file or database format. It records dataset identity and policy; Replay request
and source-snapshot identities; authority policy; cutoff; selection, ordering,
assets, and channels; included count and ordered semantic membership/digests;
Replay exclusions; Canonical Dataset category exclusions; and completeness
`NOT_ASSERTED`.

Exclusion provenance must deterministically answer which capture was excluded
and why. It includes both Replay-produced exclusions (for example, evidence or
authority unavailable by cutoff) and Canonical Dataset exclusions for
`DUPLICATE`, `CONFLICT`, and `NOT_ACCEPTED`. Non-accepted authority cannot
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

This candidate permits only independent contract review. It does not authorize
an implementation plan, source code, physical dataset materialization, Canonical
Dataset activation, canonical Replay/availability/TruthDecision activation,
production Recorder deployment, `CLOCK_SAFETY` closure, Model/training, or
Trading.

### Candidate self-review

This contract requires provenance sufficient to reconstruct included authority;
page-size-independent identity; no mixed or partial build on source drift; no
silent duplicate/conflict inclusion; no accepted-observation hash deduplication;
no invented EventIdentity; no completeness claim; no physical metadata in
semantic identity; no in-place snapshot mutation; and no research bypass of
bounded Replay authority while calling the result canonical.
