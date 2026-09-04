"""Small immutable identities used only by the Kalshi Market Identity tree."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

QUARTER_HOUR = timedelta(minutes=15)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Market identity timestamps must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True)
class MarketWindow:
    """One exact UTC quarter-hour interval."""

    open_time: datetime
    close_time: datetime

    def __post_init__(self) -> None:
        open_time = _utc(self.open_time)
        close_time = _utc(self.close_time)
        if close_time - open_time != QUARTER_HOUR:
            raise ValueError("A MarketWindow must be exactly 15 minutes")
        if open_time.minute % 15 or open_time.second or open_time.microsecond:
            raise ValueError("MarketWindow open_time must be a quarter-hour boundary")
        object.__setattr__(self, "open_time", open_time)
        object.__setattr__(self, "close_time", close_time)

    @classmethod
    def current(cls, now: datetime) -> MarketWindow:
        instant = _utc(now)
        start = instant.replace(
            minute=instant.minute - (instant.minute % 15), second=0, microsecond=0
        )
        return cls(open_time=start, close_time=start + QUARTER_HOUR)

    def next(self) -> MarketWindow:
        return MarketWindow(open_time=self.close_time, close_time=self.close_time + QUARTER_HOUR)


@dataclass(frozen=True)
class CandidateTicker:
    series_ticker: str
    ticker: str
    window: MarketWindow


@dataclass(frozen=True)
class DiscoveredMarket:
    """A LIVE15 translation of only the official fields needed for identity checks."""

    series_ticker: str
    ticker: str
    event_ticker: str | None
    open_time: datetime
    close_time: datetime
    target: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "open_time", _utc(self.open_time))
        object.__setattr__(self, "close_time", _utc(self.close_time))

    @property
    def has_published_target(self) -> bool:
        if self.target is None:
            return False
        value = self.target.strip()
        return bool(value) and value.casefold() not in {"tbd", "unknown", "pending"}


@dataclass(frozen=True)
class VerifiedMarketIdentity:
    series_ticker: str
    ticker: str
    event_ticker: str
    window: MarketWindow
    target: str


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