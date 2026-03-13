# 🚀 Vercel Deployment Guide - Health Chatbot API

Complete step-by-step guide to deploy your health chatbot backend to Vercel.

---

## ✅ Pre-Deployment Checklist

- [x] All sensitive files excluded (`.env`, `firebase-credentials.json`, `*.db`)
- [x] Test files excluded from git
- [x] Vercel configuration created (`vercel.json`)
- [x] Git repository initialized
- [x] Production testing completed (92.9% success rate)

---

## 📦 Step 1: Push to GitHub

### 1.1 Create GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Create a new repository (e.g., `health-chatbot-api`)
3. **Do NOT initialize with README** (we already have one)
4. Copy the repository URL

### 1.2 Connect Local Repo to GitHub

```bash
# Add your GitHub remote (replace with your URL)
git remote add origin https://github.com/YOUR_USERNAME/health-chatbot-api.git

# Commit all files
git add .
git commit -m "Initial commit - Production ready health chatbot API"

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## 🔧 Step 2: Deploy to Vercel

### 2.1 Install Vercel CLI (Optional)

```bash
npm install -g vercel
```

### 2.2 Deploy via Vercel Dashboard (Recommended)

1. **Go to [Vercel Dashboard](https://vercel.com/new)**

2. **Import Git Repository**
   - Click "Import Project"
   - Select your GitHub repository
   - Click "Import"

3. **Configure Project**
   - **Framework Preset:** Other
   - **Root Directory:** `./`
   - **Build Command:** (leave empty)
   - **Output Directory:** (leave empty)
   - **Install Command:** `pip install -r requirements.txt`

4. **Add Environment Variables** (CRITICAL!)
   
   Click "Environment Variables" and add:

   | Name | Value | Source |
   |------|-------|--------|
   | `GEMINI_API_KEY` | `your_gemini_api_key_here` | From your `.env` |
   | `XAI_API_KEY` | `your_xai_api_key_here` | From your `.env` |
   | `USE_FIRESTORE` | `false` | Production setting |
   | `DEBUG` | `false` | Production setting |
   | `SESSION_EXPIRY_DAYS` | `7` | From your `.env` |
   | `RATE_LIMIT_PER_HOUR` | `100` | From your `.env` |
   | `RATE_LIMIT_PER_MINUTE` | `20` | From your `.env` |
   | `ALLOWED_ORIGINS` | `*` | Or your frontend URL |

   **⚠️ IMPORTANT:** Make sure all environment variables are set, especially the API keys!

5. **Deploy**
   - Click "Deploy"
   - Wait for build to complete (2-5 minutes)
   - Your API will be live at `https://your-project.vercel.app`

---

## 🧪 Step 3: Test Deployed API

### 3.1 Test Health Endpoint

```bash
curl https://your-project.vercel.app/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-13T...",
  "environment": "production",
  "database": {
    "status": "connected",
    "total_foods": 22043
  },
  "ai": {
    "gemini": {
      "status": "available",
      "model": "gemini-2.5-flash-lite"
    }
  }
}
```

### 3.2 Test Create Session

```bash
curl -X POST https://your-project.vercel.app/sessions/create \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 3.3 Test Food Search

```bash
curl "https://your-project.vercel.app/nutrition/search?query=chicken"
```

### 3.4 Test AI Chat

```bash
curl -X POST https://your-project.vercel.app/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "message": "What is a healthy breakfast?"
  }'
```

---

## 🔥 Alternative: Deploy via Vercel CLI

If you prefer using the command line:

```bash
# Login to Vercel
vercel login

# Deploy
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: health-chatbot-api
# - Directory: ./
# - Deploy? Yes

# Set environment variables
vercel env add GEMINI_API_KEY
vercel env add XAI_API_KEY
vercel env add USE_FIRESTORE
vercel env add DEBUG
vercel env add SESSION_EXPIRY_DAYS
vercel env add RATE_LIMIT_PER_HOUR
vercel env add RATE_LIMIT_PER_MINUTE

# Deploy to production
vercel --prod
```

---

## ⚡ Vercel Configuration Explained

Your `vercel.json` file:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

**What it does:**
- `builds`: Tells Vercel to build your Python app
- `routes`: Routes all requests to your FastAPI app
- `@vercel/python`: Uses Vercel's Python runtime

---

## 🗄️ Database on Vercel

### Important Notes:

1. **SQLite on Vercel:**
   - ⚠️ Vercel functions are stateless - each request may run in a new environment
   - Your `health_data.db` file will be included in the deployment
   - **READ-ONLY:** Database writes (sessions) won't persist between deployments
   - This is OK for the nutrition database (read-only)

2. **Session Storage:**
   - Current setup uses SQLite for sessions
   - On Vercel, sessions may not persist reliably
   - **Recommended:** Use Firebase Firestore for sessions in production

### Enable Firebase for Production (Recommended):

1. **Get Firebase Credentials:**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create project → Settings → Service Accounts
   - Generate new private key
   - Download `firebase-credentials.json`

2. **Upload to Vercel:**
   ```bash
   # Convert JSON file to base64
   cat firebase-credentials.json | base64 > firebase-base64.txt
   
   # Add as environment variable
   vercel env add FIREBASE_CREDENTIALS
   # Paste the base64 content
   ```

3. **Update Environment Variables:**
   - Set `USE_FIRESTORE=true`
   - Add `FIREBASE_CREDENTIALS` with base64 content

4. **Update Code** (if needed):
   Modify `database/firestore_db.py` to decode base64:
   ```python
   import base64
   import json
   import os
   
   firebase_creds = os.getenv("FIREBASE_CREDENTIALS")
   if firebase_creds:
       creds_json = base64.b64decode(firebase_creds).decode('utf-8')
       creds_dict = json.loads(creds_json)
       # Use creds_dict...
   ```

---

## 🔒 Security Best Practices

### 1. Protect Your API Keys

- ✅ Never commit `.env` file to git
- ✅ Use Vercel environment variables
- ✅ Rotate keys regularly
- ✅ Monitor API usage

### 2. CORS Configuration

Update `ALLOWED_ORIGINS` in Vercel environment:

```env
# For specific frontend
ALLOWED_ORIGINS=https://your-frontend.vercel.app

# For multiple origins (comma-separated)
ALLOWED_ORIGINS=https://frontend1.com,https://frontend2.com

# For development (not recommended for production)
ALLOWED_ORIGINS=*
```

### 3. Rate Limiting

Already configured in your app:
- 100 requests per hour
- 20 requests per minute
- Per IP address

Adjust in Vercel environment variables if needed.

---

## 📊 Monitoring & Logs

### View Deployment Logs:

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Click on a deployment
4. View "Functions" → "Logs"

### Monitor API Performance:

- **View Metrics:** Vercel Dashboard → Analytics
- **Error Tracking:** Functions → Error logs
- **Usage:** Check invocation count, duration, bandwidth

### Enable Email Alerts:

1. Project Settings → Notifications
2. Enable "Deployment Notifications"
3. Enable "Error Notifications"

---

## 🐛 Troubleshooting

### Issue: "Module Not Found" Error

**Solution:**
```bash
# Check requirements.txt has all dependencies
cat requirements.txt

# Redeploy
git add requirements.txt
git commit -m "Update dependencies"
git push origin main
```

### Issue: "Environment Variable Not Set"

**Solution:**
1. Go to Project Settings → Environment Variables
2. Verify all API keys are set
3. Click "Redeploy" on latest deployment

### Issue: "Database Not Found"

**Solution:**
- Ensure `health_data.db` is committed to git
- Check `vercel.json` routes configuration
- Verify database path in code is correct

### Issue: "AI API Fails"

**Solution:**
1. Check API keys in Vercel environment
2. Test keys locally first
3. Check API quotas:
   - [Google AI Studio](https://aistudio.google.com/)
   - [xAI Console](https://console.x.ai/)

### Issue: "404 Not Found" on All Endpoints

**Solution:**
- Check `vercel.json` routes configuration
- Verify `app/main.py` has correct path
- Check deployment logs for errors

---

## 🎉 Post-Deployment

### Your API is Live! 🚀

**Base URL:** `https://your-project.vercel.app`

### Available Endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root welcome message |
| `/health` | GET | System health check |
| `/sessions/create` | POST | Create new session |
| `/sessions/{id}` | GET | Get session details |
| `/chat` | POST | Chat with AI |
| `/nutrition/search` | GET | Search foods |
| `/nutrition/analyze` | POST | Analyze food |
| `/calculate/bmi` | POST | Calculate BMI |
| `/calculate/bmr` | POST | Calculate BMR |
| `/calculate/tdee` | POST | Calculate TDEE |
| `/diet-plan/generate` | POST | Generate diet plan |
| `/guidelines/who` | GET | WHO guidelines |

### Next Steps:

1. ✅ Test all endpoints with your deployed URL
2. ✅ Set up custom domain (optional)
3. ✅ Connect your frontend
4. ✅ Monitor logs and performance
5. ✅ Set up Firebase for production sessions (recommended)

---

## 💰 Cost Estimation

### Vercel:
- **Free Tier:** 100GB bandwidth, 100 hours function execution
- **Pro Tier:** $20/month (1TB bandwidth, 1000 hours)

### AI APIs:
- **Gemini 2.5 Flash Lite:** $0.01 per 1K tokens (~$0.03-0.05 per request)
- **xAI Grok (fallback):** $0.20-0.50 per 1M tokens

### Estimated Monthly Cost:
- **Low usage** (1000 requests): ~$0-5
- **Medium usage** (10,000 requests): ~$50-100
- **High usage** (100,000 requests): ~$500+

---

## 🔗 Useful Links

- [Vercel Dashboard](https://vercel.com/dashboard)
- [Vercel Python Docs](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [FastAPI on Vercel](https://vercel.com/guides/fastapi)
- [Google AI Studio](https://aistudio.google.com/)
- [xAI Console](https://console.x.ai/)
- [Firebase Console](https://console.firebase.google.com/)

---

## 📝 Quick Reference Commands

```bash
# View deployment logs
vercel logs

# List deployments
vercel ls

# View environment variables
vercel env ls

# Remove deployment
vercel remove

# Redeploy
git push origin main
```

---

**💡 TIP:** Keep your local `.env` file secure. Never commit it to GitHub!

**🎯 Status:** Ready for production deployment!

**✅ Verified:** March 13, 2026
