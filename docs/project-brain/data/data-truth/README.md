# Data Truth

## Status

**Contract authority:** FINAL CLOSED.

**Implementation-plan authority:** FINAL CLOSED; see
[implementation-plan.md](implementation-plan.md).

**Data Truth engineering implementation:** FINAL CLOSED.

**Slice 1 semantic-library implementation:** FINAL CLOSED. It provides no
persistent `TruthDecision` authority.

**QuestDB reconciliation POC gate:** FINAL CLOSED. The technical result is
PASS / ACCEPTED under the approved single-writer constraint.

**Slice 2 Persistent History implementation:** FINAL CLOSED.

**Persistent `TruthDecision` history implementation:** IMPLEMENTED / FINAL
CLOSED under the approved single-writer constraint. Concurrent `decide()` and
multi-process/multi-writer authority are NOT SUPPORTED.

**Canonical TruthDecision table:** NOT CREATED / NOT AUTHORIZED.

**Canonical Data Truth runtime activation:** NOT AUTHORIZED / NOT PERFORMED.

**Replay & As-Of engineering implementation:** FINAL CLOSED.

**Canonical Replay activation:** NOT AUTHORIZED / NOT PERFORMED.

**Canonical Dataset:** CURRENT NEXT / UNIMPLEMENTED.

**Model:** UNIMPLEMENTED.

**Trading:** UNIMPLEMENTED.

This sealed authority records the approved semantic boundary and final
implementation state. Slice 1 created no persistent authority by itself; the
separately reviewed Slice 2 adapter completed only the approved single-writer
implementation boundary, not canonical activation.

## Closure evidence

- DT-S1 through DT-S4 approved the two-child semantic tree,
  provider-observation truth, provider-proven event identity only, and
  append-only authority.
- Independent Standards, Spec, and Architecture re-reviews passed.
- PR #30 merged as `089e7aba2c78a8b66cbedd5e195cdf2325b4c51f`.
- Post-merge Windows, Ubuntu, and CI Gate checks passed.
- Slice 1 PR #33 merged as
  `f80c786307fe5e2c2092a0f2955f62ca03c9c7bb`; reviewed code head
  `78660844e690eeb73cacd8a756a4e65419c1a798` passed ChatGPT direct remote
  code audit.
- Merge-SHA Windows, Ubuntu, and CI Gate checks passed, and final local seal
  passed with local main and origin/main at
  `f80c786307fe5e2c2092a0f2955f62ca03c9c7bb`.
- QuestDB reconciliation POC PR #36 merged as
  `249144de204247bd7a0589d8ba67116c48b8dcc7`; reviewed POC head
  `a4fd011586289ede142d7d087f682898aef18530` passed ChatGPT direct remote POC
  review. Merge-SHA Windows, Ubuntu, and CI Gate checks passed, as did the
  merge-SHA local opt-in POC A-L (12 passed).
- Slice 2 Persistent History PR #38 reviewed head
  `8d43a2b0a603e0276bc580cf66414967bde567dc` passed ChatGPT GitHub-visible
  review and exact-head Ubuntu, Windows, and CI Gate checks. It merged as
  `abc4bdbd52150ab33ec60c0c6902235042d199f6`; its merge-SHA Ubuntu, Windows,
  and CI Gate checks passed, as did the local seal: 39 history units, 18
  architecture tests, 4 real integrations, and 223 ordinary tests passed with
  27 skipped; Ruff, MyPy, and diff checks passed. Task-owned Java, launcher,
  port, and root residue were zero, and the remote retained main only.

## Responsibility

Data Truth converts immutable shared `CaptureFact` evidence into auditable,
append-only `TruthDecision` authority. Its truth statement is deliberately
bounded: it adjudicates what a provider evidence record means under an approved
semantic policy; it does not claim complete, globally current, or world-state
truth.

The parent owns only:

- the provider-neutral public `CaptureFact` input and `TruthDecision` output;
- policy-version authority, shared invariants, routing, and composition of its
  children; and
- the rule that decisions retain immutable contributing evidence references.

The parent does not own event-specific identity, observation acceptance rules,
QuestDB or other storage mechanics, ingestion or transport, replay, Canonical
Dataset shaping, feature/model behavior, or trading behavior.

## Inputs and outputs

**Input:** the sealed shared immutable
[CaptureFact](../storage/README.md#storage) contract. Its existing evidence
fields — `capture_id`, asset, provider, source, channel, message type, event
subtype, session/sequence metadata, provider and received timestamps, schema
version, and frozen payload — are sufficient. Data Truth creates no second
transport envelope and requests no additional fields.

`capture_id` remains immutable evidence identity. It is not general logical
event identity.

**Output:** conceptual, append-only `TruthDecision` history. A decision needs
only a category, policy version, immutable contributing `CaptureFact`
reference(s), a bounded reason/classification, and an approved logical event
identity only when one exists. Database columns, serialization, and storage
technology are intentionally not decided here.

Authoritative history is append-only. A future latest-known/current projection
may be derived from it but is non-authoritative and unimplemented.

## Semantic tree

```text
Data Truth
├── Event Facts
└── Observation Facts
```

The children are semantic siblings, not message-family leaves. They share only
the parent public contract and sealed upstream authorities. They must not have
sibling imports, private API calls, shared mutable state, or one sibling
writing the other sibling's state.

The parent routes a fact to one child according to approved policy and composes
that child result. It must not absorb either child's private semantic rules.

## Shared invariants and boundaries

Hot Store's physical replay idempotency
`(received_timestamp, capture_id)` is not Data Truth semantic identity.
Pinned QuestDB Server `10.0.1` provides sufficient generic query/execution
mechanics for the currently approved Data Truth scope. QuestDB continues to own
physical WAL, DEDUP, UPSERT, and query execution; it does not decide Data Truth
semantics. LIVE15 owns only its narrow semantic policy; no Flink, RisingWave,
Materialize, Kafka, state store, database, streaming engine, custom rule engine,
queue, replay engine, watermark engine, or generic dedup system is currently
justified. This is not a permanent prohibition: if a future separately approved
semantic or mechanical requirement exposes a proven missing mechanic, upstream
fit must be reassessed before custom infrastructure is built.

V1 has no global event-time authority, watermark, late-data engine, semantic
completeness assertion, source-precedence policy, or correction/supersession
policy. `provider_timestamp` and `received_timestamp` remain evidence and
`received_timestamp` is not silently promoted to semantic event time. Transport
gaps remain outside Data Truth.

Data Truth does not mutate CaptureFacts; own physical transport replay
deduplication; own Market Ingress transport/retry/reconnect behavior; own
QuestDB lifecycle, archive, retention, Replay & As-Of, Canonical Dataset
shaping, feature engineering, labels, models, predictions, signals, positions,
orders, PnL, or strategy-specific filtering. It does not authorize canonical
runtime activation.

## Removability

Removing either semantic child may require only parent routing/composition
adjustment. It must not require a change to the surviving child, `CaptureFact`,
Storage, Market Ingress, or QuestDB Runtime. This removability is a contract
invariant, not a future refactoring preference.

## Child authorities

- [Event Facts](event-facts.md) owns the narrow approved event-identity
  adjudication.
- [Observation Facts](observation-facts.md) owns acceptance of provider
  observations without inventing logical event identity.

## Implementation closure and current boundary

The implementation-plan authority is FINAL CLOSED. Slice 1 is FINAL CLOSED.
The QuestDB TruthDecision-history persistence/reconciliation fit is **PROVEN
UNDER THE APPROVED SINGLE-WRITER CONSTRAINT** by the FINAL CLOSED, PASS /
ACCEPTED POC gate. The POC proves direct append acknowledgement, exact
server-visible subject lookup, committed-but-no-caller-ACK reconciliation,
ambiguous absence remaining in-doubt, no blind reappend, fail-closed
conflicting/multiple authority, and append-only operation without DEDUP or
UPSERT.

The POC alone did not implement a production `questdb_history.py`, production
`find_accepted_event` behavior, or Hot Store evidence resolution. Slice 2 was
subsequently authorized, implemented, independently reviewed, merged as PR
#38, and is FINAL CLOSED under the approved single-writer constraint. It adds a
private `QuestDBTruthDecisionHistory` adapter with provider-neutral HotStore
evidence resolution, append-only WAL history without DEDUP or UPSERT,
`auto_flush=False` explicit-FSN handling, an upstream `wait_wal_table`
visibility barrier, and no blind write retry.

Canonical TruthDecision-table creation and canonical runtime activation remain
NOT AUTHORIZED / NOT PERFORMED. Concurrent `decide()`, multi-process, and
multi-writer authority remain unsupported. Replay & As-Of engineering
implementation is FINAL CLOSED; canonical Replay/runtime activation remains
NOT AUTHORIZED / NOT PERFORMED.

Current NEXT is Data System → Canonical Dataset → Contract / responsibility
definition. Canonical Dataset is CURRENT NEXT / UNIMPLEMENTED.
`SAFE_TO_BEGIN_CANONICAL_DATASET_CONTRACT_DEFINITION = YES` permits only a
separately reviewed contract/responsibility-definition task. It does not
authorize Canonical Dataset implementation, canonical Replay activation,
canonical TruthDecision activation, production Recorder deployment,
Model/training, or Trading.
