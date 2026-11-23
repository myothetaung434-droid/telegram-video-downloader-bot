# Start from the extracted folder (Windows PowerShell 5.1 compatible).
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Get-Command node.exe -ErrorAction SilentlyContinue)) { throw 'Node.js 20+ is required.' }
if (-not (Get-Command python.exe -ErrorAction SilentlyContinue)) { throw 'Python 3 is required.' }
$versionText = (& node.exe --version).Trim()
if ($LASTEXITCODE -ne 0 -or $versionText -notmatch '^v(\d+)\.') { throw 'Cannot read Node.js version' }
if ([int]$Matches[1] -lt 20) { throw 'Node.js 20 or newer is required.' }

& python.exe -c 'import requests'
if ($LASTEXITCODE -ne 0) { & python.exe -m pip install requests; if ($LASTEXITCODE -ne 0) { throw 'Python requests installation failed.' } }
& python.exe -m py_compile (Join-Path $PSScriptRoot 'bot.py')
if ($LASTEXITCODE -ne 0) { throw 'Python bot syntax check failed.' }
& node.exe --check (Join-Path $PSScriptRoot 'rednote-downloader\src\xhs.js')
if ($LASTEXITCODE -ne 0) { throw 'Downloader syntax check failed.' }

# Select a free loopback port so an old server cannot silently serve stale code.
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
$listener.Start()
$port = $listener.LocalEndpoint.Port
$listener.Stop()
$env:PORT = [string]$port
$env:HOST = '127.0.0.1'
$env:REDNOTE_LOCAL_API = "http://127.0.0.1:$port"
$env:MEDIA_REQUEST_TIMEOUT_MS = '30000'
$env:MEDIA_DOWNLOAD_RETRY_COUNT = '2'
$serverUrl = "http://127.0.0.1:$port/"
$srvDir = Join-Path $PSScriptRoot 'rednote-downloader'
$stdout = Join-Path $PSScriptRoot 'rednote-server.out.log'
$stderr = Join-Path $PSScriptRoot 'rednote-server.err.log'
$serverProcess = Start-Process -FilePath (Get-Command node.exe).Source -ArgumentList @('src/server.js') -WorkingDirectory $srvDir -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
$ready = $false
for ($attempt = 0; $attempt -lt 20; $attempt++) {
  Start-Sleep -Milliseconds 500
  if ($serverProcess.HasExited) { break }
  try { $r = Invoke-WebRequest -UseBasicParsing $serverUrl -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ready = $true; break } } catch { }
}
if (-not $ready) { throw "Downloader not responding. See $stderr" }
Write-Host "Downloader HTTP 200 (port $port; this does not confirm a video download)." 

# Keep only a public channel name, not credentials. Avoid repeated prompts on subsequent launches.
$channelFile = Join-Path $PSScriptRoot 'channel.txt'
if (Test-Path $channelFile) { $channel = (Get-Content $channelFile -Raw).Trim() } else { $channel = '' }
if ($channel -notmatch '^@[A-Za-z0-9_]{5,}$') {
  $channel = (Read-Host 'Public Telegram channel username (e.g. @FreeShareMM)').Trim()
  if ($channel -notmatch '^@[A-Za-z0-9_]{5,}$') { throw 'Invalid channel name' }
  Set-Content -Path $channelFile -Value $channel -Encoding ASCII
}
$env:CHANNEL_USERNAME = $channel
$secure = Read-Host 'Telegram bot token (hidden; do not screenshot)' -AsSecureString
$env:BOT_TOKEN = [System.Net.NetworkCredential]::new('', $secure).Password
$secure.Dispose()
try { & python.exe (Join-Path $PSScriptRoot 'bot.py') }
finally {
  Remove-Item Env:BOT_TOKEN -ErrorAction SilentlyContinue
  if ($serverProcess -and -not $serverProcess.HasExited) { Stop-Process -Id $serverProcess.Id -ErrorAction SilentlyContinue }
}
