# Market Ingress

Market Ingress has four approved children:

1. Kalshi Gateway — DONE.
2. Market Stream — NOT STARTED.
3. Reference Stream — NOT STARTED.
4. Ingress Boundary — framework and concrete asset mapping DONE.

Ingress Boundary owns SDK-to-LIVE15 meaning, asset mapping, market/window
mapping, and the output interface. Its sole map authority is
`Live15MarketScopeConfig`: BTC/KXBTC15M, ETH/KXETH15M, GOLD/KXGOLD15M,
SILVER/KXSILVER15M, XRP/KXXRP15M, SOL/KXSOL15M, HYPE/KXHYPE15M,
DOGE/KXDOGE15M, and BNB/KXBNB15M. WTI is absent. On 2026-09-04 each series
was read-only verified through official Kalshi Get Series via `kalshi-sdk`
with frequency `fifteen_min`; current market access remains provider-owned.