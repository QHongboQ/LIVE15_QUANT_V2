# Kalshi Gateway

Kalshi Gateway owns the first V2 Market Ingress capability tree:

```text
Market Scope Port -> Window Mechanics -> Candidate Predictor
                                      -> Kalshi Gateway -> kalshi-sdk
                                      -> Official Discovery -> Official Verification
Candidate and verified official identity -> Shadow Validation
```

The parent package composes and exports the thin gateway and identity leaves.
The leaves expose a future-swappable `MarketScopePort`, immutable UTC
quarter-hour windows, a New York calendar candidate hint, official discovery,
fail-closed verification, and pure shadow comparison. The concrete LIVE15
nine-asset Market Scope mapping is intentionally deferred; no asset/series map
belongs to this task.

## Upstream and reference boundaries

- `kalshi-sdk==13.0.0` owns REST transport, authentication, pagination,
  WebSocket transport, subscriptions, SID routing, reconnect, resubscribe, and
  typed Kalshi models. LIVE15 calls its public `KalshiClient.markets.get`,
  `list_all`, and future `AsyncKalshiClient.ws` seams; it does not vendor or
  recreate any transport behavior.
- `juanjo1997/kalshi-poly-arb` at
  `a1d27c6f6e620edbfacc2fcef7dc33da16529f86` was read only as behavioral
  evidence for UTC quarter-hour rotation, New York ticker calendar mechanics,
  and candidate-versus-official shadow comparison. The pinned repository has
  no explicit license, so no source was copied, vendored, or translated.
- The bounded V1 reference is the proven Kalshi official SDK transport boundary
  and fail-closed market-fact semantics. V2 does not inherit Robinhood mapping
  assumptions, direct non-Kalshi providers, Recorder runtime, or V1 code.

## Verification boundary

Candidates are optimization hints, never authorization. Official series
lookup is authoritative. Verification requires one approved-series market with
exact UTC open/close boundaries, coherent event/ticker identity, and a
published valid target from that same official market. It rejects zero or
ambiguous matches, fuzzy titles, first-open selection, first-market strike,
sibling target borrowing, and TBD/unpublished targets.

WebSocket runtime composition, persistent storage, canonical data truth,
datasets, background shadow scheduling, alerting, models, and trading are out
of scope.