from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .schemas import AuditSchema


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RegistryEntry:
    schema_id: str
    audit_type: str
    name: str
    version: str
    source_url: str
    source_title: str
    criteria_count: int
    storage_path: str
    created_at: str
    updated_at: str
    metadata: dict[str, Any]


class AuditRegistry:
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _read_index(self) -> list[dict[str, Any]]:
        if not self.registry_path.exists():
            return []
        try:
            payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                entries = payload.get("entries", [])
                return entries if isinstance(entries, list) else []
            if isinstance(payload, list):
                return payload
        except Exception:
            return []
        return []

    def _write_index(self, entries: list[dict[str, Any]]) -> None:
        payload = {"entries": entries, "updated_at": _utc_now()}
        self.registry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _coerce_schema(self, schema: AuditSchema | dict[str, Any]) -> dict[str, Any]:
        if isinstance(schema, AuditSchema):
            return schema.model_dump(mode="json")
        return dict(schema)

    def register_schema(self, schema: AuditSchema | dict[str, Any], storage_path: str | None = None) -> RegistryEntry:
        payload = self._coerce_schema(schema)
        schema_id = str(payload["schema_id"])
        now = _utc_now()
        entry = RegistryEntry(
            schema_id=schema_id,
            audit_type=str(payload.get("audit_type", "unknown")),
            name=str(payload.get("name", schema_id)),
            version=str(payload.get("version", "1.0")),
            source_url=str(payload.get("source_url", "")),
            source_title=str(payload.get("source_title", "")),
            criteria_count=len(payload.get("criteria", []) or []),
            storage_path=str(storage_path or payload.get("metadata", {}).get("saved_path", "")),
            created_at=now,
            updated_at=now,
            metadata=dict(payload.get("metadata", {})),
        )

        with self._lock:
            entries = self._read_index()
            replaced = False
            for index, item in enumerate(entries):
                if item.get("schema_id") == schema_id:
                    created_at = item.get("created_at", now)
                    entries[index] = {**asdict(entry), "created_at": created_at}
                    replaced = True
                    break
            if not replaced:
                entries.append(asdict(entry))
            self._write_index(entries)
        return entry

    def list_entries(self) -> list[dict[str, Any]]:
        with self._lock:
            entries = self._read_index()
            return sorted(entries, key=lambda item: item.get("updated_at", ""), reverse=True)

    def get_entry(self, schema_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            for item in self._read_index():
                if item.get("schema_id") == schema_id:
                    return item
        return None

    def remove_entry(self, schema_id: str) -> bool:
        with self._lock:
            entries = self._read_index()
            filtered = [entry for entry in entries if entry.get("schema_id") != schema_id]
            if len(filtered) == len(entries):
                return False
            self._write_index(filtered)
            return True
