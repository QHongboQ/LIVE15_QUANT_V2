# LIVE15_QUANT_V2 Agent Routing

Start every task here, then open `docs/project-brain/README.md`. Follow one relevant child pointer at a time until the narrowest responsible node is found. Inspect local files and Git state; do not infer responsibility from chat memory.

Parents route and summarize; children own narrower details. Split broad scopes downward, state real cross-node dependencies explicitly, and identify the responsible node before fixing a bug. Do not broadly scan the Brain or duplicate facts or sibling responsibilities.

Code uses the same modular tree: bounded modules, clear interfaces, and upper-layer composition. Keep implementation details behind interfaces; connect cross-module behavior at composition points. A narrow module change should stay local to that module, its interface, composition point, and relevant tests. Prefer composition over arbitrary inheritance or monkey-patching.

For generic infrastructure, tooling, frameworks, integration plumbing, and other solved engineering components, prefer official or mature upstream implementations; pin the exact source revision, copy/adapt minimally, and preserve provenance and license requirements. Custom infrastructure requires a concrete explanation of why suitable upstream implementations do not fit. This does not override LIVE15-owned domain semantics such as market-data truth, research/data authority, feature/model logic, prediction, trading decisions, or risk policy.

Human authorization is required before Production, irreversible/destructive data changes, real trading, critical safety/risk policy, frozen holdout access, or unauthorized deployment/restart/stop. Formal changes use bounded branches, clear Git history, and no force-push or history erasure. Formal code changes require independent review that reports PASS, FAIL, or WARNING and checks scope, interfaces, regressions, coupling, artifacts, and evidence.

For V2, local repository/workspace and actual local running state are CURRENT; Git/GitHub provide history, backup, review, and rollback. V1 is reference only, not V2 authority. Root `CHANGELOG.md` is the V2 timeline and records date, task ID, change, reason, validation/result, commit/PR, and next step without copying V1 history. Every user-facing task states Model (Luna, Terra, or Sol) and Reasoning (低, 中, 高, 超高, or 极高); choose the least expensive adequate level.
