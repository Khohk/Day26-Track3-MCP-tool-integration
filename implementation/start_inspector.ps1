$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerPath = Join-Path $ScriptDir "mcp_server.py"
$PythonPath = (Get-Command python).Source

Write-Host "Starting MCP Inspector UI..."
Write-Host "Python: $PythonPath"
Write-Host "Server: $ServerPath"
Write-Host "Browser auto-open: disabled"
Write-Host ""

$env:BROWSER = "none"
npx -y @modelcontextprotocol/inspector $PythonPath $ServerPath
