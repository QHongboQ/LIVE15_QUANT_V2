"""Official discovery through documented SDK market filters only."""
from decimal import Decimal

from kalshi.errors import KalshiNotFoundError
from kalshi.models import Market

from live15_quant_v2.data.market_ingress.kalshi_gateway.gateway import KalshiGateway
from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.models import (
    CandidateTicker,
    DiscoveredMarket,
    MarketScopeBinding,
    MarketWindow,
    OfficialStrike,
)


class OfficialMarketDiscovery:
    def __init__(self,gateway:KalshiGateway)->None: self._gateway=gateway
    def discover(self,*,binding:MarketScopeBinding,window:MarketWindow,candidate:CandidateTicker|None)->tuple[DiscoveredMarket,...]:
        raw:list[Market]=[]
        if candidate:
            try: raw.append(self._gateway.fetch_market(candidate.ticker))
            except KalshiNotFoundError: pass
        envelope=15*60
        raw.extend(self._gateway.discover_markets(series_ticker=binding.series_ticker,min_close_ts=int(window.close_time.timestamp())-envelope,max_close_ts=int(window.close_time.timestamp())+envelope))
        unique:dict[str,DiscoveredMarket]={}
        for market in raw: unique[market.ticker]=self._translate(market,binding)
        return tuple(unique.values())
    @staticmethod
    def _translate(market:Market,binding:MarketScopeBinding)->DiscoveredMarket:
        return DiscoveredMarket(binding,market.ticker,market.event_ticker,market.open_time,market.close_time,OfficialStrike(market.strike_type,OfficialMarketDiscovery._decimal(market.floor_strike),OfficialMarketDiscovery._decimal(market.cap_strike),market.yes_sub_title,market.functional_strike))
    @staticmethod
    def _decimal(value:object)->Decimal|None:
        return value if isinstance(value,Decimal) else None