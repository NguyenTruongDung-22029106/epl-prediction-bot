# ✅ CHECKLIST - Danh sách kiểm tra

Sử dụng checklist này để đảm bảo bạn đã hoàn thành tất cả các bước.

## 📦 Phase 0: Setup & Installation

- [ ] Python 3.8+ đã được cài đặt
- [ ] Virtual environment đã được tạo (`venv/`)
- [ ] Dependencies đã được cài đặt (`pip install -r requirements.txt`)
- [ ] Tất cả files trong dự án đã có

## 🔑 Phase 1: API Keys Configuration

### Discord Bot Token
- [ ] Đã tạo bot trên [Discord Developer Portal](https://discord.com/developers/applications)
- [ ] Đã copy Bot Token
- [ ] Đã enable "Message Content Intent" trong Bot settings
- [ ] Đã mời bot vào Discord server (với permissions: Send Messages, Embed Links)
- [ ] Đã điền `DISCORD_TOKEN` vào file `.env`

### Football-Data.org API Key
- [ ] Đã đăng ký tài khoản tại [Football-Data.org](https://www.football-data.org/)
- [ ] Đã lấy API key (free tier)
- [ ] Đã điền `FOOTBALL_DATA_API_KEY` vào file `.env`

### The Odds API Key
- [ ] Đã đăng ký tại [The Odds API](https://the-odds-api.com/)
- [ ] Đã lấy API key (500 requests/tháng)
- [ ] Đã điền `ODDS_API_KEY` vào file `.env`

## 🤖 Phase 2: Model Training

- [ ] Đã chạy `python model_trainer.py`
- [ ] File `epl_prediction_model.pkl` đã được tạo
- [ ] File `scaler.pkl` đã được tạo
- [ ] Test predictor thành công: `python predictor.py`

## 🚀 Phase 3: Bot Testing

- [ ] Đã chạy bot: `python bot.py`
- [ ] Bot đã đăng nhập thành công (check logs)
- [ ] Bot hiển thị status "Watching Ngoại Hạng Anh ⚽" trong Discord
- [ ] Lệnh `!help` hoạt động
- [ ] Lệnh `!lichdau` hoạt động
- [ ] Lệnh `!phantich Arsenal vs Manchester United` hoạt động

## 📊 Phase 4: Data Collection (Optional)

- [ ] Đã chạy `python data_collector.py`
- [ ] File `historical_odds.csv` đã được tạo
- [ ] File `master_dataset.csv` đã được tạo
- [ ] Đã retrain model với dữ liệu thực

## 🌐 Phase 5: Deployment (Optional)

### GitHub
- [ ] Repository đã được tạo trên GitHub
- [ ] Code đã được push (`git push`)
- [ ] File `.env` KHÔNG có trong repository (check `.gitignore`)

### Render
- [ ] Tài khoản Render đã được tạo
- [ ] Web Service đã được tạo và kết nối với GitHub
- [ ] Environment Variables đã được thêm vào Render
- [ ] Bot đã deploy thành công
- [ ] Bot hoạt động trên cloud

## 🔧 Troubleshooting Checklist

Nếu có vấn đề, kiểm tra các điểm sau:

### Bot không khởi động
- [ ] Virtual environment đã được kích hoạt?
- [ ] Dependencies đã được cài đặt?
- [ ] File `.env` có tồn tại?
- [ ] `DISCORD_TOKEN` có đúng không?
- [ ] Token có expired không?

### Lệnh không hoạt động
- [ ] Bot có quyền "Send Messages" không?
- [ ] Bot có quyền "Embed Links" không?
- [ ] "Message Content Intent" đã được enable?
- [ ] Prefix đúng là `!` không?

### Không lấy được dữ liệu
- [ ] API keys còn hiệu lực?
- [ ] Đã vượt quá rate limit chưa?
- [ ] Internet connection ổn định?
- [ ] API endpoints có thay đổi không?

### Model không dự đoán
- [ ] File `epl_prediction_model.pkl` có tồn tại?
- [ ] Đã chạy `python model_trainer.py`?
- [ ] Features có khớp với training không?

## 📝 Maintenance Checklist (Hàng tháng)

- [ ] Kiểm tra API usage (đảm bảo không vượt quá giới hạn)
- [ ] Thu thập dữ liệu mới: `python data_collector.py`
- [ ] Retrain model: `python model_trainer.py`
- [ ] Test bot sau khi retrain
- [ ] Update documentation nếu có thay đổi
- [ ] Check logs cho errors
- [ ] Monitor bot performance

## 🎯 Advanced Checklist (Nâng cao)

- [ ] Đã thêm logging vào file
- [ ] Đã setup monitoring/alerting
- [ ] Đã implement A/B testing
- [ ] Đã track prediction accuracy
- [ ] Đã tối ưu hóa API calls
- [ ] Đã implement database cho persistent storage
- [ ] Đã thêm unit tests
- [ ] Đã setup CI/CD pipeline

## 🏆 Production Ready Checklist

Trước khi đưa bot vào production:

- [ ] Tất cả features đã được test kỹ
- [ ] Error handling đầy đủ
- [ ] Logging comprehensive
- [ ] API rate limiting implemented
- [ ] Security best practices followed
- [ ] Documentation đầy đủ
- [ ] Backup strategy có sẵn
- [ ] Monitoring đã setup
- [ ] Disclaimer rõ ràng cho users
- [ ] Legal compliance checked

## 📋 Quick Status Check

Chạy các lệnh sau để kiểm tra nhanh:

```bash
# Check Python version
python --version

# Check if virtual environment is activated
echo $env:VIRTUAL_ENV  # PowerShell
echo $VIRTUAL_ENV      # Bash

# Check if packages installed
pip list | grep discord
pip list | grep pandas
pip list | grep scikit-learn

# Check if .env exists
Test-Path .env  # PowerShell
ls -la .env     # Bash

# Check if model exists
Test-Path epl_prediction_model.pkl  # PowerShell
ls -la *.pkl                         # Bash

# Test predictor
python predictor.py

# Test bot (dry run)
# Sẽ fail nếu DISCORD_TOKEN không đúng
python -c "from bot import *; print('Bot imports OK')"
```

## ✨ All Done?

Nếu tất cả các mục trong "Phase 0-3" đã được check:

🎉 **Chúc mừng! Bot của bạn đã sẵn sàng!** 🎉

Bước tiếp theo:
1. Đọc `QUICKSTART.md` để chạy bot nhanh
2. Đọc `README.md` để hiểu chi tiết
3. Đọc `DEPLOYMENT.md` để deploy lên cloud
4. Đọc `PROJECT_OVERVIEW.md` để hiểu kiến trúc

---

**Happy coding! ⚽🤖**
