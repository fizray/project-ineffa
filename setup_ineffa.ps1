param(
    [ValidateSet("auto", "cpu", "gpu")]
    [string]$Mode = "auto",
    [string]$EnvName = "ineffa-gpu",
    [string]$PythonVersion = "3.10",
    [switch]$SkipModels,
    [switch]$RunApp
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$env:UV_LINK_MODE = "copy"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-NvidiaGpu {
    $nvidia = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if (-not $nvidia) {
        return $false
    }

    & $nvidia.Source > $null 2>&1
    return $LASTEXITCODE -eq 0
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

function Get-SystemPython {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        & $py.Source "-$PythonVersion" --version > $null 2>&1
        if ($LASTEXITCODE -eq 0) {
            return @($py.Source, "-$PythonVersion")
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @($python.Source)
    }

    throw "Python not found. Install Python $PythonVersion or Miniconda first."
}

function Invoke-External {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command $($Arguments -join ' ')"
    }
}

function Invoke-Python {
    param(
        [string[]]$PythonCommand,
        [string[]]$Arguments
    )

    $exe = $PythonCommand[0]
    $baseArgs = @()
    if ($PythonCommand.Count -gt 1) {
        $baseArgs = $PythonCommand[1..($PythonCommand.Count - 1)]
    }

    Invoke-External -Command $exe -Arguments ($baseArgs + $Arguments)
}

function Invoke-Capture {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        return (& $Command @Arguments 2>$null)
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
}

function Test-CondaEnv {
    param(
        [string]$CondaCommand,
        [string]$EnvironmentName
    )

    try {
        $json = Invoke-Capture -Command $CondaCommand -Arguments @("env", "list", "--json")
        $envs = ($json | ConvertFrom-Json).envs
        foreach ($envPath in $envs) {
            if ((Split-Path -Leaf $envPath) -eq $EnvironmentName) {
                return $true
            }
        }
    } catch {
        return $false
    }

    return $false
}

function Test-CondaPackage {
    param(
        [string]$CondaCommand,
        [string]$EnvironmentName,
        [string]$PackageName
    )

    try {
        $json = Invoke-Capture -Command $CondaCommand -Arguments @("list", "-n", $EnvironmentName, $PackageName, "--json")
        $packages = $json | ConvertFrom-Json
        foreach ($package in $packages) {
            if ($package.name -eq $PackageName) {
                return $true
            }
        }
    } catch {
        return $false
    }

    return $false
}

function Install-ProjectDeps {
    param(
        [string]$PythonExe,
        [string]$RequirementsFile
    )

    Invoke-External -Command $PythonExe -Arguments @("-m", "pip", "install", "--upgrade", "pip", "uv")
    Invoke-External -Command $PythonExe -Arguments @("-m", "uv", "pip", "install", "--python", $PythonExe, "-r", $RequirementsFile)
}

function Install-Models {
    param([string]$PythonExe)

    if ($SkipModels) {
        Write-Host "Skip model setup." -ForegroundColor Yellow
        return
    }

    Write-Step "Download/check model files"
    Invoke-External -Command $PythonExe -Arguments @("scripts\setup_models.py")
}

function Verify-Install {
    param([string]$PythonExe)

    Write-Step "Verify imports"
    $verify = "import cv2, insightface, numpy, psutil, yaml; import onnxruntime as ort; from core.face_detection import FaceDetector; from core.embedding_extractor import RecognitionEngine; print('Python deps OK'); print('ONNX providers:', ', '.join(ort.get_available_providers()))"

    Invoke-External -Command $PythonExe -Arguments @("-c", $verify)
}

function Setup-Cpu {
    Write-Step "Setup CPU .venv with uv"

    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        $pythonCommand = @(Get-SystemPython)
        Invoke-Python -PythonCommand $pythonCommand -Arguments @("-m", "venv", ".venv")
    }

    Install-ProjectDeps -PythonExe $venvPython -RequirementsFile "requirements-cpu.txt"
    Install-Models -PythonExe $venvPython
    Verify-Install -PythonExe $venvPython

    Write-Host ""
    Write-Host "CPU setup complete." -ForegroundColor Green
    Write-Host "Run: .\ineffa.bat" -ForegroundColor Yellow

    if ($RunApp) {
        Invoke-External -Command $venvPython -Arguments @("main.py")
    }
}

function Setup-Gpu {
    Write-Step "Setup GPU Conda env + uv Python deps"

    $conda = Get-CondaCommand
    if (-not $conda) {
        throw "Conda not found. Install Miniconda/Anaconda or run CPU mode: .\setup_ineffa.ps1 -Mode cpu"
    }

    & $conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main > $null 2>&1
    & $conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r > $null 2>&1
    & $conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/msys2 > $null 2>&1

    if (-not (Test-CondaEnv -CondaCommand $conda -EnvironmentName $EnvName)) {
        Invoke-External -Command $conda -Arguments @("create", "-n", $EnvName, "python=$PythonVersion", "-y")
    } else {
        Write-Host "Conda environment '$EnvName' already exists." -ForegroundColor Green
    }

    $missingCondaPackages = @()
    foreach ($package in @("cudatoolkit", "cudnn", "zlib-wapi")) {
        if (-not (Test-CondaPackage -CondaCommand $conda -EnvironmentName $EnvName -PackageName $package)) {
            $missingCondaPackages += $package
        }
    }

    if ($missingCondaPackages.Count -gt 0) {
        Invoke-External -Command $conda -Arguments @("install", "-n", $EnvName, "-c", "conda-forge", "-c", "nvidia", "cudatoolkit=11.8", "cudnn=8.9.2", "zlib-wapi", "-y")
    } else {
        Write-Host "CUDA/cuDNN Conda packages already installed." -ForegroundColor Green
    }

    Invoke-External -Command $conda -Arguments @("run", "-n", $EnvName, "python", "-m", "pip", "install", "--upgrade", "pip", "uv")
    $envPython = (& $conda run -n $EnvName python -c "import sys; print(sys.executable)").Trim()
    Invoke-External -Command $conda -Arguments @("run", "-n", $EnvName, "python", "-m", "uv", "pip", "install", "--python", $envPython, "-r", "requirements-gpu.txt")

    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $conda run -n $EnvName python -c "import importlib.metadata as m, sys; names = {dist.metadata['Name'].lower() for dist in m.distributions()}; sys.exit(0 if 'onnxruntime' in names else 1)" > $null 2>&1
    $hasCpuOnnxRuntime = $LASTEXITCODE -eq 0
    $ErrorActionPreference = $oldErrorActionPreference
    if ($hasCpuOnnxRuntime) {
        Invoke-External -Command $conda -Arguments @("run", "-n", $EnvName, "python", "-m", "pip", "uninstall", "-y", "onnxruntime")
    }

    Invoke-External -Command $conda -Arguments @("run", "-n", $EnvName, "python", "-m", "uv", "pip", "install", "--python", $envPython, "--no-deps", "insightface==1.0.1")

    if (-not $SkipModels) {
        Write-Step "Download/check model files"
        Invoke-External -Command $conda -Arguments @("run", "-n", $EnvName, "python", "scripts\setup_models.py")
    } else {
        Write-Host "Skip model setup." -ForegroundColor Yellow
    }

    Write-Step "Verify imports"
    Invoke-External -Command $conda -Arguments @(
        "run", "-n", $EnvName, "python", "-c",
        "import cv2, insightface, numpy, psutil, yaml; import onnxruntime as ort; from core.face_detection import FaceDetector; from core.embedding_extractor import RecognitionEngine; print('Python deps OK'); print('ONNX providers:', ', '.join(ort.get_available_providers()))"
    )

    Write-Host ""
    Write-Host "GPU setup complete." -ForegroundColor Green
    Write-Host "Run: .\ineffa.bat" -ForegroundColor Yellow

    if ($RunApp) {
        $oldPath = $env:PATH
        $envPath = Split-Path -Parent $envPython
        $condaEnvPath = Split-Path -Parent $envPath
        $env:PATH = (@(
            $condaEnvPath,
            (Join-Path $condaEnvPath "Library\bin"),
            (Join-Path $condaEnvPath "Scripts"),
            (Join-Path $condaEnvPath "Library\usr\bin")
        ) -join ";") + ";$oldPath"
        $env:INEFFA_RUNTIME_MODE = "gpu"
        try {
            Invoke-External -Command $envPython -Arguments @("main.py")
        } finally {
            $env:PATH = $oldPath
            Remove-Item Env:\INEFFA_RUNTIME_MODE -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "Project Ineffa setup" -ForegroundColor Green
Write-Host "Mode: $Mode" -ForegroundColor Gray

if ($Mode -eq "auto") {
    if ((Test-NvidiaGpu) -and (Get-CondaCommand)) {
        $Mode = "gpu"
    } else {
        $Mode = "cpu"
    }
    Write-Host "Auto-selected mode: $Mode" -ForegroundColor Yellow
}

if ($Mode -eq "gpu") {
    Setup-Gpu
} else {
    Setup-Cpu
}
