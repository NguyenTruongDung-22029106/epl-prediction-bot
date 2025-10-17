# Script Deploy nhanh - Push to GitHub
# Chạy script này để push code lên GitHub

Write-Host "================================" -ForegroundColor Cyan
Write-Host "PUSH CODE LÊN GITHUB" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Bước 1: Nhập thông tin GitHub repository
Write-Host "Nhập thông tin GitHub repository của bạn:" -ForegroundColor Yellow
Write-Host ""

$username = Read-Host "GitHub username"
$reponame = Read-Host "Repository name (ví dụ: epl-prediction-bot)"

$remote_url = "https://github.com/$username/$reponame.git"

Write-Host ""
Write-Host "Repository URL: $remote_url" -ForegroundColor Cyan
Write-Host ""

# Bước 2: Kiểm tra git remote
Write-Host "[1/4] Kiểm tra git remote..." -ForegroundColor Yellow

$existing_remote = git remote get-url origin 2>$null

if ($existing_remote) {
    Write-Host "Remote 'origin' đã tồn tại: $existing_remote" -ForegroundColor Yellow
    $change = Read-Host "Bạn có muốn thay đổi? (y/n)"
    if ($change -eq "y") {
        git remote remove origin
        git remote add origin $remote_url
        Write-Host "✓ Đã cập nhật remote" -ForegroundColor Green
    }
} else {
    git remote add origin $remote_url
    Write-Host "✓ Đã thêm remote" -ForegroundColor Green
}

Write-Host ""

# Bước 3: Add và commit changes
Write-Host "[2/4] Commit changes..." -ForegroundColor Yellow

git add .
git commit -m "Add deployment instructions and setup for Render"

Write-Host "✓ Changes đã được commit" -ForegroundColor Green
Write-Host ""

# Bước 4: Đổi branch thành main
Write-Host "[3/4] Đảm bảo branch là main..." -ForegroundColor Yellow

$current_branch = git branch --show-current

if ($current_branch -ne "main") {
    git branch -M main
    Write-Host "✓ Đã đổi branch thành main" -ForegroundColor Green
} else {
    Write-Host "✓ Branch đã là main" -ForegroundColor Green
}

Write-Host ""

# Bước 5: Push lên GitHub
Write-Host "[4/4] Push lên GitHub..." -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Sẵn sàng push? (y/n)"

if ($confirm -eq "y") {
    Write-Host ""
    Write-Host "Đang push..." -ForegroundColor Cyan
    
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "================================" -ForegroundColor Cyan
        Write-Host "✓ PUSH THÀNH CÔNG!" -ForegroundColor Green
        Write-Host "================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Repository URL:" -ForegroundColor Yellow
        Write-Host "https://github.com/$username/$reponame" -ForegroundColor White
        Write-Host ""
        Write-Host "Bước tiếp theo:" -ForegroundColor Yellow
        Write-Host "1. Truy cập: https://render.com/" -ForegroundColor White
        Write-Host "2. Tạo New Web Service" -ForegroundColor White
        Write-Host "3. Connect repository: $reponame" -ForegroundColor White
        Write-Host "4. Đọc file DEPLOY_INSTRUCTIONS.md để biết chi tiết" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "✗ Push thất bại!" -ForegroundColor Red
        Write-Host "Có thể bạn cần:" -ForegroundColor Yellow
        Write-Host "1. Tạo repository trên GitHub trước" -ForegroundColor White
        Write-Host "2. Authenticate với GitHub (nếu private repo)" -ForegroundColor White
        Write-Host ""
    }
} else {
    Write-Host "Đã hủy push." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Nhấn Enter để thoát..."
Read-Host
