# Market Ingress

Market Ingress owns provider-adapter composition: it selects a narrow gateway
interface and keeps provider transports behind it. Its direct child is the
[Kalshi Gateway](kalshi-gateway.md). The child supplies discovery and verified
market identity facts; this parent does not own a live runtime, storage, market
scope configuration, or trading decisions.