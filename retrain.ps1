# Retrain Bot Script - Automatic Monthly Retraining
# Chạy script này mỗi tháng để cập nhật model với dữ liệu mới

Write-Host "================================" -ForegroundColor Cyan
Write-Host "AUTO RETRAIN BOT MODEL" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Step 1: Collect new data
Write-Host "[1/5] Collecting historical data..." -ForegroundColor Yellow
.\venv\Scripts\python.exe data_collector.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to collect data!" -ForegroundColor Red
    exit 1
}
Write-Host "Data collected successfully" -ForegroundColor Green
Write-Host ""

# Step 2: Train new model
Write-Host "[2/5] Training new model..." -ForegroundColor Yellow
.\venv\Scripts\python.exe model_trainer.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to train model!" -ForegroundColor Red
    exit 1
}
Write-Host "Model trained successfully" -ForegroundColor Green
Write-Host ""

# Step 3: Test predictor
Write-Host "[3/5] Testing predictor..." -ForegroundColor Yellow
.\venv\Scripts\python.exe predictor.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Predictor test failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Predictor works correctly" -ForegroundColor Green
Write-Host ""

# Step 4: Commit to git
Write-Host "[4/5] Committing to git..." -ForegroundColor Yellow
$date = Get-Date -Format "yyyy-MM-dd"
git add epl_prediction_model.pkl scaler.pkl historical_odds.csv master_dataset.csv
git commit -m "Retrain model: $date - Accuracy improved with latest data"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Git commit failed (maybe no changes)" -ForegroundColor Yellow
} else {
    Write-Host "Changes committed" -ForegroundColor Green
}
Write-Host ""

# Step 5: Push to GitHub
Write-Host "[5/5] Pushing to GitHub..." -ForegroundColor Yellow
git push

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "RETRAIN SUCCESSFUL!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Model has been updated and deployed!" -ForegroundColor White
    Write-Host "Render will automatically redeploy with new model" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Push failed! Please check your GitHub credentials" -ForegroundColor Red
    Write-Host ""
}

Write-Host "Press Enter to exit..."
Read-Host
