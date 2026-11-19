param([switch]$DependenciesOnly)
if ($env:A5_BANNER_SHOWN -ne '1') { Write-Host '解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利'; $env:A5_BANNER_SHOWN = '1' }
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
Set-Location -LiteralPath $PSScriptRoot

function Find-Python {
    $paths = @((Join-Path $PSScriptRoot '.venv\Scripts\python.exe'))
    if ($env:LOCALAPPDATA) {
        $paths += @(Get-ChildItem -Path "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $discovered = & py -3 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0) { $paths += $discovered }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $command = (Get-Command python).Source
        if ($command -notmatch 'WindowsApps') { $paths += $command }
    }
    foreach ($candidate in $paths) {
        if (-not $candidate -or -not (Test-Path -LiteralPath $candidate)) { continue }
        & $candidate -c 'import sys, venv; assert sys.version_info >= (3, 8)' 2>$null
        if ($LASTEXITCODE -eq 0) { return $candidate }
    }
    return $null
}

$basePython = Find-Python
if (-not $basePython) {
    Write-Host '未找到 Python，正在通过 winget 安装 Python 3.13（需要联网）……'
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { throw '电脑没有 Python 或 winget。请先安装 Python 3，再重新双击此入口。' }
    & winget install --id Python.Python.3.13 --exact --source winget --scope user --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw 'Python 安装未成功，已停止。' }
    $basePython = Find-Python
    if (-not $basePython) { throw '未定位到新安装的 Python，请重新打开安装入口。' }
}
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host '正在准备独立 Python 环境……'
    & $basePython -m venv (Join-Path $PSScriptRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw '创建 Python 环境失败。' }
}
Write-Host '正在从随包文件安装 Python 依赖……'
& $venvPython -m pip install --no-index --find-links (Join-Path $PSScriptRoot 'dependencies') -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw '依赖安装失败，已停止。' }
& $venvPython -B (Join-Path $PSScriptRoot 'run_action.py') unlock --self-check
if ($LASTEXITCODE -ne 0) { throw '解锁资料自检失败。' }
& $venvPython -B (Join-Path $PSScriptRoot 'run_action.py') relock --self-check
if ($LASTEXITCODE -ne 0) { throw '资料包自检失败，已停止。' }
if (-not $DependenciesOnly) {
    $driverPath = Join-Path $PSScriptRoot 'drivers\Qualcomm_QDLoader_Setup.exe'
    $info = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'drivers\installer-info.json') -Raw | ConvertFrom-Json
    if ((Get-FileHash -LiteralPath $driverPath -Algorithm SHA256).Hash -ne $info.sha256) { throw '高通驱动文件校验失败。' }
    Write-Host '即将打开你提供的高通驱动安装程序。请允许管理员提示，并按安装向导完成安装。'
    $process = Start-Process -FilePath $driverPath -Verb RunAs -Wait -PassThru
    if ($process.ExitCode -notin @(0, 1641, 3010)) { throw "驱动安装程序退出码：$($process.ExitCode)。请检查安装向导结果。" }
    Write-Host '驱动安装程序已结束；若向导要求重启电脑，请先重启。'
}
Write-Host '依赖已准备好。手机进入 9008 后，双击“一键解锁.cmd”或“一键回锁.cmd”。' -ForegroundColor Green
