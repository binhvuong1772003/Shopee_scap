# Deploy trên Render.com

## ✅ Ưu điểm Render.com:

- ✅ **FREE** - 750 giờ/tháng
- ✅ **Không cần thẻ tín dụng**
- ✅ **Auto deploy** từ GitHub
- ✅ **SSL miễn phí**

## ⚠️ Hạn chế:

- ⚠️ RAM 512MB (ít, nhưng đủ cho Playwright)
- ⚠️ Sleep sau 15 phút không dùng (free plan)
- ⚠️ Cold start ~30s
- ⚠️ Vẫn có thể bị anti-bot

## 🚀 Cách Deploy:

### Bước 1: Push code lên GitHub

```bash
cd render_scraper

# Init git
git init
git add .
git commit -m "Initial commit"

# Push lên GitHub
git remote add origin https://github.com/your-username/shopee-scraper.git
git push -u origin main
```

### Bước 2: Tạo Web Service trên Render

1. Vào: https://render.com/
2. Đăng ký bằng GitHub (không cần thẻ)
3. Click **New** → **Web Service**
4. Connect GitHub repo: `shopee-scraper`
5. Cấu hình:
   - **Name:** `shopee-scraper`
   - **Region:** `Singapore` (gần VN nhất)
   - **Branch:** `main`
   - **Root Directory:** `render_scraper` (nếu code trong subfolder)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt && playwright install chromium`
   - **Start Command:** `python main.py`
   - **Plan:** `Free`

### Bước 3: Set Environment Variables

Trong Render dashboard:

1. Vào **Environment** tab
2. Add variable:
   - **Key:** `SHOPEE_COOKIES`
   - **Value:** Paste JSON cookies từ `cookie.json`

```json
[{"name":"SPC_U","value":"...","domain":".shopee.vn"}...]
```

3. Click **Save Changes**

### Bước 4: Deploy

Click **Create Web Service** → Đợi deploy (~5 phút)

## 📡 Sử dụng API:

### URL của bạn:

```
https://shopee-scraper.onrender.com
```

### Endpoints:

**1. Health check:**
```bash
curl https://shopee-scraper.onrender.com/api/health
```

**2. Scrape fresh data:**
```bash
curl https://shopee-scraper.onrender.com/api/scrape
```

**3. Get cached data:**
```bash
curl https://shopee-scraper.onrender.com/api/offers
```

## 🔄 Auto Scrape:

Render free plan sleep sau 15 phút. Để keep alive:

### Cách 1: Cron job từ máy khác

```bash
# Crontab (mỗi 30 phút)
*/30 * * * * curl https://shopee-scraper.onrender.com/api/scrape
```

### Cách 2: UptimeRobot (Free)

1. Vào: https://uptimerobot.com/
2. Add monitor:
   - **Type:** HTTP(s)
   - **URL:** `https://shopee-scraper.onrender.com/api/scrape`
   - **Interval:** 30 minutes
3. Save

## 🔧 Troubleshooting:

### Lỗi: Out of memory

Render free plan chỉ 512MB. Giảm memory:

```python
# Trong main.py
browser = await p.chromium.launch(
    headless=True,
    args=[
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-images',  # Không load ảnh
        '--disable-extensions',
        '--single-process'
    ]
)
```

### Lỗi: Bị CAPTCHA

Cookies hết hạn. Update cookies:

1. Lấy cookies mới từ browser
2. Vào Render dashboard → Environment
3. Update `SHOPEE_COOKIES`
4. Redeploy

### Lỗi: Service sleeping

Free plan sleep sau 15 phút. Dùng UptimeRobot để ping.

## 💡 Tips:

1. **Keep alive:** Dùng UptimeRobot ping mỗi 14 phút
2. **Update cookies:** Mỗi 1-2 tuần
3. **Monitor logs:** Vào Render dashboard → Logs
4. **Upgrade nếu cần:** $7/tháng cho 512MB RAM + no sleep

## 🎯 Kết luận:

**Render.com phù hợp nếu:**
- ✅ Không có thẻ tín dụng
- ✅ Chấp nhận cold start
- ✅ Không cần scrape liên tục

**Không phù hợp nếu:**
- ❌ Cần scrape real-time
- ❌ Cần uptime 100%
- ❌ Shopee anti-bot quá mạnh

## 🔄 Alternative:

Nếu Render không work do anti-bot, dùng:
- **Local machine** + `auto_scraper_cdp.py` (FREE, 100% work)
- **VPS rẻ** ($3-5/tháng) + `server_scraper.py`
