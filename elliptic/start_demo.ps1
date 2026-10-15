$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Join-Path $PSScriptRoot 'site\dist')
Write-Host 'Elliptic demo: http://127.0.0.1:8767'
Write-Host 'Press Ctrl+C to stop.'
python -m http.server 8767 --bind 127.0.0.1
