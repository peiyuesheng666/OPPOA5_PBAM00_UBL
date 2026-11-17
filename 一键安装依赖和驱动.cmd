@echo off
chcp 65001 >nul
echo 解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "try { & '.\Setup-Environment.ps1'; exit 0 } catch { Write-Host $_ -ForegroundColor Red; exit 1 }"
if errorlevel 1 echo 安装未完成，请查看上面的提示。
pause
