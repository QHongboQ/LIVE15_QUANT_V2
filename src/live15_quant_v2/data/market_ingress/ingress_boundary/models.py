"""Immutable LIVE15-owned market-identity facts."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum

QUARTER_HOUR = timedelta(minutes=15)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True)
class MarketWindow:
    open_time: datetime
    close_time: datetime

    def __post_init__(self) -> None:
        open_time, close_time = as_utc(self.open_time), as_utc(self.close_time)
        if close_time - open_time != QUARTER_HOUR:
            raise ValueError("window must be exactly 15 minutes")
        if open_time.minute % 15 or open_time.second or open_time.microsecond:
            raise ValueError("window must start on a quarter hour")
        object.__setattr__(self, "open_time", open_time)
        object.__setattr__(self, "close_time", close_time)


@dataclass(frozen=True)
class MarketScopeBinding:
    asset_id: str
    series_ticker: str

    def __post_init__(self) -> None:
        if not self.asset_id or not self.series_ticker:
            raise ValueError("scope binding values must be non-empty")


@dataclass(frozen=True)
class CandidateTicker:
    binding: MarketScopeBinding
    ticker: str
    window: MarketWindow


@dataclass(frozen=True)
class OfficialStrike:
    strike_type: str | None
    floor_strike: Decimal | None
    cap_strike: Decimal | None
    yes_sub_title: str
    functional_strike: str | None = None

    @property
    def usable(self) -> bool:
        return self.floor_strike is not None or self.cap_strike is not None


@dataclass(frozen=True)
class DiscoveredMarket:
    observed_series_ticker: str
    ticker: str
    event_ticker: str | None
    open_time: datetime
    close_time: datetime
    strike: OfficialStrike

    def __post_init__(self) -> None:
        object.__setattr__(self, "open_time", as_utc(self.open_time))
        object.__setattr__(self, "close_time", as_utc(self.close_time))


@dataclass(frozen=True)
class VerifiedMarketIdentity:
    binding: MarketScopeBinding
    ticker: str
    event_ticker: str
    window: MarketWindow
    strike: OfficialStrike


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    NO_MATCH = "no_match"
    AMBIGUOUS = "ambiguous"
    INVALID = "invalid"


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    identity: VerifiedMarketIdentity | None = None
    reason: str | None = None

    @property
    def verified(self) -> bool:
        return self.status is VerificationStatus.VERIFIED and self.identity is not None


class ShadowStatus(StrEnum):
    MATCH = "match"
    MISMATCH = "mismatch"
    CANDIDATE_MISSING = "candidate_missing"
    OFFICIAL_MISSING = "official_missing"
    VERIFICATION_FAILED = "verification_failed"


@dataclass(frozen=True)
class ShadowResult:
    status: ShadowStatus
    candidate_ticker: str | None
    official_ticker: str | None
