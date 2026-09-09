# Data System

Data System owns the canonical `AssetId` contract: `BTC`, `ETH`, `GOLD`,
`SILVER`, `XRP`, `SOL`, `HYPE`, `DOGE`, and `BNB`. Its current children are
Market Ingress, Storage, and [Data Truth](data-truth/README.md).

Market Ingress and Storage are FINAL CLOSED. Storage owns the sealed shared
immutable `CaptureFact` contract and its FINAL CLOSED [Hot Store, Capture
Boundary, and Durable Persistence](storage/README.md) responsibilities.
Data Truth contract and engineering implementation authority are FINAL CLOSED
after Slice 1, the accepted reconciliation POC, and Slice 2 Persistent History
closure. Replay & As-Of and Canonical Dataset remain UNIMPLEMENTED; canonical
Data Truth activation remains NOT AUTHORIZED. Data Truth is a Data System
responsibility, not a Storage child; Market Ingress does not own any of those
deferred responsibilities.

Research & Model System, Decision & Trading System, Operations & Interface
System, and Engineering Foundation are separate top-level sibling systems, not
Data System children.
