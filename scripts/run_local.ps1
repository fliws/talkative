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
