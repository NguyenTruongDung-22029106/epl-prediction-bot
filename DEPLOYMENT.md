# 🚀 Hướng dẫn Deploy lên Render

Hướng dẫn chi tiết để deploy bot lên Render và chạy 24/7 miễn phí.

## 📋 Yêu cầu

- Tài khoản GitHub
- Tài khoản Render (miễn phí)
- Code đã được push lên GitHub repository

## 🔧 Bước 1: Chuẩn bị Code

### 1.1. Khởi tạo Git repository

```bash
git init
git add .
git commit -m "Initial commit: EPL Prediction Bot"
```

### 1.2. Tạo repository trên GitHub

1. Truy cập https://github.com/new
2. Tạo repository mới (ví dụ: `epl-prediction-bot`)
3. **KHÔNG** chọn "Initialize with README" (vì bạn đã có code)

### 1.3. Push code lên GitHub

```bash
git remote add origin https://github.com/your-username/epl-prediction-bot.git
git branch -M main
git push -u origin main
```

⚠️ **Lưu ý**: File `.env` sẽ KHÔNG được push lên GitHub (đã có trong `.gitignore`)

## ☁️ Bước 2: Deploy lên Render

### 2.1. Tạo tài khoản Render

1. Truy cập https://render.com/
2. Đăng ký (có thể dùng GitHub account)
3. Xác nhận email

### 2.2. Tạo Web Service mới

1. Đăng nhập Render Dashboard
2. Click **"New +"** → **"Web Service"**
3. Chọn **"Build and deploy from a Git repository"**
4. Click **"Next"**

### 2.3. Kết nối GitHub Repository

1. Click **"Connect account"** để kết nối GitHub
2. Authorize Render truy cập GitHub repositories
3. Tìm và chọn repository `epl-prediction-bot`
4. Click **"Connect"**

### 2.4. Cấu hình Service

Điền thông tin như sau:

- **Name**: `epl-prediction-bot` (hoặc tên bạn muốn)
- **Region**: Chọn region gần bạn nhất
- **Branch**: `main`
- **Root Directory**: Để trống
- **Runtime**: `Python 3`
- **Build Command**: 
  ```
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```
  python bot.py
  ```
- **Instance Type**: **Free** (chọn plan miễn phí)

### 2.5. Thêm Environment Variables

Kéo xuống phần **Environment Variables** và thêm:

| Key | Value |
|-----|-------|
| `DISCORD_TOKEN` | `your_actual_discord_token` |
| `FOOTBALL_DATA_API_KEY` | `your_actual_football_data_key` |
| `ODDS_API_KEY` | `your_actual_odds_api_key` |

⚠️ **Quan trọng**: Nhập giá trị THỰC của các API keys, không phải placeholder!

### 2.6. Deploy!

1. Click **"Create Web Service"**
2. Đợi Render build và deploy (khoảng 2-5 phút)
3. Xem logs để kiểm tra bot có chạy thành công không

## ✅ Bước 3: Kiểm tra Bot

### 3.1. Xem Logs

Trong Render dashboard:
- Tab **"Logs"** hiển thị output của bot
- Bạn sẽ thấy message: `Bot đã đăng nhập: [TÊN BOT]`

### 3.2. Test trong Discord

1. Mở Discord server nơi bot được mời vào
2. Thử lệnh:
   ```
   !help
   !lichdau
   ```

## 🔄 Bước 4: Cập nhật Bot

Mỗi khi bạn thay đổi code:

```bash
git add .
git commit -m "Update: mô tả thay đổi"
git push
```

Render sẽ **tự động** phát hiện thay đổi và deploy lại!

## 🎯 Các vấn đề thường gặp

### ❌ Bot không khởi động

**Triệu chứng**: Logs hiển thị lỗi khi khởi động

**Giải pháp**:
1. Kiểm tra Environment Variables đã đúng chưa
2. Verify `DISCORD_TOKEN` còn hiệu lực
3. Xem logs để tìm lỗi cụ thể

### ❌ Build failed

**Triệu chứng**: "Build failed" trong quá trình deployment

**Giải pháp**:
1. Kiểm tra `requirements.txt` có đúng format không
2. Xem Build logs để tìm package nào bị lỗi
3. Thử build local trước: `pip install -r requirements.txt`

### ❌ Model không tồn tại

**Triệu chứng**: Bot báo "Model file không tồn tại"

**Giải pháp**:
- Bot sẽ tự động dùng phương pháp dự đoán đơn giản
- Để có model ML, bạn cần:
  1. Train model local: `python model_trainer.py`
  2. Commit file `.pkl`: Xóa `*.pkl` khỏi `.gitignore` tạm thời
  3. Push lên GitHub
  4. Restore `.gitignore`

**Lưu ý**: File `.pkl` có thể lớn, cân nhắc dùng Git LFS

### 💤 Bot ngủ sau 15 phút không hoạt động

**Vấn đề**: Free tier của Render sẽ tắt service sau 15 phút không có activity

**Giải pháp**:
1. **Upgrade** lên Paid plan ($7/tháng) để chạy 24/7
2. Hoặc dùng service khác như:
   - Heroku Worker Dyno
   - Railway
   - Fly.io
3. Hoặc chạy bot trên máy tính cá nhân

## 🔄 Retrain Model định kỳ

Để cập nhật model với dữ liệu mới:

### Cách 1: Local → Push

```bash
# Local machine
python data_collector.py
python model_trainer.py

# Tạm thời xóa *.pkl khỏi .gitignore
git add epl_prediction_model.pkl scaler.pkl
git commit -m "Update: retrained model"
git push
```

### Cách 2: Script tự động (Nâng cao)

Tạo GitHub Action để tự động retrain mỗi tháng:

```yaml
# .github/workflows/retrain.yml
name: Retrain Model
on:
  schedule:
    - cron: '0 0 1 * *'  # 1st of every month
  workflow_dispatch:
jobs:
  retrain:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python data_collector.py
      - run: python model_trainer.py
      - run: |
          git config user.name "Bot"
          git config user.email "bot@example.com"
          git add *.pkl
          git commit -m "Auto retrain model"
          git push
```

## 📊 Monitoring

### Xem logs real-time

```bash
# Trong Render dashboard, tab Logs
# Hoặc dùng Render CLI:
render logs -f
```

### Kiểm tra health

- Render cung cấp status page
- Xem "Last Deploy" time để verify deploy thành công

## 💰 Chi phí

- **Free Tier**:
  - 750 giờ/tháng
  - Service ngủ sau 15 phút không activity
  - Đủ cho testing và personal use

- **Starter ($7/tháng)**:
  - Chạy 24/7
  - Không ngủ
  - Phù hợp cho production

## 🎉 Hoàn tất!

Bot của bạn giờ đã chạy trên cloud! 

**Next steps**:
- Monitor logs thường xuyên
- Check API usage để không vượt quá limit
- Retrain model định kỳ
- Thêm features mới!

---

**Chúc bạn deploy thành công! 🚀⚽🤖**
