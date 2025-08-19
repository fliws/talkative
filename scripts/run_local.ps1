param(
  [string]$Tokens,
  [string]$OpenAIKey,
  [string]$Topic = "Observability in microservices",
  [int]$Cap = 20,
  [int]$Delay = 3,
  [switch]$DryRun
)

$env:PYTHONPATH = "$(Resolve-Path "$PSScriptRoot\..\src")"

$env:DISCORD_BOT_TOKENS=$Tokens
$env:OPENAI_API_KEY=$OpenAIKey
$env:TOPIC=$Topic
$env:MESSAGE_CAP_PER_CHANNEL=$Cap
$env:REPLY_DELAY=$Delay
$env:DRY_RUN= $(if ($DryRun) {"true"} else {"false"})

# --- Optional settings (uncomment to override defaults) ---
# $env:MODERATION_ENABLED = "true"           # Enable moderation (default: "true")
# $env:METRICS_PORT = "8000"                 # Metrics server port (default: 8000)
# $env:HEALTH_PORT = "8001"                  # Health check port (default: 8001)
# $env:ADMIN_SECRET = ""                     # Admin restart command (default: not set)
$env:OPENAI_MODEL = "gpt-5-nano"          # OpenAI model (default: "gpt-4o-mini")
$env:MAX_OUTPUT_TOKENS = "400"             # Max tokens per OpenAI response (default: 200)
# $env:LOG_LEVEL = "INFO"                    # Logging level (default: "INFO")
# $env:LOG_TOKEN_USAGE = "true"              # Log OpenAI token usage (default: "true")
# $env:INTENTS_MESSAGE_CONTENT = "true"      # Discord message content intent (default: "true")
# $env:PERSONAS_JSON = '["Bot A", "Bot B"]' # JSON array of bot personas (default: [])
# $env:OPENAI_RPS = "3"                      # OpenAI requests per second (default: 3)

# Friendly status output
$tokenCount = 0
if ($Tokens) {
  $tokenCount = ($Tokens -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ } | Measure-Object).Count
}
Write-Host ("Mode:        {0}" -f ($(if ($DryRun) { "DRY-RUN (no messages will be sent)" } else { "LIVE" }))) -ForegroundColor Cyan
Write-Host ("Tokens:      {0}" -f $tokenCount)
Write-Host ("Topic:       {0}" -f $Topic)
Write-Host ("Delay:       {0}s" -f $Delay)
Write-Host ("Cap/Channel: {0}" -f $Cap)
Write-Host ("PYTHONPATH:  {0}" -f $env:PYTHONPATH)

python -m talkative.run
