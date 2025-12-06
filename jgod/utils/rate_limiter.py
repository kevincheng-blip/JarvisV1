from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional


logger = logging.getLogger(__name__)


@dataclass
class Bucket:
    """Store timestamps (epoch seconds) for a specific key."""
    timestamps: Deque[float] = field(default_factory=deque)


class RateLimiter:
    """
    Simple in-memory rate limiter for FinMind API.

    - minute_limit: max calls per rolling 60 seconds (default: 80, ~4800/hr)
    - hour_limit:   max calls per rolling 3600 seconds (default: 5800, conservative limit for 6000/hour plan)
    """

    def __init__(
        self,
        minute_limit: Optional[int] = 80,
        hour_limit: Optional[int] = 5800,
    ) -> None:
        self.minute_limit = minute_limit
        self.hour_limit = hour_limit
        self._lock = threading.Lock()
        self._buckets: Dict[str, Bucket] = {}
        
        # Debug log: 標記新的限速設定
        logger.debug(
            "RateLimiter initialized with limits: minute=%s, hour=%s (~%.0f calls/hr)",
            self.minute_limit,
            self.hour_limit,
            (self.minute_limit * 60) if self.minute_limit else 0,
        )

    def _get_bucket(self, key: str) -> Bucket:
        if key not in self._buckets:
            self._buckets[key] = Bucket()
        return self._buckets[key]

    def acquire(self, key: str = "default") -> None:
        """
        Block until a new call is allowed for the given key.
        Will respect both per-minute and per-hour limits.
        """
        while True:
            sleep_for = 0.0
            now = time.time()

            with self._lock:
                bucket = self._get_bucket(key)
                ts = bucket.timestamps

                # 清掉超過 1 小時的舊紀錄
                while ts and now - ts[0] > 3600:
                    ts.popleft()

                # 計算 hour limit
                hour_calls = len(ts)
                if self.hour_limit is not None and hour_calls >= self.hour_limit:
                    oldest_hour = ts[0]
                    # 距離 1 小時視窗重置還要多久
                    sleep_for = max(sleep_for, 3600 - (now - oldest_hour))

                # 計算 minute limit
                minute_calls = 0
                if self.minute_limit is not None:
                    # 只看最近 60 秒
                    # deque 可能有 1 小時內所有 call，要過濾
                    recent = [t for t in ts if now - t <= 60]
                    minute_calls = len(recent)
                    if minute_calls >= self.minute_limit:
                        oldest_minute = recent[0]
                        sleep_for = max(sleep_for, 60 - (now - oldest_minute))

                if sleep_for <= 0:
                    # 可以執行，記錄這次呼叫時間點
                    ts.append(now)
                    return

                # 需要 sleep，先記 log 再放鎖
                logger.info(
                    "RateLimiter[%s]: quota reached, "
                    "sleeping %.1f sec (minute=%s/%s, hour=%s/%s)",
                    key,
                    sleep_for,
                    minute_calls,
                    self.minute_limit,
                    hour_calls,
                    self.hour_limit,
                )

            # 真正 sleep 在 lock 外面
            time.sleep(sleep_for)
