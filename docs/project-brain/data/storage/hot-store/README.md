# Hot Store

Hot Store preserves raw capture facts behind the provider-neutral `HotStore`
interface: bounded `append_batch`, `read_capture`, and physical `read_range`.

The current adapter is QuestDB `10.0.1` through the official Python client
`questdb==5.0.0`. It is available only from
`live15_quant_v2.data.storage.hot_store.questdb_adapter`; the package root is
provider-neutral. QuestDB owns generic database mechanics; LIVE15 owns the
interface and raw-fact mapping. The raw table does not enable deduplication, so
separate capture identities remain separate stored facts. Initial writes are
explicitly limited to 500 facts per batch, based on the accepted local adapter
integration evidence.

QuestDB reads materialize through the official `QueryResult.to_pandas()` path.
Accordingly, pandas is an adapter-local runtime dependency: pandas values and
types do not cross the `HotStore` port, whose reads return `CaptureFact` values.

`CaptureFact.payload` is opaque UTF-8 text. Its current expected representation
is JSON text, preserved exactly on round trip; Hot Store performs no parsing,
normalization, or canonicalization. This contract does not claim arbitrary
binary-payload support.

This leaf preserves provider, session, optional sequence, both timestamps,
schema version, and raw payload. It does not infer Data Truth, gaps,
quarantine, replay, or any other Storage responsibility.
