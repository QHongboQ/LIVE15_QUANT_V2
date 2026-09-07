# Hot Store

**Status:** FINAL CLOSED, including the sealed native QuestDB physical
transport-idempotency bounded forward evolution. The provider-neutral
`HotStore` interface remains bounded `append_batch`, `read_capture`, and
physical `read_range`; it consumes the sealed shared immutable `CaptureFact`
contract without changing it.

The adapter is QuestDB Server `10.0.1` through the official Python client
`questdb==5.0.0`. It is available only from
`live15_quant_v2.data.storage.hot_store.questdb_adapter`; the package root is
provider-neutral. For a new physical table it creates
`TIMESTAMP(received_timestamp)`, `PARTITION BY DAY`, `WAL`, and `DEDUP UPSERT
KEYS(received_timestamp, capture_id)`.

This is physical transport idempotency only: an exact replay with the same
`capture_id` and `received_timestamp` leaves one eventual physical row, while
facts with different `capture_id` values remain distinct rows even when their
content matches. It introduces no semantic/Data Truth deduplication.

Existing physical tables are inspected first. A non-WAL, non-DEDUP, wrong-key,
wrong timestamp/type, or otherwise incompatible table fails closed at an
explicit migration-required boundary; the adapter does not silently run
`ALTER TABLE ... DEDUP ENABLE`. Previously approved `source_id`,
`message_type`, and `event_subtype` compatibility additions occur only after
core physical compatibility is accepted. Historical rows are never backfilled;
rows missing required metadata or carrying a non-canonical asset fail closed.

QuestDB owns WAL, DEDUP, and UPSERT mechanics. LIVE15 owns only physical
configuration authority, compatibility verification, `CaptureFact` mapping,
the fail-closed migration boundary, and acceptance tests. No custom WAL, queue,
dedup cache/system, retry manager, replay engine, reconnect manager, ACK
tracker, or persistence framework is introduced.

Canonical runtime activation is separate from sealed implementation capability:
canonical `hot_capture_facts` is currently **NOT MATERIALIZED**, so canonical
runtime DEDUP is **NOT ENABLED / NOT ACTIVE**. The adapter is ready to create a
future authorized new table correctly from birth; this status does not
authorize that materialization or Store-and-Forward.

QuestDB reads materialize through the official `QueryResult.to_pandas()` path.
Pandas remains adapter-local: pandas values and types do not cross the HotStore
port, whose reads return `CaptureFact` values. `CaptureFact.payload` is opaque
UTF-8 text, currently expected as JSON text and preserved exactly without
parsing, normalization, or canonicalization; arbitrary binary support is not
claimed.
