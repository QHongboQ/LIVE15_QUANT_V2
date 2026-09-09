# Changelog

## 2026-09-09 — LIVE15-V2-CANONICAL-DATASET-CONTRACT-REMOTE-REVIEW-FIX-001

**Reviewed head:** `5a48b8e0ae1c2b2e99590b0f7bb1b088772abf13` received
ChatGPT `CHANGES_REQUIRED`.

**Accepted:** Ownership, Replay-only authority input, ACCEPTED-only membership,
no-extra-dedup, complete pagination, strict As-Of, `NOT_ASSERTED`
completeness, immutability, and no physical-format selection remain unchanged.

**Fixes:** Dataset identity now binds complete semantic/audit provenance,
including included availability references and both exclusion layers; the
undefined `dataset_contract_version` was removed; `canonical-dataset/v1`
remains the single V1 semantic/identity/manifest policy version; and one
dataset identity now implies one complete semantic manifest core.

**Safety:** No implementation or runtime authorization changed.

## 2026-09-09 — LIVE15-V2-CANONICAL-DATASET-CONTRACT-DEFINITION-001

**Change:** Created the Canonical Dataset Data System child contract candidate.

**Authority and policy:** It consumes one complete bounded Replay As-Of view
and its recorded Data Truth authority. V1 candidate membership includes only
`ACCEPTED` authority; `DUPLICATE`, `CONFLICT`, and `NOT_ACCEPTED` remain
auditable exclusions.

**Determinism:** The candidate defines immutable dataset snapshots,
cryptographic identity, complete pagination, source-snapshot binding, and
page-size independence.

**Safety and references:** Completeness remains `NOT_ASSERTED`; no features,
labels, training, physical storage selection, runtime activation, or canonical
table/data change occurred. V1 Research Data Authority, V1 Parquet+ZSTD, and
V1 COLD → RDA → runner are bounded reference evidence only.

**Status:** Contract candidate pending independent ChatGPT review.

## 2026-09-09 — LIVE15-V2-PROJECT-BRAIN-DATA-TRUTH-STALE-STATUS-CLEANUP-001

**Change:** Removed stale active downstream-state claims from the FINAL CLOSED
Data Truth leaf after Replay engineering closure.

**Before / after:** The leaf described Replay as unimplemented and Replay
planning as Current NEXT. It now records Replay engineering as FINAL CLOSED and
Canonical Dataset contract / responsibility definition as Current NEXT.

**Safety / reason:** No Data Truth semantic change, Replay change, Canonical
Dataset design or implementation, or runtime, data, config, source, or test
change occurred. This prevents recursive Project Brain recovery through the
Data Truth leaf from restoring an obsolete project phase.

## 2026-09-09 — LIVE15-V2-REPLAY-AS-OF-ENGINEERING-FINAL-STATUS-REMOTE-REVIEW-FIX-001

**Reviewed head:** `7229f9a9a7ae12430e3511e79050760df7f5927b` received
ChatGPT `CHANGES_REQUIRED`.

**Fix:** Removed the stale statement that the Replay implementation plan is the
next planning gate and clarified that FINAL CLOSED applies to Replay engineering
implementation while canonical activation remains unauthorized.

**Safety:** No source, test, runtime, data, or activation change occurred.
Canonical Dataset remains CURRENT NEXT / UNIMPLEMENTED.

## 2026-09-09 — LIVE15-V2-REPLAY-AS-OF-SLICE-4-AND-ENGINEERING-FINAL-STATUS-CLOSURE-001

**Status:** Closed Slice 4 Recorder Composition and the overall Replay & As-Of
engineering implementation as FINAL CLOSED. All four engineering slices are
now FINAL CLOSED.

**Evidence:** PR #52's first reviewed head
`5f9bc6f87da5ca3f71f5e96ae0402406b32d8b90` received ChatGPT
`CHANGES_REQUIRED`; final head `75e0ef54bf8755eb81c994d96756c067e5161626`
received `PASS_WITH_HYGIENE` and passed exact-head CI. Normal merge
`306924cae59dc5a2ec9f5737e7c4103a0c5e7227` has parents
`c2b62ca6a600db9af8e9557b38b9f776b1461c19` and
`75e0ef54bf8755eb81c994d96756c067e5161626`; merge-SHA CI, the merged-main
technical seal, controlled and real task-owned Job-Object QuestDB end-to-end
acceptance, idempotent recovery with exact physical counts of one, and teardown
passed.

**Hygiene and safety:** Two empty task-owned pytest bases remain inaccessible
after verification; they are a local hygiene item, not a runtime-correctness
blocker. No ACL repair is authorized. No canonical activation, runtime, table,
data, production Recorder deployment, or production `CLOCK_SAFETY` closure
occurred.

**Next:** Canonical Dataset contract / responsibility definition through a
separate reviewable task. This does not authorize Canonical Dataset
implementation or canonical Replay/runtime activation.

## 2026-09-09 — LIVE15-V2-REPLAY-AS-OF-SLICE-4-RECORDER-COMPOSITION-REMOTE-REVIEW-FIX-001

**Review:** ChatGPT recorded `CHANGES_REQUIRED` on reviewed head
`5f9bc6f87da5ca3f71f5e96ae0402406b32d8b90`. No production composition defect
was established.

**Acceptance closeout:** Added real `AvailabilityWriter` composition recovery
coverage for exact `IN_DOUBT` reconciliation/no blind reappend and explicit
post-definite-failure re-entry; completed the public Data Truth error matrix;
proved same-ID immutable read-back mismatch rejection; linked marker failures
from a composition result to existing Replay exclusion semantics; and extended
the task-owned QuestDB path with post-success idempotent recovery and exact
evidence, TruthDecision, and semantic-marker counts.

**Hygiene:** The exact task-owned pytest base
`D:\LIVE15_QUANT_V2\.pytest-recorder-reviewfix-35201875748e450e90b26fcafda3c93b`
contained no files or `server.conf`; its only descendant was an empty pytest
case directory. After the real harness confirmed contained process, ports,
QuestDB root, and SF cleanup, one ordinary deletion returned `AccessDenied`.
No ACL repair or further deletion was attempted. This is a separate final
hygiene item, not a runtime-correctness blocker.

**Next:** Keep Slice 4 as an implementation candidate pending exact-head
re-audit. No canonical activation, runtime/table/data change, or FINAL CLOSED
claim occurred.

## 2026-09-09 — LIVE15-V2-REPLAY-AS-OF-SLICE-4-RECORDER-COMPOSITION-IMPLEMENTATION-001

**Change:** Added the upper Data System `RecorderComposition` candidate. It
uses only sealed public seams to capture a typed message, persist the immutable
CaptureFact, require one exact Hot Store readback, record evidence availability,
obtain the public Data Truth decision, and record authority availability.

**Safety / validation:** Terminal persistence outcomes stop before lower calls;
nonterminal outcomes make one readback attempt and never claim proof without an
exact fact. Typed availability failures are reported without retry, Data Truth
failures propagate, and explicit recovery never re-persists. Controlled tests,
Replay exclusion coverage, static dependency checks, and opt-in Job-Object
contained QuestDB acceptance passed. The acceptance test removed its server and
Store-and-Forward resources; Windows denied removal of its empty isolated pytest
base after verification, with no ACL repair or broader cleanup attempted.

**Next:** Run the remaining bounded validation matrix and obtain independent
exact-head review before any merge decision. No canonical runtime/table/data or
production activation occurred.

## 2026-09-09 — LIVE15-V2-REPLAY-AS-OF-SLICE-3-FINAL-STATUS-CLOSURE-001

**Change:** Closed the Slice 3 QuestDB Replay Source engineering implementation
as FINAL CLOSED.

**Evidence:** PR #50's initial rejected head was
`ced4d6820f8335a255251c2e15a97533cac8be01`; identity-corrected head
`725c6cdd8673d13528183776c7772f60a26178f6` received a second
`CHANGES_REQUIRED` result;
final approved head `d98d5798004c48aae735fef6fb6236982bb67d34` passed the
final ChatGPT exact-head review and CI. Normal merge
`4a1809d72aa0451cf357a3845451da294ea33a5a` has parents
`08b87512d9ae6e266a549f055ed19c33bc7dc7c0` and
`d98d5798004c48aae735fef6fb6236982bb67d34`; merge-SHA CI, merged-main
technical seal, controlled and real task-owned QuestDB acceptance, teardown,
and main-only remote branch state passed.

**Engineering result:** A read-only physical Replay source reconstructs sealed
evidence, TruthDecision authority, and availability evidence; preserves the
logical-versus-composite authority identity separation; validates physical
schemas and sealed models; and supports deterministic snapshot/cursor restart
and fail-closed drift semantics.

**Safety / next:** No Slice 4, Recorder composition, canonical runtime/table/
data activation, or production `CLOCK_SAFETY` closure occurred. Current NEXT is
Slice 4 — Data System Recorder Composition through a separately reviewed
implementation task.

## 2026-09-09 — LIVE15-V2-REPLAY-AS-OF-SLICE-3-QUESTDB-SOURCE-REAL-ACCEPTANCE-CLOSEOUT-001

**Prior head:** `6c9c61df5c3ec381cac987a3aa87d3487cde34c9`.

**Reason:** The controlled matrix and core real QuestDB path passed, while the
remaining real-server duplicate, source-drift, future, and backdated cases
remained open.

**Closeout evidence:** Task-owned real QuestDB acceptance now proves
fail-closed duplicate evidence, TruthDecision authority, and availability
markers; source-table reconfiguration drift; future-after-cutoff stability;
backdated eligible-membership drift; malformed-row bounded mapping; and clean
task-owned teardown.

**Safety / next:** Slice 3 remains an implementation candidate. No canonical
activation, runtime, table, or production-data change occurred; Slice 4 has not
started. The next step is the mandatory ChatGPT exact-head Slice 3 re-audit.

## 2026-09-09 — LIVE15-V2-REPLAY-AS-OF-SLICE-3-QUESTDB-SOURCE-REMOTE-REVIEW-FIX-002

**Review:** ChatGPT recorded `CHANGES_REQUIRED` on reviewed head
`725c6cdd8673d13528183776c7772f60a26178f6`. The logical-versus-composite
marker identity separation remains correct.

**Fix:** Physical availability decoding now reuses sealed `AvailabilityRecord`
semantics, including non-negative proof times. Expanded controlled acceptance
proves schema, reconstruction, pagination, restart, source drift, and
future/backdated membership behavior.

**Safety:** Slice 3 remains an implementation candidate. No Slice 4 or
canonical runtime, table, or production-data activation occurred.

## 2026-09-09 — LIVE15-V2-REPLAY-AS-OF-SLICE-3-QUESTDB-SOURCE-REMOTE-REVIEW-FIX-001

**Review:** ChatGPT recorded `CHANGES_REQUIRED` on reviewed head
`ced4d6820f8335a255251c2e15a97533cac8be01`.

**Fix:** Separated the logical evidence and TruthDecision proof-authority
identities used by Availability markers from the composite Replay
source/snapshot provenance identities. Fixtures and regressions now prove
logical Slice 2 markers qualify while composite source identities fail closed.

**Safety:** Slice 3 remains an implementation candidate. No Slice 4, canonical
activation, runtime, table, or production-data change occurred.

## 2026-09-09 — LIVE15-V2-REPLAY-AS-OF-SLICE-3-QUESTDB-SOURCE-IMPLEMENTATION-001

**Change:** Added a read-only, explicitly configured QuestDB Replay source
candidate. It verifies the physical CaptureFact, TruthDecision, and
Availability schemas; decodes their immutable records; binds deterministic
source identities without connection details; and provides no schema creation,
writer, or composition path.

**Safety:** The adapter is not activated in canonical composition and creates
no canonical table or runtime change. Controlled tests and an opt-in,
Job-Object-contained UUID-table QuestDB acceptance test cover the candidate;
Slice 4 Recorder composition remains out of scope.

**Next:** Run the full bounded validation matrix, then obtain independent
exact-head review before any merge decision.

## 2026-09-09 — LIVE15-V2-REPLAY-AS-OF-SLICE-2-FINAL-STATUS-CLOSURE-001

**Change:** Closed the Slice 2 Availability Support engineering implementation
as FINAL CLOSED.

**Evidence:** PR #48's initial reviewed head
`f2361333d8c3b231a53feca3128e64119f12e814` required changes; final approved
head `5119271b71450fa83a15de4b709fb07034a837e4` passed ChatGPT exact-head
re-audit and CI. Normal merge `a78b731a8c24879b0da41ec4d6f28bb43ebe2daf` has
parents `cd456aaba643a201809bdd360fc4fec31d1efe24` and
`5119271b71450fa83a15de4b709fb07034a837e4`; merge-SHA CI, exact merged-main
technical seal, clock engineering tests, real task-owned QuestDB acceptance,
and teardown passed. Remote branches are main-only.

**Engineering result:** Append-only availability authority support with
conservative clock semantics, exact `IN_DOUBT` reconciliation, no blind
reappend, WAL/no-DEDUP/no-UPSERT QuestDB mechanics, and strict physical
validation.

**Safety / next:** No canonical availability activation, runtime or
production-data change, Slice 3 implementation, or Recorder composition
occurred. Current NEXT is Slice 3 — QuestDB Replay Source, through a separately
reviewed implementation task; the production `CLOCK_SAFETY` gate remains open.

## 2026-09-09 — LIVE15-V2-REPLAY-AS-OF-SLICE-2-AVAILABILITY-SUPPORT-REMOTE-REVIEW-FIX-001

**Review result:** ChatGPT recorded `CHANGES_REQUIRED` on reviewed head
`f2361333d8c3b231a53feca3128e64119f12e814`.

**Change:** Preserved exact in-doubt candidates for reconciliation, contained
visibility-barrier failures as in doubt, distinguished terminal from pending
sender diagnostics, and completed and validated the required Slice 2
clock, controlled-failure, and disposable-QuestDB acceptance matrix.
Final acceptance closure includes the post-barrier zero-row `IN_DOUBT` and
second-call no-blind-reappend regression.

**Safety:** Slice 2 remains an implementation candidate; the production
`CLOCK_SAFETY` gate remains open. No Slice 3/4 or canonical runtime, table, or
data change occurred.

## 2026-09-09 — LIVE15-V2-REPLAY-AS-OF-SLICE-2-AVAILABILITY-SUPPORT-IMPLEMENTATION-001

**Change:** Created the Slice 2 Availability Support implementation candidate:
provider-neutral immutable availability models, narrow recording port and
writer, conservative monotonic proof clock, no-blind-reappend behavior, and a
disposable QuestDB availability adapter with WAL enabled and no DEDUP or
UPSERT.

**Safety:** Task-owned disposable QuestDB acceptance only. No canonical
runtime, table, or production-data change occurred; Slice 3 and Slice 4 remain
unauthorized. The production `CLOCK_SAFETY` operational gate remains open.

**Next:** Independent ChatGPT implementation review is required before merge.

## 2026-09-09 — LIVE15-V2-REPLAY-AS-OF-SLICE-1-FINAL-STATUS-CLOSURE-001

**Change:** Closed Replay & As-Of Slice 1 Pure Replay Core as FINAL CLOSED.

**Evidence:** PR #46's first head
`e2e0426628e5999733ee678729c350f6a582899f` required changes; corrected
approved head `9779c99ef79f1815ee5c4d51cad225599a94d120` passed ChatGPT
exact-head review and CI. Normal merge
`62f8c2f672ca3627d9690727ff47b80d805266d5` has parents
`fe097c1a5d112619f3949a92a341604f1760072b` and
`9779c99ef79f1815ee5c4d51cad225599a94d120`; merge-SHA CI and the merged-main
technical seal passed, and remote branches are main-only.

**Engineering result:** A request-bounded provider-neutral Replay core with
deterministic snapshot/cursor mechanics, complete error taxonomy, keyset
pagination, and deterministic exclusions is merged.

**Safety / next:** No Slice 2, QuestDB availability storage, Recorder
composition, canonical runtime, table, or production-data change occurred.
Slice 2 — Availability Support remains separately reviewed implementation work.

## 2026-09-08 — LIVE15-V2-REPLAY-AS-OF-SLICE-1-PURE-CORE-REMOTE-REVIEW-FIX-001

**Review result:** ChatGPT recorded `CHANGES_REQUIRED` on reviewed head
`e2e0426628e5999733ee678729c350f6a582899f`.

**Change:** Added a request-bounded, provider-neutral `ReplayCandidateScope`
to the source seam; made Cursor V1 schema and field types exact before
semantic cursor binding checks; canonicalized public exclusions by
`(capture_id, exclusion_code)`; and fail-closed availability evidence with an
empty reference.

**Status / safety:** Slice 1 remains an implementation candidate. No Slice 2
has started, and this change contains no QuestDB, runtime, table, or data
change.

**Validation:** Slice 1 and architecture tests, full pytest, Ruff, MyPy, and
the diff check are required before the same draft PR receives an exact-head
re-audit.

## 2026-09-08 — LIVE15-V2-REPLAY-AS-OF-SLICE-1-PURE-CORE-IMPLEMENTATION-001

**Change:** Created the Slice 1 Replay & As-Of Pure Replay Core implementation
candidate: provider-neutral request/result models, validation, deterministic
identity/snapshot/cursor/keyset semantics, a narrow source protocol, and an
in-memory source with its authorized unit and architecture tests.

**Authority / safety:** Replay & As-Of contract and implementation-plan
authority remain FINAL CLOSED. This change contains no QuestDB code, no
availability persistence, no recorder composition, no canonical activation,
and no Slice 2/3/4 implementation.

**Validation:** Slice 1 tests, architecture tests, Ruff, and MyPy passed
locally. Independent ChatGPT code review remains required before merge.

**Next:** Review this Slice 1 implementation candidate only; do not begin
availability support, a QuestDB source, or recorder composition.

## 2026-09-08 — LIVE15-V2-REPLAY-AS-OF-IMPLEMENTATION-PLAN-FINAL-STATUS-CLOSURE-001

**Change:** Closed Replay & As-Of implementation-plan authority as FINAL
CLOSED.

**Evidence:** PR #44's rejected first head
`86d51d89f02f7c3bc5e5c15a2260848c8f5d4dfb` was corrected at reviewed head
`af87756b1a948aee41253b9507c552f31df93bfc`, which passed ChatGPT re-audit and
exact-head CI. Normal merge `13af6e1cea4c087c547bfc9f6a25311ab6690b6b` has
parents `752c57e3c262e006ff127f1436e435d40376d7ee` and
`af87756b1a948aee41253b9507c552f31df93bfc`; merge-SHA CI and local docs seal
passed, and the remote branch state is main-only.

**Safety:** No implementation, source, test, config, dependency, runtime,
table, or data change occurred. Replay, availability production, and recorder
composition remain NOT IMPLEMENTED; canonical activation remains unauthorized.

**Next:** Replay & As-Of Slice 1 — Pure Replay Core implementation, through a
separately reviewed implementation task.

## 2026-09-08 — LIVE15-V2-REPLAY-AS-OF-IMPLEMENTATION-PLAN-REMOTE-REVIEW-FIX-001

**Change:** Corrected the Replay & As-Of implementation-plan candidate after
the mandatory GitHub-visible ChatGPT review recorded `CHANGES_REQUIRED` on
reviewed head `86d51d89f02f7c3bc5e5c15a2260848c8f5d4dfb`.

**Reason:** The accepted architecture required six bounded planning fixes:
deterministic request identity; source/proof-schema-bound availability;
clock-floor port and post-proof sampling; exact recorder persistence/proof/
marker boundaries; executable append definite-failure/in-doubt handling; and
the FINAL CLOSED error taxonomy mapping.

**Status / safety:** Implementation remains NOT IMPLEMENTED. No source, test,
runtime, table, data, config, or dependency change occurred; canonical
activation remains unauthorized.

**Next:** Keep PR #44 draft-only for exact-new-head ChatGPT implementation-plan
re-audit. No implementation work is authorized by this correction.

## 2026-09-08 — LIVE15-V2-REPLAY-AS-OF-IMPLEMENTATION-PLAN-DRAFT-001

**Change:** Drafted the Replay & As-Of implementation-plan authority candidate.

**Reason:** The FINAL CLOSED contract, COMPLETED availability-mechanism fit
preparation, and FINAL CLOSED snapshot-membership POC provide bounded input to
planning, not implementation.

**Status / safety:** Replay implementation and availability production remain
NOT IMPLEMENTED; canonical activation remains unauthorized. The candidate
preserves sealed Storage/Data Truth contracts, plans disposable-only QuestDB
acceptance, and requires independent review before any implementation authority
can close.

**Next:** Independent review of this implementation-plan candidate. No source,
test, runtime, table, data, Canonical Dataset, Model/training, or Trading work
is authorized by this entry.

## 2026-09-08 — LIVE15-V2-REPLAY-AS-OF-SNAPSHOT-MEMBERSHIP-POC-FINAL-STATUS-REVIEW-FIX-001

**Change:** Corrected the POC final-status classification after ChatGPT
`CHANGES_REQUIRED` review of head
`a966e794e1ce036274a5d19f52ca31f48ec09426`.

**Reason:** The prior status wording over-classified availability-mechanism fit
preparation as FINAL CLOSED. The corrected classification is COMPLETED; only
Replay contract authority and the accepted snapshot-membership POC gate are
FINAL CLOSED.

**Safety / next:** `SAFE_TO_DRAFT_REPLAY_AS_OF_IMPLEMENTATION_PLAN` remains
YES for plan drafting only. No runtime, source, test, configuration, or
dependency change occurred; implementation and availability production remain
NOT IMPLEMENTED.

## 2026-09-08 — LIVE15-V2-REPLAY-AS-OF-SNAPSHOT-MEMBERSHIP-POC-FINAL-STATUS-CLOSURE-001

**Change:** Closed the Replay & As-Of snapshot-membership POC gate as FINAL
CLOSED with technical result `PASS_WITH_FAIL_CLOSED_DRIFT`.

**Evidence:** PR #42 corrected reviewed head
`cb1d285a46abb6ba725eaf0a3287a339f85ae76c` passed ChatGPT exact-head
re-audit and hosted CI; normal merge
`b76d10b0bc480a7f84a0cd6e97dd896a2f24d124`, merge-SHA CI, and the exact
merged-main real disposable POC passed. The remote branch state is main only.

**Accepted findings:** Conservative proof time is compatible without claiming
earliest visibility; evidence proof requires exact immutable CaptureFact
read-back; DataTruth authority proof is sealed verified return; recovery never
backdates availability; the marker floor alone is insufficient under clock
rollback; a canonical fingerprint/recompute/fail-closed candidate preserves
membership safety; all valid TruthDecision categories remain authority; and
selection and ordering are independent.

**Safety:** No production Replay implementation, availability storage, runtime,
table, canonical data, Canonical Dataset, Model/training, or Trading change
occurred. Task Java process, ports, and root were clean after the real POC.

**Next:** Data System → Replay & As-Of implementation-plan authority drafting
only. The availability production mechanism remains NOT IMPLEMENTED and
canonical activation remains unauthorized.

## 2026-09-08 — LIVE15-V2-REPLAY-AS-OF-SNAPSHOT-MEMBERSHIP-POC-REMOTE-REVIEW-FIX-001

**Change:** Corrected the snapshot-membership POC after ChatGPT's
GitHub-visible `CHANGES_REQUIRED` review of head
`48f56d7751ef02e886bac5fdf1554ad722e6461d`. EVENT_TIME now selects with
`provider_timestamp` after the qualified-scope null check, all valid recorded
TruthDecision categories participate in membership, and selection axis is
independent from output ordering and cursor keys.

**Reason:** The prior POC used arrival time for EVENT_TIME filtering, treated
semantic categories other than ACCEPTED as ineligible, and represented
selection and ordering with one overloaded axis. These model defects could
hide contract violations despite an otherwise viable snapshot approach.

**Validation / result:** A corrected real disposable QuestDB POC passed the
event-time anti-false-pass window, both cross-combinations of selection and
ordering, all four valid TruthDecision categories, normal late append and
recovery, reader recreation, contained task-server restart, and exact keyset
continuation. The clock rollback adversary again proved
`max(200, 100 + 1) = 200 <= cutoff 900`; changed membership and duplicate
physical authority both failed closed. Result:
`PASS_WITH_FAIL_CLOSED_DRIFT`; clock policy:
`MEMBERSHIP_FINGERPRINT_FAIL_CLOSED_SUFFICIENT`.

**Safety:** POC-only test and changelog change. The real run used only fresh
UUID-named task root, ports, tables, and Job Object-contained processes; no
canonical runtime, service, table, or production data was changed.

**Next:** Keep PR #42 Draft for exact-head ChatGPT POC re-audit. Replay
implementation planning remains unauthorized.

## 2026-09-08 — LIVE15-V2-REPLAY-AS-OF-SNAPSHOT-MEMBERSHIP-POC-001

**Change:** Added one opt-in, disposable Windows QuestDB POC that tests a
candidate source-snapshot membership fingerprint and keyset continuation for
Replay & As-Of. This is POC evidence only; it does not add Replay production
code, an availability mechanism, or a contract change.

**Reason:** Availability-mechanism fit identified source snapshot identity and
paged membership stability as the remaining pre-plan technical blocker.

**Validation / result:** A real task-owned QuestDB 10.0.1 run using Python
client 5.0.0 passed normal late-append and late-recovery-marker continuation,
reader recreation, and a task-owned contained server restart. Page 1 bound
`[A, B]` with fingerprint
`1cac25e5b0cf95c6295abf93e303865c82733c6c3586262861faff645d3798c2`.
The explicit clock rollback adversary proved the last-marker floor alone is
insufficient: `max(200, 100 + 1) = 200 <= cutoff 900`. The changed membership
and a duplicate physical TruthDecision authority both failed closed before a
mixed continuation page. Result: `PASS_WITH_FAIL_CLOSED_DRIFT`; clock policy:
`MEMBERSHIP_FINGERPRINT_FAIL_CLOSED_SUFFICIENT` for this POC.

**Safety:** The POC used UUID-named task root, ports, tables, and a Windows Job
Object with `KILL_ON_JOB_CLOSE`; it made no canonical runtime, service, table,
or production-data change. The root, listeners, and contained Java process
were verified absent after cleanup.

**Next:** Independent POC review is required. The Replay implementation plan
remains unauthorized pending that review.

## 2026-09-08 — LIVE15-V2-REPLAY-AS-OF-CONTRACT-FINAL-STATUS-CLOSURE-001

**Change:** Closed Replay & As-Of contract authority as FINAL CLOSED. The
implementation remains NOT IMPLEMENTED, its availability evidence mechanism
remains NOT SELECTED / NOT IMPLEMENTED, and canonical activation remains NOT
AUTHORIZED.

**Reason:** The required contract lifecycle completed: PR #40's first reviewed
head required changes; corrected reviewed head
`a838ebfd6d0bd9cc427e0ec90ce08c952d794d61` passed ChatGPT re-audit and
exact-head CI; normal merge
`528815ef2883b3757515b9b9d8e3dcadc92981b6` had the exact authorized parents;
merge-SHA Ubuntu, Windows, and CI Gate checks passed; and the local docs seal
passed.

**Validation / evidence:** PR #40 contains status/contract documentation only.
No source, test, configuration, dependency, canonical runtime/table/data, or
production change occurred; remote branch state is main only.

**Next:** Data System → Replay & As-Of implementation-plan /
availability-mechanism fit preparation only. This is planning and upstream-fit
work only; it does not authorize Replay implementation, availability storage,
Canonical Dataset, Model/training, or Trading work.

**Safety:** No Replay implementation, availability storage, canonical
runtime/table/data change, Canonical Dataset, Model/training, or Trading work
occurred.

## 2026-09-08 — LIVE15-V2-REPLAY-AS-OF-CONTRACT-REMOTE-REVIEW-FIX-001

**Change:** Corrected the Replay & As-Of contract after independent
GitHub-visible review of rejected head
`77fa8264f48994fe6ab2158184651c4b9c0823e2` returned CHANGES_REQUIRED. The
request, cursor, and provenance now bind an explicit authority policy version;
EVENT_TIME selection fails closed for a null provider timestamp in qualified
scope; and V1 pagination binds immutable source snapshot membership. The draft
also replaces the unowned transport term with provider transport, QuestDB SF
transport, and Hot Store physical terminology.

**Reason:** The sealed Data Truth authority key is policy-versioned, an
event-time window cannot safely silently omit null-provider-time evidence, and
a deterministic cursor key alone cannot prove stable source membership across
pages.

**Validation / result:** Documentation-only correction candidate. Contract
review remains pending; this entry does not claim PASS. Replay implementation,
availability storage, canonical runtime/table activation, and Canonical Dataset
work remain NOT AUTHORIZED.

**Commit / PR:** Normal correction commit pending on existing Draft PR #40.

**Next:** Publish the corrected candidate, wait for exact-head CI, then return
the same Draft PR for ChatGPT contract re-audit. No implementation-plan work is
authorized by this entry.

**Safety:** No source, test, dependency, CI, runtime, canonical data/table,
service, model, or trading change occurred.

## 2026-09-08 — LIVE15-V2-REPLAY-AS-OF-CONTRACT-DRAFT-001

**Change:** Added Replay & As-Of as a direct Data System child and drafted its
bounded contract authority. The draft defines historical evidence replay,
recorded TruthDecision authority replay, strict two-dimensional As-Of
qualification, deterministic ordering, paired output, provenance, and an
explicit NOT_ASSERTED completeness state.

**Reason:** The prior authority preparation identified that exact historical
system-knowledge reconstruction requires separately recorded physical evidence
availability and recorded authority availability. The existing timestamps do
not supply either semantics, so this contract records the boundary without
reinterpreting them or selecting an availability storage mechanism.

**Validation / result:** Documentation-only candidate. `git diff --check` and
the targeted semantic-contradiction audit are required before publication.
Replay implementation, availability-ledger implementation, canonical runtime
or table activation, and canonical dataset work remain NOT AUTHORIZED.

**Commit / PR:** Contract draft commit and Draft PR pending independent review.

**Next:** Independent review of the Replay & As-Of contract. After contract
closure, prepare only the implementation plan and availability-mechanism fit;
no implementation code is authorized by this entry.

**Safety:** No source, test, dependency, CI, runtime, canonical data/table,
service, model, or trading change occurred.

## 2026-09-08 — LIVE15-V2-DATA-TRUTH-SLICE-2-FINAL-STATUS-CLOSURE-001

**Change:** Closed the Data Truth Slice 2 Persistent History implementation as
FINAL CLOSED under the approved single-writer constraint.

**Reason:** The complete required lifecycle passed: independent review of
corrected head `8d43a2b0a603e0276bc580cf66414967bde567dc`, exact-head CI, normal
PR #38 merge `abc4bdbd52150ab33ec60c0c6902235042d199f6`, merge-SHA CI, and the
exact merged-tree local seal.

**Validation / evidence:** Postmerge Ubuntu, Windows, and CI Gate checks
passed. The local merge-SHA seal passed 39 history units, 18 architecture
tests, 4 real integrations, and 223 ordinary tests with 27 skipped; Ruff,
MyPy, and diff checks passed. Current-run task Java, launcher, port, and root
residue were zero, and the remote retained main only.

**Next:** Data System → Replay & As-Of authority / planning preparation only.
This does not authorize Replay implementation, runtime deployment, Canonical
Dataset work, Model/training work, or Trading work.

**Safety:** No runtime restart, canonical TruthDecision table, canonical
activation, production-data change, or sealed semantic change occurred.

## 2026-09-08 — LIVE15-V2-DATA-TRUTH-SLICE-2-PERSISTENT-HISTORY-PUBLISH-CANDIDATE-001

**Change:** Added the private `QuestDBTruthDecisionHistory` persistent Data
Truth adapter. It uses a WAL-enabled, append-only QuestDB table without DEDUP
or UPSERT; resolves subject and accepted-event evidence through the
provider-neutral `HotStore` port; maps direct append acknowledgement to the
existing taxonomy; and uses QuestDB's `wait_wal_table` as the explicit
post-acknowledgement visibility barrier. The opt-in real-server harness now
uses a Windows Job Object to contain its disposable QuestDB process.

**Reason:** Slice 2 required a bounded, directly persistent history candidate
whose post-append visibility is an upstream server barrier rather than
semantic lookup, reconciliation, retry, or polling logic in the adapter.

**Validation / result:** Candidate validation PASS: focused history units (38
passed); Data Truth plus HotStore architecture checks (18 passed); opt-in real
QuestDB integration (3 passed); ordinary suite (222 passed, 26 skipped); Ruff
PASS; MyPy PASS; and `git diff --check` PASS. The implementation remains a
candidate pending independent GitHub-visible review. No canonical QuestDB
root, table, service, server configuration, or production activation was
changed or authorized.

**Commit / PR:** Implementation commit `0bfc647`; candidate changelog commit
pending. Publish only as a Draft PR against main at
`8ca91440ccaf30955f92d26fede98161e9fbfa29`.

**Next:** Run the final local seal, publish the two commits as a Draft PR, wait
for CI on the exact candidate head, then obtain the mandatory ChatGPT remote
audit. Production activation remains NOT AUTHORIZED.

**Safety:** No canonical runtime/data mutation, service restart, dependency or
CI configuration change, merge, push force, or production activation.

## 2026-09-08 — LIVE15-V2-DATA-TRUTH-QUESTDB-RECONCILIATION-POC-FINAL-STATUS-CLOSURE-PR-001

**Change:** Closed the Data Truth QuestDB reconciliation POC gate in current
authority. The accepted result establishes QuestDB TruthDecision-history
persistence/reconciliation mechanics as proven under the approved
single-writer constraint and advances Current NEXT to Data Truth Slice 2
authorization preparation.

**Reason:** The bounded POC lifecycle is complete: POC PR #36 merged as
`249144de204247bd7a0589d8ba67116c48b8dcc7`; reviewed POC head
`a4fd011586289ede142d7d087f682898aef18530` passed ChatGPT direct remote POC
review; the POC result was accepted; merge-SHA Windows, Ubuntu, and CI Gate
passed; and the merge-SHA local opt-in POC seal passed all cases A-L (12
passed).

**Validation / result:** The POC gate is FINAL CLOSED, PASS / ACCEPTED. The
proven bounded mechanics are direct append acknowledgement, exact
server-visible subject lookup, committed-but-no-caller-ACK reconciliation,
ambiguous absence remaining IN_DOUBT, no blind reappend, fail-closed
conflicting/multiple authority, and append-only operation without DEDUP or
UPSERT. Full pytest PASS (183 passed, 23 skipped); Ruff PASS; MyPy PASS; and
`git diff --check` PASS. No canonical root/table/service/server.conf, DEDUP,
SF, runtime, or production-data mutation occurred. Overall Data Truth and
persistent TruthDecision authority remain NOT IMPLEMENTED; Slice 2 remains NOT
AUTHORIZED.

**Commit / PR:** Status commit
`e8d16722a306645474dbc2f6a2733a25014e30f5`; changelog audit commit pending.
Draft status-closure PR pending publication and remote authority audit.

**Next:** Publish this two-commit status/authority closure as a Draft PR for
ChatGPT direct remote status audit. Slice 2 still requires separate explicit
authorization.

**Safety:** No source, test, dependency, CI, runtime, canonical activation, or
production-data change.

## 2026-09-07 — LIVE15-V2-DATA-TRUTH-QUESTDB-RECONCILIATION-POC-EXECUTION-001

**Change:** Added and executed a test-only, opt-in QuestDB TruthDecision-history
reconciliation POC on a disposable task-owned QuestDB 10.0.1 process. The POC
uses the sealed SubjectDecisionKey `(policy_version, subject_capture_id)`, a
UUID-scoped `truth_history_poc_<uuid>` table, a physical-only designated
timestamp, and no DEDUP or UPSERT configuration.

**Reason:** The pre-Slice-2 gate required real-server evidence that a
TruthDecision subject can reconcile after the server commits a frame while the
original caller never receives an acknowledgement result, without creating a
production `questdb_history.py` adapter or changing current authority.

**Validation / result:** Authorized local POC PASS on the exact main baseline
`276c5b1542fef77dcaed9980cb30f454c9d47428`, using QuestDB Server 10.0.1 and
Python `questdb==5.0.0`. The task-owned `D:\LIVE15_POC_RUN_C9D3` base used a
temporary root, four unique loopback ports, and UUID-scoped disposable tables;
all task resources were removed after execution. Cases A–L passed: normal ACK
and exact lookup; bounded visibility; definite pre-write rejection; a real
child-process frame commit followed by a fresh exact subject read and child
termination before caller ACK return; absent ambiguous outcome remains
IN_DOUBT without a second append; conflicting and multiple authority fail
closed; repeat invocation performs no second append; distinct subjects remain
append-only; no DEDUP/UPSERT metadata; and success/exception cleanup. Normal
append count = 1; committed/no-caller-ACK physical append count = 1;
ambiguous-absent physical append count = 0 after one logical attempt;
conflict new-append count = 0; second-invocation second-append count = 0.
No blind reappend, canonical root/table/runtime/service/server.conf, canonical
SF/DEDUP, or production data was used. Focused opt-in POC PASS (12 passed);
ordinary module collection PASS (12 skipped); full pytest PASS (183 passed,
23 skipped); Ruff PASS; MyPy PASS; and `git diff --check` PASS.

**Commit / PR:** Test-only POC commit
`e169d2ec3528d605d773f78f9c4c84abfaf8e6fe`; evidence commit pending. Draft
PR publication and ChatGPT remote POC review are pending; no PR is ready for
merge.

**Next:** Commit this bounded evidence, publish the two-commit branch as a
Draft PR, and obtain formal ChatGPT review of the GitHub-visible POC harness
and evidence. Slice 2 remains NOT AUTHORIZED.

**Safety:** No production TruthDecision history adapter, Slice 1 contract,
Project Brain authority/status, runtime configuration, canonical table, or
production-data change. Slice 2 remains NOT AUTHORIZED.

## 2026-09-07 — LIVE15-V2-GLOBAL-ENGINEERING-GITHUB-FIRST-REMOTE-REVIEW-AUTHORITY-REMOTE-AUDIT-FIX-001

**Change:** Generalized the global GitHub-first authority so formal ChatGPT
independent review of any repository change requires the actual changed scope
to be visible on GitHub, with source and tests included only where applicable.

**Reason:** ChatGPT's direct GitHub authority audit of PR #35 found that the
original rule correctly covered implementation and architecture review but did
not explicitly cover pure Project Brain, authority, contract, lifecycle/status,
and engineering-governance review.

**Validation / result:** Local work and validation remain allowed, but no
local-only candidate can receive formal ChatGPT independent-review PASS.
Docs-only changes require the actual remote documentation/diff/commits and may
receive bounded remote authority or status verification without reopening
unchanged production-code review. Formal review remains bound to the exact
remote head; fixes stay on the same PR through normal commits; Draft PRs do not
authorize merge; and cosmetic amend/rebase/force-push remains disallowed. Full
pytest PASS (183 passed, 11 skipped); Ruff PASS; MyPy PASS; and `git diff
--check` PASS. No source, test, runtime, Data Truth, current-plan, production,
or dependency change occurred.

**Commit / PR:** Scope-fix commit
`55cde353a04a4e4b2eab6db391f9739a3fa3708e`; audit commit pending. Existing
Draft PR #35 remains the remote review surface and is not ready for merge.

**Next:** Push these bounded fixes to PR #35 and obtain ChatGPT direct GitHub
remote authority re-audit of the new exact head. Merge remains unauthorized.

**Safety:** No QuestDB POC, Slice 2, runtime, canonical activation, or
production-data authorization change.

## 2026-09-07 — LIVE15-V2-GLOBAL-ENGINEERING-GITHUB-FIRST-REMOTE-REVIEW-AUTHORITY-001

**Change:** Added global V2 Engineering authority requiring a GitHub-visible
candidate branch and Draft PR before formal ChatGPT independent implementation
or architecture review.

**Reason:** ChatGPT does not directly access the user's local worktree. Local
implementation, validation, and Codex self-review remain valid evidence, but
they are not a ChatGPT independent audit of the actual candidate source.

**Validation / result:** The authority preserves the existing V2 lifecycle and
requires formal ChatGPT review to inspect the GitHub-visible actual
source/diff/commits/tests and applicable Hosted CI at an exact head SHA. Draft
PRs are review surfaces only, not merge authority; bounded review fixes stay on
the same PR through normal commits; CI and local self-review remain separate
evidence; and cosmetic amend/rebase/force-push is not allowed. Full pytest
PASS (183 passed, 11 skipped); Ruff PASS; MyPy PASS; and `git diff --check`
PASS. No Data Truth, runtime, production-data, source, test, dependency, or
current-plan change occurred.

**Commit / PR:** Engineering authority commit
`c68097a4d362184c131667d3b061e72be3a29780`; audit commit and Draft PR pending
publication and remote authority audit.

**Next:** Publish this two-commit global Engineering authority candidate as a
Draft PR for ChatGPT direct remote authority audit. Merge remains separately
unauthorized.

**Safety:** No runtime, canonical activation, production-data, Data Truth POC,
or Slice 2 authorization change.

## 2026-09-07 — LIVE15-V2-DATA-TRUTH-SLICE-1-FINAL-STATUS-CLOSURE-001

**Change:** Recorded the completed Data Truth Slice 1 semantic-library
lifecycle as FINAL CLOSED and advanced Current NEXT to Data Truth QuestDB
reconciliation POC authorization preparation.

**Reason:** Slice 1's technical lifecycle is complete: PR #33 merged normally,
the merge-SHA hosted checks passed, and the final local seal passed. This
status-only closure preserves the separate authorization gate required before
any QuestDB reconciliation POC or Slice 2 work.

**Validation / result:** PR #33 merged as
`f80c786307fe5e2c2092a0f2955f62ca03c9c7bb` with exact parents
`c13ae9b7fc09db1e8d0bdc51c3218b3f3b647c3a` and
`84f19d8379542b4e6441cecf505f6feb02c7f476`. Reviewed code head
`78660844e690eeb73cacd8a756a4e65419c1a798` passed ChatGPT direct remote code
audit. Merge-SHA Windows, Ubuntu, and CI Gate passed. Final local seal passed:
local main equaled origin/main, worktree was clean, local and remote Slice 1
feature branches were cleaned, targeted Data Truth tests passed (69), full
pytest passed (183 passed, 11 skipped), Ruff and MyPy passed, and `git diff
--check` passed. Slice 1 is FINAL CLOSED; overall Data Truth and persistent
TruthDecision authority remain NOT IMPLEMENTED; QuestDB fit remains PARTIAL_FIT;
the POC and Slice 2 remain NOT AUTHORIZED. No runtime, production-data, or
dependency change occurred.

**Commit / PR:** Status commit
`d9bacf9374c8a1b5feae1b8167343a97678f904c`; final-status closure PR pending
publication and remote audit.

**Next:** Publish this status-only closure as a Draft PR for ChatGPT remote
audit. The QuestDB reconciliation POC remains unauthorized; Slice 2 remains
unauthorized.

**Safety:** No source, test, QuestDB runtime, canonical `hot_capture_facts`,
canonical DEDUP, canonical SF, or production-data change.

## 2026-09-07 — LIVE15-V2-DATA-TRUTH-SLICE-1-PR33-PREMERGE-STATUS-CLOSURE-001

**Change:** Advanced Data Truth Slice 1 current authority from DRAFT PR
CANDIDATE pending direct remote review/fix to REVIEWED PR CANDIDATE for PR #33.
Recorded the ChatGPT direct remote code-audit PASS for reviewed code head
`78660844e690eeb73cacd8a756a4e65419c1a798` and set Current NEXT to guarded
merge preparation.

**Reason:** The final direct remote audit confirmed that the prior bounded
authority defects were fixed, no code blockers remain, and the reviewed Slice 1
candidate is ready for guarded merge preparation. This status closure does not
merge the PR or close Slice 1.

**Validation / result:** ChatGPT final direct remote code audit = PASS;
Standards, Spec, Architecture, Test Authority, Immutability, and Failure /
Reconciliation reviews = PASS; known code defects = NONE; architecture drift =
NONE. Targeted Data Truth tests PASS (69 passed); full pytest PASS (183 passed,
11 skipped); Ruff PASS; MyPy PASS; and `git diff --check` PASS. Slice 1 remains
NOT FINAL CLOSED; overall Data Truth and persistent TruthDecision authority
remain NOT IMPLEMENTED; the QuestDB POC and Slice 2 remain NOT AUTHORIZED. No
production, runtime, or dependency change occurred.

**Commit / PR:** Reviewed PR #33; reviewed code head
`78660844e690eeb73cacd8a756a4e65419c1a798`; pre-merge status commit
`9e043bc0bdfa1f3a3f3ccab4562e00971ee8c1b7`; PR #33 remains OPEN and DRAFT
pending hosted CI for this status-only update.

**Next:** Push the status-only closure to PR #33, verify hosted CI on the new
head, mark the PR ready for review, then obtain ChatGPT pre-merge remote
verification. Guarded merge remains separately unauthorized.

**Safety:** No source, test, QuestDB runtime, canonical `hot_capture_facts`,
canonical DEDUP, canonical SF, or production-data change.

## 2026-09-07 — LIVE15-V2-DATA-TRUTH-SLICE-1-PR33-SAME-SUBJECT-ANCHOR-CONSISTENCY-FIX-001

**Change:** Added a parent-composition consistency guard that rejects an
accepted `EventAnchor` when its accepted fact has the same `capture_id` as the
current subject after subject lookup reported no decision. Added equal- and
changed-projection regressions for this contradictory history state.

**Reason:** ChatGPT's direct remote re-audit of Draft PR #33 found that a
missing subject decision and an accepted event anchor could claim the same
immutable CaptureFact subject, allowing an impossible DUPLICATE or CONFLICT
classification.

**Validation / result:** Both same-subject variants raise
`TruthDecisionInvariantError` before append, and each performs exactly one
event-anchor lookup. Targeted Data Truth tests PASS (69 passed); full pytest
PASS (183 passed, 11 skipped); Ruff PASS; MyPy PASS; and `git diff --check`
PASS. PR #33 remains OPEN and DRAFT. This records the bounded fix only and does
not claim final ChatGPT remote-audit PASS. Slice 1 remains NOT FINAL CLOSED;
overall Data Truth implementation and persistent TruthDecision authority remain
NOT IMPLEMENTED; the QuestDB POC and Slice 2 remain NOT AUTHORIZED. No runtime,
canonical, dependency, or production-data change occurred.

**Commit / PR:** Same-subject anchor fix commit
`2568216f0adcba147052ef3ace451c35dfd88511`; PR #33 DRAFT.

**Next:** ChatGPT final direct remote audit of the updated Draft PR #33 before
any review-ready or merge decision. The QuestDB POC, Slice 2, persistent
TruthDecision authority, and canonical runtime activation remain unauthorized.

**Safety:** No QuestDB runtime, canonical `hot_capture_facts`, canonical DEDUP,
canonical SF, or production-data change.

## 2026-09-07 — LIVE15-V2-DATA-TRUTH-SLICE-1-PR33-CHATGPT-REMOTE-AUDIT-FIX-001

**Change:** Updated Draft PR #33's Slice 1 semantic-library candidate with two
bounded authority checks: `TruthDecision` now snapshots contributing capture IDs
once before validating and storing them, and Event Facts rejects an accepted
`EventAnchor` whose decision policy version differs from `data-truth/v1`.
Updated active Data Truth authority from LOCAL CANDIDATE to DRAFT PR CANDIDATE
for PR #33, pending direct remote implementation review/fix.

**Reason:** ChatGPT's direct remote code audit of Draft PR #33 returned
FAIL_WITH_BOUNDED_FIX: caller-owned contributing-ID input could change between
validation and storage; an accepted anchor's policy version was not verified;
and active Project Brain status was stale after publication.

**Validation / result:** Added an adversarial stateful-list regression proving
the stored authority is the exact once-snapshotted, validated string tuple, and
a wrong-policy accepted-anchor regression proving `TruthDecisionInvariantError`
before any append. Targeted Data Truth tests PASS (67 passed); full pytest PASS
(181 passed, 11 skipped); Ruff PASS; MyPy PASS; and `git diff --check` PASS.
PR #33 remains OPEN and DRAFT. This records the bounded fix only; it does not
claim a ChatGPT remote re-audit PASS. Slice 1 remains NOT FINAL CLOSED; overall
Data Truth implementation and persistent TruthDecision authority remain NOT
IMPLEMENTED; the QuestDB POC and Slice 2 remain NOT AUTHORIZED. No runtime,
canonical, dependency, or production-data change occurred.

**Commit / PR:** Remote-audit fix commit
`8952796d193a5bd7814c7882365a4e13711520ad`; PR #33 DRAFT.

**Next:** ChatGPT direct remote re-audit of the updated Draft PR #33 before any
review-ready or merge decision. The QuestDB POC, Slice 2, persistent
TruthDecision authority, and canonical runtime activation remain unauthorized.

**Safety:** No QuestDB runtime, canonical `hot_capture_facts`, canonical DEDUP,
canonical SF, or production-data change.

## 2026-09-07 — LIVE15-V2-DATA-TRUTH-SLICE-1-SEMANTIC-LIBRARY-INDEPENDENT-RE-REVIEW-FIX-001

**Change:** Tightened the local Slice 1 `TruthDecision` reference-input
contract to accept only `list[str]` and `tuple[str, ...]`, then store an owned
tuple. Hardened the AST import test helper to resolve normal relative
`ImportFrom` statements, including `module=None`, against the inspected module
package.

**Reason:** The independent re-review found two remaining bounded defects:
arbitrary iterable/string contributing-ID normalization could split a scalar
string into character references, and relative imports such as `from . import
observation_facts` could bypass architecture-boundary enforcement.

**Validation / result:** The pre-fix independent re-review recorded Standards
PASS; Spec, Architecture, Test Authority, and Immutability FAIL; and Failure /
Reconciliation PASS. This fix adds direct rejection coverage for scalar,
unordered, mapping, generator, and non-string-element reference input, plus
normal, aliased, multi-name, absolute, and relative AST import-form coverage.
Focused Data Truth tests PASS (65 passed); full pytest PASS (179 passed, 11
skipped); Ruff PASS; MyPy PASS; and `git diff --check` PASS. Slice 1 remains a
LOCAL CANDIDATE and is not FINAL CLOSED; Data Truth and persistent
`TruthDecision` authority remain NOT IMPLEMENTED; QuestDB fit remains
PARTIAL_FIT; the POC and Slice 2 remain NOT AUTHORIZED. No runtime,
production-data, or dependency change occurred.

**Commit / PR:** Baseline `c13ae9b7fc09db1e8d0bdc51c3218b3f3b647c3a`;
previous candidate head `a06b91fdc58fb3c9e078c84cbbde1642518edb44`; second
review-fix commit `2493c5265125593c10047b5c71e4bf0f686ba833`; PR NOT OPENED.

**Next:** Independent re-review of the local Slice 1 candidate after this
second bounded review fix. Publication, the QuestDB POC, Slice 2, persistent
TruthDecision authority, and canonical runtime activation remain unauthorized.

**Safety:** No QuestDB runtime, canonical `hot_capture_facts`, canonical DEDUP,
canonical SF, or production-data change.

## 2026-09-07 — LIVE15-V2-DATA-TRUTH-SLICE-1-SEMANTIC-LIBRARY-INDEPENDENT-REVIEW-FIX-001

**Change:** Hardened the local Data Truth Slice 1 candidate's authority
invariants and its focused architecture tests. `TruthDecision` now takes tuple
ownership of contributing capture references; corrupted event anchors now fail
closed when their decision subject or contributing references disagree with
their accepted fact; and import-boundary tests inspect Python AST imports
rather than source-text substrings.

**Reason:** The original independent review accepted the bounded Slice 1
design but found a shallow immutability leak, two missing EventAnchor
consistency checks, incomplete corrupt-anchor coverage, and brittle
architecture-import checks.

**Validation / result:** The original review recorded Standards PASS; Spec,
Architecture, Test Authority, and Immutability FAIL; and Failure /
Reconciliation PASS. This local review fix adds explicit caller-mutation,
seven corrupt-anchor, invalid-payload non-identity, and AST-boundary
regressions. Focused Data Truth tests PASS (53 passed); full pytest PASS (167
passed, 11 skipped); Ruff PASS; MyPy PASS; and `git diff --check` PASS. Slice
1 remains a local candidate pending independent re-review; persistent
TruthDecision authority remains NOT implemented; QuestDB fit remains
PARTIAL_FIT; the QuestDB POC and Slice 2 remain NOT AUTHORIZED. No runtime,
canonical, dependency, or production-data change occurred.

**Commit / PR:** Original Slice 1 candidate commit
`bc1468becb62ea118f3432c6d8ca6f7393bda464`; candidate audit commit
`ae327883ee46633731fcf454e546405415440234`; review-fix commit
`ad4feff051cc61057a0d65f899921e4545554201`; PR NOT OPENED.

**Next:** Independent re-review of the local Slice 1 candidate after this
bounded review fix. The QuestDB POC, Slice 2, persistent TruthDecision
authority, and canonical runtime activation remain unauthorized.

**Safety:** No QuestDB runtime, canonical `hot_capture_facts`, canonical DEDUP,
canonical SF, or production-data change.

## 2026-09-07 — LIVE15-V2-DATA-TRUTH-SLICE-1-SEMANTIC-LIBRARY-IMPLEMENTATION-001

**Change:** Implemented the separately authorized local Data Truth Slice 1
semantic-library candidate: immutable provider-neutral models, the narrow
three-method history seam, parent composition, Trade Event Facts, one stateless
Observation Facts policy, and focused behavior and architecture tests.

**Reason:** The sealed Data Truth contract and implementation plan authorize a
deterministic semantic library as Slice 1 before any persistent TruthDecision
authority. The candidate preserves the two-child semantic tree and defers the
mandatory QuestDB reconciliation POC and Slice 2.

**Validation / result:** Baseline validation PASS (Ruff, pytest 114 passed / 11
skipped, MyPy, and `git diff --check`). Candidate validation PASS: targeted
Data Truth tests 41 passed; full pytest 155 passed / 11 skipped; Ruff PASS;
MyPy PASS; and `git diff --check` PASS. Data Truth contract and
implementation-plan authority remain FINAL CLOSED; overall implementation
remains NOT IMPLEMENTED. Slice 1 is a local candidate pending independent
review; persistent TruthDecision authority is NOT implemented; QuestDB fit
remains PARTIAL_FIT; the QuestDB POC and Slice 2 remain NOT AUTHORIZED. No
runtime, canonical, dependency, or production-data change occurred.

**Commit / PR:** Baseline `c13ae9b7fc09db1e8d0bdc51c3218b3f3b647c3a`;
Slice 1 candidate commit `bc1468becb62ea118f3432c6d8ca6f7393bda464`; PR NOT
OPENED.

**Next:** Independent implementation review of the Slice 1 semantic-library
candidate. The QuestDB POC, Slice 2, persistent TruthDecision authority, and
canonical runtime activation remain unauthorized.

**Safety:** No QuestDB runtime, canonical `hot_capture_facts`, canonical DEDUP,
canonical SF, or production-data change.

## 2026-09-07 — LIVE15-V2-DATA-TRUTH-IMPLEMENTATION-PLAN-AUTHORITY-PREMERGE-STATUS-CLOSURE-REVIEW-FIX-001

**Change:** Corrected the remaining stale Data Truth parent implementation-gate
sentence after the independent pre-merge status-closure review.

**Reason:** The parent correctly recorded FINAL CLOSED implementation-plan
authority, but its gate still said implementation planning was the next
responsibility. Current NEXT is instead Slice 1 semantic-library candidate
preparation, which remains separately unauthorized.

**Validation / result:** The independent pre-merge status-closure review found
this one stale gate sentence; all other status-closure, architecture, global
engineering, and CI checks passed. Data Truth implementation-plan authority
remains FINAL CLOSED; implementation remains NOT IMPLEMENTED. Slice 1, the
QuestDB reconciliation POC, and Slice 2 remain unauthorized; QuestDB fit
remains PARTIAL_FIT. No source, test, dependency, runtime, or production
change. Ruff PASS; pytest PASS (114 passed, 11 skipped); MyPy PASS; and
`git diff --check` PASS.

**Commit / PR:** Implementation-gate fix commit
`4e5f115fb34d2c0c0a3c885cc706435c0751e683`; PR #32 OPEN.

**Next:** Final independent pre-merge re-audit. Slice 1, the QuestDB
reconciliation POC, Slice 2, and Data Truth implementation remain unauthorized.

**Safety:** Documentation authority only: no QuestDB runtime, canonical
`hot_capture_facts`, canonical DEDUP, canonical SF, or production-data change.

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
