"""Typed Kalshi ``pyth_value`` messages missing from SDK v13.0.0."""

from typing import Literal

from kalshi.types import DollarDecimal
from pydantic import BaseModel


class PythValuePayload(BaseModel):
    underlying_ticker: str
    value_usd: DollarDecimal
    source_ts_ms: int
    received_at: int
    model_config = {"extra": "allow", "populate_by_name": True}


class PythValueMessage(BaseModel):
    type: Literal["pyth_value"] = "pyth_value"
    sid: int
    seq: int
    msg: PythValuePayload
    model_config = {"extra": "allow", "populate_by_name": True}


class PythUnderlyingListPayload(BaseModel):
    underlying_tickers: list[str]
    model_config = {"extra": "allow", "populate_by_name": True}


class PythUnderlyingListMessage(BaseModel):
    type: Literal["pyth_value_underlying_list"] = "pyth_value_underlying_list"
    id: int | None = None
    sid: int
    seq: int
    msg: PythUnderlyingListPayload
    model_config = {"extra": "allow", "populate_by_name": True}
