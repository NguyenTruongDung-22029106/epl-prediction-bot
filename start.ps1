# Start Script - Khởi động bot nhanh
# Script này kích hoạt virtual environment và chạy bot

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Đang khởi động bot..." -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Kích hoạt virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "✓ Đã kích hoạt virtual environment" -ForegroundColor Green
} else {
    Write-Host "✗ Virtual environment không tồn tại!" -ForegroundColor Red
    Write-Host "Vui lòng chạy: .\setup.ps1" -ForegroundColor Yellow
    exit 1
}

# Kiểm tra .env
if (!(Test-Path ".env")) {
    Write-Host "✗ File .env không tồn tại!" -ForegroundColor Red
    exit 1
}

# Kiểm tra model
if (!(Test-Path "epl_prediction_model.pkl")) {
    Write-Host "⚠ Model chưa tồn tại. Đang train..." -ForegroundColor Yellow
    python model_trainer.py
}

Write-Host ""
Write-Host "Đang khởi động bot..." -ForegroundColor Yellow
Write-Host "Nhấn Ctrl+C để dừng bot" -ForegroundColor Gray
Write-Host ""

# Chạy bot
python bot.py
