# Kalshi Gateway

Kalshi Gateway is the implemented Market Ingress child. Its composition point
resolves an asset through the future-owned Market Scope Port, Window Mechanics,
Candidate Predictor, official discovery, verification, and shadow comparison.
It exposes only verified official identity facts upward.

The concrete LIVE15 nine-asset mapping is deliberately deferred. The next task
may provide one `MarketScopePort` implementation; no Gateway, window,
candidate, discovery, verification, or shadow leaf needs its own mapping.

## Official API and SDK boundary

The current official [Get Market](https://docs.kalshi.com/api-reference/market/get-market)
and [Get Markets](https://docs.kalshi.com/api-reference/market/get-markets)
documentation is the authority. The installed `kalshi-sdk==13.0.0` provides the
public `KalshiClient.markets.get` and `list_all` integration surface. Discovery
passes only documented `series_ticker`, `min_close_ts`, and `max_close_ts`, with
an empty status filter; the official compatibility table permits close-time
filters with empty status or `closed`, not active statuses. The bounded envelope
is only a retrieval heuristic: exact UTC open/close verification remains truth.
The SDK continues to own pagination, transport, authentication, WebSocket
transport, subscriptions, reconnect, and resubscribe.

`floor_strike` and `cap_strike` stay Decimal-compatible structured facts from
the same official Market object, alongside `strike_type` and `yes_sub_title`.
`functional_strike` is retained only as distinct official metadata; it never
becomes generic target truth. No title parsing, sibling borrowing, first-open
selection, first-market strike, TBD acceptance, or ambiguous selection exists.

Candidate ticker formatting is not an official Kalshi API contract. The
candidate is therefore a non-authoritative heuristic only for the observed
`KX*15M` shape, derived from the window close in America/New_York and including
the observed minute suffix. Other series omit a candidate. A candidate miss
always continues to bounded official series discovery and verification.

## Behavioral reference

`juanjo1997/kalshi-poly-arb` at
`a1d27c6f6e620edbfacc2fcef7dc33da16529f86` was consulted only for the
close-time ticker heuristic and shadow concept where official documentation is
silent. Its pinned repository has no explicit license; no source was copied,
vendored, or translated.

Storage, Data Truth, runtime scheduling, alerts, datasets, models, trading,
Nomad, Web, and Production actions are deferred and unimplemented here.