# Changelog

## 2026-09-07 — LIVE15-V2-DATA-TRUTH-IMPLEMENTATION-PLAN-AUTHORITY-PREMERGE-STATUS-CLOSURE-001

**Change:** Closed the current Project Brain implementation-plan authority
status after the independently reviewed candidate and PR #32 hosted CI passed.
Data Truth contract authority remains FINAL CLOSED; implementation-plan
authority is now FINAL CLOSED; implementation remains NOT IMPLEMENTED.

**Reason:** Current authority still described independent review as pending and
kept Current NEXT at review. Without this bounded status closure, merging PR
#32 would leave stale current authority on main.

**Validation / result:** Independent re-review PASS: Standards, Spec,
Architecture, and Global Engineering Rule. Reviewed candidate head
`68c757ec08289a53c17744ceb8607cb39dda3108`; PR #32 is OPEN. Slice 1, the
QuestDB reconciliation POC, and Slice 2 remain unauthorized; QuestDB
TruthDecision-history fit remains PARTIAL_FIT. No source, test, dependency,
runtime, or production change. Ruff PASS; pytest PASS (114 passed, 11
skipped); MyPy PASS; and `git diff --check` PASS.

**Commit / PR:** Status-closure commit
`c3c79adb22e6c7679985e3d9cfc333ae4a4e43ea`; PR #32 OPEN.

**Next:** Independent pre-merge status-closure review. Slice 1, the QuestDB
reconciliation POC, Slice 2, and Data Truth implementation remain unauthorized.

**Safety:** Documentation authority only: no QuestDB runtime, canonical
`hot_capture_facts`, canonical DEDUP, canonical SF, or production-data change.

## 2026-09-07 — LIVE15-V2-DATA-TRUTH-IMPLEMENTATION-PLAN-AUTHORITY-CANDIDATE-001

**Change:** Added the bounded Data Truth implementation-plan authority
candidate, its two production slices, single-writer initial authority,
TruthDecision subject-key/retry rules, and the mandatory pre-Slice-2 QuestDB
reconciliation POC. Added the global V2 engineering lifecycle authority:
Responsibility → Contract / Interface → Leaf Implementation → Adapter →
Composition → Integration Test → Runtime Deployment → Canonical
Activation.

**Reason:** Convert the passed implementation-planning/upstream-fit and
decision-closure results into durable authority without reopening the sealed
Data Truth semantic contract or authorizing implementation.

**Validation / result:** Data Truth contract remains FINAL CLOSED;
implementation remains NOT IMPLEMENTED. TruthDecision DEDUP is disabled,
QuestDB TruthDecision-history fit remains PARTIAL_FIT, and the disposable POC
is mandatory before Slice 2. No database, runtime, dependency, source, test,
or canonical activation was introduced. Decision closure PASS; Ruff PASS;
pytest PASS (114 passed, 11 skipped); MyPy PASS; and `git diff --check` PASS.

**Commit / PR:** Original candidate commit
`95a5b8698f83440fbd9232e16b249662a3065f75`; PR NOT OPENED / PENDING
independent review.

**Next:** Independent review of this implementation-plan authority candidate.
Slice 1, the Slice-2 QuestDB POC, and Data Truth implementation remain
unauthorized.

**Safety:** Documentation authority only: no QuestDB runtime, canonical
`hot_capture_facts`, canonical DEDUP, canonical SF, or production-data change.

## 2026-09-07 — LIVE15-V2-DATA-TRUTH-CONTRACT-POST-MERGE-AUTHORITY-CLOSURE-001

**Change:** Corrected the stale current-authority wording left after the
successful Data Truth contract merge: parent, Event Facts, Observation Facts,
Data System routing, and Current Plan now record FINAL CLOSED contract
authority while implementation remains NOT IMPLEMENTED.

**Reason:** PR #30 merged correctly, but post-merge authority readback found
candidate/pending-review wording still active in current Project Brain nodes.
The semantic contract and architecture remained sound; this task corrects
status only.

**Validation / result:** PR #30 merged as
`089e7aba2c78a8b66cbedd5e195cdf2325b4c51f`; post-merge Windows, Ubuntu, and
CI Gate checks passed. Closure validation PASS: Ruff; pytest (114 passed,
11 skipped); MyPy; and `git diff --check` all passed.

**Commit / PR:** Authority-closure commit
`dc15f12c7bc6ad37f054e6a97fcd97935eda3264`; PR NOT OPENED / PENDING REVIEW.

**Next:** Independent review of this bounded post-merge authority closure.
Data Truth implementation remains unauthorized.

**Safety:** Documentation authority only: no source, test, dependency, CI,
QuestDB runtime, canonical `hot_capture_facts`, canonical DEDUP, canonical SF,
or production-data change.

## 2026-09-07 — LIVE15-V2-DATA-TRUTH-CONTRACT-AUTHORITY-CANDIDATE-001

**Change:** Added the Data Truth contract-authority candidate: exactly two
semantic children, Event Facts and Observation Facts, with a provider-neutral
`CaptureFact` to append-only `TruthDecision` public contract.

**Reason:** Record the approved simplified semantic boundary without creating
family-specific truth engines, a second evidence envelope, storage model,
database, or runtime component. DT-S1 through DT-S4 approve the two-leaf tree,
provider-observation truth, provider-proven event identity only, and
append-only authority with derived non-authoritative projections.

**Validation / result:** Contract self-consistency, sibling independence, leaf
removability, sealed `CaptureFact` reuse, and scope checks passed. The candidate
has two semantic child leaves, zero new storage models, zero databases, and zero
runtime components. Ruff PASS; pytest PASS (114 passed, 11 skipped); MyPy PASS;
and `git diff --check` PASS. Independent review found Architecture PASS;
Standards FAIL only for missing candidate commit evidence; and Spec FAIL only
for missing explicit pinned-QuestDB sufficiency authority. This bounded review
fix is in progress.

**Commit / PR:** Candidate commit
`a21ea7747377444b60355671a315a78fa29b1a30`; PR NOT OPENED / PENDING REVIEW.

**Next:** Independent Data Truth contract re-review after this bounded review
fix. Data Truth implementation remains unauthorized.

**Safety:** Documentation authority only: no code, test, dependency, CI,
QuestDB runtime, canonical `hot_capture_facts`, canonical DEDUP, canonical SF,
or production-data change.

## 2026-09-07 — LIVE15-V2-QUESTDB-RUNTIME-DURABLE-PERSISTENCE-STALE-AUTHORITY-CLEANUP-001

**Change:** Corrected the QuestDB Runtime leaf's stale statement that Durable
Persistence was not implemented.

**Reason:** Durable Persistence contract and implementation became FINAL CLOSED
through PR #28 (`9802e431c6ec117fcc4c41e187e1f3d30ecedf27`), while the runtime
leaf retained an obsolete current-state statement.

**Validation / result:** The stale statement was confirmed; QuestDB Runtime,
Durable Persistence contract, and Durable Persistence implementation remain
FINAL CLOSED; canonical activation remains false. Ruff, pytest (114 passed,
11 skipped), MyPy, and `git diff --check` passed. Cleanup task result: PASS.

**Commit / PR:** Cleanup commit
`efbd9692d55fd5fbee981fa13ef72347a754c1d0`; PR NOT OPENED / PENDING REVIEW.

**Next:** Independent cleanup re-review after this changelog-only review fix.

**Safety:** Documentation authority only: no QuestDB runtime, code, canonical
Store-and-Forward/DEDUP configuration, canonical `hot_capture_facts`, or
production data changed. This does not authorize Data Truth.

## 2026-09-07 — LIVE15-V2-DURABLE-PERSISTENCE-PROJECT-BRAIN-CLOSURE-001

**Summary:** Durable Persistence implementation is technically sealed: core
implementation PR #26 merged as `8dac68451bd06d372eb866633def58bdc316d741`,
failure-mode acceptance PR #27 merged as
`098718febc82f28ce012ecda5e370578529ca2f1`, and the final post-merge local
seal passed. Project Brain authority now records FINAL CLOSED.

**Next:** Data System → Data Truth responsibility / contract-authority
definition. Canonical SF, DEDUP, and `hot_capture_facts` activation remain
unauthorized.

## 2026-09-07 — LIVE15-V2-DURABLE-PERSISTENCE-FINAL-ADAPTER-FAILURE-MODE-ACCEPTANCE-001

**Summary:** Added opt-in acceptance evidence for the merged
`QuestDBSFDurablePersistence` public seam against task-owned QuestDB Server
`10.0.1` / Python client `questdb==5.0.0` resources. Healthy publication
returned `ACKNOWLEDGED_OK`; same-process server outage, graceful producer
restart, and hard producer crash each returned `PERSISTED_PENDING` after local
SF publication and later delivered exactly one preserved physical fact.

**Recovery evidence:** Replacement LIVE15 processes use the actual production
adapter and trigger its lazy connection only through one distinct ordinary
`persist()` call. Pending identities are never application-republished. The
prior apparent restart failures were subprocess-harness defects; the raw
pinned QuestDB controls pass for healthy, same-process, graceful-restart, and
hard-crash recovery.

**Safety:** No production source, Project Brain authority, canonical runtime,
canonical SF/DEDUP, canonical `hot_capture_facts`, or production data changed.
No custom retry, replay, WAL, queue, or process journal was added. The test
uses short task-owned Windows paths because longer disposable paths caused a
QuestDB file-open rejection; this is harness-only evidence and not an adapter
semantic change.

**Status:** Durable Persistence failure-mode acceptance = IMPLEMENTATION
CANDIDATE pending independent acceptance review. PR not opened.

## 2026-09-07 — LIVE15-V2-DURABLE-PERSISTENCE-CORE-SF-IMPLEMENTATION-REVIEW-FIX-001

**Summary:** Corrected the bounded Durable Persistence implementation
candidate's SF result interpretation after independent review. A successful
`flush_and_get_fsn()` now permanently establishes local SF ownership, so a
later acknowledgement-observation exception returns `PERSISTED_PENDING` rather
than `IN_DOUBT`. Structured rejections now distinguish the pinned
`SenderErrorPolicy`: only `Terminal` can produce `DEFINITELY_REJECTED`, while
retriable policies remain pending for QuestDB SF replay.

**Regression evidence:** Added policy, queued-rejection, FSN-`None`,
post-publication ownership, no-double-enqueue, and historical diagnostic-loss
regressions. No retry, replay, queue, ACK tracker, schema DDL, dependency, or
Project Brain authority was added or changed. Healthy disposable live SF
acceptance passed; canonical runtime resources remain untouched.

**Validation:** Ruff, pytest, MyPy, `git diff --check`, and the bounded live
SF integration passed. This remains an implementation candidate pending
independent re-review; PR not opened.

## 2026-09-07 — LIVE15-V2-DURABLE-PERSISTENCE-CORE-SF-IMPLEMENTATION-001

**Summary:** Added the bounded Durable Persistence implementation candidate:
the provider-neutral `persist(CaptureFact) -> PersistenceResult` seam and its
QuestDB Store-and-Forward adapter using the pinned QuestDB Server `10.0.1` /
Python client `questdb==5.0.0` integration.

**Scope and contract:** `sf_dir`, stable `sender_id`, physical table name, and
acknowledgement timeout are explicit. The adapter uses only `sf_durability =
memory`, treats successful `flush_and_get_fsn()` as local ownership transfer,
returns `PERSISTED_PENDING` on an acknowledgement timeout, correlates
structured rejection ranges, and fails closed on relevant diagnostic loss. It
does not expose FSNs as receipts or add a custom WAL, queue, retry, replay,
reconnect, ACK-tracker, or persistence framework.

**Safety and evidence:** Unit coverage exercises all five result categories,
exact CaptureFact mapping, no double enqueue after ownership transfer, and
close lifecycle. A bounded live SF test uses only a UUID-scoped disposable
table and task-owned temporary SF directory; the canonical table, canonical SF
parent, runtime configuration, and production data remain untouched. Project
Brain authority remains: Durable Persistence contract FINAL CLOSED;
implementation NOT IMPLEMENTED.

**Validation:** Ruff, pytest, MyPy, `git diff --check`, and the bounded live
SF integration passed. PR not opened; this is an implementation candidate for
independent review.

## 2026-09-07 — LIVE15-V2-HOT-STORE-NATIVE-DEDUP-PROJECT-BRAIN-CLOSURE-001

**Summary:** Closed the Hot Store native QuestDB physical transport-idempotency
evolution in current Project Brain authority.

**Evidence:** Implementation `811dd957be96aaa8b4433f03452c73dc32b09e20` and
review fix `f7b17eb01e1ba7390f4bb1927619aa0d92eab30a` passed independent
re-review. PR #24 merged as `c5dde82a2b164b06681d63a55ce2c6f2a1922758`;
hosted PR and post-merge Windows, Ubuntu, and CI Gate checks passed, as did the
final local seal. Merged-main validation passed: Ruff, pytest (98 passed, 5
expected environment-gated live skips), MyPy, and `git diff --check`. The
combined live integration passed five cases in one process with no connection
stall: exact replay left one physical row and distinct IDs at the same timestamp
left two.

**Runtime distinction:** The canonical `hot_capture_facts` table remains absent
and canonical DEDUP is not enabled; SF is not enabled and production data is
unchanged. The sealed adapter capability configures a future authorized new
table with native `WAL DEDUP UPSERT KEYS(received_timestamp, capture_id)`.

**Status:** Hot Store native physical transport-idempotency evolution = FINAL
CLOSED.

**Next:** Storage → Durable Persistence implementation. Durable Persistence is
not implemented.

## 2026-09-06 — LIVE15-V2-HOT-STORE-NATIVE-DEDUP-BOUNDED-EVOLUTION-IMPLEMENTATION-001

**Summary:** Added the bounded Hot Store native QuestDB physical transport-
idempotency implementation candidate.

**Why:** The preceding read-only DEDUP prerequisite and absent-table disposition
gates established that the canonical `hot_capture_facts` table was never
materialized. A newly materialized table must therefore be born with native
QuestDB `WAL DEDUP UPSERT KEYS(received_timestamp, capture_id)` rather than be
silently converted later.

**Validation / evidence:** The QuestDB adapter now inspects existing table
metadata first and accepts only the exact WAL, DEDUP, designated
`received_timestamp`, `TIMESTAMP_NS`, `capture_id VARCHAR`, and approved
two-column UPSERT-key configuration. Existing nonconforming tables fail closed
before metadata-column compatibility alters. Task-scoped disposable live
QuestDB `10.0.1` tests passed for exact replay (one physical row), distinct
capture IDs at one timestamp (two physical rows), an already-correct table,
non-DEDUP fail-closed behavior, and success/exception cleanup. The canonical
table remains absent; the historical `hot_store_adapter_integration` residue
was not touched. No Store-and-Forward, runtime configuration, custom retry,
queue, WAL, semantic deduplication, or dependency changed.

**Commit:** Pending.

**PR:** Not opened.

**Status:** Hot Store native DEDUP bounded evolution = IMPLEMENTATION CANDIDATE;
not FINAL CLOSED.

**Next step:** Independent review only. Do not materialize the canonical table,
enable canonical DEDUP, or begin Durable Persistence implementation.

## 2026-09-06 — LIVE15-V2-DURABLE-PERSISTENCE-CONTRACT-BRAIN-CLOSURE-001

**Summary:** Closed the Durable Persistence contract authority in the current
Project Brain without beginning Durable Persistence implementation.

**Why:** The contract candidate completed independent review, its review fix,
PR #22 merge, post-merge CI, and final local seal. Current authority must now
route the next prerequisite precisely rather than imply that implementation can
begin.

**Validation / evidence:** Baseline and PR #22 merge:
`e98e233cc2a3adb5f11997e7dbe00cde3556cf41`; review fix:
`a577a73363aa2a2a5a1dce5406292a168cccfae2`. The upstream contract-fit gate
found QuestDB SF a STRONG fit for the approved scope with no additional
upstream required. Independent review, hosted Windows and Ubuntu checks, CI
Gate, post-merge Windows and Ubuntu checks, post-merge CI Gate, final local
seal, Ruff, pytest (88 passed, 1 expected environment-gated skip), MyPy, and
`git diff --check` passed. No source, test, dependency, QuestDB Runtime, SF,
DEDUP, Hot Store, or Durable Persistence implementation changed.

**Commit:** `8ae33589340f95322c5625b405a18c31135c4172`.

**PR:** Pending.

**Status:** Durable Persistence contract authority = FINAL CLOSED;
implementation = NOT IMPLEMENTED.

**Next step:** Storage → Hot Store physical transport-idempotency / DEDUP
prerequisite gate. Before any mutation, audit duplicate
`(received_timestamp, capture_id)` pairs and duplicate `capture_id` values
read-only; collisions stop for an explicit decision, with no automatic repair,
deletion, or silent deduplication.

## 2026-09-06 — LIVE15-V2-DURABLE-PERSISTENCE-CONTRACT-AUTHORITY-001

**Summary:** Defined the Storage Durable Persistence contract / authority
candidate without beginning implementation.

**Why:** The completed upstream contract-fit gate established that pinned
`questdb==5.0.0` Store-and-Forward owns the approved generic transient-failure
mechanisms, while LIVE15 needs a narrow CaptureFact handoff and result-semantics
seam.

**Validation / evidence:** Baseline:
`d9199a84286d4fe7873ce1d3a31670c8656a39ea`. The candidate defines local
disk-backed SF publication, process-restart and transient network/server
failure scope; sender identity; at-least-once replay; physical idempotency
requirement `(received_timestamp, capture_id)`; ACK timeout and structured
rejection semantics; and the explicit future bounded Hot Store DEDUP evolution
prerequisite. The pinned Python `5.0.0` client supports `sf_dir` and
`sender_id`, but only usable `sf_durability=memory`; it has no approved periodic
stable-storage contract, so host/power-loss RPO remains a future Operations /
HA / DR concern. No additional upstream, custom queue/WAL/retry/replay system,
source, tests, dependencies, QuestDB configuration, SF, DEDUP, or Hot Store
change was added.

**Commit:** `8946596d94eaef2866d16c04929b8be9ebdf4956`.

**PR:** Pending.

**Status:** Durable Persistence = CONTRACT / AUTHORITY CANDIDATE; not
implemented.

**Next step:** Independent review of this contract authority. Do not enable SF
or DEDUP and do not begin Durable Persistence implementation.

## 2026-09-06 — LIVE15-V2-QUESTDB-RUNTIME-PLATFORM-PROJECT-BRAIN-CLOSURE-001

**Summary:** Persisted the completed QuestDB Runtime Platform technical seal as
FINAL CLOSED current authority.

**Why:** The canonical runtime deployment candidate completed independent
review, PR publication, hosted CI, merge, post-merge CI, and final local seal;
the Project Brain must now reflect that durable completion before the next Data
System stage begins.

**Validation / evidence:** PR #20 merged as
`b1d415aef1b1c2f3d1a8688e9d3358647ee836ab`. Hosted Windows and Ubuntu checks,
CI Gate, post-merge CI, final local Ruff, pytest (88 passed, 1 expected
environment-gated skip), MyPy, and `git diff --check` passed. The canonical
QuestDB runtime health and metrics passed, as did the real sealed Hot Store
integration. No runtime, service, configuration, source, test, dependency,
DEDUP, application-side Store-and-Forward, or Durable Persistence change
occurred in this closure task.

**Commit:** `28fec936673007cd22960d6ebc5b0d98064fddb4`.

**PR:** Pending.

**Status:** QuestDB Runtime Platform = FINAL CLOSED.

**Next step:** Storage → Durable Persistence, starting with upstream-first
responsibility and contract-fit work while consuming the sealed runtime.

## 2026-09-06 — LIVE15-V2-QUESTDB-RUNTIME-PLATFORM-BOOTSTRAP-RESUME-001

**Summary:** Recorded the completed canonical QuestDB Runtime Platform
deployment as a validation candidate after the Hot Store QuestDB `10.0.1`
compatibility repair was sealed.

**Why:** The original platform bootstrap installed the official runtime but was
interrupted by real Hot Store adapter compatibility defects. Those defects are
now FINAL CLOSED, so the existing runtime could be verified and its durable
deployment evidence recorded without reinstalling or reconfiguring it.

**Validation / evidence:** Baseline:
`ca07197d0e139e50e0b76655cc04117902ab3207`. Official QuestDB Server `10.0.1`
remains installed at `D:\LIVE15_V2_RUNTIME\questdb\dist\10.0.1`, with canonical
root `D:\LIVE15_V2_RUNTIME\questdb\root`, canonical SF parent
`D:\LIVE15_V2_RUNTIME\questdb\sf`, and official service
`QuestDB:LIVE15_V2` (`QuestDB Server [LIVE15_V2]`) Running with AutoStart.
The retained bootstrap evidence records the official
`questdb-10.0.1-rt-windows-x86-64.tar.gz` artifact (88,871,519 bytes) and
verified SHA-256 `e8ea640e3e68a70a700cdf0a05f60e374efa33d6ed2399be8e4a70677a98d092`
against the available vendor checksum; the archive is no longer retained
locally. `metrics.enabled=true`; health and Prometheus metrics endpoints passed
on min HTTP `9003`; HTTP/QWP `9000`, PGWire `8812`, and ILP TCP `9009` listen.
`questdb==5.0.0` imports, and the sealed Hot Store live integration passed
against this runtime using only `hot_store_adapter_integration`. No reinstallation,
DEDUP, Durable Persistence, or application-side Store-and-Forward configuration
was added.

**Commit or PR:** Pending commit.

**Status:** QuestDB Runtime Platform = DEPLOYED / VALIDATION CANDIDATE.

**Next step:** Independent review; then PR, CI, merge, and local seal. Only
after that seal does execution return to Storage → Durable Persistence.

## 2026-09-06 — LIVE15-V2-HOT-STORE-QUESTDB10-NULLABLE-TEXT-COMPAT-FIX-001

**Summary:** Corrected three bounded QuestDB `10.0.1` provider-adapter
compatibility details while preserving the FINAL CLOSED Hot Store contract.

**Why:** The canonical official runtime exposed a guarded multi-column
`ADD COLUMN` failure (`[86] column 'message_type' already exists`), then
revealed that `questdb==5.0.0` requires the domain `AssetId` to cross the
sender boundary as its plain-string `.value`, and that pandas materializes a
nullable `event_subtype` as `NaN` rather than contract-required `None`.

**Validation / evidence:** The migration now uses one independently guarded
official `ADD COLUMN` statement per metadata column; the adapter writes the
canonical asset string and maps nullable pandas text back to `None`, failing
closed for non-string non-null values. Focused Hot Store tests and the existing
official live integration against QuestDB `10.0.1` passed using only its
disposable `hot_store_adapter_integration` table. No unrelated data was
affected; no deduplication, Store-and-Forward application configuration, retry,
or dependency was added.

**Commit or PR:** Pending commit.

**Status:** Hot Store = FINAL CLOSED — bounded compatibility fix candidate.

**Next step:** Independent review of the bounded compatibility fix; QuestDB
Runtime bootstrap remains blocked pending that review and seal.

## 2026-09-06 — LIVE15-V2-QUESTDB-RUNTIME-PROJECT-BRAIN-AUTHORITY-001

**Summary:** Added the minimum Operations / Runtime Project Brain routing tree
for the approved canonical LIVE15 V2 QuestDB Runtime Platform.

**Why:** The preceding bootstrap task correctly stopped because no Operations /
Runtime authority existed. The human approved the minimum routing needed before
the platform bootstrap can proceed.

**Validation / evidence:** No QuestDB server, Windows service, runtime root, or
Store-and-Forward parent was installed or created, and no deletion occurred.
The project environment verified `questdb==5.0.0`. This task adds routing only.

**Commit or PR:** Pending commit.

**Status:** QuestDB Runtime = APPROVED FOR PLATFORM BOOTSTRAP; UNIMPLEMENTED.

**Next step:** QuestDB Runtime Platform Bootstrap using official QuestDB
documentation.

## 2026-09-06 — LIVE15-V2-STORAGE-CAPTURE-BOUNDARY-PROJECT-BRAIN-CLOSURE-001

**Summary:** Closed the Storage Capture Boundary phase in the Project Brain
after its independently reviewed implementation, bounded public-contract review
fix, merge, hosted CI, post-merge validation, and local seal.

**Why:** Make every current Storage authority reflect the completed code and
contract without beginning Durable Persistence or any other Storage child.

**Validation / evidence:** Final independent re-review passed. PR #16 Windows,
Ubuntu, and CI Gate passed; post-merge main Windows, Ubuntu, and CI Gate also
passed. Local Ruff, pytest (84 passed, 1 expected live-QuestDB skip), MyPy, and
`git diff --check` passed. Local main and `origin/main` equal the merge SHA; the
feature branch was removed locally and remotely; no unexpected worktrees or
task residue remained; QuestDB was not started; and `.git` remained owned by the
normal user.

**Commit or PR:** PR #16. Implementation:
`713d9afefef0d6001c6c3e5c1f8ca2c06a17c1ea`; review fix:
`914084164f8e617e5c578dd6ccf73101fbee3312`; merge:
`2d00ad1fcc13456e801e9335c5ccc3c10a7399c1`.

**Status:** Storage Capture Boundary = FINAL CLOSED.

**Next step:** Storage → Durable Persistence. Begin with an upstream-first
responsibility and contract-fit audit before implementation.

## 2026-09-06 — LIVE15-V2-STORAGE-CAPTURE-BOUNDARY-IMPLEMENTATION-001

**Summary:** Added the first bounded Storage Capture Boundary implementation
candidate. It synchronously freezes exact approved typed Market Ingress
data-plane messages into the shared immutable `CaptureFact` contract.

**Why:** Establish the approved upstream-first seam from verifier-issued or
scope-approved ingress messages to captured facts without introducing a
Recorder, persistence, or any Storage sibling composition.

**Validation / evidence:** Ruff, pytest (82 passed, 1 expected live-QuestDB
skip), MyPy, and `git diff --check` passed. Independent review found the
Capture Boundary data path, authority, timestamp, freeze, and runtime boundaries
sound, but identified one governance defect: the required Pyth exact type caused
an undocumented public Reference Stream contract expansion. The bounded
follow-up formalizes only the required public `PythValueMessage` contract; final
independent re-review remains pending. No QuestDB runtime, Hot Store write,
async runtime, I/O, queue, retry, WAL, Data Truth, replay, archive, retention,
or new dependency was added.

**Commit or PR:** Implementation candidate:
`713d9afefef0d6001c6c3e5c1f8ca2c06a17c1ea`; no PR opened.

**Status:** Capture Boundary = implementation candidate / in progress; not
FINAL CLOSED.

**Next step:** Final independent re-review of the Capture Boundary candidate and
its narrow Reference Stream public-contract evolution only. Do not begin another
Storage child.

## 2026-09-05 — LIVE15-V2-SHARED-CAPTURE-CONTRACT-PROJECT-BRAIN-CLOSURE-001

**Summary:** Closed the Shared Capture Contract phase in the Project Brain after
its merged implementation, fail-closed legacy-row review fix, independent
re-review, hosted CI, and local-main seal.

**Why:** Make the durable current state and single next action accurate without
starting Capture Boundary implementation.

**Validation / evidence:** Final independent re-review passed. PR #14 Windows,
Ubuntu, and CI Gate passed; post-merge main Windows, Ubuntu, and CI Gate also
passed. Local Ruff, pytest (64 passed, 1 expected live-QuestDB skip), MyPy, and
`git diff --check` passed. Local main and `origin/main` both equal the merge
SHA; the merged feature branch was removed locally and remotely; no task residue
remained; QuestDB was not started; and `.git` remained owned by the normal user.

**Commit or PR:** PR #14. Implementation evidence:
`ac91a4404b6239c454fd2f50893e5d91332abf6a`; review-fix evidence:
`eab7d514a9618b8b90733e78ff32e16adac15936`; merge:
`98a0aa397d4a61f327dd7dcce9a9fae0ebb30f58`.

**Status:** Storage Shared Capture Contract = FINAL CLOSED.

**Next step:** Storage → Capture Boundary. It remains unimplemented and requires
separate authorization.

## 2026-09-05 — LIVE15-V2-STORAGE-SHARED-CAPTURE-CONTRACT-MIGRATION-001

**Summary:** Moved the immutable shared `CaptureFact` contract to Storage,
introduced the canonical nine-value Data System `AssetId`, and migrated the
sealed Hot Store QuestDB adapter and bounded tests to preserve source,
message-type, optional event-subtype, and nullable provider-time metadata.

**Why:** Prepare the future Capture Boundary sibling to use a shared Storage
contract without depending on Hot Store-private models, while preserving the
existing physical raw-fact behavior.

**Validation / evidence:** Initial implementation validation passed: Ruff,
pytest (61 passed, 1 expected live-QuestDB skip), MyPy, and `git diff --check`.
Independent review passed the architecture/shared-contract direction, but found
that existing rows were not semantically upgraded by physical schema addition
and that this entry's audit trail was stale. The bounded follow-up addresses
those review defects. No Capture Boundary, new runtime, upstream dependency,
QuestDB live test, Data Truth, or other Storage child was implemented.

**Commit or PR:** Implementation evidence commit:
`ac91a4404b6239c454fd2f50893e5d91332abf6a`; no PR opened.

**Next step:** Final independent re-review remains pending. Capture Boundary,
PR, merge, and the next Storage child remain blocked until it passes.

## 2026-09-05 — LIVE15-V2-HOT-STORE-VERIFY-CLEANUP-AND-COMMIT-001

**Summary:** Removed the QuestDB adapter from the provider-neutral Hot Store
package root, documented the adapter-local pandas and opaque payload boundary,
and added regressions for exact text round trips, the public surface, and raw
orderbook snapshot/delta fixture coverage.

**Why:** Close the bounded Hot Store review findings without changing the port,
storage behavior, or any deferred Storage child.

**Validation / evidence:** A single disposable official QuestDB 10.0.1 live
adapter integration test passed for both orderbook snapshot and orderbook delta,
including stable capture-ID duplicate assertions. After runtime cleanup, Ruff,
the local suite (55 passed, 1 expected live-test skip), MyPy, and
`git diff --check` passed. The independent re-review found no code or
specification defect, but identified two changelog audit-trail defects; this
correction addresses those audit defects.

**Commit or PR:** Implementation evidence commit:
`3f816806b7b534892b46fdd47578fca31d52f170`; no PR opened.

**Next step:** Final independent re-review remains pending. PR, merge, and the
next Storage child remain blocked until that re-review passes.

## 2026-09-05 — LIVE15-V2-STORAGE-HOT-STORE-QUESTDB-IMPLEMENTATION-001

**Summary:** Added the first Storage leaf: a provider-neutral Hot Store interface and a thin QuestDB adapter using the pinned official Python client.

**Why:** Preserve captured raw facts behind a replaceable seam while using the accepted QuestDB 10.0.1 upstream candidate for generic database mechanics.

**Validation / evidence:** Unit contracts cover exact raw round trips, duplicate facts, optional sequence, out-of-order provider times, the nine-asset fixture set, physical range retrieval, explicit 500-row batching, unavailable databases, and rejected writes. The bounded official local QuestDB adapter integration suite passed. No Data Truth or other Storage child was implemented.

**Commit or PR:** Pending independent review.

**Next step:** Independent review of Hot Store only; do not begin another Storage child.

This is the permanent, human-readable activity log for LIVE15_QUANT_V2. Every meaningful V2 task must update this file in the same commit or PR.

## 2026-09-04 — LIVE15-V2-MARKET-INGRESS-FINAL-HARDENING-002

**Summary:** Re-opened the Market Ingress closeout after a fresh adversarial audit found three residual authority/validation holes: verifier provenance could be copied to a reconstructed `VerifiedMarketIdentity`, public `ReferenceStream` composition accepted caller-injected reference scope, and one-sided strike types did not reject contradictory extra bounds. The fix binds provenance to the exact issued identity object, makes the authoritative Reference Stream own the canonical nine-asset reference scope internally, tightens strike shapes, strengthens exact-nine invariants, and cleans residual documentation/formatting drift.

**Why:** A green closeout must survive caller-bypass and copy/replace attacks at public composition boundaries, not only happy-path tests. The same pass also removes stale wording and records the exact SDK backpressure/completeness constraint before Storage design begins.

**Validation / evidence:** Added adversarial regressions for copied identity provenance, reference-scope injection, and contradictory strike shapes. The change preserves SDK transport/reconnect ownership and does not begin Storage, Data Truth, Replay, Dataset, Model, Trading, Operations, or Production work. Hosted validation is required before merge.

**Commit or PR:** This final-hardening PR.

**Next step:** Independent review and merge authorization, followed by post-merge local/main verification. Storage still requires separate explicit user authorization.

## 2026-09-04 — LIVE15-V2-MARKET-INGRESS-CLOSEOUT-HYGIENE-001

**Summary:** Closed the remaining Market Ingress stage-hygiene findings after
PR #10 hardening: removed the stale Data System root re-export, refreshed root
and current-plan status, documented SDK queue/backpressure completeness
boundaries, documented provider DTO containment, and removed the obsolete
`tests/.gitkeep` placeholder.

**Why:** Leave one accurate responsibility tree and one clean public API surface
before Storage begins, while recording that typed SDK iterators are ingress
interfaces rather than a lossless persistence guarantee.

**Validation / evidence:** Ruff, pytest, mypy, hosted Ubuntu/Windows checks, CI Gate, and the post-merge main workflow passed.

**Commit or PR:** PR #11, merged as `66200608bef0a9b6ebf9afd7af900249fdfc23b1`.

**Next step:** Final adversarial hardening audit before any Storage work.

## 2026-09-04 — LIVE15-V2-MARKET-INGRESS-HARDENING-001

**Summary:** Hardened Market Ingress authority boundaries found during the stage
closeout audit: Market Stream now requires verifier-issued identity provenance,
the public Market Ingress composition path always uses the sole concrete
nine-asset LIVE15 scope, and structured strike validation follows the documented
`greater` / `less` / `between` field semantics. Missing official market identity
also fails closed.

**Why:** Prevent callers from bypassing the approved nine-asset authority by
supplying an arbitrary scope or a merely type-correct `VerifiedMarketIdentity`,
and prevent malformed or unknown strike shapes from being promoted to verified
market truth.

**Validation / evidence:** Regression tests cover forged identity rejection,
parent-scope enforcement, exact structured-strike semantics, and missing event
identity. Ruff, pytest, mypy, hosted Ubuntu/Windows checks, CI Gate, and the
post-merge main workflow passed.

**Commit or PR:** PR #10, merged as `7ec1dd59fcfae9870f5f07b6af9a6391735c654a`.

**Next step:** Complete bounded stage-hygiene cleanup and final closeout
verification before any Storage work.

## 2026-09-04 — LIVE15-V2-REFERENCE-STREAM-001

**Summary:** Added the fixed nine-asset Reference Stream with SDK-native CF
Benchmarks and an isolated, version-guarded Pyth Value v13 compatibility leaf.

**Why:** Complete Market Ingress reference subscriptions without introducing a
direct Pyth client or replacing SDK transport/reliability machinery.

**Validation / evidence:** Authorized read-only CF discovery verified all seven
crypto IDs. The bounded demo Pyth probe was accepted but yielded no messages;
typed Pyth parsing and SDK queue dispatch are proven offline. Local and hosted
validation pass.

**Commit or PR:** `73e6a77` / PR #8.

**Next step:** Independent review and merge authorization; then Storage/Data
Truth design only if separately approved.
## 2026-09-04 — LIVE15-V2-MARKET-STREAM-REVIEW-CLOSEOUT-001

**Summary:** Independent review closeout preserved Market Stream runtime code
unchanged and added one offline Ingress Boundary verified-output to Market
Stream handoff regression.

**Why:** Record the actual recursive responsibility tree and durable downstream
contracts without changing market behavior.

**Validation / evidence:** Documents raw orderbook snapshot aliasing and active
SDK session ownership. No market semantics changed; local and hosted validation
pass.

**Commit or PR:** PR #7.

**Next step:** Independent review and merge authorization; then Reference
Stream unless priority changes.
## 2026-09-04 — LIVE15-V2-MARKET-STREAM-SDK-001

**Summary:** Added the Market Stream sibling as a thin composition of typed
`kalshi-sdk==13.0.0` orderbook, ticker, trade, and market-lifecycle
subscriptions selected only by `VerifiedMarketIdentity`.

**Why:** Complete Market Ingress child #2 without duplicating SDK transport,
authentication, reconnect, sequence, routing, or message-decoding machinery.

**Validation / evidence:** The installed SDK contract is inspected offline for
the four async typed public helpers. Offline delegation and ownership tests,
local validation, and hosted Ubuntu/Windows/CI Gate validation pass.

**Commit or PR:** PR #7.

**Next step:** Independent review and merge authorization; then Reference
Stream unless priority changes.
## 2026-09-03 — LIVE15-V2-REPOSITORY-BOOTSTRAP-001

**Summary:** Created the clean V2 repository and connected the local workspace to public GitHub on the `main` branch.

**Why:** Establish version history and rollback before architecture or implementation work begins.

**Validation / evidence:** Initial root files only; no V1 code copied, no implementation performed, and no Production changes.

**Commit or PR:** Initial commit recorded by Git history.

**Next step:** Blueprint discussion and architecture/design work.

## Entry convention

Each meaningful V2 task entry includes: Date, Task ID, Summary, Why, Validation / evidence, Commit or PR when available, and Next step.

## 2026-09-04 — LIVE15-V2-FOUNDATION-ENVIRONMENT-001

**Summary:** Established the reproducible Python 3.12/uv foundation in the V2 repository with a project-local environment and minimal package, test, and Project Brain skeleton.

**Why:** Provide a clean, isolated development baseline before business functionality or architecture work begins.

**Validation / evidence:** `uv` environment and lockfile created; `kalshi-sdk==13.0.0`, pytest, ruff, and mypy installed; complete current `mattpocock/skills` set installed under V2; foundation checks passed; no business implementation or Production action.

**Commit or PR:** PR #1.

**Next step:** Foundation review, then approved blueprint discussion.

## 2026-09-04 — LIVE15-V2-BRAIN-BOOTSTRAP-FINALIZATION-001

**Summary:** Finalized the minimal V2 Project Brain routing, approved current-plan, and reference-only V1 proven-paths document.

**Why:** Establish V2-owned governance and planning without importing V1 current state, roadmap, bugs, or implementation assumptions.

**Validation / evidence:** AGENTS routing, approved Brain routes, V2-only plan, and reference-only policy checked; foundation tests/lint/type checks remain green; no code, dependencies, skills, runtime, Production, or V1 changes.

**Commit or PR:** PR #1.

**Next step:** Foundation review before any business module implementation.

## 2026-09-04 — LIVE15-V2-V1-PROVEN-PATHS-AUDIT-001

**Summary:** Independently audited and corrected the V1 proven-path reference inventory against merged V1 PRs, resulting main authorities, and acceptance evidence.

**Why:** Prevent V2 from mistaking merged experiments, later-broken runtime states, partial POCs, or V1 bug workarounds for stable success paths.

**Validation / evidence:** Main proven references expanded to bounded Kalshi SDK/WS recovery, Recorder truth contracts, Research Data Authority, Project Brain/context recovery, Nomad lifecycle, immutable release/runtime identity, React Admin/MUI Web implementation, Parquet+ZSTD packaging, and verified COLD-to-research flow; partial/research-only and explicitly-not-proven paths are separated.

**Commit or PR:** PR #1.

**Next step:** Final independent foundation review and single authorized squash merge if PASS.

## 2026-09-04 — LIVE15-V2-UPSTREAM-CI-BASELINE-001

**Summary:** Closed the unmerged custom CI Router exploration in PR #2 and adopted an upstream-derived static Foundation CI workflow from `OvertureMaps/overturemaps-py` at pinned commit `9410974885ab5e9de107b15c0ba000a248c36a36`.

**Why:** Apply the approved Upstream First principle to generic CI infrastructure while retaining V2-owned domain semantics.

**Validation / evidence:** Closeout adds one repository-owned uv version authority, restores the separate Rule 9 rejection, and records the complete upstream MIT third-party notice. The workflow retains its Ubuntu/Windows matrix, SHA-pinned actions, locked dependency sync, pytest, Ruff, mypy, and CI Gate; local and hosted PR validation pass.

**Commit or PR:** PR #3.

**Next step:** Independent review before any business module implementation.

## 2026-09-04 — LIVE15-V2-DATA-KALSHI-GATEWAY-TREE-001

**Summary:** Created the V2 Data System / Market Ingress / Kalshi Gateway responsibility tree, with a thin read-only `kalshi-sdk` adapter and Market Identity leaves for scope, windows, candidate hints, official discovery, verification, and shadow comparison.

**Why:** Establish a clean Kalshi-only ingress boundary before any concrete asset mapping, storage, data truth, model, or trading work.

**Validation / evidence:** Final closeout records official series-query provenance, removes candidate authorization and ticker-prefix truth assumptions, completes Data System routing/current plan, and documents the stable public interface and usage. Official docs and installed `kalshi-sdk==13.0.0` APIs rechecked; local and hosted validation pass. The concrete LIVE15 Market Scope map remains deferred.

**Commit or PR:** PR #4.

**Next step:** Concrete LIVE15 Market Scope Config only after review and merge.

## 2026-09-04 — LIVE15-V2-MARKET-SCOPE-CONFIG-001

**Summary:** Added the concrete nine-asset LIVE15 Market Scope Config.

**Why:** Completes Ingress Boundary asset mapping.

**Validation / evidence:** Official read-only Kalshi Get Series verification found all nine mapped series with `fifteen_min` frequency; offline scope tests validate bijection, immutability, public export, MarketScopePort compatibility, resolver integration, and fail-closed unknowns.

**Commit or PR:** PR #5.

**Next step:** Independent review and merge authorization; then Market Stream design unless priority changes.

## 2026-09-04 — LIVE15-V2-INGRESS-SIBLING-SEPARATION-001

**Summary:** Physically separated Ingress Boundary from Kalshi Gateway so the two approved Market Ingress children no longer share one implementation subtree; narrowed the Kalshi Gateway public surface to provider access only and typed its WebSocket seam as the SDK `KalshiWebSocket`.

**Why:** Enforce the approved recursive responsibility tree before Market Stream starts. A sibling module must not be hidden inside another sibling, and future consumers must not depend on provider-specific identity paths.

**Validation / evidence:** The structural-only final seam removes the old `kalshi_gateway/identity` subtree; Kalshi Gateway remains provider-only; and the Market Ingress parent composes the Gateway public capability with the Ingress Boundary public resolver factory through `MarketDiscoveryPort`. Offline tests prove parent composition and import ownership without a network dependency; final local and hosted Ubuntu, Windows, and CI Gate validation pass.

**Commit or PR:** PR #6.

**Next step:** Independent review; then Market Stream design after explicit merge authorization.
