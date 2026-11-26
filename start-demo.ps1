$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectDir 'backend'
$frontendDir = Join-Path $projectDir 'frontend'
$pythonExe = Join-Path $backendDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Backend virtual environment missing. Follow README installation first.' }
if (-not (Test-Path -LiteralPath (Join-Path $frontendDir 'node_modules\vite'))) { throw 'Frontend dependencies missing. Run npm ci in frontend first.' }
foreach ($port in @(8000, 5173)) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { throw "Port $port is already in use. Stop the existing service or start manually on different ports." }
}
Start-Process -FilePath $pythonExe -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000') -WorkingDirectory $backendDir -WindowStyle Hidden
Start-Process -FilePath (Get-Command npm.cmd).Source -ArgumentList @('run', 'dev') -WorkingDirectory $frontendDir -WindowStyle Hidden
Write-Host 'Started local services. Open http://127.0.0.1:5173 after startup.'
Write-Host 'QA Workspace defaults to retrieval-only; no Gemini calls are made in that mode.'
