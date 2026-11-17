@echo off
chcp 65001 >nul
echo 解锁方案/脚本/文件 By 酷安@Dev裴月笙 公益解锁文件，禁止倒卖盈利
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Unlock.ps1"
