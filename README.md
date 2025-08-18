# Talkative Harness

Discord multi-bot conversation harness for debugging and generating controlled traffic.

## Features
- Multiple Discord bots converse across all text channels
- Topic-driven, persona prompts per bot
- OpenAI-generated replies with moderation
- Fixed reply delay, per-channel message caps
- Structured logs and optional Prometheus metrics
- Dry-run mode, sandbox server, deterministic seeding
- Containerized with health/metrics endpoints

## Quick start
1. Prepare environment variables (see below).
2. Provide a `configs/config.example.yaml` or env-only config.
3. Build and run the container.

## Environment
- DISCORD_BOT_TOKENS: comma-separated list of tokens (>=1)
- OPENAI_API_KEY: OpenAI API key
- TOPIC: shared topic string
- PERSONAS_JSON: JSON array of per-bot prompt strings (len matches tokens) or leave empty to use defaults
- REPLY_DELAY: seconds (float)
- MESSAGE_CAP_PER_CHANNEL: integer
- LOG_LEVEL: DEBUG|INFO|WARNING|ERROR
- LOG_TOKEN_USAGE: true|false
- MODERATION_ENABLED: true|false
- DRY_RUN: true|false
- METRICS_PORT: integer (optional)
- HEALTH_PORT: integer (optional)
- ADMIN_SECRET: secret word to restart conversations

## Local run
- Python: 3.11+
```powershell
python -m venv .venv; . .venv/Scripts/Activate.ps1
pip install -e .[dev]
python -m talkative.run
```

## Docker
```powershell
# Build
docker build -t talkative-harness:latest -f ops/Dockerfile .
# Run
docker run --rm -e DISCORD_BOT_TOKENS=token1,token2 -e OPENAI_API_KEY=sk-... -e TOPIC="Observability in microservices" -e REPLY_DELAY=3 -e MESSAGE_CAP_PER_CHANNEL=50 talkative-harness:latest
```

## Kubernetes
See `ops/k8s/` for examples; configure secrets and limits accordingly.
