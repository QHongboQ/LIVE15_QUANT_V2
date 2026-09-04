# Data System

The Data System owns bounded ingress contracts for externally observed market
facts. Its direct child is [Market Ingress](market-ingress/README.md), which
composes provider-specific gateways behind narrow read-only interfaces and
exposes verified provider facts upward. Storage, canonical data truth,
datasets, research, models, execution, and operations are explicitly out of
scope.