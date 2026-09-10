# Canonical Dataset implementation plan

## 1. Status

**Plan status:** CANDIDATE / PENDING INDEPENDENT REVIEW.
**Contract authority:** FINAL CLOSED.
**Engineering implementation:** NOT IMPLEMENTED / NOT AUTHORIZED.
**Physical materialization:** NOT AUTHORIZED / NOT PERFORMED.

This is a plan only. It creates no Python module, physical artifact, table,
runtime activation, Research & Model behavior, or Trading behavior. The next
gate is ChatGPT exact-head implementation-plan review.

## 2. Authority and prerequisites

The sole authority input is the FINAL CLOSED public Replay interface:

```text
ReplayAsOf.read(AsOfRequest) -> AsOfReplayView
```

The builder consumes paired `AuthoritativeReplayRecord` values. `CaptureFact`,
`TruthDecision`, `TruthDecisionCategory`, `TradeNotAcceptedReason`,
`EventIdentity`, and `ReplayExclusion` retain their sealed meanings. The
builder must not call Data Truth, Storage, availability writers/stores, a
QuestDB adapter, Market Ingress, or SQL; it does not re-qualify As-Of.

The exact V1 policy is `canonical-dataset/v1`: `ACCEPTED` is included;
`DUPLICATE`, `CONFLICT`, and `NOT_ACCEPTED` are excluded with audit provenance.
This is admissibility, never a new truth decision or a second dedup engine.

## 3. Contract invariants

- One build consumes every Replay page through `next_cursor = None`; a page is
  never a dataset and a later failure returns no partial snapshot.
- Replay-delivered `ARRIVAL` or `STRICT_EVENT` order is retained; the builder
  does not re-sort included records.
- `page_size` and cursor tokens are delivery mechanics, never semantic inputs.
- `EventIdentity = None` is valid. Two alike accepted Observation Facts remain
  two rows.
- `COMPLETENESS = NOT_ASSERTED` is preserved with no coverage/current/leakage
  claim.
- Snapshot identity is SHA-256 of canonical semantic bytes. A snapshot is
  immutable: no update-current, overwrite, or latest authority exists.
- Physical representation is unselected and cannot affect dataset identity.

## 4. Proposed package/module layout

After separate implementation authorization, use a small cohesive package:

```text
data/canonical_dataset/
├─ __init__.py          # public exports only
├─ models.py            # immutable Canonical Dataset values
├─ builder.py           # deep builder: bytes, digests, pages, invariants,
│                        # membership, manifest, and identity
└─ materialization.py   # later physical adapter, after format selection only
```

Slice 1 requires only `models.py` and `builder.py`. There is deliberately no
serializer, hasher, pager, policy, or error-framework module: the builder is a
deep module with one small interface and local verification. `materialization.py`
is not created until a separately accepted format-fit POC selects an adapter.

`models.py` owns immutable `CanonicalDatasetSnapshot`,
`CanonicalDatasetManifest`, `CanonicalIncludedRecord`,
`CanonicalCategoryExclusion`, and `CanonicalReplayExclusion`. An included
record retains the sealed `AuthoritativeReplayRecord` and adds its digest; it
does not copy or reinterpret CaptureFact or TruthDecision semantics.

## 5. Public seam

```text
CanonicalDatasetBuilder(replay: ReplayAsOf)
build(request: AsOfRequest) -> CanonicalDatasetSnapshot
```

`build()` requires a fresh request (`cursor is None`) and returns an immutable
in-memory snapshot only after complete traversal. Continuation requests are
private mechanics made from the same request plus the returned cursor. Tests
use the existing public `ReplayAsOf` with `InMemoryReplaySource`; no second,
hypothetical Replay protocol is introduced for one adapter.

A later physical adapter receives only a completed snapshot; it never reads
Replay or Data Truth. The pure core has no filesystem, Parquet, QuestDB,
DuckDB, object-store, or layout dependency.

## 6. Internal ownership

`CanonicalDatasetBuilder` owns traversal, cross-page invariants, V1
admissibility, deterministic exclusions, semantic manifest construction, and
all-or-nothing identity derivation. Replay owns request validation, availability
qualification, cursor/source-snapshot meaning, and Replay errors. Data Truth
owns decision and event-identity meaning. A future physical adapter owns
bytes-on-disk integrity and publication, never semantic membership.

## 7. Deterministic serialization

`builder.py` owns exactly one private canonical-value encoder and one canonical
JSON byte function. Every record digest and manifest identity uses it; callers
cannot independently assemble hash objects.

V1 bytes are UTF-8 JSON with `sort_keys=True`, separators `(',', ':')`, and
`ensure_ascii=False`. Keys must be strings and are sorted; lists/tuples become
arrays in supplied semantic order unless a named canonicalization rule says
otherwise. `None` is `null`; integers are JSON integer tokens; booleans and
floats are rejected unless a later policy defines them. Strings, especially
`CaptureFact.payload`, are exact immutable strings: no trim, parse,
normalization, `repr()`, or platform-dependent formatting.

`StrEnum` values encode as `.value`; `AssetId` as its approved string;
`TruthDecisionCategory` and `TradeNotAcceptedReason` as `.value`.
`EventIdentity` is `null` or an object with its four named fields.
`contributing_capture_ids` preserves tuple order. Canonical Replay exclusions
sort by `(capture_id, code)` and category exclusions by `(capture_id, category,
record_digest, disposition)`. Python `hash()`, time, UUIDs, paths, physical
order, page size, and cursors are prohibited identity inputs.

## 8. Authoritative-record digest

One concept, `authoritative_record_digest(record)`, hashes this object:

```text
{
  capture_fact: {
    capture_id, asset, provider, source_id, channel, message_type,
    event_subtype, sid, seq, provider_timestamp, received_timestamp,
    schema_version, payload
  },
  truth_decision: {
    subject_capture_id, category, policy_version, contributing_capture_ids,
    reason, event_identity: {provider, source_id, message_type, trade_id} | null
  },
  evidence_availability_reference,
  authority_availability_reference
}
```

It applies to included and category-excluded records alike. It never hashes only
`capture_id`, decodes availability references, or creates a parallel truth value.

Slice 1 will keep expected field-name sets for `CaptureFact`, `TruthDecision`,
and `EventIdentity`, compare them to `dataclasses.fields()` before serialization,
and fail closed on drift. Tests mutate every listed field and assert a changed
digest. A new immutable upstream field therefore cannot silently fall out of
identity semantics without an explicit policy/version review.

## 9. Manifest and dataset identity

First create `semantic_manifest_core`, then derive:

```text
dataset_identity = SHA-256(canonical_json_utf8(semantic_manifest_core))
```

The identity is not inside its own core. The core includes:

- `dataset_policy_version = canonical-dataset/v1`;
- Replay `request_identity` and `source_snapshot_identity`;
- authority policy, `COMPLETENESS = NOT_ASSERTED`, As-Of cutoff, selection
  axis/window, ordering, ordering-rule version, and canonical asset/channel
  filters;
- ordered included authoritative-record digests;
- canonical category exclusions with capture ID, category, record digest, and
  fixed V1 disposition; and
- canonical Replay exclusions with public capture ID and `ReplayExclusionCode`.

`request_identity` transitively binds the request, but normalized request
context is also explicit for independent audit. The builder normalizes assets
and channels by the sealed Replay rules (sorted unique values, `None` when
unfiltered) and requires agreement with the first view's request identity.
The final manifest adds derived identity and nonsemantic display counts only.
It never adds path, encoding, checksum, file time, or cursor. Same identity
with unequal cores fails closed as an identity conflict.

## 10. Full-pagination algorithm

1. Reject a caller cursor; call `ReplayAsOf.read()` with the semantic request
   and `cursor=None`.
2. Capture first-page request identity, source snapshot, authority policy,
   cutoff, selection window, ordering, ordering-rule version, completeness, and
   canonicalized Replay exclusions as traversal invariants.
3. Process delivered records in order: include `ACCEPTED`; transform each other
   category into a category exclusion using its authoritative-record digest.
4. While `next_cursor` exists, replace only the cursor on the same semantic
   request and read the next page.
5. Require all subsequent page invariants and canonical Replay exclusions to
   equal the first page; append without re-sorting.
6. Only at terminal cursor construct the core, final manifest, identity, and
   immutable snapshot.

Any invariant mismatch, malformed policy, model-field drift, or identity
conflict fails the whole build. `ReplayAsOfError`, including
`SOURCE_UNAVAILABLE` and `CURSOR_MISMATCH`, escapes unchanged. There is no
restart-from-latest, cursor discard, source mixing, or partial output.

## 11. Error behavior

Canonical Dataset owns only unsupported dataset policy, malformed/inconsistent
cross-page view, immutable-model/manifest invariant failure, and semantic
identity conflict. It preserves sealed Replay failures rather than duplicating
or weakening Replay's error taxonomy. No generic error framework is needed.

## 12. Physical-format POC gate

No final format is selected. Slice 2 is a bounded format-fit POC using a small
approved read-only V2 fixture or synthetic completed snapshot, never production
data. Parquet + ZSTD through mature PyArrow is the strong initial candidate
because V1 supplies reference evidence; V1 code, adoption, and Production
activation are neither inherited nor authorized.

The POC must demonstrate exact round-trip CaptureFact, TruthDecision,
availability references, ordered membership, and manifest; exact payload
strings; nulls (`provider_timestamp=None`, `EventIdentity=None`); deterministic
re-read; artifact checksum; schema fidelity; practical cross-platform read;
compression; read/write throughput; bounded memory; and upstream maturity. It
returns `ACCEPT`, `REJECT`, or `DEFER`. One minimal alternative is permitted
only after a concrete documented failure of the primary candidate; no
multi-format bakeoff is authorized.

## 13. Semantic versus physical identity

`dataset_identity` identifies semantic content. A physical artifact checksum
identifies encoded bytes and detects corruption. Valid encodings may share a
dataset identity; a claimed matching identity never excuses checksum or read-
back failure. The POC and later adapter keep both values separate, with no
physical value in the semantic core.

## 14. Immutable materialization strategy

Only after selected-format acceptance and separate Slice 3 authorization, an
adapter writes a dataset-identity-addressed or manifest-bound artifact to
staging, writes/verifies manifest and checksum, performs exact read-back, then
atomically promotes using mature upstream or standard-library filesystem
mechanics. It never overwrites or creates authoritative `latest`. If the
identity destination exists, it verifies semantic/artifact compatibility and
fails closed on any difference. This is not authorization to implement it now.

## 15. Implementation slices

### Slice 1 — Pure Canonical Dataset Core

Implement immutable models; the deep builder; canonical bytes; record digest;
complete pages; invariants; V1 membership/exclusions; manifest; identity; and
in-memory snapshot. No database, filesystem, physical dependency, or format.

### Slice 2 — Physical-format fit POC

Own only candidate-format evidence and `ACCEPT`/`REJECT`/`DEFER`. A pass does
not create production materialization code.

### Slice 3 — Physical materialization adapter

Only after separately accepted format selection: selected encoder, immutable
artifact/manifest write, checksum/read-back, atomic publication, and collision
fail-closed behavior. It depends on Slice 1, never Replay or Data Truth.

### Slice 4 decision — no separate slice by default

If Slice 3 exists, a narrow composition acceptance can prove
`ReplayAsOf → Builder → verified artifact`. A Slice 4 is warranted only if a
future Research & Model interface creates a real second adapter/seam; it must
not implement Research & Model logic.

## 16. Test plan

Slice 1 tests precede code and cover empty, one, multiple, and mixed results;
all non-accepted categories; `EventIdentity=None`; two alike accepted
Observation Facts retained independently; and delivered ARRIVAL/STRICT_EVENT
order. Identity tests mutate every CaptureFact/TruthDecision field, both
availability references, replay-exclusion code, category/disposition, request
context/identity, source snapshot, authority policy, ordering, and completeness.

They prove deterministic bytes, repeated rebuild equality, one-page/multi-page
equality, small/large page-size equality, and cursor/page-size absence from the
core. Failure tests cover page/exclusion mismatch, later-page cursor or source
failure with no output, source drift, field-set drift, malformed policy, and
identity conflict. `provider_timestamp=None` behavior is accepted or rejected
only as delivered by Replay; the builder neither substitutes a timestamp nor
re-qualifies As-Of. Slice 2/3 tests use only synthetic or task-owned fixtures.

## 17. Architecture checks

Future architecture tests permit only Replay public-package and sealed semantic
model imports. They reject HotStore, QuestDB sources, TruthDecisionHistory,
AvailabilityStore/Writer, Market Ingress, SQL, `DataTruth.decide`, and Research
& Model imports. Slice 1 also rejects physical/filesystem imports. A later
materialization adapter may receive a narrow exception only after selection and
still cannot use Replay internals or Data Truth persistence.

## 18. Acceptance gates

- **Gate A:** pure-core architecture and contract fit.
- **Gate B:** pure-core deterministic unit/in-memory Replay acceptance.
- **Gate C:** physical-format POC recommendation (`ACCEPT`/`REJECT`/`DEFER`).
- **Gate D:** separately authorized selected physical-adapter acceptance.
- **Gate E:** disposable Replay-to-Builder-to-verified-artifact acceptance.

No gate alone authorizes production runtime/data, Recorder, model training, or
trading. Every implementation slice needs its own bounded task, review,
exact-head CI, guarded merge, merge-SHA CI, and closure.

## 19. Upstream dependency strategy

Slice 1 uses only standard `dataclasses`, `json`, and `hashlib`; no new
dependency is justified. After the POC, PyArrow may be proposed only if it is
selected for Parquet + ZSTD. That proposal must pin an exact compatible version,
document columnar responsibility, upstream maturity/security cadence, and
Apache-2.0 license/provenance. Standard-library atomic rename is preferred for
same-filesystem local promotion; otherwise an upstream filesystem primitive must
be justified. No V1 code is copied.

## 20. Explicit non-authorization and next gate

This candidate authorizes no implementation, format selection, materialization,
QuestDB/data/runtime change, canonical Replay/Availability/TruthDecision
activation, Recorder deployment, features, labels, Model/training, or Trading.
The asset universe remains BTC, ETH, GOLD, SILVER, XRP, SOL, HYPE, DOGE, and
BNB; WTI does not exist.

The next gate is ChatGPT independent exact-head implementation-plan review.
Only full review/fix/CI/guarded-merge/merge-SHA-CI/final-closure can make plan
authority FINAL CLOSED; implementation then still needs separate authorization.
