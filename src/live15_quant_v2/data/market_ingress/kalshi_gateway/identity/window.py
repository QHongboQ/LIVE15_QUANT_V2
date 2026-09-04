"""UTC quarter-hour mechanics; this is the sole implementation owner."""
from datetime import datetime

from live15_quant_v2.data.market_ingress.kalshi_gateway.identity.models import (
    QUARTER_HOUR,
    MarketWindow,
    as_utc,
)


def current(now: datetime) -> MarketWindow:
    instant=as_utc(now)
    open_time=instant.replace(minute=instant.minute-instant.minute%15,second=0,microsecond=0)
    return MarketWindow(open_time,open_time+QUARTER_HOUR)
def next_window(window: MarketWindow)->MarketWindow:
    return MarketWindow(window.close_time,window.close_time+QUARTER_HOUR)