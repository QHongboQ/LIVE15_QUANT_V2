# LIVE15_QUANT_V2 Agent Routing

The V2 Project Brain under `docs/project-brain/` is the local durable and current project authority. Navigation starts here and follows the recursive responsibility tree.

Each tree node owns only its scope. Child nodes refine parent responsibility. Cross-node dependencies must be explicit. Code follows the same modular-tree and composition philosophy.

Production actions, irreversible data changes, real trading, and critical safety mutations require explicit human authorization. Formal changes use Git history and review. The root `CHANGELOG.md` is the visible project timeline.
