# 📝 Tổng quan Dự án - Bot Nhà Tiên tri Ngoại Hạng Anh

## 🎯 Mục tiêu Dự án

Xây dựng một Discord bot sử dụng Machine Learning để phân tích và đưa ra khuyến nghị về kèo chấp Châu Á cho các trận đấu Ngoại Hạng Anh.

## 📂 Cấu trúc Dự án

```
Discord/
├── 📄 Core Files
│   ├── bot.py                      # Bot Discord chính với các commands
│   ├── data_collector.py           # Thu thập dữ liệu từ APIs
│   ├── model_trainer.py            # Huấn luyện ML models
│   └── predictor.py                # Logic dự đoán và khuyến nghị
│
├── 📋 Configuration
│   ├── .env                        # API keys (KHÔNG commit)
│   ├── .gitignore                  # Git ignore rules
│   ├── requirements.txt            # Python dependencies
│   └── Procfile                    # Deployment config cho Render
│
├── 📖 Documentation
│   ├── README.md                   # Hướng dẫn đầy đủ
│   ├── QUICKSTART.md               # Khởi động nhanh
│   └── DEPLOYMENT.md               # Hướng dẫn deploy
│
├── 🔧 Scripts
│   ├── setup.ps1                   # Auto setup cho Windows
│   └── start.ps1                   # Quick start script
│
└── 🤖 Generated Files (auto-created)
    ├── epl_prediction_model.pkl    # Trained ML model
    ├── scaler.pkl                  # Feature scaler
    ├── historical_odds.csv         # Dữ liệu kèo lịch sử
    └── master_dataset.csv          # Dataset hoàn chỉnh
```

## 🎮 Các Lệnh Bot

### `!lichdau`
Hiển thị lịch thi đấu Ngoại Hạng Anh trong 7 ngày tới từ Football-Data.org API.

**Output**:
- Danh sách các trận đấu sắp tới
- Thời gian (UTC)
- Trạng thái trận đấu
- Logo Premier League

### `!phantich <Đội A> vs <Đội B>`
Phân tích trận đấu và đưa ra khuyến nghị.

**Process**:
1. Thu thập thống kê của cả hai đội
2. Lấy kèo chấp Châu Á (với cache 3 giờ)
3. Chuẩn bị features
4. Dự đoán bằng ML model
5. Trả về khuyến nghị với độ tin cậy

**Output**:
- Kèo chấp Châu Á từ nhà cái
- Khuyến nghị (chọn đội nào)
- Độ tin cậy (confidence %)
- Thống kê chi tiết của cả hai đội
- Disclaimer

### `!help`
Hiển thị hướng dẫn sử dụng bot.

## 🔄 Workflow Chi tiết

### Phase 0: Setup
```
1. Install dependencies
2. Configure API keys in .env
3. Train initial model
4. Run bot
```

### Phase 1: Data Collection (data_collector.py)
```
collect_historical_odds()
    ↓
Download CSV từ football-data.co.uk
    ↓
feature_engineering()
    ↓
create_master_dataset()
    ↓
Save: master_dataset.csv
```

### Phase 2: Model Training (model_trainer.py)
```
load_dataset()
    ↓
prepare_data() → X, y
    ↓
train_test_split
    ↓
train_models()
  ├── Random Forest
  ├── Gradient Boosting
  └── Logistic Regression
    ↓
Cross-validation & Evaluation
    ↓
save_best_model()
    ↓
Save: epl_prediction_model.pkl
```

### Phase 3: Prediction (predictor.py)
```
predict_match(home_stats, away_stats, odds_data)
    ↓
load_model()
    ↓
prepare_features()
    ↓
model.predict() & predict_proba()
    ↓
Return: recommendation + confidence
```

### Phase 4: Bot Commands (bot.py)
```
Discord Command (!phantich)
    ↓
Parse team names
    ↓
get_team_stats() for both teams
    ↓
get_odds_data() with caching
    ↓
predict_match()
    ↓
Format Discord Embed
    ↓
Send to user
```

## 🧠 Machine Learning Pipeline

### Features (15 features)

**Home Team Features**:
- `home_goals_scored_avg`: Goals trung bình
- `home_goals_conceded_avg`: Thủng lưới trung bình
- `home_goals_avg`: Goals trên sân nhà
- `home_shots_per_game`: Số sút/trận
- `home_possession_avg`: Tỷ lệ kiểm soát bóng
- `home_points_last_5`: Điểm trong 5 trận gần nhất

**Away Team Features**: (tương tự)
- `away_goals_scored_avg`
- `away_goals_conceded_avg`
- `away_goals_avg`
- `away_shots_per_game`
- `away_possession_avg`
- `away_points_last_5`

**Odds Features**:
- `handicap_value`: Giá trị kèo chấp (ví dụ: -0.5, 0, +0.5)
- `home_odds`: Tỷ lệ đội nhà
- `away_odds`: Tỷ lệ đội khách

### Target Variable

`handicap_result`: 
- 1 = Đội nhà thắng kèo
- 0 = Đội khách thắng kèo hoặc hòa

### Models Tested

1. **Random Forest** (100 trees, max_depth=10)
2. **Gradient Boosting** (100 estimators, learning_rate=0.1)
3. **Logistic Regression** (max_iter=1000)

### Evaluation Metrics

- **Accuracy**: Tỷ lệ dự đoán đúng
- **Precision**: Độ chính xác của dự đoán positive
- **Recall**: Khả năng tìm ra positive cases
- **F1 Score**: Harmonic mean của Precision và Recall
- **Cross-Validation**: 5-fold CV

### Current Performance (Mock Data)

Best Model: **Logistic Regression**
- Accuracy: 72%
- F1 Score: 50%
- CV Score: 73.25% (±4.44%)

*Lưu ý: Performance sẽ tốt hơn với dữ liệu thực*

## 🔌 API Integration

### 1. Football-Data.org
- **Purpose**: Thống kê trận đấu, lịch thi đấu
- **Endpoint**: `/competitions/PL/matches`, `/teams/{id}`
- **Rate Limit**: 10 requests/phút (free tier)
- **Authentication**: X-Auth-Token header

### 2. The Odds API
- **Purpose**: Kèo cược real-time
- **Endpoint**: `/sports/soccer_epl/odds`
- **Rate Limit**: 500 requests/tháng (free tier)
- **Authentication**: API key parameter
- **Caching**: 3 giờ để tiết kiệm requests

### 3. football-data.co.uk
- **Purpose**: Dữ liệu kèo lịch sử
- **Format**: CSV files
- **No Auth**: Public data
- **Usage**: Download historical odds for training

## 💾 Data Flow

```
APIs → data_collector.py → CSV files
                              ↓
                    master_dataset.csv
                              ↓
                    model_trainer.py
                              ↓
              epl_prediction_model.pkl
                              ↓
                        predictor.py
                              ↓
                          bot.py
                              ↓
                      Discord Users
```

## 🛡️ Security & Best Practices

### Environment Variables
- Tất cả API keys trong `.env`
- File `.env` trong `.gitignore`
- KHÔNG hard-code keys trong code

### Rate Limiting
- Caching cho odds data (3 giờ)
- Retry logic với exponential backoff
- Monitor API usage

### Error Handling
- Try-catch blocks cho tất cả API calls
- Fallback methods khi model không có
- User-friendly error messages

### Logging
- INFO level cho operations bình thường
- ERROR level cho exceptions
- Logs giúp debug production issues

## 📈 Improvement Roadmap

### Short-term (1-2 tuần)
- [ ] Implement actual Football-Data API integration
- [ ] Add more features (corners, cards, etc.)
- [ ] Improve feature engineering
- [ ] Add data validation

### Medium-term (1 tháng)
- [ ] Collect real historical data
- [ ] Retrain với dữ liệu thực
- [ ] A/B test different models
- [ ] Add confidence intervals

### Long-term (2-3 tháng)
- [ ] Deep Learning models (LSTM, Transformer)
- [ ] Multi-league support
- [ ] Web dashboard
- [ ] Betting performance tracking

## 🎓 Learning Resources

### Machine Learning
- Scikit-learn documentation
- "Hands-On Machine Learning" by Aurélien Géron
- Kaggle soccer prediction competitions

### Discord Bots
- discord.py documentation
- Discord Developer Portal guides

### Football Analytics
- Statsbomb articles
- Expected Goals (xG) models
- FiveThirtyEight soccer predictions

## ⚠️ Disclaimer

**Quan trọng**: 
- Bot này chỉ mang tính giáo dục và tham khảo
- KHÔNG phải lời khuyên đầu tư
- Không đảm bảo lợi nhuận
- Cá cược có rủi ro cao
- Tuân thủ luật pháp địa phương về cá cược

## 📞 Support

- GitHub Issues: Báo lỗi và đề xuất tính năng
- Documentation: README.md, QUICKSTART.md, DEPLOYMENT.md
- Code comments: Chi tiết trong từng file

## 🎉 Acknowledgments

- **Football-Data.org**: API thống kê miễn phí
- **The Odds API**: API kèo cược
- **football-data.co.uk**: Dữ liệu lịch sử
- **discord.py**: Framework bot Discord
- **scikit-learn**: Machine Learning library

---

**Made with ⚽ and 🤖**
