# Data Truth

## Status

**Contract authority:** FINAL CLOSED.

**Implementation-plan authority:** FINAL CLOSED; see
[implementation-plan.md](implementation-plan.md).

**Implementation:** NOT IMPLEMENTED.

**Slice 1 semantic-library implementation:** DRAFT PR CANDIDATE — PR #33,
pending direct remote implementation review/fix. It provides no persistent
`TruthDecision` authority.

This sealed authority records the approved semantic boundary. The Slice 1 Draft
PR candidate creates no schema, table, runtime component, canonical activation,
or implementation authority beyond its bounded semantic library.

## Closure evidence

- DT-S1 through DT-S4 approved the two-child semantic tree,
  provider-observation truth, provider-proven event identity only, and
  append-only authority.
- Independent Standards, Spec, and Architecture re-reviews passed.
- PR #30 merged as `089e7aba2c78a8b66cbedd5e195cdf2325b4c51f`.
- Post-merge Windows, Ubuntu, and CI Gate checks passed.

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

## Implementation gate

The implementation-plan authority is FINAL CLOSED. Current NEXT is direct
remote review / bounded fix of Data Truth Slice 1 Draft PR #33. Slice 1 is a
Draft PR candidate only and is not FINAL CLOSED. The required QuestDB
reconciliation POC and Slice 2 remain NOT AUTHORIZED; the POC remains mandatory
before Slice 2. Any newly identified generic mechanical need must first undergo
upstream-fit review before custom infrastructure is introduced. This authority
does not authorize persistent TruthDecision authority or canonical runtime
activation.
