# Market Ingress

Market Ingress has four approved children, and code ownership must match this sibling tree:

1. [Kalshi Gateway](kalshi-gateway.md) — DONE.
2. [Market Stream](market-stream.md) — DONE.
3. Reference Stream — NOT STARTED.
4. [Ingress Boundary](ingress-boundary.md) — DONE.

## Implemented responsibility tree

```text
Market Ingress
├─ Kalshi Gateway
│  ├─ down: kalshi-sdk provider access
│  └─ up: provider capability
├─ Ingress Boundary
│  ├─ down: provider discovery capability
│  └─ up: VerifiedMarketIdentity
├─ Market Stream
│  ├─ down: MarketStreamSocket / SDK typed subscription capability
│  └─ up: SDK typed async iterators
└─ Reference Stream
   └─ NOT STARTED
```

The parent owns this recursive responsibility tree, but current runtime parent
composition is deliberately limited to Kalshi Gateway plus Ingress Boundary for
market identity. Each child has its own public interface; Market Stream is
intentionally public through `live15_quant_v2.data.market_ingress.market_stream`
rather than a parent re-export. A caller combines the published
`VerifiedMarketIdentity` output with an active SDK streaming capability at that
child interface. No sibling owns another sibling.