# CI Architecture

V2 CI is a modular, dependency-aware control plane. `ci/router.py` discovers
registered leaf descriptors and selects impacted scopes; each descriptor owns
its scope-specific checks, while `ci/run_scope.py` executes one selected scope.

GitHub Actions is a thin, generic orchestrator that supplies the changed-file range,
installs the pinned Python runtime, runs the Router without project synchronization, expands its matrix, and
publishes one stable `CI Gate` above the changing internal scope jobs. CI consumes authoritative project and module configuration rather than duplicating derived concrete values. Each selected leaf descriptor owns its own environment setup and checks; SCOPE mode includes only the requested scope and its upstream dependencies, while AUTO preserves downstream impact propagation. A registry with zero descriptors is invalid and fails closed.

The only registered business-independent scope is `foundation`. New CI scopes
are added only when their corresponding V2 module exists and its descriptor and
checks are approved.
