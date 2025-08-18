from __future__ import annotations

from prometheus_client import Counter, Histogram

# Counters
MESSAGES_SEEN = Counter(
    "h_messages_seen_total", "Total messages seen by all bots", ["guild", "channel", "bot"],
)
MESSAGES_POSTED = Counter(
    "h_messages_posted_total", "Total messages posted by bots", ["guild", "channel", "bot"],
)
MESSAGES_BLOCKED = Counter(
    "h_messages_blocked_total", "Messages blocked by moderation", ["guild", "channel", "bot"],
)
MESSAGES_DUPLICATE_SKIPPED = Counter(
    "h_messages_duplicate_skipped_total", "Near-duplicate messages skipped", ["guild", "channel", "bot"],
)
OPENAI_ERRORS = Counter(
    "h_openai_errors_total", "OpenAI API errors", ["type"],
)
DISCORD_ERRORS = Counter(
    "h_discord_errors_total", "Discord errors", ["type"],
)
OPENAI_TOKENS = Counter(
    "h_openai_tokens_total", "OpenAI token usage", ["type"],
)

# Histograms
OPENAI_LATENCY = Histogram(
    "h_openai_latency_seconds", "OpenAI API call latency", buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10)
)
REPLY_LATENCY = Histogram(
    "h_reply_latency_seconds", "End-to-end time from receipt to post", buckets=(0.5, 1, 2, 3, 5, 8, 13)
)
