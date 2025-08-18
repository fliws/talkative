from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class LoggingConfig(BaseModel):
    level: str = Field(default="INFO")
    token_usage: bool = Field(default=True)


class RuntimeConfig(BaseModel):
    topic: str = Field(default="General debugging topic")
    reply_delay: float = Field(default=3.0)
    message_cap_per_channel: int = Field(default=50)
    moderation_enabled: bool = Field(default=True)
    dry_run: bool = Field(default=False)
    metrics_port: Optional[int] = Field(default=8000)
    health_port: Optional[int] = Field(default=8001)
    admin_secret: Optional[str] = None


class OpenAIConfig(BaseModel):
    api_key: str
    model: str = Field(default="gpt-4o-mini")
    max_output_tokens: int = Field(default=200)


class DiscordConfig(BaseModel):
    bot_tokens: List[str] = Field(default_factory=list)
    intents_message_content: bool = Field(default=True)


class HarnessConfig(BaseModel):
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    openai: OpenAIConfig
    discord: DiscordConfig
    personas: List[str] = Field(default_factory=list)

    @field_validator("personas")
    @classmethod
    def validate_personas(cls, v, info):  # type: ignore[no-untyped-def]
        if not isinstance(v, list):
            return []
        return [str(x) for x in v]


def load_config() -> HarnessConfig:
    # Load from env first; optional JSON for personas
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required")
    tokens_env = os.getenv("DISCORD_BOT_TOKENS", "")
    bot_tokens = [t.strip() for t in tokens_env.split(",") if t.strip()]
    if not bot_tokens:
        raise RuntimeError("At least one DISCORD_BOT_TOKENS is required")

    persons_json = os.getenv("PERSONAS_JSON")
    personas: List[str] = []
    if persons_json:
        try:
            data = json.loads(persons_json)
            if isinstance(data, list):
                personas = [str(x) for x in data]
        except json.JSONDecodeError:
            personas = []

    topic = os.getenv("TOPIC", "General debugging topic")
    reply_delay = float(os.getenv("REPLY_DELAY", "3"))
    cap = int(os.getenv("MESSAGE_CAP_PER_CHANNEL", "50"))
    moderation_enabled = os.getenv("MODERATION_ENABLED", "true").lower() == "true"
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    metrics_port = int(os.getenv("METRICS_PORT", "8000")) if os.getenv("METRICS_PORT") else None
    health_port = int(os.getenv("HEALTH_PORT", "8001")) if os.getenv("HEALTH_PORT") else None
    admin_secret = os.getenv("ADMIN_SECRET")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "200"))

    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_token_usage = os.getenv("LOG_TOKEN_USAGE", "true").lower() == "true"

    intents_message_content = os.getenv("INTENTS_MESSAGE_CONTENT", "true").lower() == "true"

    return HarnessConfig(
        logging=LoggingConfig(level=log_level, token_usage=log_token_usage),
        runtime=RuntimeConfig(
            topic=topic,
            reply_delay=reply_delay,
            message_cap_per_channel=cap,
            moderation_enabled=moderation_enabled,
            dry_run=dry_run,
            metrics_port=metrics_port,
            health_port=health_port,
            admin_secret=admin_secret,
        ),
        openai=OpenAIConfig(api_key=api_key, model=model, max_output_tokens=max_output_tokens),
        discord=DiscordConfig(bot_tokens=bot_tokens, intents_message_content=intents_message_content),
        personas=personas,
    )
