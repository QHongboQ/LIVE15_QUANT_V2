# Hot Store

Hot Store preserves raw capture facts behind the provider-neutral `HotStore`
interface: bounded `append_batch`, `read_capture`, and physical `read_range`.
It consumes Storage's shared `CaptureFact` contract rather than owning capture
semantics.

The current adapter is QuestDB `10.0.1` through the official Python client
`questdb==5.0.0`. It is available only from
`live15_quant_v2.data.storage.hot_store.questdb_adapter`; the package root is
provider-neutral. QuestDB owns generic database mechanics; LIVE15 owns the
interface and raw-fact mapping. The raw table does not enable deduplication, so
separate capture identities remain separate stored facts. Initial writes are
explicitly limited to 500 facts per batch, based on the accepted local adapter
integration evidence. The adapter adds newly required raw metadata columns
non-destructively when an existing table is reused. That physical schema change
does not semantically upgrade historical rows: no metadata or asset identity is
backfilled, and rows missing required source/message metadata or carrying a
non-canonical asset are incompatible with the shared contract and fail closed.

QuestDB reads materialize through the official `QueryResult.to_pandas()` path.
Accordingly, pandas is an adapter-local runtime dependency: pandas values and
types do not cross the `HotStore` port, whose reads return `CaptureFact` values.

`CaptureFact.payload` is opaque UTF-8 text. Its current expected representation
is JSON text, preserved exactly on round trip; Hot Store performs no parsing,
normalization, or canonicalization. This contract does not claim arbitrary
binary-payload support.

This leaf preserves provider, source ID, channel, message type, optional event
subtype, session, optional sequence, nullable provider timestamp, received
timestamp, schema version, and raw payload. It does not infer Capture Boundary,
Data Truth, gaps, quarantine, replay, or any other Storage responsibility.
