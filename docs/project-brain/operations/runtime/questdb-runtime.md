# QuestDB Runtime

**Status:** APPROVED FOR PLATFORM BOOTSTRAP. UNIMPLEMENTED.

This leaf owns the canonical LIVE15 V2 QuestDB Runtime Platform:

- official QuestDB Server installation and version;
- canonical LIVE15 V2 QuestDB root;
- official Windows QuestDB service and tag;
- QuestDB server configuration and ports;
- official QuestDB lifecycle commands;
- QuestDB health and metrics upstream endpoints;
- canonical persistent Store-and-Forward parent directory; and
- runtime provenance and version evidence.

**Target upstream:** QuestDB Server `10.0.1`; official `questdb` Python client
`5.0.0`.

The runtime is consumed by Storage / Hot Store and Storage / Durable
Persistence. It is not a child of Hot Store: Hot Store and Durable Persistence
do not own QuestDB installation or service lifecycle. This task adds no
source-code dependency.

```text
Operations / Runtime → Runtime Infrastructure → QuestDB Runtime
                                                ↑ consumed by
                                                ├── Storage / Hot Store
                                                └── Storage / Durable Persistence
```

QuestDB Runtime does not own CaptureFact, Capture Boundary, Hot Store
row/schema mapping, the Hot Store append/read contract, Durable Persistence
delivery semantics, Data Truth, replay, archive, retention, model/trading
logic, or LIVE15 application service lifecycle.

When QuestDB upstream binds a generic capability set together, LIVE15 does not
artificially split its internals into custom leaves. For example,
Store-and-Forward may bind disk spool, reconnect, replay, ACK tracking,
backpressure, and crash recovery as one upstream-owned capability set. LIVE15
leaves own only their external contract and responsibility boundary.
