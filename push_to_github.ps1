# Push to GitHub Script
Write-Host "================================" -ForegroundColor Cyan
Write-Host "PUSH CODE TO GITHUB" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$username = "NguyenTruongDung-22029106"
$reponame = "epl-prediction-bot"
$remote_url = "https://github.com/$username/$reponame.git"

Write-Host "Repository: $remote_url" -ForegroundColor Cyan
Write-Host ""

# Check git remote
Write-Host "[1/3] Checking git remote..." -ForegroundColor Yellow
$existing_remote = git remote get-url origin 2>$null

if ($existing_remote) {
    Write-Host "Remote exists: $existing_remote" -ForegroundColor Yellow
    git remote remove origin
}

git remote add origin $remote_url
Write-Host "Remote added successfully" -ForegroundColor Green
Write-Host ""

# Ensure main branch
Write-Host "[2/3] Checking branch..." -ForegroundColor Yellow
$current_branch = git branch --show-current

if ($current_branch -ne "main") {
    git branch -M main
    Write-Host "Changed to main branch" -ForegroundColor Green
} else {
    Write-Host "Already on main branch" -ForegroundColor Green
}
Write-Host ""

# Push to GitHub
Write-Host "[3/3] Pushing to GitHub..." -ForegroundColor Yellow
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Repository URL:" -ForegroundColor Yellow
    Write-Host "https://github.com/$username/$reponame" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://render.com/" -ForegroundColor White
    Write-Host "2. Create New Web Service" -ForegroundColor White
    Write-Host "3. Connect repository: $reponame" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Push failed!" -ForegroundColor Red
    Write-Host "Make sure you created the repository on GitHub first" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press Enter to exit..."
Read-Host
