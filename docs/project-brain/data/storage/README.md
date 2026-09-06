# Storage

Storage owns the shared immutable `CaptureFact` contract: canonical asset,
provider, source, channel, message type, optional event subtype, stream/session
metadata, nullable provider timestamp, received timestamp, schema version, and
opaque payload text. This shared contract is sealed. Its [Hot Store](hot-store/README.md)
and [Capture Boundary](capture-boundary.md) children are FINAL CLOSED: Hot Store
owns physical retention and retrieval, while Capture Boundary freezes approved
typed Market Ingress messages into immutable facts.

Capture Boundary remains a Storage sibling of Hot Store and does not depend on
Hot Store-private models. The next Storage responsibility is Durable
Persistence; other Storage responsibilities remain unimplemented and are not
defined by this routing node.
