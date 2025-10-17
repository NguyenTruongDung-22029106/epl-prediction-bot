# 🚀 QUICKSTART - Khởi động nhanh

Hướng dẫn nhanh để chạy bot trong 5 phút!

## ⚡ Các bước nhanh

### 1️⃣ Cài đặt Dependencies (30 giây)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2️⃣ Cấu hình API Keys (2 phút)

Mở file `.env` và điền thông tin:

```env
DISCORD_TOKEN=your_discord_bot_token_here
FOOTBALL_DATA_API_KEY=your_football_data_api_key_here
ODDS_API_KEY=your_odds_api_key_here
```

**Lấy API Keys:**
- **Discord**: https://discord.com/developers/applications (Tạo bot mới)
- **Football-Data**: https://www.football-data.org/ (Đăng ký miễn phí)
- **The Odds API**: https://the-odds-api.com/ (Đăng ký miễn phí)

### 3️⃣ Train Model (30 giây)

```bash
python model_trainer.py
```

Bot sẽ tự động tạo mock data và train model nếu chưa có dữ liệu thực.

### 4️⃣ Chạy Bot! (Ngay lập tức)

```bash
python bot.py
```

## 🎮 Test Bot

Trong Discord channel, thử các lệnh:

```
!help
!lichdau
!phantich Arsenal vs Manchester United
```

## 📊 Thu thập dữ liệu thực (Tùy chọn)

Để có dữ liệu thực từ các mùa giải trước:

```bash
python data_collector.py
```

Sau đó retrain model:

```bash
python model_trainer.py
```

## ⚠️ Troubleshooting Nhanh

**Bot không khởi động?**
- Kiểm tra `DISCORD_TOKEN` trong `.env`
- Đảm bảo đã kích hoạt virtual environment

**Lỗi import?**
- Chạy lại: `pip install -r requirements.txt`

**Model không dự đoán?**
- Chạy: `python model_trainer.py` để tạo model

## 🎯 Tiếp theo

1. Mời bot vào Discord server của bạn
2. Thử các lệnh phân tích
3. Đọc README.md để hiểu chi tiết hơn
4. Deploy lên Render để bot chạy 24/7

---

**Chúc mừng! Bot của bạn đã sẵn sàng! ⚽🤖**
