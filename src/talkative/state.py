from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from typing import Deque, Dict, List, Tuple


class ChannelState:
    def __init__(self, cap: int, max_context: int = 20):
        self.cap = cap
        self.count = 0
        self.history: Deque[Dict[str, str]] = deque(maxlen=max_context)
        self.lock = asyncio.Lock()


class GlobalState:
    def __init__(self, cap: int, max_context: int = 20):
        self.channels: Dict[Tuple[int, int], ChannelState] = {}
        self.cap = cap
        self.max_context = max_context
        self.restart_event = asyncio.Event()

    def get_channel(self, guild_id: int, channel_id: int) -> ChannelState:
        key = (guild_id, channel_id)
        if key not in self.channels:
            self.channels[key] = ChannelState(self.cap, self.max_context)
        return self.channels[key]
