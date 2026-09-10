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
├─ Replay & As-Of — ENGINEERING FINAL CLOSED; ACTIVATION NOT AUTHORIZED
└─ [Canonical Dataset](canonical-dataset/README.md) — CONTRACT FINAL CLOSED;
   IMPLEMENTATION PLAN CANDIDATE / PENDING INDEPENDENT REVIEW;
   IMPLEMENTATION NOT AUTHORIZED
```

Market Ingress and Storage are FINAL CLOSED. Storage owns the sealed shared
immutable `CaptureFact` contract and its FINAL CLOSED [Hot Store, Capture
Boundary, and Durable Persistence](storage/README.md) responsibilities.
Data Truth contract and engineering implementation authority are FINAL CLOSED
after Slice 1, the accepted reconciliation POC, and Slice 2 Persistent History
closure. Replay & As-Of contract authority and implementation-plan authority
are FINAL CLOSED; Slices 1–4 and the overall Replay & As-Of engineering
implementation are FINAL CLOSED. It owns
historical evidence replay, recorded-authority replay, and strict bounded
As-Of views; it does not own transport replay, physical replay, ingress
recovery, or Data Truth adjudication. Canonical Dataset contract authority is
FINAL CLOSED; its implementation-plan candidate is pending independent review,
and its implementation remains NOT AUTHORIZED. Canonical Data Truth activation
remains NOT AUTHORIZED / NOT PERFORMED. Data
Truth and Replay & As-Of are Data System responsibilities, not Storage
children; Market Ingress does not own any of those deferred responsibilities.

Research & Model System, Decision & Trading System, Operations & Interface
System, and Engineering Foundation are separate top-level sibling systems, not
Data System children.
