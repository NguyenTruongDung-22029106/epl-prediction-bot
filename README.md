# ⚽ Bot "Nhà Tiên tri Ngoại Hạng Anh" 🤖

Bot Discord sử dụng Machine Learning để phân tích và đưa ra khuyến nghị về kèo chấp Châu Á cho các trận đấu Ngoại Hạng Anh.

## 🌟 Tính năng

- **📅 Lịch thi đấu**: Xem lịch thi đấu Ngoại Hạng Anh 7 ngày tới
- **🔮 Phân tích trận đấu**: Phân tích dựa trên Machine Learning và đưa ra khuyến nghị về kèo chấp
- **📊 Thống kê chi tiết**: Hiển thị thống kê form, goals, và các chỉ số quan trọng

## 📋 Yêu cầu

- Python 3.8+
- Discord Bot Token
- Football-Data.org API Key (miễn phí)
- The Odds API Key (miễn phí, 500 requests/tháng)
- (Tùy chọn) Google AI Studio API Key (`GOOGLE_API_KEY`) để tạo phân tích ngôn ngữ tự động
- (Tùy chọn) API-Football RapidAPI Key (`RAPIDAPI_KEY`) nếu muốn dữ liệu trận đấu real-time thay cho Football-Data.org

## 🚀 Cài đặt

### 1. Clone repository

```bash
 **📊 Thống kê chi tiết**: Hiển thị thống kê form, goals, và các chỉ số quan trọng
 **📈 Multi-line Over/Under**: Xác suất cho các mốc 1.5, 2.5, 3.5 với bảng tỷ lệ
 **🎯 Poisson Correct Score**: Dự đoán top 5 tỉ số khả dĩ và gợi ý tỉ số chính
 **🧠 AI Insight (tuỳ chọn)**: Nếu có `GOOGLE_API_KEY`, bot tạo đoạn phân tích tự nhiên bằng Gemini
cd Discord
```

### 2. Tạo virtual environment

Khi chạy trên Render (web service):
Build Command:
```bash
pip install -r requirements.txt
```
Start Command:
```bash
python bot.py
```
Health endpoints:
```
GET /health   -> {"status":"healthy"}
GET /token    -> Thông tin kiểm tra token (masked)
```
```powershell
 Dự đoán tổng số bàn (Over/Under line 2.5 + bảng O/U đa mốc 1.5 / 2.5 / 3.5)
 Dự đoán tỉ số chính xác (Poisson top 5 + tỉ số gợi ý)
```

### 3. Cài đặt dependencies
└── poisson_model.py            # Logic Poisson cho tỉ số đúng

```bash
pip install -r requirements.txt
```

4. Cấu hình:
    - Build Command:
       ```bash
       pip install -r requirements.txt
       ```
    - Start Command:
       ```bash
       python bot.py
       ```
5. Environment Variables bắt buộc / khuyến nghị:
    - `DISCORD_TOKEN` (bắt buộc)
    - `FOOTBALL_DATA_API_KEY` (khuyến nghị)
    - `ODDS_API_KEY` (khuyến nghị để lấy odds thật + caching 3h)
    - `GOOGLE_API_KEY` (tuỳ chọn AI insight)
    - `RAPIDAPI_KEY` (tuỳ chọn API-Football, fallback nếu 403)
6. Health check: đảm bảo `/health` trả về JSON
7. Nếu log báo "Improper token has been passed" → regenerate Discord Bot Token và cập nhật lại.
### 4. Cấu hình API Keys

Tạo file `.env` từ template và điền thông tin:

```bash
copy .env.example .env   # Windows PowerShell
```

Sau đó mở file `.env` và điền các API keys:

```env
DISCORD_TOKEN=your_discord_bot_token_here
FOOTBALL_DATA_API_KEY=your_football_data_api_key_here
ODDS_API_KEY=your_odds_api_key_here
```

   - Truy cập [Discord Developer Portal](https://discord.com/developers/applications)
   - Tạo New Application

---
_Last updated: Multi-line O/U, Poisson score prediction, AI insight, Render deployment notes._
   - Vào tab Bot và copy token

2. **Football-Data.org API Key**:
   - Đăng ký tại [Football-Data.org](https://www.football-data.org/)
   - Lấy API key miễn phí (10 requests/phút)

3. **The Odds API Key**:
   - Đăng ký tại [The Odds API](https://the-odds-api.com/)
   - Lấy API key miễn phí (500 requests/tháng)

4. **Google AI Studio (Gemini) API Key - tùy chọn**:
5. **API-Football RapidAPI Key - tùy chọn**:
   - Đăng ký tại RapidAPI và subscribe [API-Football](https://rapidapi.com/api-sports/api/api-football/)
   - Lấy key và thêm vào `RAPIDAPI_KEY`
   - Cho phép lấy fixtures gần nhất của đội để tính goals/form (ưu tiên dùng trước Football-Data; nếu lỗi sẽ fallback)
   - Truy cập [Google AI Studio](https://aistudio.google.com/) đăng ký và tạo API Key
   - Thêm vào `.env` dưới tên `GOOGLE_API_KEY`
   - Nếu không có key này bot vẫn chạy bình thường, chỉ bỏ qua phần "AI Phân Tích"

### 5. Thu thập dữ liệu và Training Model

#### Thu thập dữ liệu lịch sử:

```bash
python data_collector.py
```

Lệnh này sẽ:
- Tải dữ liệu kèo lịch sử từ football-data.co.uk
- Tạo file `historical_odds.csv`
- Thực hiện feature engineering
- Tạo file `master_dataset.csv`

#### Huấn luyện model:

```bash
python model_trainer.py
```

Lệnh này sẽ:
- Load dữ liệu từ `master_dataset.csv`
- Huấn luyện nhiều models (Random Forest, Gradient Boosting, Logistic Regression)
- So sánh performance
- Lưu model tốt nhất vào `epl_prediction_model.pkl`

**Lưu ý**: Nếu chưa có dữ liệu thực, script sẽ tạo mock data để test.

### 6. Chạy Bot

```bash
python bot.py
```

## 🎮 Sử dụng

### Lệnh Bot

#### `!lichdau`
Hiển thị lịch thi đấu Ngoại Hạng Anh trong 7 ngày tới.

```
!lichdau
```

#### `!phantich <Đội A> vs <Đội B>`
Phân tích trận đấu và đưa ra khuyến nghị về kèo chấp Châu Á.

```
!phantich Arsenal vs Manchester United
```

Kết quả sẽ bao gồm:
- Kèo chấp Châu Á từ nhà cái
- Khuyến nghị của bot (chọn đội nào)
- Độ tin cậy (xác suất từ model)
- Thống kê chi tiết của hai đội
- Dự đoán tổng số bàn (Over/Under line 2.5)
- Dự đoán tỉ số chính xác (Poisson top 5)
- (Nếu cấu hình `GOOGLE_API_KEY`) Phân tích ngôn ngữ tự động AI
- Disclaimer về tính tham khảo

#### `!help`
Hiển thị hướng dẫn sử dụng.

```
!help
```

## 📁 Cấu trúc Dự án

```
Discord/
├── bot.py                      # Bot Discord chính
├── data_collector.py           # Thu thập và xử lý dữ liệu
├── model_trainer.py            # Huấn luyện Machine Learning model
├── predictor.py                # Logic dự đoán
├── poisson_model.py            # Mô hình Poisson cho tỉ số
├── ai_helper.py                # Tích hợp Google AI Studio (tùy chọn)
├── requirements.txt            # Dependencies
├── .env                        # API keys (không commit)
├── .gitignore                 # Ignore sensitive files
├── README.md                   # Hướng dẫn này
├── Procfile                    # Cho deployment trên Render
│
├── historical_odds.csv         # Dữ liệu kèo lịch sử (tự động tạo)
├── master_dataset.csv          # Dataset hoàn chỉnh (tự động tạo)
└── epl_prediction_model.pkl    # Model đã training (tự động tạo)
└── epl_goals_model.pkl         # Model dự đoán tổng bàn thắng (tự động tạo)
```

## 🔧 Deployment lên Render

### 1. Push code lên GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Tạo Web Service trên Render

1. Đăng nhập [Render](https://render.com/)
2. Tạo New Web Service
3. Kết nối với GitHub repository
4. Cấu hình:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. Thêm Environment Variables:
   - `DISCORD_TOKEN`
   - `FOOTBALL_DATA_API_KEY`
   - `ODDS_API_KEY`

### 3. Deploy

Nhấn "Create Web Service" và đợi deployment hoàn tất.

## 📊 Chi tiết Kỹ thuật

### Machine Learning Pipeline

1. **Data Collection**:
   - Football-Data.org API cho thống kê trận đấu
   - football-data.co.uk cho dữ liệu kèo lịch sử

2. **Feature Engineering**:
   - Form 5 trận gần nhất
   - Goals scored/conceded average
   - Home/Away performance
   - Head-to-head history
   - Handicap value và odds

3. **Models**:
   - Random Forest Classifier
   - Gradient Boosting Classifier
   - Logistic Regression

4. **Evaluation**:
   - Accuracy, Precision, Recall, F1 Score
   - 5-fold Cross Validation

### API Rate Limits

- **Football-Data.org**: 10 requests/phút (free tier)
- **The Odds API**: 500 requests/tháng (free tier)

Bot có caching mechanism để tránh vượt quá giới hạn:
- Cache kèo cược trong 3 giờ
- Reuse data cho cùng một trận đấu

## ⚠️ Disclaimer

**Dự đoán của bot chỉ mang tính tham khảo dựa trên phân tích thống kê và Machine Learning. Đây không phải lời khuyên đầu tư hay cá cược. Vui lòng cân nhắc kỹ và tự chịu trách nhiệm cho các quyết định của mình.**

## 🔄 Bảo trì và Cập nhật

### Retrain Model

Model nên được retrain định kỳ (mỗi tháng) để cập nhật với dữ liệu mới:

```bash
# Thu thập dữ liệu mới
python data_collector.py

# Retrain model
python model_trainer.py
```

### Monitoring

Theo dõi số lượng API calls để đảm bảo không vượt quá giới hạn:
- Check logs thường xuyên
- Monitor bot performance trên Discord

## 🐛 Troubleshooting

### Bot không khởi động
- Kiểm tra `DISCORD_TOKEN` trong file `.env`
- Kiểm tra logs để xem lỗi cụ thể

### Không lấy được dữ liệu
- Verify API keys còn hiệu lực
- Check rate limits
- Kiểm tra internet connection

### Model không dự đoán được
- Đảm bảo đã chạy `model_trainer.py` để tạo model
- Check file `epl_prediction_model.pkl` có tồn tại không

## 📝 License

MIT License

## 👥 Contribution

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

Mọi thắc mắc và góp ý, vui lòng tạo issue trên GitHub.

---

**Chúc bạn sử dụng bot thành công! ⚽🤖**
