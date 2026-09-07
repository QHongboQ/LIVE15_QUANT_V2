"""QuestDB Store-and-Forward implementation of the Durable Persistence seam."""

import os
import re
from collections.abc import Iterator
from typing import Any

import questdb

from live15_quant_v2.data.storage.capture import CaptureFact
from live15_quant_v2.data.storage.durable_persistence import (
    PersistenceResult,
    PersistenceStatus,
)

_TABLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


class QuestDBSFDurablePersistence:
    """Persist immutable capture facts through the pinned QuestDB SF client."""

    def __init__(
        self,
        *,
        connection_string: str,
        table_name: str,
        sf_dir: str | os.PathLike[str],
        sender_id: str,
        acknowledgement_timeout_millis: int,
    ) -> None:
        if not _TABLE_NAME.fullmatch(table_name):
            raise ValueError("table_name must be a simple SQL identifier")
        if not sender_id:
            raise ValueError("sender_id must be non-empty")
        if not isinstance(acknowledgement_timeout_millis, int) or isinstance(
            acknowledgement_timeout_millis, bool
        ):
            raise TypeError("acknowledgement_timeout_millis must be an int")
        if acknowledgement_timeout_millis < 0:
            raise ValueError("acknowledgement_timeout_millis must be non-negative")

        self._connection_string = connection_string
        self._table_name = table_name
        self._sf_dir = os.fspath(sf_dir)
        self._sender_id = sender_id
        self._acknowledgement_timeout_millis = acknowledgement_timeout_millis
        self._database: questdb.QuestDB | None = None

    def close(self) -> None:
        """Release the upstream connection pool without publishing new work."""

        if self._database is not None:
            self._database.close()
            self._database = None

    def persist(self, fact: CaptureFact) -> PersistenceResult:
        """Publish one fact to local SF and interpret its current upstream outcome."""

        try:
            database = self._database_for_use()
            sender = database.sender()
        except (OSError, questdb.QuestDBError) as error:
            return self._pre_publication_failure(error)

        try:
            database_dropped_before = database.error_events_dropped
            sender_dropped_before = sender.error_events_dropped()
            sender.row(
                self._table_name,
                symbols={
                    "asset": fact.asset.value,
                    "provider": fact.provider,
                    "channel": fact.channel,
                },
                columns={
                    "capture_id": fact.capture_id,
                    "source_id": fact.source_id,
                    "message_type": fact.message_type,
                    "event_subtype": fact.event_subtype,
                    "sid": fact.sid,
                    "seq": fact.seq,
                    "provider_timestamp": (
                        None
                        if fact.provider_timestamp is None
                        else questdb.TimestampNanos(fact.provider_timestamp)
                    ),
                    "schema_version": fact.schema_version,
                    "payload": fact.payload,
                },
                at=questdb.TimestampNanos(fact.received_timestamp),
            )
            fsn = sender.flush_and_get_fsn()
        except (OSError, questdb.QuestDBError) as error:
            self._close_sender(sender)
            return self._pre_publication_failure(error)

        if fsn is None:
            self._close_sender(sender)
            return PersistenceResult(PersistenceStatus.IN_DOUBT)

        try:
            acknowledged = sender.await_acked_fsn(
                fsn, timeout_millis=self._acknowledgement_timeout_millis
            )
            rejection_status = self._rejection_status(sender, fsn)
            diagnostic_loss = (
                sender.error_events_dropped() != sender_dropped_before
                or database.error_events_dropped != database_dropped_before
            )
        except (OSError, questdb.QuestDBError):
            self._close_sender(sender)
            return PersistenceResult(PersistenceStatus.PERSISTED_PENDING)

        self._close_sender(sender)
        if rejection_status is not None:
            return PersistenceResult(rejection_status)
        if diagnostic_loss:
            return PersistenceResult(PersistenceStatus.IN_DOUBT)
        if not acknowledged:
            return PersistenceResult(PersistenceStatus.PERSISTED_PENDING)
        return PersistenceResult(PersistenceStatus.ACKNOWLEDGED_OK)

    def _database_for_use(self) -> questdb.QuestDB:
        if self._database is None:
            self._database = questdb.connect(
                self._connection_string,
                sf_dir=self._sf_dir,
                sender_id=self._sender_id,
                sf_durability="memory",
                auto_flush=False,
            )
        return self._database

    @staticmethod
    def _pre_publication_failure(error: BaseException) -> PersistenceResult:
        if getattr(error, "in_doubt", False):
            return PersistenceResult(PersistenceStatus.IN_DOUBT)
        return PersistenceResult(PersistenceStatus.LOCAL_PERSISTENCE_FAILED)

    @staticmethod
    def _close_sender(sender: Any) -> None:
        sender.close(flush=False)

    @staticmethod
    def _rejection_status(sender: Any, fsn: int) -> PersistenceStatus | None:
        status: PersistenceStatus | None = None
        for error in _sender_errors(sender):
            if not error.from_fsn <= fsn <= error.to_fsn:
                continue
            if error.applied_policy is questdb.SenderErrorPolicy.Terminal:
                status = PersistenceStatus.DEFINITELY_REJECTED
            elif status is None:
                status = PersistenceStatus.PERSISTED_PENDING
        return status


def _sender_errors(sender: Any) -> Iterator[Any]:
    while (error := sender.poll_error()) is not None:
        yield error
