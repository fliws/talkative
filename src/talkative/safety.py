from __future__ import annotations

import hashlib
import time
from collections import deque
from typing import Deque, Dict, Tuple


class SafetyGuards:
    def __init__(self, max_context: int = 20, dedupe_window: int = 10, bot_streak_cap: int = 5):
        self.max_context = max_context
        self.dedupe_window = dedupe_window
        self.bot_streak_cap = bot_streak_cap
        self.recent_hashes: Deque[str] = deque(maxlen=dedupe_window)
        self.bot_streak: Dict[Tuple[int, int], int] = {}  # (guild_id, channel_id) -> streak count
        self.cooldowns: Dict[Tuple[int, int, str], float] = {}  # (guild, channel, bot_id) -> until_ts

    def is_duplicate(self, text: str) -> bool:
        h = hashlib.sha256(text.strip().lower().encode()).hexdigest()[:16]
        if h in self.recent_hashes:
            return True
        self.recent_hashes.append(h)
        return False

    def can_post(self, guild_id: int, channel_id: int, bot_id: str) -> bool:
        now = time.time()
        key = (guild_id, channel_id, bot_id)
        until = self.cooldowns.get(key, 0)
        return now >= until

    def cooldown(self, guild_id: int, channel_id: int, bot_id: str, seconds: float) -> None:
        self.cooldowns[(guild_id, channel_id, bot_id)] = time.time() + seconds

    def on_bot_message(self, guild_id: int, channel_id: int) -> bool:
        key = (guild_id, channel_id)
        cur = self.bot_streak.get(key, 0) + 1
        self.bot_streak[key] = cur
        return cur <= self.bot_streak_cap

    def reset_streak(self, guild_id: int, channel_id: int) -> None:
        self.bot_streak[(guild_id, channel_id)] = 0
