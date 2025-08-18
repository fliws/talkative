from talkative.config import load_config
import os
import pytest


def test_load_config_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-xxx")
    monkeypatch.setenv("DISCORD_BOT_TOKENS", "a,b")
    cfg = load_config()
    assert cfg.openai.api_key == "sk-xxx"
    assert len(cfg.discord.bot_tokens) == 2
