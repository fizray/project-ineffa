# Quick Verification Script for Face Attendance System
# Checks if all components are installed correctly

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Face Attendance System - Verification" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Test 1: Python
Write-Host "1. Python Version:" -ForegroundColor Yellow
try {
    $pythonVer = python --version 2>&1
    Write-Host "   $pythonVer" -ForegroundColor Green
} catch {
    Write-Host "   X Python not found!" -ForegroundColor Red
    $allGood = $false
}

# Test 2: Virtual Environment
Write-Host "`n2. Virtual Environment:" -ForegroundColor Yellow
if (Test-Path "venv\Scripts\python.exe") {
    Write-Host "   OK Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "   X Virtual environment not found!" -ForegroundColor Red
    $allGood = $false
}

# Test 3: NVIDIA GPU
Write-Host "`n3. NVIDIA GPU:" -ForegroundColor Yellow
try {
    $gpuInfo = nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   OK $gpuInfo" -ForegroundColor Green
    } else {
        Write-Host "   X nvidia-smi failed or not found" -ForegroundColor Red
    }
} catch {
    Write-Host "   X NVIDIA GPU not detected!" -ForegroundColor Red
    Write-Host "   -> Application will run in CPU mode" -ForegroundColor Yellow
}

# Activate venv for Python tests
if (Test-Path "venv\Scripts\Activate.ps1") {
    # We can't easily activate venv in the running script and have it persist for 'python' calls if we rely on the shell's path.
    # Instead, we will use the full path to the python executable in venv.
    $venvPython = ".\venv\Scripts\python.exe"
    
    # Test 5: PyTorch
    Write-Host "`n5. PyTorch:" -ForegroundColor Yellow
    try {
        # Simplified command to avoid quoting hell
        & $venvPython -c "import torch; print('Version:', torch.__version__); print('CUDA:', torch.cuda.is_available())" 2>&1 | Write-Host -ForegroundColor Green
    } catch {
        Write-Host "   X PyTorch not installed!" -ForegroundColor Red
        $allGood = $false
    }
    
    # Test 6: OpenCV
    Write-Host "`n6. OpenCV:" -ForegroundColor Yellow
    try {
        & $venvPython -c "import cv2; print('Version:', cv2.__version__)" 2>&1 | Write-Host -ForegroundColor Green
    } catch {
        Write-Host "   X OpenCV not installed!" -ForegroundColor Red
        $allGood = $false
    }
    
    # Test 7: InsightFace
    Write-Host "`n7. InsightFace:" -ForegroundColor Yellow
    try {
        & $venvPython -c "import insightface; print('OK')" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   OK Installed" -ForegroundColor Green
        } else {
            Write-Host "   X Import failed" -ForegroundColor Red
            $allGood = $false
        }
    } catch {
        Write-Host "   X insightface not installed!" -ForegroundColor Red
        $allGood = $false
    }
    
    # Test 8: Other dependencies
    Write-Host "`n8. Other Dependencies:" -ForegroundColor Yellow
    $deps = @("numpy", "yaml", "onnxruntime")
    $missingDeps = @()
    
    foreach ($dep in $deps) {
        try {
            & $venvPython -c "import $dep" 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   OK $dep" -ForegroundColor Green
            } else {
                $missingDeps += $dep
            }
        } catch {
            $missingDeps += $dep
        }
    }
    
    if ($missingDeps.Count -gt 0) {
        Write-Host "   X Missing: $($missingDeps -join ', ')" -ForegroundColor Red
        $allGood = $false
    }
    
    # Test 9: Camera
    Write-Host "`n9. Camera:" -ForegroundColor Yellow
    try {
        & $venvPython -c "import cv2; cap = cv2.VideoCapture(0); ok = cap.isOpened(); cap.release(); print('OK' if ok else 'FAIL')" 2>&1 | ForEach-Object {
            if ($_ -match "OK") {
                Write-Host "   OK Camera detected" -ForegroundColor Green
            } else {
                Write-Host "   ! Camera not detected" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "   ! Cannot test camera" -ForegroundColor Yellow
    }
    
    # Test 10: Application Components
    Write-Host "`n10. Application Components:" -ForegroundColor Yellow
    $components = @(
        "main.py",
        "config.yaml",
        "core/face_detection.py",
        "core/embedding_extractor.py",
        "core/ui_system.py",
        "enrollment_tool.py"
    )
    
    $missingFiles = @()
    foreach ($comp in $components) {
        if (Test-Path $comp) {
            Write-Host "   OK $comp" -ForegroundColor Green
        } else {
            $missingFiles += $comp
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Host "   X Missing files: $($missingFiles -join ', ')" -ForegroundColor Red
        $allGood = $false
    }
    
    # Test 11: Core Modules Import
    Write-Host "`n11. Core Modules Import:" -ForegroundColor Yellow
    try {
        & $venvPython -c "from core.face_detection import FaceDetector; from core.embedding_extractor import RecognitionEngine; print('Core modules OK')" 2>&1 | Write-Host -ForegroundColor Green
    } catch {
        Write-Host "   X Failed to import core modules!" -ForegroundColor Red
        $allGood = $false
    }

} else {
    Write-Host "   X Cannot run Python tests (venv missing)" -ForegroundColor Red
    $allGood = $false
}

# Summary
Write-Host "`n==================================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "OK All checks passed! Ready to run!" -ForegroundColor Green
} else {
    Write-Host "! Some checks failed!" -ForegroundColor Yellow
}
Write-Host ""
