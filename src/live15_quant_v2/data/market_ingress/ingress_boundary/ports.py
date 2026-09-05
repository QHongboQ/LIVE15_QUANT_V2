"""Ingress Boundary ports."""
from collections.abc import Iterable
from typing import Protocol

from kalshi.models import Market

from live15_quant_v2.data.market_ingress.ingress_boundary.models import (
 MarketScopeBinding,
)


class MarketScopePort(Protocol):
 def binding_for_asset(self,asset_id:str)->MarketScopeBinding|None: ...
 def binding_for_series(self,series_ticker:str)->MarketScopeBinding|None: ...
class MarketDiscoveryPort(Protocol):
 def discover_markets(self,*,series_ticker:str,min_close_ts:int,max_close_ts:int)->Iterable[Market]: ...