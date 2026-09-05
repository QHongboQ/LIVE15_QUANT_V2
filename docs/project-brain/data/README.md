# Data System

Data System has two implemented children: Market Ingress and Storage.

Storage currently routes only its implemented [Hot Store](storage/README.md) leaf. Data Truth, Replay &
As-Of, and Canonical Dataset remain unimplemented. Market Ingress does not own those deferred
responsibilities.

Research & Model System, Decision & Trading System, Operations & Interface
System, and Engineering Foundation are separate top-level sibling systems, not
Data System children.
