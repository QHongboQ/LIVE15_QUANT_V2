# QuestDB Runtime

**Status:** PLATFORM DEPLOYED — VALIDATION CANDIDATE.

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

The canonical platform deployment evidence is:

- official QuestDB Server `10.0.1` Windows runtime artifact,
  `questdb-10.0.1-rt-windows-x86-64.tar.gz` (88,871,519 bytes); the prior
  bootstrap verification recorded local SHA-256
  `e8ea640e3e68a70a700cdf0a05f60e374efa33d6ed2399be8e4a70677a98d092`
  matching the available vendor checksum. The archive is not retained locally;
  this task does not redownload it solely to recreate that evidence.
- canonical distribution: `D:\LIVE15_V2_RUNTIME\questdb\dist\10.0.1`;
  canonical root: `D:\LIVE15_V2_RUNTIME\questdb\root`; canonical
  Store-and-Forward parent: `D:\LIVE15_V2_RUNTIME\questdb\sf`.
- official Windows service tag `LIVE15_V2`, service name
  `QuestDB:LIVE15_V2`, and display name `QuestDB Server [LIVE15_V2]`, Running
  with AutoStart, using
  `D:\LIVE15_V2_RUNTIME\questdb\root\conf\server.conf`.
- `metrics.enabled=true`; the service listens on `0.0.0.0:9000` (HTTP/QWP),
  `0.0.0.0:8812` (PGWire), `0.0.0.0:9003` (min HTTP), and `0.0.0.0:9009`
  (ILP TCP). `http://127.0.0.1:9003/status` returns HTTP 200 `Status:
  Healthy`; `/metrics` returns HTTP 200 Prometheus text.
- `questdb==5.0.0` imports in the repository environment. The sealed Hot
  Store's bounded live integration passes against this server, including schema
  create, append acknowledgement, exact raw round-trip, nine assets, distinct
  capture IDs, out-of-order facts, filters, and the 500-row limit.

Durable Persistence is not implemented. Disk-backed application
Store-and-Forward is not enabled, and this platform deployment does not set
`sf_dir`, `sender_id`, `sf_durability`, Store-and-Forward capacity, retry,
acknowledgement policy, or deduplication.

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
