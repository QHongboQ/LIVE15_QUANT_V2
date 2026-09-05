# Hot Store

Hot Store preserves raw capture facts behind the provider-neutral `HotStore`
interface: bounded `append_batch`, `read_capture`, and physical `read_range`.

The current adapter is QuestDB `10.0.1` through the official Python client
`questdb==5.0.0`. QuestDB owns generic database mechanics; LIVE15 owns the
interface and raw-fact mapping. The raw table does not enable deduplication, so
separate capture identities remain separate stored facts. Initial writes are
explicitly limited to 500 facts per batch, based on the accepted local adapter
integration evidence.

This leaf preserves provider, session, optional sequence, both timestamps,
schema version, and raw payload. It does not infer Data Truth, gaps,
quarantine, replay, or any other Storage responsibility.
