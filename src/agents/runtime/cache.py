from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CacheEntry:
    value: Any
    created_at: float
    ttl_seconds: int

    def is_valid(self) -> bool:
        return (time.time() - self.created_at) < self.ttl_seconds


def build_cache_key(prefix: str, payload: Any) -> str:
    serialized = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    raw = f"{prefix}:{serialized}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class TTLCache:
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._entries: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._entries.get(key)
            if not entry:
                return None
            if entry.is_valid():
                return entry.value
            del self._entries[key]
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds or self.ttl_seconds
        with self._lock:
            self._entries[key] = CacheEntry(value=value, created_at=time.time(), ttl_seconds=ttl)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._entries:
                del self._entries[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def stats(self) -> dict[str, Any]:
        with self._lock:
            valid = 0
            expired = 0
            for entry in self._entries.values():
                if entry.is_valid():
                    valid += 1
                else:
                    expired += 1
            return {
                "total_entries": len(self._entries),
                "valid_entries": valid,
                "expired_entries": expired,
                "ttl_seconds": self.ttl_seconds,
            }
