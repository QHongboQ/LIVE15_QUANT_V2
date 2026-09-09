# Data System

Data System owns the canonical `AssetId` contract: `BTC`, `ETH`, `GOLD`,
`SILVER`, `XRP`, `SOL`, `HYPE`, `DOGE`, and `BNB`. Its current children are
Market Ingress, Storage, [Data Truth](data-truth/README.md),
[Replay & As-Of](replay-as-of/README.md), and the future Canonical Dataset:

```text
Data System
├─ Market Ingress — FINAL CLOSED
├─ Storage — FINAL CLOSED
├─ Data Truth — FINAL CLOSED
├─ Replay & As-Of — CONTRACT AUTHORITY FINAL CLOSED
└─ Canonical Dataset — FUTURE / UNIMPLEMENTED
```

Market Ingress and Storage are FINAL CLOSED. Storage owns the sealed shared
immutable `CaptureFact` contract and its FINAL CLOSED [Hot Store, Capture
Boundary, and Durable Persistence](storage/README.md) responsibilities.
Data Truth contract and engineering implementation authority are FINAL CLOSED
after Slice 1, the accepted reconciliation POC, and Slice 2 Persistent History
closure. Replay & As-Of contract authority = FINAL CLOSED and its
implementation = NOT IMPLEMENTED. It owns historical evidence replay,
recorded-authority replay, and strict bounded As-Of views; it does not own
transport replay, physical replay, ingress recovery, or Data Truth
adjudication. Canonical Dataset remains FUTURE / UNIMPLEMENTED; canonical Data
Truth activation remains NOT AUTHORIZED. Data Truth and Replay & As-Of are Data
System responsibilities, not Storage children; Market Ingress does not own any
of those deferred responsibilities.

Research & Model System, Decision & Trading System, Operations & Interface
System, and Engineering Foundation are separate top-level sibling systems, not
Data System children.
