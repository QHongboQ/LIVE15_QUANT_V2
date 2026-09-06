# Storage

Storage owns the shared immutable `CaptureFact` contract: canonical asset,
provider, source, channel, message type, optional event subtype, stream/session
metadata, nullable provider timestamp, received timestamp, schema version, and
opaque payload text. Its implemented child, [Hot Store](hot-store/README.md),
consumes that contract for physical retention and retrieval.

[Capture Boundary](capture-boundary.md) is an implementation candidate that
freezes approved typed Market Ingress messages into `CaptureFact`. It is a
Storage sibling of Hot Store, and does not depend on Hot Store-private models.
Other Storage responsibilities remain deferred and are not defined by this
leaf.
