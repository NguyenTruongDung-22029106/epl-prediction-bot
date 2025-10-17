# Setup Script - Windows PowerShell
# Script này tự động thiết lập môi trường cho bot

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Bot Nhà Tiên tri Ngoại Hạng Anh" -ForegroundColor Green
Write-Host "Setup Script" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Bước 1: Kiểm tra Python
Write-Host "[1/5] Kiểm tra Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python đã cài đặt: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python chưa được cài đặt!" -ForegroundColor Red
    Write-Host "Vui lòng tải Python từ: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Bước 2: Tạo Virtual Environment
Write-Host "[2/5] Tạo Virtual Environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✓ Virtual environment đã tồn tại" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "✓ Đã tạo virtual environment" -ForegroundColor Green
}
Write-Host ""

# Bước 3: Kích hoạt Virtual Environment và cài đặt dependencies
Write-Host "[3/5] Cài đặt dependencies..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
pip install -r requirements.txt --quiet
Write-Host "✓ Đã cài đặt tất cả dependencies" -ForegroundColor Green
Write-Host ""

# Bước 4: Kiểm tra file .env
Write-Host "[4/5] Kiểm tra cấu hình..." -ForegroundColor Yellow
if (Test-Path ".env") {
    # Kiểm tra xem .env có chứa API keys thực không
    $envContent = Get-Content .env -Raw
    if ($envContent -match "your_.*_here") {
        Write-Host "⚠ File .env tồn tại nhưng chưa được cấu hình" -ForegroundColor Yellow
        Write-Host "Vui lòng mở file .env và điền các API keys" -ForegroundColor Yellow
    } else {
        Write-Host "✓ File .env đã được cấu hình" -ForegroundColor Green
    }
} else {
    Write-Host "✗ File .env không tồn tại!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Bước 5: Train model nếu chưa có
Write-Host "[5/5] Kiểm tra model..." -ForegroundColor Yellow
if (Test-Path "epl_prediction_model.pkl") {
    Write-Host "✓ Model đã tồn tại" -ForegroundColor Green
} else {
    Write-Host "Model chưa tồn tại. Đang train model với mock data..." -ForegroundColor Yellow
    python model_trainer.py
    if (Test-Path "epl_prediction_model.pkl") {
        Write-Host "✓ Đã train model thành công" -ForegroundColor Green
    } else {
        Write-Host "✗ Không thể train model" -ForegroundColor Red
    }
}
Write-Host ""

# Hoàn tất
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "✓ SETUP HOÀN TẤT!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Để chạy bot:" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python bot.py" -ForegroundColor White
Write-Host ""
Write-Host "Hoặc dùng script khởi động:" -ForegroundColor Yellow
Write-Host "  .\start.ps1" -ForegroundColor White
Write-Host ""
