# Windows equivalent of the Makefile. Run through ..\mealplanner.cmd, e.g.:
#   .\mealplanner setup | preview | new-week | send-email | serve | install | uninstall | status
param([string]$Command = "help")

$ErrorActionPreference = "Stop"
$AppDir = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $AppDir ".venv\Scripts"
$Python = Join-Path $Venv "python.exe"
$PythonW = Join-Path $Venv "pythonw.exe"
$DataDir = Join-Path $AppDir "data"
$LogFile = Join-Path $DataDir "mealplanner.log"
$Shortcut = Join-Path ([Environment]::GetFolderPath("Startup")) "MealPlanner.lnk"
Set-Location $AppDir

function Test-Python([string[]]$Cmd) {
    # Native stderr can raise under ErrorActionPreference=Stop in Windows PowerShell 5.1
    $ErrorActionPreference = "Continue"
    try {
        $exe = $Cmd[0]; $rest = @($Cmd | Select-Object -Skip 1)
        & $exe @rest -c "import sys; sys.exit(sys.version_info < (3, 10))" 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

function Find-Python {
    # Prefer the py launcher; a bare "python" may be the Microsoft Store stub
    $candidates = @()
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $candidates += ,@("py", "-3.13"); $candidates += ,@("py", "-3.12")
        $candidates += ,@("py", "-3.11"); $candidates += ,@("py", "-3.10"); $candidates += ,@("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) { $candidates += ,@("python") }
    foreach ($c in $candidates) { if (Test-Python $c) { return $c } }
    throw "Python 3.10+ not found. Install it with: winget install -e --id Python.Python.3.12  (then open a new PowerShell window)"
}

function Require-Setup {
    if (-not (Test-Path $Python)) { throw "Run '.\mealplanner setup' first." }
}

function Lan-Address {
    # The IPv4 address of the adapter that holds the default route (skips VPN/Hyper-V adapters)
    $ErrorActionPreference = "Continue"
    try {
        $route = Get-NetRoute -DestinationPrefix "0.0.0.0/0" | Sort-Object RouteMetric | Select-Object -First 1
        $ip = Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $route.ifIndex |
            Select-Object -First 1 -ExpandProperty IPAddress
        if ($ip) { return $ip }
    } catch {}
    return $env:COMPUTERNAME
}

function Stop-Server {
    Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe' OR Name = 'python.exe'" |
        Where-Object { $_.CommandLine -like "*mealplanner serve*" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

switch ($Command) {
    "setup" {
        $py = Find-Python
        $exe = $py[0]; $pyArgs = @($py | Select-Object -Skip 1)
        & $exe @pyArgs -m venv .venv
        & $Python -m pip install --upgrade pip --quiet
        & $Python -m pip install -r requirements.txt
        New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
        if (-not (Test-Path ".env")) {
            Copy-Item ".env.example" ".env"
            (Get-Content ".env") -replace '^BASE_URL=.*', "BASE_URL=http://$(Lan-Address):8765" | Set-Content ".env" -Encoding UTF8
        }
        if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
            Write-Warning "Claude Code isn't installed yet: irm https://claude.ai/install.ps1 | iex"
        }
        Write-Host ""
        Write-Host "Setup done. Next: notepad .env" -ForegroundColor Green
    }
    "preview"    { Require-Setup; & $Python -m mealplanner new-week --no-email }
    "new-week"   { Require-Setup; & $Python -m mealplanner new-week }
    "send-email" { Require-Setup; & $Python -m mealplanner send-email }
    "prefs"      { Require-Setup; & $Python -m mealplanner prefs }
    "serve"      { Require-Setup; & $Python -m mealplanner serve }
    "install" {
        Require-Setup
        New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
        $shell = New-Object -ComObject WScript.Shell
        $lnk = $shell.CreateShortcut($Shortcut)
        $lnk.TargetPath = $PythonW
        $lnk.Arguments = "-m mealplanner serve"
        $lnk.WorkingDirectory = $AppDir
        $lnk.WindowStyle = 7
        $lnk.Description = "Meal Planner"
        $lnk.Save()
        Stop-Server
        Start-Process -FilePath $PythonW -ArgumentList "-m", "mealplanner", "serve" -WorkingDirectory $AppDir
        Start-Sleep -Seconds 4
        Write-Host "Running in the background and will start every time you log in." -ForegroundColor Green
        Write-Host "If Windows Firewall asks about Python, allow it on Private networks."
        Write-Host "Logs: $LogFile"
    }
    "uninstall" {
        Stop-Server
        Remove-Item $Shortcut -ErrorAction SilentlyContinue
        Write-Host "Stopped and removed from startup."
    }
    "status" {
        $running = Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe' OR Name = 'python.exe'" |
            Where-Object { $_.CommandLine -like "*mealplanner serve*" }
        if ($running) { Write-Host "Running." -ForegroundColor Green } else { Write-Host "Not running." -ForegroundColor Yellow }
        if (Test-Path $LogFile) { Get-Content $LogFile -Tail 20 }
    }
    default {
        Write-Host "Usage: .\mealplanner <setup|preview|new-week|send-email|serve|install|uninstall|status|prefs>"
    }
}
