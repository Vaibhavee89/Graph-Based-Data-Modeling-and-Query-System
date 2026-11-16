"""Simple in-memory sliding-window rate limiter (per client, per process)."""
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, Request

from app.config import settings


class RateLimiter:
    """Allow at most `limit` calls per `window` seconds for each key."""

    def __init__(self, limit: int, window: float = 60.0):
        self.limit = limit
        self.window = window
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> float:
        """Record a hit. Returns 0 if allowed, else seconds until a slot frees."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return self.window - (now - hits[0])
            hits.append(now)

            # Drop idle keys so the dict can't grow without bound
            if len(self._hits) > 10_000:
                for k in [k for k, v in self._hits.items() if not v or now - v[-1] >= self.window]:
                    del self._hits[k]
            return 0.0


def client_key(request: Request) -> str:
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


_chat_limiter = RateLimiter(limit=settings.rate_limit_per_minute)


def rate_limit_chat(request: Request) -> None:
    """FastAPI dependency: 429 when a client exceeds the chat rate limit."""
    retry_after = _chat_limiter.check(client_key(request))
    if retry_after > 0:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment and try again.",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )
