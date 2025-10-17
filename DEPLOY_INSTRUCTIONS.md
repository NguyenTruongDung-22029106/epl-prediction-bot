# 🚀 HƯỚNG DẪN DEPLOY LÊN RENDER - CHI TIẾT

## ✅ Checklist trước khi deploy

- [x] Code đã được commit vào Git
- [ ] Đã tạo GitHub repository
- [ ] Code đã được push lên GitHub
- [ ] Đã có tài khoản Render
- [ ] Đã có API keys (Discord, Football-Data, The Odds API)

---

## 📋 BƯỚC 1: Push code lên GitHub

### 1.1. Tạo repository trên GitHub

1. Truy cập: https://github.com/new
2. Điền thông tin:
   - **Repository name**: `epl-prediction-bot` (hoặc tên bạn muốn)
   - **Description**: "Discord bot dự đoán kèo Ngoại Hạng Anh với Machine Learning"
   - **Visibility**: Public hoặc Private (tùy bạn)
   - **KHÔNG chọn** "Initialize with README" (vì đã có code)
3. Click **"Create repository"**

### 1.2. Kết nối và push code

GitHub sẽ hiển thị hướng dẫn. Chạy các lệnh sau trong PowerShell:

```powershell
# Thêm remote (thay YOUR_USERNAME và YOUR_REPO)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Đổi tên branch thành main (nếu cần)
git branch -M main

# Push code
git push -u origin main
```

**Ví dụ cụ thể:**
```powershell
git remote add origin https://github.com/john123/epl-prediction-bot.git
git branch -M main
git push -u origin main
```

⚠️ **Lưu ý**: File `.env` sẽ KHÔNG được push (đã có trong `.gitignore`)

---

## 🌐 BƯỚC 2: Tạo Web Service trên Render

### 2.1. Đăng ký/Đăng nhập Render

1. Truy cập: https://render.com/
2. Click **"Get Started"**
3. Đăng ký bằng GitHub account (khuyến nghị) hoặc email
4. Xác nhận email nếu cần

### 2.2. Tạo Web Service mới

1. Trong Render Dashboard, click **"New +"** (góc trên bên phải)
2. Chọn **"Web Service"**
3. Click **"Build and deploy from a Git repository"**
4. Click **"Next"**

### 2.3. Kết nối GitHub Repository

1. Click **"Connect account"** để authorize Render
2. Cho phép Render truy cập GitHub repositories
3. Trong danh sách repositories, tìm và click **"Connect"** bên cạnh `epl-prediction-bot`

### 2.4. Cấu hình Web Service

Điền thông tin như sau:

| Field | Value |
|-------|-------|
| **Name** | `epl-prediction-bot` (hoặc tên bạn muốn) |
| **Region** | Chọn gần bạn nhất (ví dụ: Singapore) |
| **Branch** | `main` |
| **Root Directory** | Để trống |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python bot.py` |

### 2.5. Chọn Instance Type

- **Instance Type**: Chọn **"Free"**
  - 750 giờ/tháng
  - Service sẽ "ngủ" sau 15 phút không hoạt động
  - Phù hợp để test

⚠️ **Quan trọng cho Discord Bot**: 
- Bot Discord cần chạy liên tục để nhận messages
- Free tier sẽ "ngủ" sau 15 phút không có HTTP requests
- Để chạy 24/7, cần upgrade lên **Starter ($7/tháng)**

**Khuyến nghị**: Bắt đầu với Free để test, sau đó upgrade nếu hài lòng.

---

## 🔐 BƯỚC 3: Thêm Environment Variables

Kéo xuống phần **"Environment Variables"** và thêm:

### 3.1. Click "Add Environment Variable"

Thêm 3 biến sau:

#### Variable 1: DISCORD_TOKEN
- **Key**: `DISCORD_TOKEN`
- **Value**: Token của bạn (ví dụ: `MTIzNDU2Nzg5MDEyMzQ1Njc4.GaBcDe.FgHiJk...`)

#### Variable 2: FOOTBALL_DATA_API_KEY
- **Key**: `FOOTBALL_DATA_API_KEY`
- **Value**: API key từ Football-Data.org

#### Variable 3: ODDS_API_KEY
- **Key**: `ODDS_API_KEY`
- **Value**: API key từ The Odds API

### 3.2. Verify

Đảm bảo cả 3 variables đã được thêm đúng:
```
DISCORD_TOKEN = ••••••••••••••••••••
FOOTBALL_DATA_API_KEY = ••••••••••••••••••••
ODDS_API_KEY = ••••••••••••••••••••
```

---

## 🎯 BƯỚC 4: Deploy!

1. Click **"Create Web Service"** (button màu xanh)
2. Render sẽ bắt đầu deploy:
   - Clone repository từ GitHub
   - Install dependencies
   - Start bot

### 4.1. Theo dõi quá trình deploy

Trong tab **"Logs"**, bạn sẽ thấy:

```
==> Cloning from https://github.com/your-username/epl-prediction-bot...
==> Running 'pip install -r requirements.txt'
    Collecting discord.py>=2.3.2
    ...
==> Build successful 🎉
==> Starting service with 'python bot.py'
    INFO: Bot đã đăng nhập: NHA (ID: 1428621146634588200)
    INFO: Đang hoạt động trên X server(s)
```

✅ **Thành công** khi thấy: `Bot đã đăng nhập`

---

## ✅ BƯỚC 5: Verify Bot hoạt động

### 5.1. Check Logs

Tab "Logs" nên hiển thị:
```
INFO: Bot đã đăng nhập: [TÊN BOT] (ID: ...)
INFO: Đang hoạt động trên X server(s)
```

### 5.2. Test trong Discord

Vào Discord server và thử:
```
!help
!lichdau
!phantich Arsenal vs Manchester United
```

---

## 🔄 BƯỚC 6: Auto-Deploy (Bonus)

Sau khi setup xong, mỗi khi bạn push code mới lên GitHub:

```powershell
git add .
git commit -m "Update: your changes"
git push
```

Render sẽ **TỰ ĐỘNG** deploy lại! 🎉

---

## ⚙️ Cấu hình nâng cao (Optional)

### Upgrade để chạy 24/7

1. Vào Service Settings
2. Chọn **"Starter"** plan ($7/tháng)
3. Bot sẽ chạy liên tục không bị "ngủ"

### Thêm Health Check (nếu cần)

Nếu muốn bot không bị "ngủ" trên Free tier:
1. Thêm endpoint `/health` vào bot
2. Dùng external service ping định kỳ (ví dụ: UptimeRobot)

---

## 🐛 Troubleshooting

### ❌ Build failed

**Triệu chứng**: "Build failed" trong logs

**Giải pháp**:
```powershell
# Test build local trước
pip install -r requirements.txt
python bot.py
```

### ❌ Bot không đăng nhập

**Triệu chứng**: Error "Improper token"

**Giải pháp**:
1. Check Environment Variables có đúng không
2. Verify DISCORD_TOKEN chính xác
3. Đảm bảo không có khoảng trắng thừa

### ❌ Bot "ngủ" sau 15 phút

**Lý do**: Free tier của Render

**Giải pháp**:
- Upgrade lên Starter plan ($7/tháng)
- Hoặc setup health check + external pinger

### ❌ Model không tồn tại

**Triệu chứng**: "Model file không tồn tại"

**Giải pháp**:
Bot sẽ tự động dùng phương pháp dự đoán đơn giản (fallback).

Để có ML model:
1. Train local: `python model_trainer.py`
2. Tạm thời xóa `*.pkl` khỏi `.gitignore`
3. Commit và push: `git add *.pkl && git commit -m "Add model" && git push`
4. Restore `.gitignore`

---

## 📊 Monitoring

### Xem Logs real-time

1. Vào Render Dashboard
2. Click vào service của bạn
3. Tab **"Logs"**

### Check Status

- **Live**: Bot đang chạy ✅
- **Deploy in progress**: Đang deploy 🔄
- **Failed**: Có lỗi ❌

---

## 💰 Chi phí

### Free Tier
- ✅ Miễn phí
- ✅ 750 giờ/tháng
- ⚠️ Service ngủ sau 15 phút không activity
- ⚠️ Khởi động lại mất ~30 giây

### Starter ($7/tháng)
- ✅ Chạy 24/7
- ✅ Không bao giờ ngủ
- ✅ Tốt hơn cho Discord bot

---

## 🎉 Hoàn tất!

Bot của bạn giờ đã chạy trên cloud! 🚀

**URL Service**: Render sẽ cung cấp URL (ví dụ: `https://epl-prediction-bot.onrender.com`)

**Next steps**:
- Monitor logs thường xuyên
- Test tất cả commands
- Upgrade plan nếu cần chạy 24/7
- Retrain model định kỳ

---

## 📞 Cần giúp đỡ?

- Render Docs: https://render.com/docs
- Discord.py Docs: https://discordpy.readthedocs.io/
- GitHub repo của bạn: Issues tab

**Chúc bạn deploy thành công! ⚽🤖**
