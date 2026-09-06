# Storage

Storage owns the shared immutable `CaptureFact` contract: canonical asset,
provider, source, channel, message type, optional event subtype, stream/session
metadata, nullable provider timestamp, received timestamp, schema version, and
opaque payload text. Its implemented child, [Hot Store](hot-store/README.md),
consumes that contract for physical retention and retrieval.

Capture Boundary remains an unimplemented Storage sibling and therefore does
not depend on Hot Store-private models. Other Storage responsibilities remain
deferred and are not defined by this leaf.
