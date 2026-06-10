from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config import EVIDENCE_CACHE_DIR


class EvidenceCache:
    def __init__(self, cache_dir: Path | None = None, ttl_seconds: int = 24 * 60 * 60) -> None:
        self.cache_dir = Path(cache_dir or EVIDENCE_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def make_key(self, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _path(self, cache_key: str) -> Path:
        return self.cache_dir / f"{cache_key}.json"

    def get(self, cache_key: str) -> Optional[dict[str, Any]]:
        path = self._path(cache_key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            created_at = datetime.fromisoformat(payload.get("_cached_at", ""))
            age = (datetime.now(timezone.utc) - created_at).total_seconds()
            if age > self.ttl_seconds:
                return None
            return payload
        except Exception:
            return None

    def set(self, cache_key: str, payload: dict[str, Any]) -> None:
        path = self._path(cache_key)
        cache_payload = dict(payload)
        cache_payload["_cached_at"] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(cache_payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    def clear(self) -> None:
        for item in self.cache_dir.glob("*.json"):
            try:
                item.unlink()
            except OSError:
                pass

    def stats(self) -> dict[str, Any]:
        files = list(self.cache_dir.glob("*.json"))
        return {
            "cache_dir": str(self.cache_dir),
            "entries": len(files),
            "ttl_seconds": self.ttl_seconds,
        }


evidence_cache = EvidenceCache()
