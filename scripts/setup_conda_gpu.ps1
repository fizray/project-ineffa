# Setup script for Conda environment with GPU support (CUDA + cuDNN)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Setting up Conda Environment for GPU (ONNX Runtime)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check Conda
# Try to find conda in PATH or specific user location
$condaPath = Get-Command conda -ErrorAction SilentlyContinue
if (-not $condaPath) {
    $userCondaPath = "C:\Users\fiz\miniconda3\condabin"
    if (Test-Path $userCondaPath) {
        Write-Host "Found Conda at $userCondaPath, adding to PATH..." -ForegroundColor Yellow
        $env:PATH = "$userCondaPath;$env:PATH"
    }
}

# Fix for CondaToSNonInteractiveError
Write-Host "Checking Conda Terms of Service..." -ForegroundColor Gray
try {
    # Attempt to accept ToS automatically
    cmd /c "conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main"
    cmd /c "conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r"
    cmd /c "conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/msys2"
} catch {
    # Ignore errors if 'conda tos' is not available
}

try {
    $condaVer = conda --version 2>&1
    Write-Host "Found Conda: $condaVer" -ForegroundColor Green
} catch {
    Write-Host "Conda not found! Please install Anaconda or Miniconda first." -ForegroundColor Red
    Write-Host "Download: https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Yellow
    exit 1
}

# 2. Create Environment
$envName = "ineffa-gpu"
Write-Host "`n[1/4] Creating Conda environment: $envName..." -ForegroundColor Yellow
# Check if env exists
$envExists = conda env list | Select-String $envName
if ($envExists) {
    Write-Host "Environment '$envName' already exists." -ForegroundColor Yellow
    $choice = Read-Host "Do you want to remove it and reinstall? (y/n)"
    if ($choice -eq 'y') {
        conda env remove -n $envName -y
        conda create -n $envName python=3.10 -y
    }
} else {
    conda create -n $envName python=3.10 -y
}

# 3. Install CUDA & cuDNN
# We install CUDA 11.8 and compatible cuDNN. 
# This is generally the most stable configuration for onnxruntime-gpu 1.16+
# zlib-wapi is required by cuDNN on Windows but often missing
Write-Host "`n[2/4] Installing CUDA 11.8, cuDNN, and zlib-wapi..." -ForegroundColor Yellow
conda install -n $envName -c conda-forge -c nvidia cudatoolkit=11.8 cudnn=8.9.2 zlib-wapi -y

# 4. Install Pip Requirements
Write-Host "`n[3/4] Installing Python dependencies..." -ForegroundColor Yellow

# We use 'conda run' to execute pip inside the environment without activating it in the shell
# This is more robust for scripts.
try {
    conda run -n $envName pip install -r requirements.txt
    
    # Explicitly reinstall onnxruntime-gpu to ensure we have the GPU version
    # Sometimes requirements.txt might just say 'onnxruntime' or have conflicts
    Write-Host "`n[4/4] Verifying ONNX Runtime GPU..." -ForegroundColor Yellow
    conda run -n $envName pip install onnxruntime-gpu --force-reinstall
    
} catch {
    Write-Host "Error installing dependencies." -ForegroundColor Red
    exit 1
}

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "To start the application:" -ForegroundColor Cyan
Write-Host "1. conda activate $envName" -ForegroundColor Yellow
Write-Host "2. python launcher.py" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Green
