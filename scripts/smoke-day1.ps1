param(
    [string]$HostUrl = "http://127.0.0.1:8000"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-PythonExeOrThrow {
    # Prefer a real path to python.exe to avoid relying on 'py' launcher
    $pythonExe = $null

    # Try Python Launcher for 3.11 specifically
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            & py -3.11 --version | Out-Null
            $pythonExe = & py -3.11 -c "import sys; print(sys.executable)"
        } catch { }
    }

    # Fallback to whichever 'python' is on PATH
    if (-not $pythonExe -and (Get-Command python -ErrorAction SilentlyContinue)) {
        try {
            & python --version | Out-Null
            $pythonExe = & python -c "import sys; print(sys.executable)"
        } catch { }
    }

    if (-not $pythonExe -or -not (Test-Path $pythonExe)) {
        throw "Python not found. Install Python 3.11 (winget install -e --id Python.Python.3.11), then re-run."
    }
    return $pythonExe
}

Write-Host "[Smoke] Ensuring virtual environment..."
if (-not (Test-Path .venv)) {
    $pythonExe = Get-PythonExeOrThrow
    & $pythonExe -m venv .venv
}

$venvPython = Join-Path (Resolve-Path ".").Path ".venv/Scripts/python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment not created. Ensure Python is installed and try again."
}

Write-Host "[Smoke] Installing minimal server deps..."
& $venvPython -m pip install -U pip | Out-Null
& $venvPython -m pip install fastapi==0.111.0 "uvicorn[standard]"==0.30.1 pydantic==2.8.2 python-multipart==0.0.9 | Out-Null

Write-Host "[Smoke] Starting API server..."
$p = Start-Process -FilePath $venvPython -ArgumentList @("-m","uvicorn","services.api.main:app","--host","127.0.0.1","--port","8000") -PassThru
Start-Sleep -Seconds 4

try {
    Write-Host "[Smoke] GET /health"
    $health = Invoke-RestMethod "$HostUrl/health"
    $health | ConvertTo-Json -Depth 5 | Write-Host

    # Ensure a test file exists
    if (-not (Test-Path test.pdf)) {
        # Minimal bytes; endpoint validates extension only for Day 1
        "Dummy PDF content" | Out-File -FilePath test.pdf -Encoding ascii -Force
    }

    Write-Host "[Smoke] POST /data/upload"
    # Use system curl.exe for reliable multipart upload
    $uploadOut = & curl.exe -s -S -X POST `
        -F "file=@test.pdf;type=application/pdf" `
        -F "subject=Economics" `
        -F "chapter=1" `
        "$HostUrl/data/upload"
    Write-Host $uploadOut

    Write-Host "[Smoke] Negative test: non-PDF"
    if (-not (Test-Path test.txt)) { "hello" | Out-File -FilePath test.txt -Encoding ascii -Force }
    $neg = & curl.exe -s -S -o NUL -w "%{http_code}" -X POST `
        -F "file=@test.txt;type=text/plain" `
        -F "subject=Economics" `
        -F "chapter=1" `
        "$HostUrl/data/upload"
    Write-Host "HTTP $neg (expected 400)"
}
finally {
    if ($p -and !$p.HasExited) {
        Write-Host "[Smoke] Stopping server..."
        Stop-Process -Id $p.Id -Force
    }
}

Write-Host "[Smoke] Done."
