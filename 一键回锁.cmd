@echo off
setlocal
chcp 65001 >nul
echo 解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利
set "A5_BANNER_SHOWN=1"
cd /d "%~dp0runtime"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "try { & '.\一键回锁.ps1'; exit 0 } catch { Write-Host $_ -ForegroundColor Red; exit 1 }"
pause
