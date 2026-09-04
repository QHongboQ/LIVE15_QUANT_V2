# Data System

Data System owns V2 data responsibilities and routes their future children. This
PR implements only its [Market Ingress](market-ingress/README.md) child, which
composes provider-specific gateways behind narrow read-only interfaces and
exposes verified provider facts upward. Storage, canonical Data Truth, datasets,
research, models, execution, and operations are deferred responsibilities: they
are not implemented by this task. Market Ingress itself does not own them.