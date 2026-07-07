@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo [1/2] 停止旧服务...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8081.*LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
    echo       已终止 PID %%a
)
timeout /t 1 /nobreak >nul

echo [2/2] 启动服务...
python -m src.main
