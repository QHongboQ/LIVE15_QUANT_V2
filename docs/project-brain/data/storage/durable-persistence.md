# Durable Persistence

**Contract authority status:** FINAL CLOSED.

**Implementation status:** NOT IMPLEMENTED. QuestDB Store-and-Forward (SF) is
NOT ENABLED, DEDUP is NOT ENABLED, and the Hot Store DEDUP evolution is NOT
IMPLEMENTED. This contract-authority closure authorizes no implementation work.

Durable Persistence begins when Capture Boundary hands it a valid immutable
`CaptureFact`. It owns attempting local durable handoff and exposing correct
delivery and result semantics for that fact across the approved transient
failure scope.

## Contract-authority closure evidence

The upstream contract-fit gate completed with QuestDB SF a STRONG fit for the
approved scope and no additional upstream required. Independent review passed;
the review-fix commit is `a577a73363aa2a2a5a1dce5406292a168cccfae2`. PR #22
merged as `e98e233cc2a3adb5f11997e7dbe00cde3556cf41`; hosted and post-merge
Windows, Ubuntu, and CI Gate checks passed, as did the final local contract
seal, Ruff, pytest (88 passed, 1 expected environment-gated skip), MyPy, and
`git diff --check`.

The next engineering prerequisite is the bounded Hot Store physical
transport-idempotency / DEDUP evolution gate. Before any mutation, it must run
read-only audits for duplicate `(received_timestamp, capture_id)` pairs and
duplicate `capture_id` values. If either audit finds collisions, stop for an
explicit migration decision: no automatic repair, deletion, or silent
deduplication is permitted.

The internal ownership-transfer point is successful local QuestDB
Store-and-Forward (SF) publication. Before that publication succeeds, LIVE15
Durable Persistence owns the definite outcome. After it succeeds, the pinned
official QuestDB Python client owns continued reconnect, replay, resend, and
background delivery; Durable Persistence still owns exposing the correct
LIVE15 result for the fact.

## Approved scope

The approved contract covers local disk-backed QuestDB SF publication, LIVE15
process-restart recovery, transient network and QuestDB server outages,
reconnect, replay/resend, completion observation, bounded capacity failure,
server-rejection visibility, and physical transport-replay idempotency.

It does not own pre-`CaptureFact` Market Ingress loss, completeness, gap
detection, freshness, Data Truth, research Replay / As-Of semantics, archive,
retention, or model/trading semantics. It also does not guarantee sudden host
power loss, OS/page-cache loss, physical disk/media failure, or host
destruction. Host/power-loss RPO is a future Operations / HA / DR concern;
this approved scope does not justify a second broker or queue.

## Upstream decision

The pinned upstream is `questdb==5.0.0`, consumed through the FINAL CLOSED
QuestDB Runtime Platform. For this approved scope, QuestDB SF is the strong
upstream fit and no additional upstream is required.

QuestDB SF owns its disk spool, slot locking, sender-restart recovery,
reconnect, replay/resend, background delivery, completion watermarks, and
bounded backpressure. LIVE15 must not build a custom WAL, disk queue, retry
manager, replay engine, reconnect manager, generic ACK tracker, or generic
persistence framework.

For the exact pinned Python `5.0.0` build, `sf_dir` and `sender_id` are
supported. The underlying client exposes `memory`, `flush`, and `append` for
`sf_durability`, but only `memory` is usable; `flush` and `append` are not
supported stable-storage modes. No `sf_sync_interval_millis` or periodic
stable-storage contract is approved. Current online documentation that
describes periodic durability must not be used to claim host/power-loss
durability for this pinned build.

## Identity and transport idempotency

`capture_id` is an opaque, immutable, globally unique identity for one newly
created `CaptureFact` in the LIVE15 persistence domain. UUID4 is not required
by the public contract; Capture Boundary's current UUID4 default is one
implementation that satisfies the invariant.

An exact transport replay preserves `capture_id`, `received_timestamp`, and
the complete `CaptureFact`; it must not mint a new identity. Distinct newly
captured facts with identical content have distinct `capture_id` values and
remain distinct.

QuestDB SF delivery is at least once. An ACK loss or an acknowledgement not
durably observed can therefore replay a server-accepted frame. LIVE15 requires
physical, not semantic/Data Truth, idempotency for an exact replay. The
approved candidate physical key is `(received_timestamp, capture_id)`:
`received_timestamp` is the existing designated QuestDB timestamp and must be
part of QuestDB UPSERT KEYS; `capture_id` separates different facts at the same
timestamp.

Hot Store owns QuestDB physical table/schema configuration. Durable
Persistence owns the requirement that transport replay of the same immutable
`CaptureFact` identity is physically idempotent. A future bounded Hot Store
forward evolution must enable the approved physical DEDUP configuration; it is
an explicit prerequisite, not a hidden modification.

Before any such activation, perform read-only audits for duplicate
`(received_timestamp, capture_id)` pairs and duplicate `capture_id` values. If
either audit returns rows, stop and escalate for an explicit migration decision;
do not delete, repair, or silently deduplicate data.

## Result and rejection semantics

`flush_and_get_fsn()` returning successfully proves local SF publication and
returns a lease-local frame sequence number (FSN). An FSN is not a durable
LIVE15 receipt and is not portable across sender leases.

`await_acked_fsn(fsn, timeout)` returning `False` means a no-progress timeout:
the frame is still pending, not definitely rejected. A `True` completion
watermark alone is also insufficient to prove `ACKNOWLEDGED_OK`, because the
watermark may advance for a drop-and-continue server rejection. Future work
must correlate completion with the pinned client's structured rejection channel:
`error_handler`, `poll_error()`, `SenderError`, `SenderError.applied_policy`,
`SenderError.message_sequence`, `SenderError.from_fsn`, and
`SenderError.to_fsn`.

The negative rejection observation also has a pinned upstream loss boundary.
`PooledSender.poll_error()` and `PooledSender.error_events_dropped()` expose
diagnostics and the count dropped from a borrowed connection's bounded
rejection ring. The `QuestDB` `error_handler` receives server rejections and
`QuestDB.error_events_dropped` reports diagnostics discarded by its bounded
drop-oldest handler inbox. `ACKNOWLEDGED_OK` requires the relevant completion
watermark, no structured rejection covering the relevant FSN/range, and no
detected rejection-diagnostic loss that could make that negative observation
unreliable. If diagnostics were dropped and LIVE15 cannot prove the loss is
irrelevant to the relevant FSN, diagnostic loss cannot produce success: do not
return `ACKNOWLEDGED_OK`. QuestDB owns these bounded channels and counters;
LIVE15 owns only this fail-closed interpretation, not a custom recovery,
journal, queue, or ACK/rejection tracker.

The minimal result categories are:

- `LOCAL_PERSISTENCE_FAILED`: SF definitely did not accept ownership.
- `PERSISTED_PENDING`: SF accepted local ownership but server acceptance is not
  proven.
- `ACKNOWLEDGED_OK`: server completion is proven, no rejection covers the
  relevant frame, and relevant rejection-diagnostic loss is ruled out.
- `DEFINITELY_REJECTED`: structured upstream evidence proves rejection.
- `IN_DOUBT`: an upstream exception leaves publication/ownership ambiguous.

After successful local SF publication, LIVE15 must not enqueue the same
`CaptureFact` again merely because an ACK wait times out. It may observe the
pending result, but QuestDB SF owns reconnect/replay after transfer.

## Sender identity and future acceptance

The canonical SF parent is `D:\LIVE15_V2_RUNTIME\questdb\sf`. Each logical
LIVE15 producer/pool will receive one stable sender-ID base across restarts;
concurrent producers sharing that parent must use distinct bases. Pool slot
suffixes are upstream details. A sender-ID slot collision must fail loudly.

Future integration acceptance must distinguish QuestDB's upstream mechanism
from the LIVE15 contract assertion for: healthy publish/ack; pre-publication
failure; network loss; server restart; lost ACK after server acceptance;
process restart with queued data; exact replay; distinct IDs with identical
content; capacity exhaustion; unavailable/unwritable SF directory; sender-ID
collision; close with pending data; structured server rejection; and completion
watermark/rejection correlation; and structured rejection-diagnostic
overflow/drop. The last case must force or simulate diagnostic loss and prove
that completion watermark plus an empty rejection poll cannot report
`ACKNOWLEDGED_OK` when upstream loss evidence exists.

```text
Storage
├── Capture Boundary                         FINAL CLOSED
├── Hot Store                                FINAL CLOSED
│   └── future bounded physical DEDUP evolution prerequisite
└── Durable Persistence
    ├── QuestDB Python 5.0.0 SF              upstream-owned
    │   ├── spool / slot locking
    │   ├── reconnect / replay / resend
    │   ├── completion watermarks
    │   └── background delivery / bounded backpressure
    └── LIVE15 thin seam
        ├── configuration authority and sender identity
        ├── CaptureFact handoff / ownership transfer
        ├── result and rejection semantics
        └── integration acceptance tests
```
