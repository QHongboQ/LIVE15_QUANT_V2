# CI Architecture

V2 CI is a modular, dependency-aware control plane. `ci/router.py` discovers
registered leaf descriptors and selects impacted scopes; each descriptor owns
its scope-specific checks, while `ci/run_scope.py` executes one selected scope.

GitHub Actions is a thin orchestrator that supplies the changed-file range,
installs the approved foundation, runs the Router, expands its matrix, and
publishes one stable `CI Gate` above the changing internal scope jobs.

The only registered business-independent scope is `foundation`. New CI scopes
are added only when their corresponding V2 module exists and its descriptor and
checks are approved.
