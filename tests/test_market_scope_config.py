from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.scope import (
 Live15MarketScopeConfig,
)

EXPECTED={"BTC":"KXBTC15M","ETH":"KXETH15M","GOLD":"KXGOLD15M","SILVER":"KXSILVER15M","XRP":"KXXRP15M","SOL":"KXSOL15M","HYPE":"KXHYPE15M","DOGE":"KXDOGE15M","BNB":"KXBNB15M"}
def test_nine_asset_bijective_scope():
 c=Live15MarketScopeConfig();assert len(EXPECTED)==9;assert c.binding_for_asset("WTI") is None
 for asset,series in EXPECTED.items():
  binding=c.binding_for_asset(asset);assert binding and binding.series_ticker==series;assert c.binding_for_series(series)==binding
 assert c.binding_for_asset("UNKNOWN") is None and c.binding_for_series("UNKNOWN") is None
