# V2 Project Brain

This directory is the durable, current project authority for LIVE15_QUANT_V2.

Navigation starts at the repository `AGENTS.md` and follows the recursive responsibility tree. Each node owns only its scope; child nodes refine parent responsibility, and cross-node dependencies must be explicit.

The project follows the same modular-tree and composition philosophy in code. Production actions, irreversible data changes, real trading, and critical safety mutations require explicit human authorization. Formal changes use Git history and review. The root `CHANGELOG.md` is the visible project timeline.

Deeper Brain branches will be added only after their responsibilities are discussed and approved.
