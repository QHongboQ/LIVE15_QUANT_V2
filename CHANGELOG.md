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

## 2026-09-04 — LIVE15-V2-MODULAR-CI-ROUTER-001

**Summary:** Added the modular CI Router, declarative foundation scope, single-scope runner, thin GitHub Actions workflow, and CI Brain owner.

**Why:** Keep CI aligned with the V2 responsibility tree so future modules can register bounded checks without turning Foundation CI into a whole-repository runner.

**Validation / evidence:** Authority-routing closeout adds explicit `uv.toml` version-file enforcement, control-plane ownership for `.python-version` and `uv.toml`, zero-registry fail-closed routing, runner-neutral forwarding, immutable action pins, and focused authority-routing regressions; 28 tests, foundation-owned setup, Ruff, mypy, and diff checks passed.

**Commit or PR:** PR #2; implementation commits `0840b59` and `6c1607a`, followed by the correction commit, are recorded in Git history.

**Next step:** Independent review; continue foundation discussion before the first business module.