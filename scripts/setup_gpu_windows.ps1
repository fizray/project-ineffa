# Face Attendance PoC - Windows GPU Setup Script
# Automated setup untuk Windows dengan NVIDIA GPU

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Face Attendance PoC - GPU Setup untuk Windows" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Function untuk check prerequisites
function Test-Prerequisites {
    Write-Host "Checking prerequisites..." -ForegroundColor Yellow
    
    # Check Python
    Write-Host "`n1. Checking Python..." -ForegroundColor White
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "   ✓ Python found: $pythonVersion" -ForegroundColor Green
        
        # Check Python version (should be 3.9-3.11)
        if ($pythonVersion -match "Python 3\.(9|10|11)") {
            Write-Host "   ✓ Python version compatible" -ForegroundColor Green
        } else {
            Write-Host "   ⚠ Warning: Python 3.9-3.11 recommended, you have $pythonVersion" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ✗ Python not found! Please install Python 3.9-3.11 from https://www.python.org" -ForegroundColor Red
        return $false
    }
    
    # Check NVIDIA GPU
    Write-Host "`n2. Checking NVIDIA GPU..." -ForegroundColor White
    try {
        $nvidiaCheck = nvidia-smi 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✓ NVIDIA GPU detected" -ForegroundColor Green
            nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | ForEach-Object {
                Write-Host "   GPU: $_" -ForegroundColor Cyan
            }
        } else {
            throw "nvidia-smi failed"
        }
    } catch {
        Write-Host "   ⚠ NVIDIA GPU or driver not detected" -ForegroundColor Yellow
        Write-Host "   → Will setup for CPU mode instead" -ForegroundColor Yellow
        return "CPU"
    }
    
    # Check CUDA
    Write-Host "`n3. Checking CUDA..." -ForegroundColor White
    try {
        $cudaVersion = nvcc --version 2>&1 | Select-String -Pattern "release (\d+\.\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }
        if ($cudaVersion) {
            Write-Host "   ✓ CUDA Toolkit found: $cudaVersion" -ForegroundColor Green
        } else {
            throw "CUDA not found"
        }
    } catch {
        Write-Host "   ⚠ CUDA Toolkit not found" -ForegroundColor Yellow
        Write-Host "   → Download from: https://developer.nvidia.com/cuda-downloads" -ForegroundColor Yellow
        $response = Read-Host "   Continue with CPU mode? (Y/N)"
        if ($response -ne 'Y') {
            return $false
        }
        return "CPU"
    }
    
    return "GPU"
}

# Function untuk setup virtual environment
function Setup-VirtualEnvironment {
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host "Setting up Virtual Environment" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    
    # Check if venv already exists
    if (Test-Path "venv") {
        Write-Host "`n⚠ Virtual environment already exists" -ForegroundColor Yellow
        $response = Read-Host "Delete and recreate? (Y/N)"
        if ($response -eq 'Y') {
            Write-Host "Removing old virtual environment..." -ForegroundColor Yellow
            Remove-Item -Recurse -Force venv
        } else {
            Write-Host "Using existing virtual environment..." -ForegroundColor Green
            return $true
        }
    }
    
    # Create venv
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Virtual environment created" -ForegroundColor Green
        return $true
    } else {
        Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
        return $false
    }
}

# Function untuk install PyTorch
function Install-PyTorch {
    param (
        [string]$Mode
    )
    
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host "Installing PyTorch" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    
    # Activate venv
    Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
    
    # Upgrade pip
    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    
    if ($Mode -eq "GPU") {
        Write-Host "`nDetecting CUDA version..." -ForegroundColor Yellow
        try {
            $cudaVersion = nvcc --version 2>&1 | Select-String -Pattern "release (\d+)\.(\d+)" | ForEach-Object { 
                $major = $_.Matches.Groups[1].Value
                $minor = $_.Matches.Groups[2].Value
                "$major.$minor"
            }
            
            Write-Host "CUDA Version: $cudaVersion" -ForegroundColor Cyan
            
            # Determine PyTorch CUDA version
            if ($cudaVersion -match "12\.") {
                Write-Host "`nInstalling PyTorch with CUDA 12.1 support..." -ForegroundColor Yellow
                pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
            } elseif ($cudaVersion -match "11\.") {
                Write-Host "`nInstalling PyTorch with CUDA 11.8 support..." -ForegroundColor Yellow
                pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
            } else {
                Write-Host "⚠ Unsupported CUDA version, installing CPU version..." -ForegroundColor Yellow
                pip install torch torchvision torchaudio
            }
        } catch {
            Write-Host "⚠ Error detecting CUDA, installing CPU version..." -ForegroundColor Yellow
            pip install torch torchvision torchaudio
        }
    } else {
        Write-Host "`nInstalling PyTorch (CPU version)..." -ForegroundColor Yellow
        pip install torch torchvision torchaudio
    }
    
    # Verify PyTorch installation
    Write-Host "`nVerifying PyTorch installation..." -ForegroundColor Yellow
    $torchCheck = python -c "import torch; print(f'PyTorch {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')" 2>&1
    Write-Host $torchCheck -ForegroundColor Cyan
    
    return $LASTEXITCODE -eq 0
}

# Function untuk install dependencies
function Install-Dependencies {
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host "Installing Application Dependencies" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    
    Write-Host "`nInstalling packages..." -ForegroundColor Yellow
    
    # Install each package
    $packages = @(
        "numpy>=1.24,<2.0",
        "opencv-python>=4.7,<4.10",
        "facenet-pytorch>=2.5,<3.0",
        "scipy>=1.10,<1.13",
        "Pillow>=10.0,<11.0",
        "PyYAML>=6.0,<7.0",
        "pandas>=2.0,<2.3",
        "matplotlib>=3.7,<3.9",
        "seaborn>=0.12,<0.14"
    )
    
    foreach ($package in $packages) {
        Write-Host "Installing $package..." -ForegroundColor White
        pip install $package --quiet
    }
    
    Write-Host "`n✓ All dependencies installed" -ForegroundColor Green
    return $true
}

# Function untuk verify setup
function Test-Setup {
    param (
        [string]$Mode
    )
    
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host "Verifying Setup" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    
    Write-Host "`n1. Testing PyTorch..." -ForegroundColor White
    $torchTest = python -c "import torch; print('OK' if torch.__version__ else 'FAIL')" 2>&1
    if ($torchTest -match "OK") {
        Write-Host "   ✓ PyTorch working" -ForegroundColor Green
    } else {
        Write-Host "   ✗ PyTorch failed" -ForegroundColor Red
        return $false
    }
    
    Write-Host "`n2. Testing OpenCV..." -ForegroundColor White
    $cvTest = python -c "import cv2; print('OK' if cv2.__version__ else 'FAIL')" 2>&1
    if ($cvTest -match "OK") {
        Write-Host "   ✓ OpenCV working" -ForegroundColor Green
    } else {
        Write-Host "   ✗ OpenCV failed" -ForegroundColor Red
        return $false
    }
    
    Write-Host "`n3. Testing facenet-pytorch..." -ForegroundColor White
    $facenetTest = python -c "import facenet_pytorch; print('OK')" 2>&1
    if ($facenetTest -match "OK") {
        Write-Host "   ✓ facenet-pytorch working" -ForegroundColor Green
    } else {
        Write-Host "   ✗ facenet-pytorch failed" -ForegroundColor Red
        return $false
    }
    
    if ($Mode -eq "GPU") {
        Write-Host "`n4. Testing GPU acceleration..." -ForegroundColor White
        $gpuTest = python -c "from embedding_extractor import EmbeddingExtractor; ext = EmbeddingExtractor(model_name='vgg_face2', config={'enable_gpu': True}); info = ext.get_model_info(); print('GPU' if info['device'] == 'cuda' else 'CPU')" 2>&1
        if ($gpuTest -match "GPU") {
            Write-Host "   ✓ GPU acceleration working" -ForegroundColor Green
            Write-Host "   Device: $gpuTest" -ForegroundColor Cyan
        } else {
            Write-Host "   ⚠ GPU acceleration not working, using CPU" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`n5. Testing camera..." -ForegroundColor White
    $camTest = python -c "import cv2; cap = cv2.VideoCapture(0); result = 'OK' if cap.isOpened() else 'FAIL'; cap.release(); print(result)" 2>&1
    if ($camTest -match "OK") {
        Write-Host "   ✓ Camera detected" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ Camera not detected (check later)" -ForegroundColor Yellow
    }
    
    return $true
}

# Function untuk create directories
function Initialize-Directories {
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host "Creating Application Directories" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    
    $dirs = @("gallery", "snapshots", "logs")
    
    foreach ($dir in $dirs) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir | Out-Null
            Write-Host "✓ Created $dir/" -ForegroundColor Green
        } else {
            Write-Host "  $dir/ already exists" -ForegroundColor Gray
        }
    }
    
    return $true
}

# Main execution
function Main {
    Write-Host "`nStarting setup process...`n" -ForegroundColor Cyan
    
    # Check prerequisites
    $mode = Test-Prerequisites
    if ($mode -eq $false) {
        Write-Host "`n✗ Prerequisites check failed. Please install required software." -ForegroundColor Red
        Write-Host "`nRequired:" -ForegroundColor Yellow
        Write-Host "  - Python 3.9-3.11: https://www.python.org" -ForegroundColor White
        Write-Host "  - NVIDIA Driver: https://www.nvidia.com/download/index.aspx" -ForegroundColor White
        Write-Host "  - CUDA Toolkit: https://developer.nvidia.com/cuda-downloads" -ForegroundColor White
        return
    }
    
    Write-Host "`n✓ Prerequisites check completed" -ForegroundColor Green
    Write-Host "Mode: $mode" -ForegroundColor Cyan
    
    # Setup virtual environment
    if (!(Setup-VirtualEnvironment)) {
        Write-Host "`n✗ Failed to setup virtual environment" -ForegroundColor Red
        return
    }
    
    # Install PyTorch
    if (!(Install-PyTorch -Mode $mode)) {
        Write-Host "`n✗ Failed to install PyTorch" -ForegroundColor Red
        return
    }
    
    # Install dependencies
    if (!(Install-Dependencies)) {
        Write-Host "`n✗ Failed to install dependencies" -ForegroundColor Red
        return
    }
    
    # Create directories
    if (!(Initialize-Directories)) {
        Write-Host "`n✗ Failed to create directories" -ForegroundColor Red
        return
    }
    
    # Verify setup
    if (!(Test-Setup -Mode $mode)) {
        Write-Host "`n✗ Setup verification failed" -ForegroundColor Red
        return
    }
    
    # Success!
    Write-Host "`n==================================================" -ForegroundColor Green
    Write-Host "Setup completed successfully! 🚀" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
    
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "1. Activate virtual environment:" -ForegroundColor White
    Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "`n2. Run the application:" -ForegroundColor White
    Write-Host "   python main.py" -ForegroundColor Yellow
    Write-Host "`n3. Enroll users:" -ForegroundColor White
    Write-Host "   python enrollment_tool.py --mode realtime --user-id emp001 --user-name ""John Doe"" --num-images 20" -ForegroundColor Yellow
    Write-Host "`n4. For help:" -ForegroundColor White
    Write-Host "   Read SETUP_WINDOWS_GPU.md for detailed documentation" -ForegroundColor Yellow
    Write-Host ""
}

# Run main
Main
