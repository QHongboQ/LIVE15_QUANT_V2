# Changelog

This is the permanent, human-readable activity log for LIVE15_QUANT_V2. Every meaningful V2 task must update this file in the same commit or PR.

## 2026-09-03 — LIVE15-V2-REPOSITORY-BOOTSTRAP-001

**Summary:** Created the clean V2 repository and connected the local workspace to public GitHub on the `main` branch.

**Why:** Establish version history and rollback before architecture or implementation work begins.

**Validation / evidence:** Initial root files only; no V1 code copied, no implementation performed, and no Production changes.

**Commit or PR:** Initial commit to be recorded by Git history.

**Next step:** Blueprint discussion and architecture/design work.

## Entry convention

Each meaningful V2 task entry includes: Date, Task ID, Summary, Why, Validation / evidence, Commit or PR when available, and Next step.

## 2026-09-04 — LIVE15-V2-FOUNDATION-ENVIRONMENT-001

**Summary:** Established the reproducible Python 3.12/uv foundation in the V2 repository with a project-local environment and minimal package, test, and Project Brain skeleton.

**Why:** Provide a clean, isolated development baseline before business functionality or architecture work begins.

**Validation / evidence:** `uv` environment and lockfile created; `kalshi-sdk==13.0.0`, pytest, ruff, and mypy installed; complete current `mattpocock/skills` set installed under V2; foundation checks passed; no business implementation or Production action.

**Commit or PR:** To be recorded by Git history.

**Next step:** Foundation review, then approved blueprint discussion.

## 2026-09-04 — LIVE15-V2-BRAIN-BOOTSTRAP-FINALIZATION-001

**Summary:** Finalized the minimal V2 Project Brain routing, approved current-plan, and reference-only V1 proven-paths document.

**Why:** Establish V2-owned governance and planning without importing V1 current state, roadmap, bugs, or implementation assumptions.

**Validation / evidence:** AGENTS routing, approved Brain routes, V2-only plan, and reference-only policy checked; foundation tests/lint/type checks remain green; no code, dependencies, skills, runtime, Production, or V1 changes.

**Commit or PR:** PR #1; commit recorded by Git history.

**Next step:** Foundation review before any business module implementation.

## 2026-09-04 — LIVE15-V2-V1-PROVEN-PATHS-AUDIT-001

**Summary:** Independently audited the initial V1 proven-path reference against V1 merged PRs, resulting `main` authorities, and acceptance evidence; expanded it from four examples into a bounded inventory of ten proven capability references plus partial/research-only and explicitly-not-proven sections.

**Why:** Prevent V2 from treating a merged V1 PR, POC, historical implementation, or later-broken host state as proof that an entire subsystem was stable.

**Validation / evidence:** Verified representative merged evidence for Kalshi SDK transport, Production GAP recovery, Research Data Authority, Project Brain/context recovery, Nomad lifecycle, immutable release/runtime identity, React Admin/MUI Web, Parquet+ZSTD packaging, and COLD-to-research isolation; preserved explicit boundaries for Pyth, ControlCenter host state, Production archive activation, H2, Vector, models, WTI, and holdout history.

**Commit or PR:** PR #1; audit correction begins at commit `77592d078289fe68ecaf9b476cbf412bddd0d181`.

**Next step:** Re-run final PR #1 foundation review before merge.
