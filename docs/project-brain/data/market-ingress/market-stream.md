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
generic sequence mechanics, message decoding, and per-subscription queue
behavior. Market Stream does not own discovery, identity verification,
Reference Stream, Storage, Data Truth, or any downstream truth/freshness policy.

## Public interface

Import `MarketStream` from:

`live15_quant_v2.data.market_ingress.market_stream`

Construct it with the approved SDK WebSocket capability and call its explicit
async methods: `orderbook(identity)`, `ticker(identity)`, `trades(identity)`,
or `lifecycle(identity)`. Each returns the corresponding SDK typed async
iterator unchanged.

## Session ownership

`MarketStream` expects an already-active SDK WebSocket session/capability. The
caller owns connection lifecycle and may compose it conceptually as:

```python
async with ws.connect() as session:
    stream = MarketStream(session)
    # consume a typed stream with an already verified identity
```

Market Stream does not own `connect()`, `close()`, authentication, reconnect,
or session lifecycle.

## Raw orderbook snapshot warning

Market Stream preserves raw SDK typed orderbook messages unchanged. The raw
`subscribe_orderbook_delta()` snapshot payload `yes` / `no` dictionaries may
be mutated in place by later SDK delta processing. Therefore a typed raw
`OrderbookSnapshotMessage` is not an immutable persistence or replay fact.
Market Stream does not copy or freeze these values. The future immutable fact
boundary in Storage / Data Truth must freeze or copy a snapshot before granting
persistence or replay authority.

## SDK queue and backpressure boundary

Market Stream deliberately preserves the pinned SDK queue policy rather than
reimplementing reliability. The SDK uses fail-fast/error behavior for the
stateful `orderbook_delta` stream, while latest-wins channels such as ticker,
trade, and lifecycle may use bounded `DROP_OLDEST` queues.

Therefore these typed iterators are provider-ingress interfaces, not a promise
of lossless persistence completeness. Future Storage / Data Truth work must
establish its own explicit capture, completeness, freshness, and gap contract
before persisted facts can be treated as authoritative. That downstream
contract must not be implemented here by adding custom transport, reconnect,
or sequence machinery.

## Test ownership

The upstream SDK tests subscription helper commands, ticker forwarding,
orderbook initial snapshots, trade receipt, market-lifecycle subscription,
connection/session lifecycle, and reconnect/sequence machinery. LIVE15 tests
only its verified-identity handoff, typed delegation boundary, and module
ownership contract; it does not duplicate SDK transport tests.

## Dependency rule

Market Stream is a direct Market Ingress sibling. It consumes the public
`VerifiedMarketIdentity` interface and a narrow structural SDK-stream
capability. It does not import private Ingress Boundary leaves or Kalshi
Gateway internals. The Market Ingress parent remains the sibling composition
point.
