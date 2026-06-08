from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditHistoryStore:
    def __init__(self, history_path: Path):
        self.history_path = history_path
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _read(self) -> list[dict[str, Any]]:
        if not self.history_path.exists():
            return []
        try:
            payload = json.loads(self.history_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return payload
        except Exception:
            return []
        return []

    def _write(self, entries: list[dict[str, Any]]) -> None:
        self.history_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    def record(self, entry: dict[str, Any]) -> dict[str, Any]:
        payload = dict(entry)
        payload.setdefault("timestamp", _utc_now())
        with self._lock:
            entries = self._read()
            entries.append(payload)
            self._write(entries)
        return payload

    def list_entries(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            entries = self._read()
            return entries[-limit:]

    def stats(self, limit: int = 1000) -> dict[str, Any]:
        entries = self.list_entries(limit=limit)
        by_event: dict[str, int] = {}
        scores: list[int] = []
        for entry in entries:
            event_type = str(entry.get("event_type", "unknown"))
            by_event[event_type] = by_event.get(event_type, 0) + 1
            score = entry.get("score")
            if isinstance(score, int):
                scores.append(score)
        return {
            "total_entries": len(entries),
            "by_event_type": by_event,
            "average_score": round(sum(scores) / len(scores), 2) if scores else None,
            "history_path": str(self.history_path),
        }
