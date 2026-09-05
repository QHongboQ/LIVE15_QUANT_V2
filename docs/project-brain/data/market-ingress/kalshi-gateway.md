# Kalshi Gateway

## Responsibility

This Market Ingress child owns only provider access through the pinned `kalshi-sdk==13.0.0` public APIs. It exposes narrow read-only market query primitives and typed WebSocket access. The SDK owns transport, authentication, pagination, reconnect/resubscribe, SID management, and generic sequence/gap mechanics.

Kalshi Gateway does **not** own LIVE15 asset scope, market/window semantics, candidate authorization, identity verification, shadow comparison, storage, or trading decisions.

## Public interface

Callers import only `KalshiGateway` from:

`live15_quant_v2.data.market_ingress.kalshi_gateway`

`KalshiGateway.subscription_access()` returns the SDK `KalshiWebSocket` type, not an untyped `object`.

## Dependency rule

Kalshi Gateway is a provider leaf. It must not import the sibling Ingress Boundary, and Ingress Boundary must not import it concretely. The Market Ingress parent composes the Gateway's provider discovery capability with the Boundary's public resolver factory:

`Market Ingress parent -> { Kalshi Gateway, Ingress Boundary } -> kalshi-sdk`

Market Stream may use SDK WebSocket capabilities through the approved provider-access surface, while stream semantics remain owned by the Market Stream child.
