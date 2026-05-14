@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "SERVER_PATH=%SCRIPT_DIR%mcp_server.py"

for /f "delims=" %%P in ('where python') do (
  set "PYTHON_PATH=%%P"
  goto :found_python
)

echo Python was not found on PATH. Activate your virtual environment first.
exit /b 1

:found_python
echo Starting MCP Inspector UI...
echo Python: %PYTHON_PATH%
echo Server: %SERVER_PATH%
echo Browser auto-open: disabled
echo.

set "BROWSER=none"
npx -y @modelcontextprotocol/inspector "%PYTHON_PATH%" "%SERVER_PATH%"
