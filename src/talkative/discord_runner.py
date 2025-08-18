from __future__ import annotations

import asyncio
import os
import random
import time
from typing import Dict, List, Optional

import discord
from aiolimiter import AsyncLimiter
from loguru import logger

from .config import HarnessConfig
from .metrics import (
    DISCORD_ERRORS,
    MESSAGES_BLOCKED,
    MESSAGES_DUPLICATE_SKIPPED,
    MESSAGES_POSTED,
    MESSAGES_SEEN,
    REPLY_LATENCY,
)
from .openai_client import OpenAIClient
from .safety import SafetyGuards
from .state import GlobalState


def build_intents(cfg: HarnessConfig) -> discord.Intents:
    intents = discord.Intents.none()
    intents.guilds = True
    intents.messages = True
    intents.message_content = cfg.discord.intents_message_content
    return intents


class BotClient(discord.Client):
    def __init__(self, bot_index: int, persona: str, cfg: HarnessConfig, 
                 openai_client: OpenAIClient, state: GlobalState, safety: SafetyGuards, 
                 limiter: AsyncLimiter, dry_run: bool):
        super().__init__(intents=build_intents(cfg))
        self.bot_index = bot_index
        self.persona = persona
        self.cfg = cfg
        self.oa = openai_client
        self.state = state
        self.safety = safety
        self.limiter = limiter
        self.dry_run = dry_run
        self.bot_id: Optional[int] = None
        self.topic = cfg.runtime.topic

    async def on_ready(self):
        self.bot_id = self.user.id if self.user else None
        logger.info(f"Bot {self.bot_index} ready as {self.user}")
        # Seed initial messages across all text channels using the first bot only
        if self.bot_index == 0:
            await self._seed_all_channels()

    async def _seed_all_channels(self):
        for guild in list(self.guilds):
            for channel in guild.text_channels:
                ch_state = self.state.get_channel(guild.id, channel.id)
                async with ch_state.lock:
                    if ch_state.count > 0 or ch_state.count >= ch_state.cap:
                        continue
                await asyncio.sleep(0.2)
                try:
                    await self._post_seed_message(guild, channel)
                except Exception as e:
                    DISCORD_ERRORS.labels(type=e.__class__.__name__).inc()
                    logger.error(f"Seed post failed: {e}")

    async def _post_seed_message(self, guild: discord.Guild, channel: discord.TextChannel):
        ch_state = self.state.get_channel(guild.id, channel.id)
        guild_name = guild.name
        channel_name = channel.name
        content = (
            f"Kickoff: Let's discuss '{self.topic}'. I'll start—what's your take?"
        )
        # Moderation and dedupe
        if self.cfg.runtime.moderation_enabled and await self.oa.moderate(content):
            MESSAGES_BLOCKED.labels(guild=guild_name, channel=channel_name, bot=str(self.bot_index)).inc()
            return
        if self.safety.is_duplicate(content):
            MESSAGES_DUPLICATE_SKIPPED.labels(guild=guild_name, channel=channel_name, bot=str(self.bot_index)).inc()
            return
        async with ch_state.lock:
            if ch_state.count >= ch_state.cap:
                return
            ch_state.count += 1
            ch_state.history.append({"role": "assistant", "content": content})
        if self.dry_run:
            logger.info(f"[DRY-RUN] Seed to #{channel_name}: {content[:120]}...")
        else:
            await channel.send(content)
            MESSAGES_POSTED.labels(guild=guild_name, channel=channel_name, bot=str(self.bot_index)).inc()

    async def on_message(self, message: discord.Message):
        if self.user and message.author.id == self.user.id:  # ignore self
            return

        guild = message.guild
        channel = message.channel
        if not isinstance(channel, discord.TextChannel) or guild is None:
            return

        guild_name = guild.name
        channel_name = channel.name

        # Admin restart command
        admin_secret = self.cfg.runtime.admin_secret
        if admin_secret and message.content.strip() == admin_secret:
            logger.info("Admin restart signal received")
            self.state.restart_event.set()
            return

        # Respect per-channel cap
        ch_state = self.state.get_channel(guild.id, channel.id)
        async with ch_state.lock:
            if ch_state.count >= ch_state.cap:
                return
            # Append message into history
            role = "assistant" if message.author.bot else "user"
            ch_state.history.append({"role": role, "content": message.content})

        MESSAGES_SEEN.labels(guild=guild_name, channel=channel_name, bot=str(self.bot_index)).inc()

        # Anti-bot streak
        if message.author.bot:
            if not self.safety.on_bot_message(guild.id, channel.id):
                return
        else:
            self.safety.reset_streak(guild.id, channel.id)

        # Per-bot cooldown
        if not self.safety.can_post(guild.id, channel.id, str(self.bot_index)):
            return

        # Wait fixed delay
        await asyncio.sleep(self.cfg.runtime.reply_delay)

        # Build prompt and maybe summarize
        sys_prompt = (
            f"You are bot #{self.bot_index}. Persona: {self.persona}. "
            f"Stay strictly on the shared topic: '{self.topic}'. Be concise."
        )
        # Summarize if history is near limit
        need_summary = False
        history_snapshot: List[Dict[str, str]] = []
        async with ch_state.lock:
            if ch_state.history.maxlen and len(ch_state.history) >= (ch_state.history.maxlen - 1):
                history_snapshot = list(ch_state.history)
                need_summary = True
        if need_summary:
            try:
                summary = await self.oa.summarize(self.topic, history_snapshot)
                async with ch_state.lock:
                    last = list(ch_state.history)[-5:]
                    ch_state.history.clear()
                    ch_state.history.append({"role": "system", "content": f"Summary so far: {summary}"})
                    for it in last:
                        ch_state.history.append(it)
            except Exception as e:
                logger.warning(f"Summarization failed: {e}")
        messages = [{"role": "system", "content": sys_prompt}]
        messages.extend(list(ch_state.history))

        # Generate reply via OpenAI
        start = time.perf_counter()
        try:
            async with self.limiter:
                reply = await self.oa.chat(messages)
        except Exception as e:
            DISCORD_ERRORS.labels(type="openai").inc()
            logger.error(f"OpenAI error: {e}")
            return
        finally:
            REPLY_LATENCY.observe(time.perf_counter() - start)

        # Moderation
        if self.cfg.runtime.moderation_enabled:
            flagged = await self.oa.moderate(reply)
            if flagged:
                MESSAGES_BLOCKED.labels(guild=guild_name, channel=channel_name, bot=str(self.bot_index)).inc()
                logger.warning("Reply blocked by moderation")
                return

        # Deduplicate
        if self.safety.is_duplicate(reply):
            MESSAGES_DUPLICATE_SKIPPED.labels(guild=guild_name, channel=channel_name, bot=str(self.bot_index)).inc()
            return

        # Post if under cap
        async with ch_state.lock:
            if ch_state.count >= ch_state.cap:
                return
            ch_state.count += 1
            ch_state.history.append({"role": "assistant", "content": reply})

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would post to #{channel_name}: {reply[:120]}...")
        else:
            try:
                await channel.send(reply)
                MESSAGES_POSTED.labels(guild=guild_name, channel=channel_name, bot=str(self.bot_index)).inc()
            except Exception as e:
                DISCORD_ERRORS.labels(type=e.__class__.__name__).inc()
                logger.error(f"Discord send error: {e}")
                return

        # Cooldown to avoid fast loops
        self.safety.cooldown(guild.id, channel.id, str(self.bot_index), self.cfg.runtime.reply_delay)


async def run_bots(cfg: HarnessConfig) -> None:
    oa = OpenAIClient(
        cfg.openai.api_key,
        cfg.openai.model,
        cfg.openai.max_output_tokens,
        token_logging=cfg.logging.token_usage,
    )
    safety = SafetyGuards()
    state = GlobalState(cap=cfg.runtime.message_cap_per_channel)

    # OpenAI rate limiter
    rps = int(os.getenv("OPENAI_RPS", "3"))
    limiter = AsyncLimiter(rps, 1)

    personas: List[str] = cfg.personas
    if not personas or len(personas) < len(cfg.discord.bot_tokens):
        # pad with generic personas
        while len(personas) < len(cfg.discord.bot_tokens):
            idx = len(personas) + 1
            personas.append(f"Helpful engineer #{idx} focused on the topic.")

    clients: List[BotClient] = []
    tasks: List[asyncio.Task] = []

    for i, token in enumerate(cfg.discord.bot_tokens):
        persona = personas[i]
        client = BotClient(i, persona, cfg, oa, state, safety, limiter, cfg.runtime.dry_run)
        clients.append(client)
        tasks.append(asyncio.create_task(client.start(token)))

    async def restart_monitor():
        while True:
            await state.restart_event.wait()
            logger.info("Restart signal received: resetting channel counters and histories")
            for ch_key, ch_state in list(state.channels.items()):
                async with ch_state.lock:
                    ch_state.count = 0
                    ch_state.history.clear()
            state.restart_event.clear()

    monitor_task = asyncio.create_task(restart_monitor())
    await asyncio.gather(*tasks, monitor_task)

