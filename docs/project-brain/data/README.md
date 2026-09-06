# Data System

Data System owns the canonical `AssetId` contract: `BTC`, `ETH`, `GOLD`,
`SILVER`, `XRP`, `SOL`, `HYPE`, `DOGE`, and `BNB`. It has two implemented
children: Market Ingress and Storage.

Storage owns the shared immutable `CaptureFact` contract and its implemented
[Hot Store](storage/README.md) leaf. Capture Boundary, Data Truth, Replay &
As-Of, and Canonical Dataset remain unimplemented. Market Ingress does not own
those deferred responsibilities.

Research & Model System, Decision & Trading System, Operations & Interface
System, and Engineering Foundation are separate top-level sibling systems, not
Data System children.
