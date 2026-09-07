# Storage

Storage owns the shared immutable `CaptureFact` contract: canonical asset,
provider, source, channel, message type, optional event subtype, stream/session
metadata, nullable provider timestamp, received timestamp, schema version, and
opaque payload text. This shared contract is sealed. Its [Hot Store](hot-store/README.md)
and [Capture Boundary](capture-boundary.md) children are FINAL CLOSED: Hot Store
owns physical retention and retrieval, while Capture Boundary freezes approved
typed Market Ingress messages into immutable facts.

Capture Boundary remains a Storage sibling of Hot Store and does not depend on
Hot Store-private models. The [Durable Persistence contract authority](durable-persistence.md)
is FINAL CLOSED; Durable Persistence implementation is NOT IMPLEMENTED. The
next Storage action is the bounded Hot Store physical transport-idempotency /
DEDUP prerequisite gate, starting with QuestDB `10.0.1` / Python client `5.0.0`
contract fit and read-only collision audits before any mutation. Other Storage
responsibilities remain unimplemented and are not defined by this routing node.
