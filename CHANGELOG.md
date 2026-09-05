# Changelog

This is the permanent, human-readable activity log for LIVE15_QUANT_V2. Every meaningful V2 task must update this file in the same commit or PR.

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
