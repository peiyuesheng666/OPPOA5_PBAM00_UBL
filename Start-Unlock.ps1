Write-Host '解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利'
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
Set-Location -LiteralPath $PSScriptRoot
try {
    & (Join-Path $PSScriptRoot 'Setup-Environment.ps1') -DependenciesOnly
    $pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    & $pythonExe -u one_click_unlock.py
    if ($LASTEXITCODE -ne 0) { throw '已停止，请查看上面的提示和 runs 文件夹。' }
} catch {
    Write-Host $_ -ForegroundColor Red
}
Read-Host '按回车关闭窗口'
