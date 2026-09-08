# V2 Engineering Lifecycle

This compact global authority defines the default V2 construction and
deployment lifecycle. It is not a child of Data Truth or any other domain
responsibility.

```text
Responsibility ownership
→ Contract / Interface
→ Leaf implementation
→ Adapter
→ Composition
→ Integration Test
→ Runtime deployment
→ Canonical activation
```

1. Establish responsibility and tree ownership before implementation.
2. Use stable interfaces and adapters at cross-responsibility, external API,
   database, or runtime seams when replacement or isolation has real value.
   Pure internal semantic logic does not require artificial interfaces.
3. Lower-level implementations adapt to approved upper contracts; do not
   reshape the upper architecture around one database or vendor API. Prefer
   mature upstream mechanics behind adapters.
4. Compose and wire bounded leaves only after they satisfy their contracts.
5. Deploy runtime capability only after implementation and integration
   validation. Canonical or production activation is last and separately
   authorized when required.
6. Infrastructure installed or exercised earlier for upstream-fit work or a
   bounded POC is capability evidence, not business-contract authority.
7. Do not create an interface per function or a module per message family.
