# ✅ CHECKLIST DEPLOY LÊN RENDER

## 🎯 Mục tiêu: Deploy bot lên Render để chạy 24/7

---

## ☑️ PHASE 1: Chuẩn bị GitHub (10 phút)

### Bước 1: Tạo GitHub Repository
- [ ] Đã truy cập https://github.com/new
- [ ] Tạo repository mới (ví dụ: `epl-prediction-bot`)
- [ ] Chọn Public hoặc Private
- [ ] **KHÔNG** check "Initialize with README"
- [ ] Click "Create repository"

### Bước 2: Push Code lên GitHub

**Cách 1: Dùng Script (Khuyến nghị)**
```powershell
.\push_to_github.ps1
```

**Cách 2: Manual**
```powershell
# Thay YOUR_USERNAME và YOUR_REPO
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

- [ ] Code đã được push thành công
- [ ] Verify trên GitHub: thấy tất cả files (trừ .env)

---

## ☑️ PHASE 2: Setup Render (5 phút)

### Bước 1: Tạo tài khoản
- [ ] Truy cập https://render.com/
- [ ] Đăng ký bằng GitHub account
- [ ] Verify email (nếu cần)

### Bước 2: Tạo Web Service
- [ ] Click "New +" → "Web Service"
- [ ] Chọn "Build and deploy from Git repository"
- [ ] Authorize Render truy cập GitHub
- [ ] Connect repository của bạn

### Bước 3: Cấu hình Service

Điền các thông tin:
- [ ] **Name**: `epl-prediction-bot`
- [ ] **Region**: Singapore hoặc gần bạn
- [ ] **Branch**: `main`
- [ ] **Runtime**: `Python 3`
- [ ] **Build Command**: `pip install -r requirements.txt`
- [ ] **Start Command**: `python bot.py`
- [ ] **Instance Type**: `Free` (để test) hoặc `Starter` (cho 24/7)

---

## ☑️ PHASE 3: Environment Variables (2 phút)

Thêm 3 biến môi trường:

### Variable 1: DISCORD_TOKEN
- [ ] Key: `DISCORD_TOKEN`
- [ ] Value: (token từ file .env của bạn)

### Variable 2: FOOTBALL_DATA_API_KEY
- [ ] Key: `FOOTBALL_DATA_API_KEY`
- [ ] Value: (API key từ file .env)

### Variable 3: ODDS_API_KEY
- [ ] Key: `ODDS_API_KEY`
- [ ] Value: (API key từ file .env)

⚠️ **Quan trọng**: Copy chính xác từ file `.env`, không có khoảng trắng thừa!

---

## ☑️ PHASE 4: Deploy! (3-5 phút)

- [ ] Click "Create Web Service"
- [ ] Đợi Render build và deploy
- [ ] Theo dõi logs trong tab "Logs"

### ✅ Thành công khi thấy:
```
INFO: Bot đã đăng nhập: NHA (ID: ...)
INFO: Đang hoạt động trên X server(s)
```

---

## ☑️ PHASE 5: Verify (2 phút)

### Kiểm tra Logs
- [ ] Tab "Logs" hiển thị bot đã đăng nhập
- [ ] Không có error message

### Test trong Discord
- [ ] `!help` - hiển thị hướng dẫn
- [ ] `!lichdau` - hiển thị lịch thi đấu
- [ ] `!phantich Arsenal vs Manchester United` - phân tích trận đấu

---

## 🎉 HOÀN THÀNH!

Nếu tất cả đều ✅, bot của bạn đã chạy trên cloud!

### 📝 Lưu ý quan trọng:

#### Free Tier
- ✅ Miễn phí
- ⚠️ Bot sẽ "ngủ" sau 15 phút không có activity
- ⚠️ Khởi động lại mất ~30 giây khi có message mới

#### Starter Plan ($7/tháng)
- ✅ Chạy 24/7 không bao giờ ngủ
- ✅ Phản hồi ngay lập tức
- ✅ Phù hợp cho production

### 🔄 Cập nhật Bot

Khi muốn update code:
```powershell
git add .
git commit -m "Update: mô tả thay đổi"
git push
```
Render sẽ tự động deploy lại! ✨

---

## 🐛 Gặp vấn đề?

### ❌ Push GitHub thất bại
- Đảm bảo đã tạo repository trên GitHub
- Check username/repo name đúng chưa

### ❌ Build failed trên Render
- Check logs để xem lỗi cụ thể
- Verify requirements.txt đúng format
- Test build local: `pip install -r requirements.txt`

### ❌ Bot không đăng nhập
- Check Environment Variables
- Verify DISCORD_TOKEN chính xác
- Đảm bảo đã enable Message Content Intent

### ❌ Bot "ngủ" trên Free tier
- Đây là hành vi bình thường của Free tier
- Upgrade lên Starter để chạy 24/7

---

## 📚 Tài liệu tham khảo

- **DEPLOY_INSTRUCTIONS.md** - Hướng dẫn chi tiết từng bước
- **README.md** - Tổng quan về bot
- **Render Docs** - https://render.com/docs

---

## 🎯 Bước tiếp theo

- [ ] Monitor logs định kỳ
- [ ] Test tất cả commands
- [ ] Xem xét upgrade plan nếu cần
- [ ] Share bot với bạn bè!

**Chúc mừng! Bot của bạn đã lên cloud! 🚀⚽🤖**
