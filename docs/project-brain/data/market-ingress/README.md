# Market Ingress

Market Ingress has four approved children, and code ownership must match this sibling tree:

1. [Kalshi Gateway](kalshi-gateway.md) — DONE.
2. Market Stream — NOT STARTED.
3. Reference Stream — NOT STARTED.
4. [Ingress Boundary](ingress-boundary.md) — DONE.

`Kalshi Gateway` owns only provider access: official SDK REST/WS/auth access and narrow read-only market-query primitives. It does not own LIVE15 market identity, asset scope, window semantics, verification, or downstream output facts.

`Ingress Boundary` owns SDK-to-LIVE15 meaning, asset mapping, market/window semantics, fail-closed identity verification, diagnostic shadow comparison, and the verified output interface. Its sole map authority is `Live15MarketScopeConfig`: BTC/KXBTC15M, ETH/KXETH15M, GOLD/KXGOLD15M, SILVER/KXSILVER15M, XRP/KXXRP15M, SOL/KXSOL15M, HYPE/KXHYPE15M, DOGE/KXDOGE15M, and BNB/KXBNB15M. WTI is absent. On 2026-09-04 each series was read-only verified through official Kalshi Get Series via `kalshi-sdk` with frequency `fifteen_min`.

The allowed dependency direction is one-way: `Ingress Boundary -> Kalshi Gateway`. `Kalshi Gateway` must not import `Ingress Boundary`. Future Market Stream and Reference Stream code must consume the Ingress Boundary public interface instead of importing provider-specific identity paths.
