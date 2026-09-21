from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shadowflow.models import MergePacket, RunRecord, RunStage


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class RunStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    status_message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    packet_json TEXT,
                    events_json TEXT NOT NULL,
                    approval_json TEXT
                )
                """
            )

    def create(self, run_id: str, provider: str) -> RunRecord:
        now = now_iso()
        record = RunRecord(
            id=run_id,
            stage=RunStage.QUEUED,
            status_message="Queued",
            provider=provider,
            created_at=now,
            updated_at=now,
        )
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (run_id, provider, record.stage.value, record.status_message, now, now, None, "[]", None),
            )
        return record

    def update(
        self,
        run_id: str,
        *,
        stage: RunStage | None = None,
        status_message: str | None = None,
        event: dict[str, Any] | None = None,
        packet: MergePacket | None = None,
        approval: dict[str, Any] | None = None,
    ) -> None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(run_id)
            events = json.loads(row["events_json"])
            if event:
                events.append({"at": now_iso(), **event})
            conn.execute(
                """
                UPDATE runs
                SET stage = ?, status_message = ?, updated_at = ?, packet_json = ?, events_json = ?, approval_json = ?
                WHERE id = ?
                """,
                (
                    (stage or RunStage(row["stage"])).value,
                    status_message if status_message is not None else row["status_message"],
                    now_iso(),
                    packet.model_dump_json() if packet is not None else row["packet_json"],
                    json.dumps(events, ensure_ascii=False),
                    json.dumps(approval, ensure_ascii=False) if approval is not None else row["approval_json"],
                    run_id,
                ),
            )

    def get(self, run_id: str) -> RunRecord:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        packet = MergePacket.model_validate_json(row["packet_json"]) if row["packet_json"] else None
        approval = json.loads(row["approval_json"]) if row["approval_json"] else None
        return RunRecord(
            id=row["id"],
            stage=RunStage(row["stage"]),
            status_message=row["status_message"],
            provider=row["provider"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            packet=packet,
            events=json.loads(row["events_json"]),
            approval=approval,
        )

    def list(self, limit: int = 20) -> list[RunRecord]:
        with self._lock, self._connect() as conn:
            ids = [row["id"] for row in conn.execute("SELECT id FROM runs ORDER BY created_at DESC LIMIT ?", (limit,))]
        return [self.get(run_id) for run_id in ids]
