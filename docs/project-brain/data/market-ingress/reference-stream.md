# Reference Stream

## Responsibility tree

```text
Reference Stream
├─ Reference Scope
│  ├─ seven crypto assets -> verified CF Benchmarks index IDs
│  ├─ GOLD -> Metal.XAU/USD
│  └─ SILVER -> Metal.XAG/USD
├─ CF Benchmarks
│  └─ native kalshi-sdk helper
├─ Pyth Value
│  └─ isolated v13 compatibility leaf over SDK generic subscribe
└─ Public composition
```

Reference Stream selects the immutable LIVE15 reference scope and returns SDK
native typed async iterators. It does not own market discovery, storage, Data
Truth, freshness policy, connection lifecycle, authentication, reconnect,
resubscribe, SID mapping, queues, or sequence tracking.

## Reference scope

`Live15ReferenceScopeConfig` is the only LIVE15-owned asset-to-source mapping:

| Asset | Source | Provider ID |
| --- | --- | --- |
| BTC | CF Benchmarks | `BRTI` |
| ETH | CF Benchmarks | `ETHUSD_RTI` |
| XRP | CF Benchmarks | `XRPUSD_RTI` |
| SOL | CF Benchmarks | `SOLUSD_RTI` |
| HYPE | CF Benchmarks | `HYPEUSD_RTI` |
| DOGE | CF Benchmarks | `DOGEUSD_RTI` |
| BNB | CF Benchmarks | `BNBUSD_RTI` |
| GOLD | Pyth Value | `Metal.XAU/USD` |
| SILVER | Pyth Value | `Metal.XAG/USD` |

WTI is absent. The seven CF IDs were verified through an authorized bounded
read-only `subscribe_cfbenchmarks_value(index_ids=["all"])` discovery on
2026-09-04. Gold and Silver identifiers are from the pinned upstream AsyncAPI
at commit `16c0b8368cc27991311d513a8dc5a0814dd786e0`.

## CF Benchmarks

CF Benchmarks uses the SDK-native
`subscribe_cfbenchmarks_value(index_ids=...)` helper and preserves its
`CFBenchmarksValueMessage | CFBenchmarksIndexListMessage` iterator unchanged.

## Pyth Value compatibility

Kalshi's official AsyncAPI defines `pyth_value` and the two fixed metal
underlyings, but `kalshi-sdk==13.0.0` lacks native Pyth models, a Pyth helper,
and the parameter/model registry entries needed by its public generic
subscription mechanism. The isolated `pyth_value/sdk_compat.py` compatibility
leaf is version-guarded to exactly v13.0.0, idempotently registers only
`underlying_tickers` forwarding plus `pyth_value` and
`pyth_value_underlying_list` message models, and fails closed on unexpected or
conflicting SDK registry shape.

After that registration, Pyth Value calls only the SDK public generic
`subscribe("pyth_value", params={"underlying_tickers": [...]})` and preserves
`PythValueMessage | PythUnderlyingListMessage`. It neither forks nor wraps SDK
transport/reliability machinery. When a future pinned SDK supplies native typed
Pyth Value support, delete this compatibility leaf and use the native helper.

## Public interface and session ownership

Import `ReferenceStream`, `Live15ReferenceScopeConfig`, and the scope model
from:

`live15_quant_v2.data.market_ingress.reference_stream`

`ReferenceStream` requires an already-active SDK WebSocket session/capability.
The caller owns session lifecycle; `cfbenchmarks()` and `pyth_values()` only
start the approved typed subscriptions for the fixed scope.

```python
from live15_quant_v2.data.market_ingress.reference_stream import (
    Live15ReferenceScopeConfig,
    ReferenceStream,
)

async with websocket.connect() as session:
    references = ReferenceStream(Live15ReferenceScopeConfig(), session)
    cf_messages = await references.cfbenchmarks()
    pyth_messages = await references.pyth_values()
```

The returned iterators have no storage or trading side effect. The caller is
responsible for consuming them while it owns the SDK session.

## Test ownership

The SDK owns testing of transport, authentication, sessions, reconnect,
resubscribe, SID mapping, generic queue behavior, and sequence machinery.
LIVE15 tests only its exact scope, native/helper delegation, isolated
compatibility registration, typed dispatcher routing, and public composition.