"""Pure provider-neutral request validation, qualification, and pagination."""

import base64
import hashlib
import json
from dataclasses import dataclass
from typing import NoReturn, TypeGuard, cast

from live15_quant_v2.data.asset import AssetId
from live15_quant_v2.data.replay_as_of.models import (
    AsOfReplayView,
    AsOfRequest,
    AuthoritativeReplayRecord,
    AvailabilityReference,
    CompletenessState,
    ReplayAsOfError,
    ReplayErrorCode,
    ReplayExclusion,
    ReplayExclusionCode,
    ReplayOrdering,
    SelectionAxis,
    SelectionWindow,
)
from live15_quant_v2.data.replay_as_of.source import (
    ReplayCandidateScope,
    ReplaySource,
    ReplaySourceRecord,
    SourceAuthorityIdentities,
)

REQUEST_VERSION = "replay-as-of-request/v1"
ORDERING_RULE_VERSION = "replay-as-of-ordering/v1"
SNAPSHOT_SCHEME_VERSION = "replay-as-of-snapshot/v1"
CURSOR_VERSION = "replay-as-of-cursor/v1"
V1_POLICY = "data-truth/v1"

type _ArrivalKey = tuple[int, str]
type _StrictEventKey = tuple[int, int, str]
type _OrderingKey = _ArrivalKey | _StrictEventKey


@dataclass(frozen=True, slots=True)
class _ValidatedRequest:
    request: AsOfRequest
    assets: tuple[AssetId, ...] | None
    channels: tuple[str, ...] | None


@dataclass(frozen=True, slots=True)
class _QualifiedRecord:
    source_record: ReplaySourceRecord
    public_record: AuthoritativeReplayRecord


@dataclass(frozen=True, slots=True)
class _ValidatedAvailability:
    available_at_ns: int
    reference: str


@dataclass(frozen=True, slots=True)
class _DecodedCursor:
    version: str
    ordering: ReplayOrdering
    request_identity: str
    source_snapshot_identity: str
    last_key: list[object]


class ReplayAsOf:
    """The Slice 1 provider-neutral Replay read service."""

    def __init__(self, source: ReplaySource, *, max_page_size: int) -> None:
        if not _is_int(max_page_size) or max_page_size <= 0:
            raise ValueError("max_page_size must be a positive integer")
        self._source = source
        self._max_page_size = max_page_size

    def read(self, request: AsOfRequest) -> AsOfReplayView:
        """Build one deterministic, bounded As-Of page from the source seam."""
        validated = _validate_request(request, self._max_page_size)
        request_identity = _request_identity(validated)
        authorities = self._source.source_authorities()
        candidates = tuple(self._source.candidate_records(_candidate_scope(validated)))
        qualified, exclusions = _qualify(candidates, validated)
        selected = _select(qualified, validated.request.selection_window)
        _require_ordering_timestamps(selected, validated.request.ordering)
        ordered = tuple(
            sorted(
                selected,
                key=lambda item: _ordering_key(item.source_record, validated.request.ordering),
            )
        )
        snapshot_identity = _snapshot_identity(validated, authorities, ordered)
        last_key = _cursor_last_key(
            validated.request.cursor,
            validated.request.ordering,
            request_identity,
            snapshot_identity,
            ordered,
        )
        continued = _continue_after(ordered, validated.request.ordering, last_key)
        page = continued[: validated.request.page_size]
        next_cursor = None
        if len(continued) > len(page):
            next_cursor = _encode_cursor(
                validated.request.ordering,
                request_identity,
                snapshot_identity,
                _ordering_key(page[-1].source_record, validated.request.ordering),
            )
        return AsOfReplayView(
            tuple(item.public_record for item in page),
            request_identity,
            validated.request.authority_policy_version,
            validated.request.as_of_cutoff_ns,
            validated.request.selection_window,
            validated.request.ordering,
            ORDERING_RULE_VERSION,
            snapshot_identity,
            CompletenessState.NOT_ASSERTED,
            tuple(sorted(exclusions, key=lambda exclusion: (exclusion.capture_id, exclusion.code.value))),
            next_cursor,
        )


def _validate_request(request: AsOfRequest, max_page_size: int) -> _ValidatedRequest:
    if not _is_int(request.as_of_cutoff_ns):
        _invalid_request("cutoff must be an integer")
    if request.authority_policy_version != V1_POLICY:
        _invalid_request("unsupported authority policy")
    if not isinstance(request.selection_window, SelectionWindow):
        _invalid_request("selection window must be SelectionWindow")
    window = request.selection_window
    if not isinstance(window.axis, SelectionAxis):
        _invalid_request("unsupported selection axis")
    if not _is_int(window.start_ns) or not _is_int(window.end_ns):
        _invalid_request("selection bounds must be integers")
    if window.start_ns >= window.end_ns:
        _invalid_request("selection window must be half-open and non-empty")
    if not isinstance(request.ordering, ReplayOrdering):
        _invalid_request("unsupported ordering")
    if not _is_int(request.page_size) or not 0 < request.page_size <= max_page_size:
        _invalid_request("page size is outside the configured bound")
    if request.cursor is not None and not isinstance(request.cursor, str):
        _invalid_request("cursor must be a string or None")
    return _ValidatedRequest(
        request,
        _canonical_assets(request.assets),
        _canonical_channels(request.channels),
    )


def _canonical_assets(raw: object) -> tuple[AssetId, ...] | None:
    if raw is None:
        return None
    if isinstance(raw, (str, bytes)):
        _invalid_request("assets must be a collection of AssetId values")
    if not isinstance(raw, tuple):
        _invalid_request("assets must be an immutable collection")
    if not raw:
        _invalid_request("unfiltered assets must be represented by None")
    if not all(isinstance(asset, AssetId) for asset in raw):
        _invalid_request("assets must be approved AssetId values")
    return tuple(sorted(set(raw), key=str))


def _canonical_channels(raw: object) -> tuple[str, ...] | None:
    if raw is None:
        return None
    if isinstance(raw, (str, bytes)) or not isinstance(raw, tuple):
        _invalid_request("channels must be an immutable collection")
    if not raw:
        _invalid_request("unfiltered channels must be represented by None")
    if not all(isinstance(channel, str) and channel and len(channel) <= 128 for channel in raw):
        _invalid_request("channels must be bounded non-empty strings")
    return tuple(sorted(set(raw)))


def _request_identity(validated: _ValidatedRequest) -> str:
    request = validated.request
    return _digest(
        {
            "assets": None if validated.assets is None else [str(asset) for asset in validated.assets],
            "authority_policy_version": request.authority_policy_version,
            "channels": None if validated.channels is None else list(validated.channels),
            "as_of_cutoff_ns": request.as_of_cutoff_ns,
            "ordering": request.ordering.value,
            "ordering_rule_version": ORDERING_RULE_VERSION,
            "request_version": REQUEST_VERSION,
            "selection_axis": request.selection_window.axis.value,
            "selection_end_ns": request.selection_window.end_ns,
            "selection_start_ns": request.selection_window.start_ns,
        }
    )


def _candidate_scope(validated: _ValidatedRequest) -> ReplayCandidateScope:
    """Expose only validated semantic bounds to the provider-neutral source."""
    request = validated.request
    window = request.selection_window
    return ReplayCandidateScope(
        request.authority_policy_version,
        request.as_of_cutoff_ns,
        window.axis,
        window.start_ns,
        window.end_ns,
        validated.assets,
        validated.channels,
        request.ordering,
    )


def _qualify(
    candidates: tuple[ReplaySourceRecord, ...],
    validated: _ValidatedRequest,
) -> tuple[tuple[_QualifiedRecord, ...], tuple[ReplayExclusion, ...]]:
    qualified: list[_QualifiedRecord] = []
    exclusions: list[ReplayExclusion] = []
    keys: set[tuple[str, str]] = set()
    for candidate in candidates:
        fact = candidate.capture_fact
        decision = candidate.truth_decision
        if decision.policy_version != validated.request.authority_policy_version:
            continue
        if validated.assets is not None and fact.asset not in validated.assets:
            continue
        if validated.channels is not None and fact.channel not in validated.channels:
            continue
        if fact.capture_id != decision.subject_capture_id:
            _raise(ReplayErrorCode.MALFORMED_AUTHORITY, "decision subject does not match fact")
        key = (decision.policy_version, decision.subject_capture_id)
        if key in keys:
            _raise(ReplayErrorCode.AUTHORITY_CONFLICT, "duplicate authority subject")
        keys.add(key)
        evidence = _availability_state(candidate.evidence_availability, fact.capture_id, "evidence")
        authority = _availability_state(candidate.authority_availability, fact.capture_id, "authority")
        if evidence is None:
            exclusions.append(
                ReplayExclusion(ReplayExclusionCode.EVIDENCE_NOT_AVAILABLE_BY_CUTOFF, fact.capture_id)
            )
            continue
        if authority is None:
            exclusions.append(
                ReplayExclusion(ReplayExclusionCode.AUTHORITY_NOT_AVAILABLE_BY_CUTOFF, fact.capture_id)
            )
            continue
        if evidence.available_at_ns > validated.request.as_of_cutoff_ns:
            exclusions.append(
                ReplayExclusion(ReplayExclusionCode.EVIDENCE_NOT_AVAILABLE_BY_CUTOFF, fact.capture_id)
            )
            continue
        if authority.available_at_ns > validated.request.as_of_cutoff_ns:
            exclusions.append(
                ReplayExclusion(ReplayExclusionCode.AUTHORITY_NOT_AVAILABLE_BY_CUTOFF, fact.capture_id)
            )
            continue
        qualified.append(
            _QualifiedRecord(
                candidate,
                AuthoritativeReplayRecord(fact, decision, evidence.reference, authority.reference),
            )
        )
    return tuple(qualified), tuple(exclusions)


def _availability_state(
    availability: AvailabilityReference,
    capture_id: str,
    name: str,
) -> _ValidatedAvailability | None:
    timestamp_present = availability.available_at_ns is not None
    reference_present = availability.reference is not None
    if timestamp_present != reference_present:
        _raise(
            ReplayErrorCode.AVAILABILITY_EVIDENCE_MISSING,
            f"partial {name} availability for {capture_id}",
        )
    if not timestamp_present:
        return None
    if (
        not _is_int(availability.available_at_ns)
        or not isinstance(availability.reference, str)
        or not availability.reference
    ):
        _raise(
            ReplayErrorCode.AVAILABILITY_EVIDENCE_MISSING,
            f"invalid {name} availability for {capture_id}",
        )
    return _ValidatedAvailability(availability.available_at_ns, availability.reference)


def _select(
    qualified: tuple[_QualifiedRecord, ...],
    window: SelectionWindow,
) -> tuple[_QualifiedRecord, ...]:
    if window.axis is SelectionAxis.EVENT_TIME:
        selected: list[_QualifiedRecord] = []
        for item in qualified:
            provider_timestamp = item.source_record.capture_fact.provider_timestamp
            if provider_timestamp is None:
                _raise(ReplayErrorCode.UNSUPPORTED_EVENT_TIME, "qualified record lacks provider timestamp")
            if window.start_ns <= provider_timestamp < window.end_ns:
                selected.append(item)
        return tuple(selected)
    return tuple(
        item
        for item in qualified
        if window.start_ns <= item.source_record.capture_fact.received_timestamp < window.end_ns
    )


def _require_ordering_timestamps(
    selected: tuple[_QualifiedRecord, ...],
    ordering: ReplayOrdering,
) -> None:
    if ordering is ReplayOrdering.STRICT_EVENT and any(
        item.source_record.capture_fact.provider_timestamp is None for item in selected
    ):
        _raise(ReplayErrorCode.UNSUPPORTED_EVENT_TIME, "selected record lacks provider timestamp")


def _snapshot_identity(
    validated: _ValidatedRequest,
    authorities: SourceAuthorityIdentities,
    selected: tuple[_QualifiedRecord, ...],
) -> str:
    membership = sorted(
        (item.source_record.truth_decision.policy_version, item.source_record.truth_decision.subject_capture_id)
        for item in selected
    )
    request = validated.request
    return _digest(
        {
            "assets": None if validated.assets is None else [str(asset) for asset in validated.assets],
            "authority_policy_version": request.authority_policy_version,
            "availability_authority_identity": authorities.availability,
            "channels": None if validated.channels is None else list(validated.channels),
            "as_of_cutoff_ns": request.as_of_cutoff_ns,
            "evidence_authority_identity": authorities.evidence,
            "membership": membership,
            "ordering": request.ordering.value,
            "ordering_rule_version": ORDERING_RULE_VERSION,
            "selection_axis": request.selection_window.axis.value,
            "selection_end_ns": request.selection_window.end_ns,
            "selection_start_ns": request.selection_window.start_ns,
            "snapshot_scheme_version": SNAPSHOT_SCHEME_VERSION,
            "truth_decision_authority_identity": authorities.truth_decision,
        }
    )


def _cursor_last_key(
    cursor: object,
    ordering: ReplayOrdering,
    request_identity: str,
    snapshot_identity: str,
    selected: tuple[_QualifiedRecord, ...],
) -> _OrderingKey | None:
    if cursor is None:
        return None
    payload = _decode_cursor(cursor)
    if payload.version != CURSOR_VERSION:
        _raise(ReplayErrorCode.INVALID_CURSOR, "unsupported cursor version")
    if payload.request_identity != request_identity:
        _raise(ReplayErrorCode.CURSOR_MISMATCH, "cursor is bound to another request")
    if payload.source_snapshot_identity != snapshot_identity:
        _raise(ReplayErrorCode.SOURCE_UNAVAILABLE, "source snapshot cannot be reproduced")
    if payload.ordering is not ordering:
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor ordering is inconsistent")
    key = _decode_ordering_key(payload.last_key, ordering)
    if key not in {_ordering_key(item.source_record, ordering) for item in selected}:
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor key is not in rebuilt membership")
    return key


def _encode_cursor(
    ordering: ReplayOrdering,
    request_identity: str,
    snapshot_identity: str,
    last_key: _OrderingKey,
) -> str:
    payload = {
        "last_key": list(last_key),
        "ordering": ordering.value,
        "request_identity": request_identity,
        "source_snapshot_identity": snapshot_identity,
        "version": CURSOR_VERSION,
    }
    encoded = _canonical_json(payload).encode("utf-8")
    return base64.urlsafe_b64encode(encoded).decode("ascii").rstrip("=")


def _decode_cursor(cursor: object) -> _DecodedCursor:
    if not isinstance(cursor, str):
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor must be a string")
    try:
        padding = "=" * (-len(cursor) % 4)
        decoded = base64.b64decode(cursor + padding, altchars=b"-_", validate=True)
        payload = json.loads(decoded.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor is not valid URL-safe JSON")
    if not isinstance(payload, dict):
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor must contain an object")
    typed_payload = cast(dict[str, object], payload)
    required_fields = {
        "version",
        "ordering",
        "request_identity",
        "source_snapshot_identity",
        "last_key",
    }
    if set(typed_payload) != required_fields:
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor has an unsupported shape")
    version = typed_payload["version"]
    ordering = typed_payload["ordering"]
    request_identity = typed_payload["request_identity"]
    snapshot_identity = typed_payload["source_snapshot_identity"]
    last_key = typed_payload["last_key"]
    if not isinstance(version, str):
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor text fields must be strings")
    if not isinstance(ordering, str):
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor text fields must be strings")
    if not isinstance(request_identity, str):
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor text fields must be strings")
    if not isinstance(snapshot_identity, str):
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor text fields must be strings")
    if not isinstance(last_key, list):
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor key must be a list")
    try:
        parsed_ordering = ReplayOrdering(ordering)
    except ValueError:
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor ordering is unsupported")
    return _DecodedCursor(version, parsed_ordering, request_identity, snapshot_identity, last_key)


def _decode_ordering_key(raw: object, ordering: ReplayOrdering) -> _OrderingKey:
    if not isinstance(raw, list):
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor key must be a list")
    expected_length = 2 if ordering is ReplayOrdering.ARRIVAL else 3
    if len(raw) != expected_length:
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor key has the wrong shape")
    capture_id = raw[-1]
    numeric_values = raw[:-1]
    if not all(_is_int(value) for value in numeric_values) or not isinstance(capture_id, str):
        _raise(ReplayErrorCode.INVALID_CURSOR, "cursor capture ID must be a string")
    if ordering is ReplayOrdering.ARRIVAL:
        return (numeric_values[0], capture_id)
    return (numeric_values[0], numeric_values[1], capture_id)


def _continue_after(
    selected: tuple[_QualifiedRecord, ...],
    ordering: ReplayOrdering,
    last_key: _OrderingKey | None,
) -> tuple[_QualifiedRecord, ...]:
    if last_key is None:
        return selected
    return tuple(
        item
        for item in selected
        if _ordering_key(item.source_record, ordering) > last_key
    )


def _ordering_key(record: ReplaySourceRecord, ordering: ReplayOrdering) -> _OrderingKey:
    fact = record.capture_fact
    if ordering is ReplayOrdering.ARRIVAL:
        return (fact.received_timestamp, fact.capture_id)
    if fact.provider_timestamp is None:
        _raise(ReplayErrorCode.UNSUPPORTED_EVENT_TIME, "strict event ordering needs provider timestamp")
    return (fact.provider_timestamp, fact.received_timestamp, fact.capture_id)


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _is_int(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _invalid_request(message: str) -> NoReturn:
    _raise(ReplayErrorCode.INVALID_REQUEST, message)


def _raise(code: ReplayErrorCode, message: str) -> NoReturn:
    raise ReplayAsOfError(code, message)
