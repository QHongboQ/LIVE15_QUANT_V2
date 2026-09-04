"""Sole concrete LIVE15 nine-asset market-scope authority."""
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.models import (
 MarketScopeBinding,
)


class Live15MarketScopeConfig:
 _BINDINGS=(MarketScopeBinding("BTC","KXBTC15M"),MarketScopeBinding("ETH","KXETH15M"),MarketScopeBinding("GOLD","KXGOLD15M"),MarketScopeBinding("SILVER","KXSILVER15M"),MarketScopeBinding("XRP","KXXRP15M"),MarketScopeBinding("SOL","KXSOL15M"),MarketScopeBinding("HYPE","KXHYPE15M"),MarketScopeBinding("DOGE","KXDOGE15M"),MarketScopeBinding("BNB","KXBNB15M"))
 def __init__(self)->None:
  self._assets={b.asset_id:b for b in self._BINDINGS};self._series={b.series_ticker:b for b in self._BINDINGS}
  if len(self._assets)!=9 or len(self._series)!=9:raise RuntimeError("bindings must be bijective")
 def binding_for_asset(self,asset_id:str)->MarketScopeBinding|None:return self._assets.get(asset_id)
 def binding_for_series(self,series_ticker:str)->MarketScopeBinding|None:return self._series.get(series_ticker)