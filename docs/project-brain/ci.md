# CI Architecture

Current V2 CI is a static GitHub Actions Foundation workflow derived from the
pinned upstream baseline below. It runs the complete current Foundation check
set on Ubuntu and Windows; there is no custom CI Router, scope registry, graph
routing, or path filtering.

## Upstream provenance

- Upstream repository: `OvertureMaps/overturemaps-py`
- Source file: `.github/workflows/test-run.yml`
- Pinned source commit: `9410974885ab5e9de107b15c0ba000a248c36a36`
- License: MIT; complete third-party notice: [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md)
- Adopted: 2026-09-04
- Local adaptations: replaced the upstream multi-Python matrix with the current
  Ubuntu/Windows matrix; rely on repository `.python-version`; use locked V2
  dependency sync; run pytest, Ruff, and mypy; omit OvertureMaps CLI, geospatial
  data, publishing, packaging, and release behavior; rename the upstream rollup
  status to `CI Gate`.

The workflow preserves the upstream structure for triggers, least-privilege
permissions, concurrency cancellation, SHA-pinned checkout/setup actions,
static matrix checks, and rollup status. Future generic CI changes first inspect
this pinned baseline and current mature upstream options before custom work.

The CI Control Plane owns the workflow. Leaf-level business modules may define
module-specific validation only when they exist and have an approved upstream
or domain-specific rationale.