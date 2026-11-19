$ErrorActionPreference = 'Stop'
if ($env:A5_BANNER_SHOWN -ne '1') { Write-Host '解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利'; $env:A5_BANNER_SHOWN = '1' }
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
Set-Location -LiteralPath $PSScriptRoot
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw '请先运行根目录的“一键安装依赖和驱动.cmd”。' }
& $pythonPath -B -c 'import serial'
if ($LASTEXITCODE -ne 0) { throw '依赖不完整，请运行根目录的“一键安装依赖和驱动.cmd”。' }
& (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') -B (Join-Path $PSScriptRoot 'run_action.py') relock
if ($LASTEXITCODE -ne 0) { throw '操作停止，请查看上面的提示。' }
