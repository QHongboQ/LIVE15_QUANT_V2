# Storage

Storage owns the shared immutable `CaptureFact` contract: canonical asset,
provider, source, channel, message type, optional event subtype, stream/session
metadata, nullable provider timestamp, received timestamp, schema version, and
opaque payload text. This shared contract is sealed. Its [Hot Store](hot-store/README.md)
and [Capture Boundary](capture-boundary.md) children are FINAL CLOSED: Hot Store
owns physical retention and retrieval, including its sealed native QuestDB
physical transport-idempotency evolution, while Capture Boundary freezes
approved typed Market Ingress messages into immutable facts.

Capture Boundary remains a Storage sibling of Hot Store and does not depend on
Hot Store-private models. New Hot Store tables use QuestDB-native `WAL DEDUP
UPSERT KEYS(received_timestamp, capture_id)`; existing incompatible tables fail
closed rather than receiving silent DEDUP activation. This fulfills the physical
transport-idempotency prerequisite of the [Durable Persistence contract authority](durable-persistence.md),
which is FINAL CLOSED. Durable Persistence implementation is FINAL CLOSED.
Storage's currently defined responsibilities are closed. Canonical
`hot_capture_facts` remains unmaterialized, so this sealed implementation
capability does not activate canonical runtime DEDUP or Store-and-Forward.
