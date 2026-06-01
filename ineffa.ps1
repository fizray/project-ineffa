param(
    [string]$EnvName = "ineffa-gpu"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Write-Header {
    Clear-Host
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "Project Ineffa Launcher" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Cyan
}

function Pause-Menu {
    Write-Host ""
    Read-Host "Press Enter to return to menu" | Out-Null
}

function Get-CondaCommand {
    $cmd = Get-Command conda -ErrorAction SilentlyContinue
    if ($cmd) {
        if ($cmd.Source) {
            return $cmd.Source
        }
        return $cmd.Name
    }

    $candidates = @(
        "$env:USERPROFILE\miniconda3\condabin\conda.bat",
        "$env:USERPROFILE\anaconda3\condabin\conda.bat",
        "C:\ProgramData\miniconda3\condabin\conda.bat",
        "C:\ProgramData\anaconda3\condabin\conda.bat"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Get-CondaEnvPath {
    param([string]$EnvironmentName)

    $conda = Get-CondaCommand
    if (-not $conda) {
        return $null
    }

    $json = & $conda env list --json 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $null
    }

    $envs = ($json | ConvertFrom-Json).envs
    foreach ($envPath in $envs) {
        if ((Split-Path -Leaf $envPath) -eq $EnvironmentName) {
            return $envPath
        }
    }

    return $null
}

function Get-PythonPath {
    param([ValidateSet("cpu", "gpu")] [string]$Mode)

    if ($Mode -eq "cpu") {
        $python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
        if (Test-Path $python) {
            return $python
        }
        throw "CPU environment not found. Run setup CPU first."
    }

    $envPath = Get-CondaEnvPath -EnvironmentName $EnvName
    if (-not $envPath) {
        throw "GPU Conda environment '$EnvName' not found. Run setup GPU first."
    }

    $python = Join-Path $envPath "python.exe"
    if (Test-Path $python) {
        return $python
    }

    throw "GPU Python not found at $python"
}

function Invoke-ProjectPython {
    param(
        [ValidateSet("cpu", "gpu")] [string]$Mode,
        [string]$Script,
        [string[]]$Arguments = @()
    )

    $python = Get-PythonPath -Mode $Mode
    $oldRuntimeMode = $env:INEFFA_RUNTIME_MODE
    $oldPath = $env:PATH
    $env:INEFFA_RUNTIME_MODE = $Mode
    try {
        if ($Mode -eq "gpu") {
            $envPath = Get-CondaEnvPath -EnvironmentName $EnvName
            if ($envPath) {
                $condaDllPaths = @(
                    $envPath,
                    (Join-Path $envPath "Library\bin"),
                    (Join-Path $envPath "Scripts"),
                    (Join-Path $envPath "Library\usr\bin")
                )
                $env:PATH = ($condaDllPaths -join ";") + ";$oldPath"
            }
        }
        & $python $Script @Arguments
    } finally {
        if ($null -eq $oldRuntimeMode) {
            Remove-Item Env:\INEFFA_RUNTIME_MODE -ErrorAction SilentlyContinue
        } else {
            $env:INEFFA_RUNTIME_MODE = $oldRuntimeMode
        }
        $env:PATH = $oldPath
    }
}

function Select-Mode {
    param([string]$Prompt = "Mode")

    Write-Host ""
    Write-Host "${Prompt}:"
    Write-Host "1. CPU (.venv)"
    Write-Host "2. GPU (Conda: $EnvName)"
    $choice = Read-Host "Select mode"

    switch ($choice) {
        "1" { return "cpu" }
        "2" { return "gpu" }
        default { throw "Invalid mode." }
    }
}

function Run-Setup {
    param([ValidateSet("auto", "cpu", "gpu")] [string]$Mode)

    $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ".\setup_ineffa.ps1", "-Mode", $Mode)
    & powershell @args
}

function Run-Attendance {
    $mode = Select-Mode -Prompt "Run attendance"
    Invoke-ProjectPython -Mode $mode -Script "main.py"
}

function Run-Benchmark {
    $mode = Select-Mode -Prompt "Run benchmark"
    Invoke-ProjectPython -Mode $mode -Script "bench.py"
}

function Run-Enroll {
    $mode = Select-Mode -Prompt "Enroll user"
    $userId = Read-Host "User ID"
    $userName = Read-Host "User name"
    $samples = Read-Host "Samples (blank = 5)"
    if ([string]::IsNullOrWhiteSpace($samples)) {
        $samples = "5"
    }

    Invoke-ProjectPython -Mode $mode -Script "enrollment_tool.py" -Arguments @("--id", $userId, "--name", $userName, "--samples", $samples)
}

function Run-ModelSetup {
    $mode = Select-Mode -Prompt "Setup models"
    Invoke-ProjectPython -Mode $mode -Script "scripts\setup_models.py"
}

function Run-Verify {
    $mode = Select-Mode -Prompt "Verify environment"
    $code = "import cv2, insightface, numpy, psutil, yaml; import onnxruntime as ort; print('Python deps OK'); print('ONNX providers:', ', '.join(ort.get_available_providers()))"
    $python = Get-PythonPath -Mode $mode
    & $python -c $code
}

function Run-CameraCheck {
    $mode = Select-Mode -Prompt "Check cameras"
    Invoke-ProjectPython -Mode $mode -Script "scripts\check_cameras.py"
}

function Clear-AttendanceLogs {
    $targets = @("attendance.csv", "data\attendance.csv")
    foreach ($target in $targets) {
        if (Test-Path $target) {
            Remove-Item -LiteralPath $target -Force
            Write-Host "Removed $target" -ForegroundColor Yellow
        }
    }
}

while ($true) {
    Write-Header
    Write-Host "Setup"
    Write-Host "  1. Setup auto"
    Write-Host "  2. Setup CPU"
    Write-Host "  3. Setup GPU"
    Write-Host ""
    Write-Host "Run"
    Write-Host "  4. Attendance"
    Write-Host "  5. Enroll user"
    Write-Host "  6. Benchmark"
    Write-Host ""
    Write-Host "Tools"
    Write-Host "  7. Setup/check models"
    Write-Host "  8. Verify environment"
    Write-Host "  9. Check cameras"
    Write-Host "  10. Clear attendance logs"
    Write-Host "  0. Exit"
    Write-Host "==================================================" -ForegroundColor Cyan

    $choice = Read-Host "Select option"

    try {
        switch ($choice) {
            "1" { Run-Setup -Mode "auto"; Pause-Menu }
            "2" { Run-Setup -Mode "cpu"; Pause-Menu }
            "3" { Run-Setup -Mode "gpu"; Pause-Menu }
            "4" { Run-Attendance; Pause-Menu }
            "5" { Run-Enroll; Pause-Menu }
            "6" { Run-Benchmark; Pause-Menu }
            "7" { Run-ModelSetup; Pause-Menu }
            "8" { Run-Verify; Pause-Menu }
            "9" { Run-CameraCheck; Pause-Menu }
            "10" { Clear-AttendanceLogs; Pause-Menu }
            "0" { exit 0 }
            default { Write-Host "Invalid option." -ForegroundColor Red; Start-Sleep -Seconds 1 }
        }
    } catch {
        Write-Host ""
        Write-Host $_.Exception.Message -ForegroundColor Red
        Pause-Menu
    }
}
