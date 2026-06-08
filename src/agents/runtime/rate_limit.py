from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def allow(self, client_id: str) -> tuple[bool, dict[str, Any]]:
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            history = [stamp for stamp in self._requests[client_id] if stamp > cutoff]
            self._requests[client_id] = history

            if len(history) >= self.max_requests:
                return False, self._build_status(client_id, now=now, history=history)

            history.append(now)
            self._requests[client_id] = history
            return True, self._build_status(client_id, now=now, history=history)

    def _build_status(
        self,
        client_id: str,
        *,
        now: float | None = None,
        history: list[float] | None = None,
    ) -> dict[str, Any]:
        now = time.time() if now is None else now
        cutoff = now - self.window_seconds
        history = history if history is not None else [stamp for stamp in self._requests[client_id] if stamp > cutoff]
        remaining = max(0, self.max_requests - len(history))
        reset_in = self.window_seconds - (now - history[0]) if history else float(self.window_seconds)
        return {
            "client_id": client_id,
            "requests_used": len(history),
            "requests_limit": self.max_requests,
            "requests_remaining": remaining,
            "window_seconds": self.window_seconds,
            "reset_in_seconds": max(0.0, float(reset_in)),
        }

    def status(self, client_id: str) -> dict[str, Any]:
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            history = [stamp for stamp in self._requests[client_id] if stamp > cutoff]
            return self._build_status(client_id, now=now, history=history)

    def clear(self, client_id: str | None = None) -> None:
        with self._lock:
            if client_id is None:
                self._requests.clear()
            else:
                self._requests.pop(client_id, None)
