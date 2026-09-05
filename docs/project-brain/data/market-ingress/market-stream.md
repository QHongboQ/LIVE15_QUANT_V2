# Market Stream

## Responsibility

Market Stream is the Market Ingress child that selects already verified LIVE15
markets and delegates typed orderbook, ticker, trade, and lifecycle
subscriptions to the pinned `kalshi-sdk==13.0.0` WebSocket interface.

Its public `MarketStream` interface accepts only `VerifiedMarketIdentity` and
uses the verified official `identity.ticker`. Candidate tickers, raw asset IDs,
and arbitrary ticker strings are not subscription authority; absent or invalid
identity input fails closed before any SDK subscription is started.

## Ownership

Market Stream owns the thin composition of the four typed subscription leaves.
It preserves the SDK async iterators and message classes, including the
lifecycle `MarketLifecycleMessage | EventFeeUpdateMessage` union.

The SDK owns transport, authentication, reconnect/resubscribe, SID routing,
generic sequence mechanics, and message decoding. Market Stream does not own
discovery, identity verification, Reference Stream, Storage, Data Truth, or
any downstream truth/freshness policy.

## Public interface

Import `MarketStream` from:

`live15_quant_v2.data.market_ingress.market_stream`

Construct it with the approved SDK WebSocket capability and call its explicit
async methods: `orderbook(identity)`, `ticker(identity)`, `trades(identity)`,
or `lifecycle(identity)`. Each returns the corresponding SDK typed async
iterator unchanged.

## Dependency rule

Market Stream is a direct Market Ingress sibling. It consumes the public
`VerifiedMarketIdentity` interface and a narrow structural SDK-stream
capability. It does not import private Ingress Boundary leaves or Kalshi
Gateway internals. The Market Ingress parent remains the sibling composition
point.