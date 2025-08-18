from __future__ import annotations

import asyncio
from typing import Any, Dict, List, cast

from loguru import logger
from openai import OpenAI
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from .metrics import OPENAI_ERRORS, OPENAI_LATENCY, OPENAI_TOKENS


class OpenAIClient:
    def __init__(self, api_key: str, model: str, max_output_tokens: int = 200, token_logging: bool = True) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.token_logging = token_logging

    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        async for attempt in AsyncRetrying(
            wait=wait_exponential_jitter(initial=0.5, max=8.0),
            stop=stop_after_attempt(5),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        ):
            with attempt:
                with OPENAI_LATENCY.time():
                    try:
                        resp = await asyncio.to_thread(
                            self.client.chat.completions.create,
                            model=self.model,
                            messages=cast(Any, messages),
                            temperature=temperature,
                            max_tokens=self.max_output_tokens,
                        )
                    except Exception as e:  # pragma: no cover - network
                        OPENAI_ERRORS.labels(type=e.__class__.__name__).inc()
                        raise

                choice = resp.choices[0]
                text = choice.message.content or ""
                usage = getattr(resp, "usage", None)
                if usage:
                    OPENAI_TOKENS.labels(type="prompt").inc(getattr(usage, "prompt_tokens", 0) or 0)
                    OPENAI_TOKENS.labels(type="completion").inc(getattr(usage, "completion_tokens", 0) or 0)
                    OPENAI_TOKENS.labels(type="total").inc(getattr(usage, "total_tokens", 0) or 0)
                    if self.token_logging:
                        logger.bind(event="openai_usage").info(
                            {
                                "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                                "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
                                "total_tokens": getattr(usage, "total_tokens", 0) or 0,
                                "model": self.model,
                            }
                        )
                return text
        raise RuntimeError("OpenAI chat: exhausted retries without response")

    async def moderate(self, text: str) -> bool:
        """Return True if content is flagged and should be blocked."""
        try:
            result = await asyncio.to_thread(
                self.client.moderations.create,
                model="omni-moderation-latest",
                input=text[:5000],
            )
            out = result.results[0]
            return bool(getattr(out, "flagged", False))
        except Exception as e:  # pragma: no cover
            logger.warning(f"Moderation check failed: {e}")
            OPENAI_ERRORS.labels(type="moderation").inc()
            return False

    async def summarize(self, topic: str, history: List[Dict[str, str]]) -> str:
        sys = {
            "role": "system",
            "content": (
                "You are a concise summarizer for a Discord channel."
                " Produce a short bullet summary capturing the ongoing topic."
            ),
        }
        user = {
            "role": "user",
            "content": f"Topic: {topic}\nSummarize the following conversation briefly:",
        }
        msgs = [sys, user] + history[-20:]
        return await self.chat(msgs, temperature=0.3)
