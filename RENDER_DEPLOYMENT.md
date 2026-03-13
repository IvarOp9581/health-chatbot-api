# 🚀 Render Deployment Guide - Health Chatbot API

Complete guide to deploy your FastAPI backend to Render.

---

## ✅ Why Render is Better for FastAPI

- ✅ **Native Python support** - No adapters needed
- ✅ **Persistent storage** - Database survives deployments
- ✅ **Free tier** - 750 hours/month free
- ✅ **Auto-deploy** - Push to GitHub = instant deploy
- ✅ **Fast cold starts** - Better than Vercel for Python

---

## 🚀 Deploy to Render (5 Minutes)

### Step 1: Push Your Code to GitHub ✅

Already done! Your repo: https://github.com/IvarOp9581/health-chatbot-api

---

### Step 2: Create Render Account

1. Go to: https://render.com/
2. Click **"Get Started for Free"**
3. Sign up with **GitHub** (easiest way)

---

### Step 3: Create New Web Service

1. Once logged in, click **"New +"** → **"Web Service"**
2. Connect your GitHub account (if not already)
3. Select repository: **`IvarOp9581/health-chatbot-api`**
4. Click **"Connect"**

---

### Step 4: Configure Web Service

Render will auto-detect most settings, but verify these:

| Setting | Value |
|---------|-------|
| **Name** | `health-chatbot-api` (or your choice) |
| **Region** | `Oregon (US West)` (or closest to you) |
| **Branch** | `main` |
| **Root Directory** | (leave blank) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt; python database/migrate.py` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | `Free` |

**Important:** The build command will:
- Install dependencies
- Create the database from CSV (22,043 foods)

---

### Step 5: Add Environment Variables

Click **"Advanced"** → Add these environment variables:

| Variable Name | Value |
|--------------|-------|
| `GEMINI_API_KEY` | Your Gemini API key |
| `XAI_API_KEY` | Your xAI API key |
| `USE_FIRESTORE` | `false` |
| `DEBUG` | `false` |
| `SESSION_EXPIRY_DAYS` | `7` |
| `RATE_LIMIT_PER_HOUR` | `100` |
| `RATE_LIMIT_PER_MINUTE` | `20` |
| `ALLOWED_ORIGINS` | `*` |

**💡 Tip:** Copy your actual API keys from your local `API_KEYS_SECURE.md` file

---

### Step 6: Deploy!

1. Click **"Create Web Service"** at the bottom
2. Render will:
   - ⏳ Build your app (2-3 minutes)
   - 📦 Install dependencies
   - 🗄️ Create database
   - 🚀 Start your server
3. Wait for **"Live"** status (green checkmark)

---

## 🎯 After Deployment

### Your API URL:

Render will give you a URL like:
```
https://health-chatbot-api.onrender.com
```

### Test Your API:

```bash
# Health check
curl https://health-chatbot-api.onrender.com/health

# Create session
curl -X POST https://health-chatbot-api.onrender.com/sessions/create \
  -H "Content-Type: application/json" \
  -d '{}'

# Search food
curl "https://health-chatbot-api.onrender.com/nutrition/search?query=chicken"

# Chat with AI
curl -X POST https://health-chatbot-api.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "message": "What is a healthy breakfast?"
  }'
```

---

## 📊 Important Notes About Render Free Tier

### ✅ What You Get:
- 750 hours/month free
- 512 MB RAM
- Persistent disk storage (database survives)
- Auto-deploy from GitHub
- SSL certificate (HTTPS)

### ⚠️ Limitations:
- **Cold starts:** After 15 minutes of inactivity, service "spins down"
- First request after sleep takes **30-60 seconds** to wake up
- Subsequent requests are fast
- Database persists even during sleep

### 💡 Solution for Cold Starts:
- Keep service warm with a ping service (UptimeRobot, cron-job.org)
- Or upgrade to paid plan ($7/month) for always-on

---

## 🔄 Auto-Deploy on Git Push

Once set up, Render automatically redeploys when you push to GitHub:

```bash
git add .
git commit -m "Update API"
git push origin main
# Render automatically deploys in 2-3 minutes
```

---

## 🗄️ Database on Render

### Storage:
- Database lives in your service's disk
- **Persists between deployments** ✅
- Located at: `/opt/render/project/src/health_data.db`

### If You Need to Reset Database:
1. Go to Render dashboard
2. Click **"Manual Deploy"** → **"Clear build cache & deploy"**
3. This will rebuild database from CSV

---

## 📊 Monitoring Your API

### View Logs:
1. Go to your service in Render dashboard
2. Click **"Logs"** tab
3. See real-time logs:
   ```
   🚀 Starting Health Chatbot Backend...
   ✅ Database initialized
   🤖 AI Status: {'gemini': 'available'}
   ✅ Server ready!
   ```

### View Metrics:
- Click **"Metrics"** tab
- See CPU, memory, request count

---

## 🔧 Troubleshooting

### Issue: Build Failed

**Check logs for:**
- Missing dependencies in `requirements.txt`
- Database migration errors
- Python version mismatch

**Solution:**
```bash
# Test locally first
pip install -r requirements.txt
python database/migrate.py
uvicorn app.main:app --reload
```

### Issue: Service Crashing

**Check logs for:**
- Missing environment variables
- Database connection errors
- Import errors

**Solution:**
1. Verify all environment variables are set
2. Check **"Events"** tab for crash details

### Issue: Slow First Request

This is normal - service sleeps after 15 minutes of inactivity.

**Solutions:**
- Use a ping service (free)
- Upgrade to paid plan ($7/month)

---

## 🎨 Optional: Custom Domain

### Add Your Own Domain:

1. Go to **Settings** → **Custom Domains**
2. Click **"Add Custom Domain"**
3. Enter your domain: `api.yourdomain.com`
4. Add CNAME record to your DNS:
   ```
   CNAME api <your-service>.onrender.com
   ```
5. SSL certificate auto-configured ✅

---

## 💰 Cost Breakdown

### Free Tier:
- ✅ 750 hours/month free
- ✅ Perfect for testing and low-traffic apps
- ⚠️ Services spin down after 15 min inactivity

### Paid Tier ($7/month):
- ✅ Always-on (no cold starts)
- ✅ More RAM and CPU
- ✅ Priority support

---

## 🔐 Security Best Practices

### Environment Variables:
- ✅ Never commit API keys to GitHub
- ✅ Use Render's environment variable system
- ✅ Rotate keys periodically

### CORS:
Update `ALLOWED_ORIGINS` to your frontend URL:
```env
ALLOWED_ORIGINS=https://your-frontend.com
```

### Rate Limiting:
Already configured in your app:
- 100 requests/hour per IP
- 20 requests/minute per IP

---

## 📚 Quick Reference

### Render Dashboard:
https://dashboard.render.com/

### Your Repository:
https://github.com/IvarOp9581/health-chatbot-api

### Documentation:
- [Render Python Docs](https://render.com/docs/deploy-fastapi)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

## ✅ Deployment Checklist

Before deploying:
- [x] Code pushed to GitHub
- [x] `requirements.txt` exists
- [x] `render.yaml` configured
- [x] API keys ready to add
- [ ] Render account created
- [ ] Service configured
- [ ] Environment variables added
- [ ] Deployment successful
- [ ] API tested

---

## 🎉 You're Ready to Deploy!

**Next Steps:**
1. Go to https://render.com/
2. Sign up with GitHub
3. Click **"New +"** → **"Web Service"**
4. Follow the steps above
5. Your API will be live in 5 minutes! 🚀

---

**Need help?** Check the logs in Render dashboard or refer back to this guide.

**Version:** 1.0.0  
**Last Updated:** March 13, 2026  
**Deploy Time:** ~5 minutes  
**Status:** Production Ready ✅
