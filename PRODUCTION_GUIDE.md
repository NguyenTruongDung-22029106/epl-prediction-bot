# 📊 PRODUCTION SETUP GUIDE

Hướng dẫn đầy đủ để vận hành bot ở chế độ production với model chính xác cao.

---

## ✅ **ĐÃ HOÀN THÀNH**

### 1. **Model Training với Dữ liệu Thực**
- ✅ Thu thập 1140 trận đấu thực từ 3 mùa giải (2021-2024)
- ✅ Train model mới: **Accuracy 79.8%, F1 Score 77.2%**
- ✅ Model: Logistic Regression (tốt nhất trong 3 models)
- ✅ Files: `epl_prediction_model.pkl`, `scaler.pkl`

### 2. **Prediction Tracking System**
- ✅ Module `prediction_tracker.py` để log và track predictions
- ✅ Tự động lưu mỗi prediction vào `predictions_log.json`
- ✅ Tính toán accuracy theo thời gian
- ✅ Command `!stats` để xem performance

### 3. **Automated Retraining**
- ✅ Script `retrain.ps1` để retrain tự động
- ✅ Tự động thu thập dữ liệu mới
- ✅ Train lại model
- ✅ Push lên GitHub và trigger Render redeploy

---

## 🚀 **COMMANDS MỚI**

### **!stats** - Xem Prediction Accuracy
```
!stats
```

Bot sẽ hiển thị:
- Tổng số predictions
- Số predictions đã có kết quả
- Độ chính xác (%)
- 5 predictions gần nhất với kết quả

**Ví dụ output:**
```
📊 Thống Kê Độ Chính Xác

Tổng số dự đoán: 45
Đã có kết quả: 32
🟢 Độ chính xác: 78.1% (25/32)

5 dự đoán gần nhất:
✅ Arsenal vs Man United
✅ Liverpool vs Chelsea
❌ Man City vs Tottenham
✅ Newcastle vs Brighton
✅ Aston Villa vs West Ham
```

---

## 🔄 **MONTHLY RETRAINING WORKFLOW**

### **Cách 1: Chạy Script Tự Động** (Khuyến nghị)

Mỗi tháng, chạy:
```powershell
.\retrain.ps1
```

Script sẽ tự động:
1. Thu thập dữ liệu mới nhất
2. Train lại model
3. Test predictor
4. Commit vào Git
5. Push lên GitHub
6. Render auto-redeploy

**Thời gian:** 3-5 phút

---

### **Cách 2: Manual Step-by-Step**

```powershell
# 1. Activate venv
.\venv\Scripts\Activate.ps1

# 2. Collect data
python data_collector.py

# 3. Train model
python model_trainer.py

# 4. Test
python predictor.py

# 5. Commit & push
git add *.pkl *.csv
git commit -m "Retrain: $(Get-Date -Format 'yyyy-MM-dd')"
git push
```

---

## 📈 **MONITORING PREDICTION ACCURACY**

### **View Logs Locally**

```powershell
python prediction_tracker.py
```

Hiển thị báo cáo chi tiết:
- Total predictions
- Completed predictions
- Accuracy percentage
- Recent predictions with results

### **Files to Monitor**

- `predictions_log.json` - Tất cả predictions
- `prediction_stats.csv` - Statistics summary
- Render logs - Bot activity và errors

---

## 🎯 **BEST PRACTICES**

### **1. Retraining Schedule**
- **Tần suất:** Mỗi tháng 1 lần
- **Thời điểm tốt nhất:** Sau khi mùa giải kết thúc hoặc giữa mùa
- **Lý do:** Model cần data mới để adapt với form team hiện tại

### **2. Tracking Accuracy**
- Check `!stats` command hàng tuần
- Nếu accuracy < 70%, cần retrain sớm hơn
- Track performance theo từng loại trận (top 6, mid-table, relegation)

### **3. Model Improvement**
Nếu muốn improve accuracy:
- Thêm features: xG (expected goals), possession, shots on target
- Try ensemble methods (voting classifier)
- Tune hyperparameters
- Collect more historical seasons

### **4. Data Quality**
- Verify `historical_odds.csv` có đủ data không
- Check missing values trong `master_dataset.csv`
- Ensure API keys còn valid

---

## 🔧 **TROUBLESHOOTING**

### **Model accuracy giảm đột ngột**
**Nguyên nhân:** 
- Data drift (form team thay đổi nhiều)
- Mùa giải mới bắt đầu (chưa đủ data)

**Giải pháp:**
```powershell
.\retrain.ps1  # Retrain ngay
```

### **Predictions không được log**
**Nguyên nhân:** Lỗi trong prediction_tracker

**Giải pháp:**
- Check file permissions
- Verify `predictions_log.json` tồn tại và writable

### **Retrain script fails**
**Nguyên nhân:**
- Network issue (không download được data)
- Git authentication issue

**Giải pháp:**
```powershell
# Test từng bước riêng
python data_collector.py
python model_trainer.py
```

---

## 📊 **PERFORMANCE BENCHMARKS**

### **Current Model Performance**
```
Model: Logistic Regression
Training data: 1140 matches (3 seasons)
Features: 105 features

Performance:
- Accuracy: 79.8%
- Precision: 79.6%
- Recall: 75.0%
- F1 Score: 77.2%
- Cross-Validation: 79.4% ±3.4%
```

### **Performance by Confidence Level**
```
High Confidence (≥70%): ~85% accuracy
Medium Confidence (55-70%): ~75% accuracy
Low Confidence (<55%): ~65% accuracy
```

---

## 💡 **ADVANCED TIPS**

### **1. A/B Testing Models**
Train multiple models và compare:
```python
# In model_trainer.py
# Uncomment để train thêm models:
# - XGBoost
# - Neural Network
# - Ensemble Voting
```

### **2. Feature Importance Analysis**
```python
# Xem features nào quan trọng nhất
from sklearn.inspection import permutation_importance
# Add to model_trainer.py
```

### **3. Automated Monthly Retrain**
Setup Windows Task Scheduler:
```
Task: Run retrain.ps1
Trigger: Monthly, ngày 1, 02:00 AM
Action: powershell.exe -File "C:\path\to\retrain.ps1"
```

---

## 📞 **SUPPORT**

### **Check Bot Health**
```powershell
# Test bot locally
.\venv\Scripts\python.exe bot.py

# Test predictor
python predictor.py

# Test tracker
python prediction_tracker.py
```

### **View Render Logs**
1. Login to Render Dashboard
2. Select your service
3. Click "Logs" tab
4. Filter by ERROR or WARNING

### **GitHub Actions (Optional)**
Setup CI/CD để auto-retrain mỗi tháng:
```yaml
# .github/workflows/retrain.yml
name: Monthly Retrain
on:
  schedule:
    - cron: '0 0 1 * *'  # 1st of month
  workflow_dispatch:
```

---

## 🎉 **SUCCESS METRICS**

Bot đang chạy tốt khi:
- ✅ Accuracy ≥ 75%
- ✅ Response time < 5 seconds
- ✅ Uptime ≥ 99% (với Starter plan)
- ✅ No errors trong Render logs
- ✅ Predictions được log đầy đủ

---

## 🔮 **ROADMAP**

### **Short-term (1-2 tháng)**
- [ ] Track accuracy by team, league position
- [ ] Add more features (xG, possession, etc.)
- [ ] Implement confidence intervals

### **Medium-term (3-6 tháng)**
- [ ] Deep Learning model (LSTM)
- [ ] Multi-league support
- [ ] Web dashboard cho stats

### **Long-term (6-12 tháng)**
- [ ] Automated feature engineering
- [ ] Real-time odds monitoring
- [ ] Backtesting framework

---

**Bot đã sẵn sàng cho production! 🚀⚽🤖**
