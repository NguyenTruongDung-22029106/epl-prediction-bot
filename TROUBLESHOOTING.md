# 🔧 TROUBLESHOOTING GUIDE

Hướng dẫn khắc phục sự cố cho EPL Prediction Bot.

---

## ❌ **Lỗi: "X has 15 features, but LogisticRegression is expecting 105 features"**

### **Nguyên nhân:**
- Render đang sử dụng **cached code** cũ
- Code mới đã push nhưng Render chưa rebuild
- Python imports bị cache

### **Giải pháp:**

#### **Option 1: Clear Build Cache (Khuyến nghị)**

1. Vào Render Dashboard: https://dashboard.render.com
2. Click vào service **"epl-prediction-bot"**
3. Click **"Manual Deploy"** (góc trên bên phải)
4. Chọn **"Clear build cache & deploy"**
5. Click **"Deploy"**

⏱️ Thời gian: 3-5 phút

---

#### **Option 2: Xóa và tạo lại service**

Nếu Option 1 không work:

1. Delete service hiện tại
2. Create new Web Service
3. Connect GitHub repo
4. Deploy lại

---

#### **Option 3: Check logs để debug**

Xem Render Logs để kiểm tra:

```bash
# Tìm dòng này:
DEBUG: Features prepared - shape: (1, X), columns: Y

# X phải là 107 (hoặc gần 105)
# Nếu X = 15 → Code cũ vẫn đang chạy
```

Nếu vẫn thấy 15 features → Render cache chưa clear.

---

## 🔄 **Kiểm tra code local vs Render**

### **Test local:**

```powershell
.\venv\Scripts\python.exe -c "from predictor import prepare_features; from data_collector import get_team_stats; h=get_team_stats('Arsenal'); a=get_team_stats('Chelsea'); df=prepare_features(h,a); print(f'Features: {len(df.columns)}')"
```

**Expected output:**
```
INFO:predictor:Prepared 107 features for prediction
Features: 107
```

### **Check Render logs:**

1. Vào Render Dashboard → Logs
2. Trigger một prediction trong Discord: `!phantich Arsenal vs Chelsea`
3. Tìm dòng:
   ```
   DEBUG: Features prepared - shape: (1, 107), columns: 107
   ```

Nếu local = 107 nhưng Render = 15 → Clear cache và redeploy.

---

## 📊 **Các lỗi khác**

### **"Model chưa được huấn luyện"**

**Nguyên nhân:** File `epl_prediction_model.pkl` không tồn tại

**Giải pháp:**
```powershell
# Train model locally
.\venv\Scripts\python.exe model_trainer.py

# Push lên GitHub
git add *.pkl
git commit -m "Add trained model"
git push
```

---

### **"Không thể lấy dữ liệu kèo"**

**Nguyên nhân:** API keys không đúng hoặc hết quota

**Giải pháp:**
- Check `.env` file có đầy đủ keys không
- Verify API keys còn valid
- Check API quota (The Odds API: 500 requests/month)

---

### **Bot không response trong Discord**

**Checklist:**
1. ✅ Bot đã login? (Check Render logs: "Bot đã đăng nhập")
2. ✅ Bot đã được invite vào server?
3. ✅ Bot có permissions? (Send Messages, Embed Links)
4. ✅ Command đúng format? (`!phantich Arsenal vs Chelsea`)

---

## 🛠️ **Force Redeploy từ Local**

Nếu cần force Render deploy ngay:

```powershell
# Empty commit để trigger auto-deploy
git commit --allow-empty -m "Force redeploy"
git push
```

Render sẽ auto-deploy sau 1-2 phút.

---

## 📝 **Debug Checklist**

Khi gặp lỗi, check theo thứ tự:

1. [ ] Local code có chạy được không? (`python bot.py`)
2. [ ] Features count local = bao nhiêu? (Should be ~107)
3. [ ] Code đã push lên GitHub chưa? (`git status`)
4. [ ] Render đã deploy version mới chưa? (Check commit hash trong Events)
5. [ ] Render logs có errors không?
6. [ ] Bot đã login thành công chưa?

---

## 🆘 **Emergency Reset**

Nếu tất cả đều fail:

### **Full Reset:**

```powershell
# 1. Delete service trên Render
# 2. Clear local cache
rm -r .venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Test local
python bot.py

# 4. Recreate Render service
# Follow RENDER.md instructions
```

---

## 📞 **Support Resources**

- **Render Docs**: https://render.com/docs
- **Discord.py Docs**: https://discordpy.readthedocs.io
- **Scikit-learn Docs**: https://scikit-learn.org

---

**Nếu vẫn gặp vấn đề, paste full error logs để debug chi tiết hơn!** 🔍
