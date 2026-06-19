"""
In-memory sliding window rate limiter.
"""
from collections import defaultdict
import time
import asyncio


class RateLimiter:
    def __init__(self):
        self.windows = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check(self, key_id: str, limit: int, window_seconds: int = 60) -> bool:
        async with self._lock:
            now = time.time()
            cutoff = now - window_seconds
            self.windows[key_id] = [t for t in self.windows[key_id] if t > cutoff]
            if len(self.windows[key_id]) >= limit:
                return False
            self.windows[key_id].append(now)
            return True
