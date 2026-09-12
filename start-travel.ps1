$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'web/dist/index.html'))) {
    Write-Host '请先在 web 目录运行 npm install 和 npm run build。'
    exit 1
}
Write-Host '慢游旅行助手启动后，请打开 http://127.0.0.1:8766'
python serve.py --host 127.0.0.1 --port 8766
