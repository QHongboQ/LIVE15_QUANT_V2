# V1 Proven Paths (Reference Only)

V1 is a reference library of proven implementation experience. It is not V2 current authority, not a migration plan, and not permission to copy V1 code.

`PROVEN` below always applies to the stated bounded capability, never to the whole V1 system. V1 ended with known operational blockers, so a merged PR alone is not enough to claim that an entire subsystem was stable. When V2 reaches a capability, inspect the merged PRs, resulting V1 `main`, and validation/acceptance evidence, then redesign/reimplement the useful path inside V2 boundaries.

Prefer `merged PR + resulting main + acceptance evidence`. Do not use abandoned/unmerged branches as proof of success.

## Main proven references

### 1. Kalshi official SDK transport boundary

**Status:** PROVEN IMPLEMENTATION REFERENCE.

**Evidence:** [PR #7](https://github.com/QHongboQ/LIVE15_QUANT/pull/7), [PR #40](https://github.com/QHongboQ/LIVE15_QUANT/pull/40).

**What proved useful:** keep official Kalshi transport/auth/API behavior behind a narrow LIVE15 adapter; use typed SDK decoding; replace the SDK session cleanly at rollover rather than adding a parallel receive loop; malformed/insufficient snapshots fail closed.

**Boundary:** PR #7 is historical/read-only provider evidence, not proof of the realtime Recorder by itself. Do not infer direct Pyth/Coinbase/Binance/Hyperliquid ownership from this path.

### 2. Kalshi WebSocket resync, session isolation, and DataGap recovery

**Status:** PROVEN PRODUCTION REFERENCE.

**Evidence:** [PR #40](https://github.com/QHongboQ/LIVE15_QUANT/pull/40), [PR #117](https://github.com/QHongboQ/LIVE15_QUANT/pull/117) preserved the failed first acceptance, [PR #118](https://github.com/QHongboQ/LIVE15_QUANT/pull/118) fixed the old-session authority race, and [PR #120](https://github.com/QHongboQ/LIVE15_QUANT/pull/120) recorded the second Production acceptance PASS.

**What proved useful:** old-session events may remain durable history but must never regain active authority after reconnect; replacement-session fresh snapshots restore book authority; gap closure must match recovered facts exactly; sequence/session boundaries remain explicit and fail closed.

**Boundary:** reuse the recovery semantics, not the whole V1 Recorder implementation.

### 3. Recorder truth, gap, quarantine, as-of, and settlement contracts

**Status:** PROVEN CONTRACT REFERENCE.

**Evidence:** merged V1 Recorder/data-truth work including [PR #34](https://github.com/QHongboQ/LIVE15_QUANT/pull/34) and [PR #125](https://github.com/QHongboQ/LIVE15_QUANT/pull/125), plus the final V1 Recorder truth authority on `main`.

**What proved useful:** immutable raw facts; strict as-of/freshness; semantic gap identity separated from mutable provenance; quarantine rather than fabricated replay baselines; official finalized Kalshi settlement remains terminal truth; true semantic conflicts fail closed.

**Boundary:** this does **not** mean the whole V1 Recorder runtime was stable. The final V1 system still had a Pyth criticality failure boundary. V2 may reuse truth semantics, not the old Recorder architecture wholesale.

### 4. Research Data Authority

**Status:** PROVEN IMPLEMENTATION REFERENCE.

**Evidence:** [PR #29](https://github.com/QHongboQ/LIVE15_QUANT/pull/29).

**What proved useful:** typed source registry, deterministic research-universe snapshots, explicit freshness/capability contracts, metadata-only coverage evidence, and prevention of research/model entrypoints silently selecting uncontrolled current data.

**Boundary:** this is data-governance/reference architecture, not proof of model edge.

### 5. Project Brain, skills, and context recovery

**Status:** PROVEN ENGINEERING-WORKFLOW REFERENCE.

**Evidence:** [PR #32](https://github.com/QHongboQ/LIVE15_QUANT/pull/32), later authority consolidation in [PR #122](https://github.com/QHongboQ/LIVE15_QUANT/pull/122).

**What proved useful:** durable Git-backed project context, compact root routing, recursive responsibility ownership, independent review, and fresh-session recovery from repository authority instead of chat memory.

**Boundary:** V2 keeps the mechanism but starts with its own clean Brain/current state/history. V1 current-state documents are not copied.

### 6. Nomad + Windows SCM lifecycle ownership

**Status:** PROVEN LIFECYCLE REFERENCE.

**Evidence:** Recorder/ControlCenter cutover work and final lifecycle consolidation, especially [PR #110](https://github.com/QHongboQ/LIVE15_QUANT/pull/110), [PR #123](https://github.com/QHongboQ/LIVE15_QUANT/pull/123), [PR #127](https://github.com/QHongboQ/LIVE15_QUANT/pull/127), [PR #129](https://github.com/QHongboQ/LIVE15_QUANT/pull/129), and [PR #130](https://github.com/QHongboQ/LIVE15_QUANT/pull/130).

**What proved useful:** let Nomad/Windows SCM own generic process start/stop/restart/update/revert; retain business truth outside the scheduler; prevent dual lifecycle ownership; prefer native Nomad job history/revert over a custom rollback controller.

**Boundary:** do not copy RuntimeSupervisor or the old multi-wrapper lifecycle. The later V1 audit also found current ControlCenter host ownership unreconciled, so the proven reference is the lifecycle design/cutover path, not a claim that every V1 host process remained healthy forever.

### 7. Immutable release and runtime identity

**Status:** PROVEN IMPLEMENTATION REFERENCE.

**Evidence:** [PR #45](https://github.com/QHongboQ/LIVE15_QUANT/pull/45), subsequent release hardening, and [PR #167](https://github.com/QHongboQ/LIVE15_QUANT/pull/167).

**What proved useful:** SHA-pinned immutable application releases, manifest-verified identity, explicit separation of application release/runtime/mutable data/secrets, exact dependency closure, final-path virtual environments, and native Nomad deployment/revert instead of movable-venv promotion.

**Boundary:** implementation was merged and validated, but later host rollout remained separately gated. Treat this as release/runtime design evidence, not proof of a final V1 host state.

### 8. React Admin + Material UI Web shell

**Status:** PROVEN WEB IMPLEMENTATION REFERENCE.

**Evidence:** [PRs #131-#139](https://github.com/QHongboQ/LIVE15_QUANT/pulls?q=is%3Apr+is%3Aclosed+131+132+133+134+135+136+137+138+139), with production-verified Web-owner closeout in [PR #142](https://github.com/QHongboQ/LIVE15_QUANT/pull/142).

**What proved useful:** React Admin + Material UI + Vite packaged as the sole Web shell; typed/read-only FastAPI boundaries; immutable bundle delivery; local HTTP/WebSocket browser boundary; no browser-direct third-party market-data connections; bounded realtime/history projections.

**Boundary:** the Web implementation was proven, but the final V1 full-system audit later found ControlCenter host ownership/desktop launch unreconciled. Do not treat that final host-launch state as proven.

### 9. Parquet + ZSTD package/archive format path

**Status:** PROVEN IMPLEMENTATION REFERENCE; PRODUCTION ACTIVATION NOT PROVEN.

**Evidence:** storage bakeoff [PR #157](https://github.com/QHongboQ/LIVE15_QUANT/pull/157), verified retention implementation [PR #158](https://github.com/QHongboQ/LIVE15_QUANT/pull/158), named multi-root layout [PR #160](https://github.com/QHongboQ/LIVE15_QUANT/pull/160), and later archive-authority reconciliation.

**What proved useful:** Arrow RecordBatch as the semantic bridge; Parquet + ZSTD as the selected retention format; deterministic replay verification; manifest state; bounded fail-closed purge authorization; named storage roots with one active writer root and explicit historical-root resolution.

**Boundary:** V1 never completed normal Production archive activation/purge acceptance. Arrow IPC was benchmark/prototype evidence, not the selected final cold format. S3/MinIO was not selected. V2 should revalidate the packaging path against a small read-only V1 fixture before adopting it.

### 10. Verified COLD archive -> RDA -> isolated research runner

**Status:** PROVEN OFFLINE ENGINEERING REFERENCE.

**Evidence:** isolated runner [PR #35](https://github.com/QHongboQ/LIVE15_QUANT/pull/35), COLD research adapter [PR #36](https://github.com/QHongboQ/LIVE15_QUANT/pull/36), and end-to-end bounded bridge [PR #38](https://github.com/QHongboQ/LIVE15_QUANT/pull/38).

**What proved useful:** checksum/replay/provenance/as-of validation before research consumption; quarantine exclusion; immutable input identity; isolated outputs; atomic checksummed checkpoints; deterministic checkpoint/resume; a single typed seam from verified stored evidence into research tooling.

**Boundary:** the end-to-end proof was an offline engineering smoke, not formal model training or model-performance validation.

## Partial / research-only references

These may contain useful engineering ideas, but must not be promoted to the main proven list as completed V2 choices:

- **Historical Kalshi acquisition / walk-forward research:** useful read-only acquisition, chronological grouping, purge/embargo, provenance and leakage controls; not proof of predictive edge.
- **DepthFeed H2 path:** snapshot acquisition/materialization and plan/rate-limit guards worked, but `REAL_H2_DATA_READY` was not established and formal H2 model training was not unlocked.
- **Vector telemetry POC:** technical PASS only; Production adoption was NO-GO/deferred.
- **Symbolic factors / model research:** research infrastructure executed, but recorded results included no robust path/symbolic-factor edge; do not describe this as a successful model.

## Explicitly not proven / do not inherit

Do not turn these V1 paths into V2 success claims:

- the whole V1 Recorder runtime as a stable subsystem;
- direct V1 Pyth/Hermes critical-path architecture;
- RuntimeSupervisor or the old multi-wrapper WinSW lifecycle;
- final V1 ControlCenter host/desktop-launch operational state;
- Production Parquet activation/purge acceptance;
- Vector Production adoption;
- S3/MinIO adoption;
- Arrow IPC as the final cold-storage format;
- ST-005 custom throughput lane as a completed stable solution;
- WTI retirement as a completed V1 migration;
- formal model-training success, Champion/Challenger promotion, Router/Hard Risk, or real-money execution success;
- the old frozen-holdout path as a clean template.

## V2 use rule

A V1 reference never authorizes copying code or carrying forward V1 bugs/compatibility layers. At each V2 capability boundary:

1. identify the relevant V1 proven reference;
2. verify its bounded success claim against merged PR/main/acceptance evidence;
3. re-check current upstream projects and APIs;
4. design the smallest V2 interface for the current nine-asset system;
5. implement cleanly in V2;
6. validate independently before merge.

V1 WTI assumptions, old roadmap sequencing, bug workarounds, current-state claims, deployment state, and changelog history remain outside V2 authority.
