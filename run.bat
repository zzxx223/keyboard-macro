@echo off
chcp 65001 >nul 2>&1
REM ============================================
REM 键盘宏应用程序启动器
REM 以管理员身份运行以获得完整的键盘钩子支持
REM ============================================

cd /d "%~dp0"

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未以管理员身份运行。
    echo [警告] 正在请求提权以启用键盘钩子...
    powershell -Command "Start-Process -FilePath '%~dp0run.bat' -Verb RunAs"
    exit /b
)

REM 优先使用同目录下的 venv，其次使用系统 python
if exist "%~dp0venv\Scripts\pythonw.exe" (
    set "PYTHON=%~dp0venv\Scripts\pythonw.exe"
) else (
    set "PYTHON=pythonw"
)

echo 正在启动键盘宏应用程序...
"%PYTHON%" "%~dp0main.py"
