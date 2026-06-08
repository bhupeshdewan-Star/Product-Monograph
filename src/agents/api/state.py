from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ..auditor.history import AuditHistoryStore
from ..auditor.registry import AuditRegistry
from ..runtime.cache import TTLCache
from ..runtime.rate_limit import SlidingWindowRateLimiter


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


@dataclass
class GlobalAgentsState:
    cache: TTLCache
    rate_limiter: SlidingWindowRateLimiter
    registry: AuditRegistry
    history: AuditHistoryStore


def create_state() -> GlobalAgentsState:
    package_root = Path(__file__).resolve().parents[1]
    registry_path = Path(
        os.getenv("GLOBAL_AGENTS_REGISTRY_PATH", str(package_root / "auditor" / "registry_index.json"))
    )
    history_path = Path(
        os.getenv("GLOBAL_AGENTS_HISTORY_PATH", str(package_root / "auditor" / "audit_history.json"))
    )
    cache_ttl = _env_int("GLOBAL_AGENTS_CACHE_TTL", 3600)
    rate_limit_requests = _env_int("GLOBAL_AGENTS_RATE_LIMIT_REQUESTS", 100)
    rate_limit_window = _env_int("GLOBAL_AGENTS_RATE_LIMIT_WINDOW", 60)

    return GlobalAgentsState(
        cache=TTLCache(ttl_seconds=cache_ttl),
        rate_limiter=SlidingWindowRateLimiter(
            max_requests=rate_limit_requests,
            window_seconds=rate_limit_window,
        ),
        registry=AuditRegistry(registry_path=registry_path),
        history=AuditHistoryStore(history_path=history_path),
    )


_STATE: GlobalAgentsState | None = None


def get_state() -> GlobalAgentsState:
    global _STATE
    if _STATE is None:
        _STATE = create_state()
    return _STATE
