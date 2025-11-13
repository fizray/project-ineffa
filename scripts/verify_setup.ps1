# Quick Verification Script untuk GPU Setup
# Check apakah semua komponen sudah terinstall dengan benar

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Face Attendance PoC - GPU Verification" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Test 1: Python
Write-Host "1. Python Version:" -ForegroundColor Yellow
try {
    $pythonVer = python --version 2>&1
    Write-Host "   $pythonVer" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Python not found!" -ForegroundColor Red
    $allGood = $false
}

# Test 2: Virtual Environment
Write-Host "`n2. Virtual Environment:" -ForegroundColor Yellow
if (Test-Path "venv\Scripts\python.exe") {
    Write-Host "   ✓ Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "   ✗ Virtual environment not found!" -ForegroundColor Red
    $allGood = $false
}

# Test 3: NVIDIA GPU
Write-Host "`n3. NVIDIA GPU:" -ForegroundColor Yellow
try {
    $gpuInfo = nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ $gpuInfo" -ForegroundColor Green
    } else {
        throw "nvidia-smi failed"
    }
} catch {
    Write-Host "   ✗ NVIDIA GPU not detected!" -ForegroundColor Red
    Write-Host "   → Application will run in CPU mode" -ForegroundColor Yellow
}

# Test 4: CUDA
Write-Host "`n4. CUDA Toolkit:" -ForegroundColor Yellow
try {
    $cudaVer = nvcc --version 2>&1 | Select-String -Pattern "release (\d+\.\d+)"
    if ($cudaVer) {
        Write-Host "   ✓ CUDA $($cudaVer.Matches.Groups[1].Value)" -ForegroundColor Green
    } else {
        throw "CUDA not found"
    }
} catch {
    Write-Host "   ✗ CUDA Toolkit not found!" -ForegroundColor Red
    Write-Host "   → Download from: https://developer.nvidia.com/cuda-downloads" -ForegroundColor Yellow
}

# Activate venv for Python tests
if (Test-Path "venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
    
    # Test 5: PyTorch
    Write-Host "`n5. PyTorch:" -ForegroundColor Yellow
    try {
        $torchInfo = python -c "import torch; print(f'Version: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')" 2>&1
        Write-Host $torchInfo -ForegroundColor Green
    } catch {
        Write-Host "   ✗ PyTorch not installed!" -ForegroundColor Red
        $allGood = $false
    }
    
    # Test 6: OpenCV
    Write-Host "`n6. OpenCV:" -ForegroundColor Yellow
    try {
        $cvVer = python -c "import cv2; print(f'Version: {cv2.__version__}')" 2>&1
        Write-Host "   ✓ $cvVer" -ForegroundColor Green
    } catch {
        Write-Host "   ✗ OpenCV not installed!" -ForegroundColor Red
        $allGood = $false
    }
    
    # Test 7: facenet-pytorch
    Write-Host "`n7. facenet-pytorch:" -ForegroundColor Yellow
    try {
        python -c "import facenet_pytorch; print('OK')" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✓ Installed" -ForegroundColor Green
        } else {
            throw "Import failed"
        }
    } catch {
        Write-Host "   ✗ facenet-pytorch not installed!" -ForegroundColor Red
        $allGood = $false
    }
    
    # Test 8: Other dependencies
    Write-Host "`n8. Other Dependencies:" -ForegroundColor Yellow
    $deps = @("numpy", "scipy", "PIL", "yaml", "pandas", "matplotlib", "seaborn")
    $missingDeps = @()
    
    foreach ($dep in $deps) {
        try {
            python -c "import $dep" 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✓ $dep" -ForegroundColor Green
            } else {
                $missingDeps += $dep
            }
        } catch {
            $missingDeps += $dep
        }
    }
    
    if ($missingDeps.Count -gt 0) {
        Write-Host "   ✗ Missing: $($missingDeps -join ', ')" -ForegroundColor Red
        $allGood = $false
    }
    
    # Test 9: Camera
    Write-Host "`n9. Camera:" -ForegroundColor Yellow
    try {
        $camTest = python -c "import cv2; cap = cv2.VideoCapture(0); ok = cap.isOpened(); cap.release(); print('OK' if ok else 'FAIL')" 2>&1
        if ($camTest -match "OK") {
            Write-Host "   ✓ Camera detected" -ForegroundColor Green
        } else {
            Write-Host "   ⚠ Camera not detected" -ForegroundColor Yellow
            Write-Host "   → Check camera connection or try different camera_id in config.yaml" -ForegroundColor Gray
        }
    } catch {
        Write-Host "   ⚠ Cannot test camera" -ForegroundColor Yellow
    }
    
    # Test 10: Application Components
    Write-Host "`n10. Application Components:" -ForegroundColor Yellow
    $components = @(
        "main.py",
        "config.yaml",
        "face_detection.py",
        "liveness_detection.py",
        "embedding_extractor.py",
        "matching_engine.py",
        "logging_system.py",
        "ui_system.py",
        "enrollment_tool.py",
        "testing_tool.py"
    )
    
    $missingFiles = @()
    foreach ($comp in $components) {
        if (Test-Path $comp) {
            Write-Host "   ✓ $comp" -ForegroundColor Green
        } else {
            $missingFiles += $comp
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Host "   ✗ Missing files: $($missingFiles -join ', ')" -ForegroundColor Red
        $allGood = $false
    }
    
    # Test 11: GPU Acceleration Test
    Write-Host "`n11. GPU Acceleration:" -ForegroundColor Yellow
    try {
        Write-Host "   Testing embedding extractor with GPU..." -ForegroundColor Gray
        $gpuTest = python -c @"
from embedding_extractor import EmbeddingExtractor
import time

# Test dengan GPU
ext_gpu = EmbeddingExtractor(model_name='vgg_face2', config={'enable_gpu': True})
info = ext_gpu.get_model_info()
print(f"Device: {info['device']}")
print(f"Model: {info['model_name']}")

# Performance test
import numpy as np
import cv2
test_img = np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8)

start = time.time()
for i in range(10):
    emb = ext_gpu.extract_embedding(test_img)
elapsed = time.time() - start

print(f"10 embeddings in {elapsed:.2f}s ({10/elapsed:.1f} FPS)")
"@ 2>&1
        
        Write-Host $gpuTest -ForegroundColor Cyan
    } catch {
        Write-Host "   ✗ GPU test failed!" -ForegroundColor Red
        Write-Host "   $($_.Exception.Message)" -ForegroundColor Gray
    }
}

# Summary
Write-Host "`n==================================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "✓ All checks passed! Ready to run!" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "`nQuick Start:" -ForegroundColor Cyan
    Write-Host "1. .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "2. python main.py" -ForegroundColor Yellow
} else {
    Write-Host "⚠ Some checks failed!" -ForegroundColor Yellow
    Write-Host "==================================================" -ForegroundColor Yellow
    Write-Host "`nPlease run setup script:" -ForegroundColor Cyan
    Write-Host ".\setup_gpu_windows.ps1" -ForegroundColor Yellow
}
Write-Host ""
