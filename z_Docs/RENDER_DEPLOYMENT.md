# Deploying SC Backend to Render

**Complete guide for deploying your FastAPI backend to Render.com**

---

## 📋 Table of Contents

1. [Why Render?](#why-render)
2. [Prerequisites](#prerequisites)
3. [Prepare Your Repository](#prepare-your-repository)
4. [Deploy to Render](#deploy-to-render)
5. [Configure Environment Variables](#configure-environment-variables)
6. [Post-Deployment](#post-deployment)
7. [Update Frontend Connection](#update-frontend-connection)
8. [Troubleshooting](#troubleshooting)
9. [Updating Your Deployment](#updating-your-deployment)
10. [Cost & Free Tier](#cost--free-tier)

---

## 🎯 Why Render?

Render is perfect for this FastAPI backend because:

- ✅ **Free tier available** - Perfect for testing and small projects
- ✅ **Easy Python/FastAPI support** - No configuration needed
- ✅ **Automatic deployments** - Updates when you push to GitHub
- ✅ **Built-in HTTPS** - Secure by default
- ✅ **Simple environment variables** - Easy to configure
- ✅ **Works great with Supabase** - Your database is already cloud-ready

**Alternatives**: Railway, Heroku, DigitalOcean App Platform, AWS/Azure (more complex)

---

## 📦 Prerequisites

Before deploying, ensure you have:

- [ ] GitHub account (free)
- [ ] Render account (free) - Sign up at [render.com](https://render.com)
- [ ] Your Supabase project running (see `SETUP_GUIDE.md`)
- [ ] Supabase credentials ready:
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
- [ ] Your backend code pushed to GitHub

---

## 🔧 Prepare Your Repository

### Step 1: Create Required Files

Your repository should already have most files, but let's verify and add what's missing.

#### 1.1 Verify `requirements.txt` exists

✅ **Already exists** - Your file at root level is correct:

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.2
supabase==2.9.1
python-dotenv==1.0.1
requests==2.32.3
psycopg2-binary==2.9.10
python-multipart==0.0.17
```

#### 1.2 Create `render.yaml` (Optional but Recommended)

Create this file in your repository root for easier deployment:

**File**: `render.yaml`

```yaml
services:
  - type: web
    name: sc-backend
    env: python
    region: oregon  # or singapore, frankfurt, ohio - choose closest to your users
    plan: free  # Change to 'starter' ($7/mo) for production
    branch: main  # or 'master' - your default branch name
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: SUPABASE_URL
        sync: false  # Will set manually in Render dashboard
      - key: SUPABASE_KEY
        sync: false  # Will set manually in Render dashboard
    healthCheckPath: /health
```

#### 1.3 Create `build.sh` (Alternative Start Script)

**File**: `build.sh` (in root directory)

```bash
#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

Make it executable (on Mac/Linux):
```bash
chmod +x build.sh
```

#### 1.4 Verify `.gitignore` includes sensitive files

Your `.gitignore` should include:

```gitignore
# Environment variables
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# IDE
.vscode/
.idea/
```

### Step 2: Push to GitHub

If not already done:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Render deployment"

# Create GitHub repository and push
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---

## 🚀 Deploy to Render

### Step 1: Create Render Account

1. Go to [render.com](https://render.com)
2. Click **"Get Started"**
3. Sign up with GitHub (recommended - easier integration)

### Step 2: Create New Web Service

1. **From Dashboard**:
   - Click **"New +"** button (top right)
   - Select **"Web Service"**

2. **Connect Repository**:
   - If first time: Click **"Connect GitHub"** and authorize Render
   - Select your repository from the list
   - If you don't see it, click **"Configure account"** and grant access

3. **Configure Service**:

   Fill in these fields:

   | Field | Value |
   |-------|-------|
   | **Name** | `sc-backend` (or your preferred name) |
   | **Region** | Choose closest to your users (e.g., Oregon, Singapore) |
   | **Branch** | `main` (or `master`) |
   | **Root Directory** | Leave empty (unless your code is in a subdirectory) |
   | **Environment** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | **Plan** | `Free` (or `Starter` for production) |

4. **Advanced Settings** (Click "Advanced"):

   - **Python Version**: `3.11.0` (or your version)
   - **Health Check Path**: `/health`
   - **Auto-Deploy**: `Yes` (deploys automatically on git push)

### Step 3: Click "Create Web Service"

Render will now:
1. Clone your repository
2. Install dependencies
3. Start your FastAPI app
4. Assign a URL (e.g., `https://sc-backend.onrender.com`)

⏱️ **First deployment takes 5-10 minutes**

---

## 🔐 Configure Environment Variables

After creating the service, you need to add your Supabase credentials.

### In Render Dashboard:

1. **Go to your service** (sc-backend)
2. **Click "Environment"** tab (left sidebar)
3. **Add Environment Variables**:

   Click **"Add Environment Variable"** and add:

   | Key | Value |
   |-----|-------|
   | `SUPABASE_URL` | `https://your-project.supabase.co` |
   | `SUPABASE_KEY` | `your-supabase-anon-key` |
   | `PYTHON_VERSION` | `3.11.0` |

4. **Click "Save Changes"**

   ⚠️ **Important**: After adding environment variables, Render will automatically redeploy your service.

### Getting Supabase Credentials:

1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL** → Use for `SUPABASE_URL`
   - **anon/public key** → Use for `SUPABASE_KEY`

---

## ✅ Post-Deployment

### Step 1: Check Deployment Status

1. **In Render Dashboard**:
   - Go to your service
   - Check **"Logs"** tab to see deployment progress
   - Wait for: `✓ Build successful` and `✓ Deploy live`

2. **Your Service URL**:
   - Found at top of dashboard: `https://sc-backend.onrender.com`
   - Or in "Settings" tab

### Step 2: Test Your API

#### Test 1: Health Check

Open in browser:
```
https://your-service-name.onrender.com/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "message": "API is running",
  "database": "connected",
  "timestamp": "2025-12-10"
}
```

#### Test 2: Root Endpoint

```
https://your-service-name.onrender.com/
```

**Expected Response**:
```json
{
  "message": "Welcome to SC Backend API! 🎉",
  "status": "running",
  "version": "2.0.0",
  ...
}
```

#### Test 3: Interactive Docs

Visit:
```
https://your-service-name.onrender.com/docs
```

You should see the Swagger UI with all your endpoints!

#### Test 4: Events API

```
https://your-service-name.onrender.com/api/events/list
```

Should return your events list.

### Step 3: Test with cURL

```bash
# Health check
curl https://your-service-name.onrender.com/health

# Get events
curl https://your-service-name.onrender.com/api/events/list

# Create event
curl -X POST https://your-service-name.onrender.com/api/events/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Event",
    "date": "2025-12-25",
    "time": "10:00",
    "location": "Online"
  }'
```

---

## 🔗 Update Frontend Connection

### Step 1: Update CORS Settings (Backend)

In `app/main.py`, update CORS to include your production frontend URL:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Local development
        "http://localhost:3001",
        "https://your-frontend-app.vercel.app",  # Add your frontend URL
        "https://your-frontend-app.netlify.app", # Add if using Netlify
        # Remove "*" for production security
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Important**: Remove `"*"` from `allow_origins` in production for security!

Commit and push:
```bash
git add app/main.py
git commit -m "Update CORS for production"
git push
```

Render will automatically redeploy! ✨

### Step 2: Update Frontend Environment Variables

In your frontend project:

**Development** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Production** (Vercel/Netlify dashboard):
```bash
NEXT_PUBLIC_API_URL=https://your-service-name.onrender.com
```

### Step 3: Test Frontend Connection

From your frontend:

```javascript
// Should now connect to production API
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`);
const data = await response.json();
console.log('Production API:', data);
```

---

## 🐛 Troubleshooting

### Issue: Build Failed

**Check Logs**:
1. Go to Render Dashboard → Your Service → **Logs**
2. Look for error messages

**Common Causes**:

- **Missing dependencies**: Add to `requirements.txt`
- **Wrong Python version**: Set `PYTHON_VERSION` env var
- **Import errors**: Check your import paths

**Solution**:
```bash
# Test locally first
pip install -r requirements.txt
python -m app.main

# If it works locally, push to GitHub
git add .
git commit -m "Fix dependencies"
git push
```

### Issue: Deploy Successful but App Crashes

**Symptoms**: Build succeeds but logs show errors when starting

**Check**:
1. Go to **Logs** tab
2. Look for Python errors

**Common Causes**:

- **Missing environment variables**: Add `SUPABASE_URL` and `SUPABASE_KEY`
- **Wrong start command**: Should be `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Port binding**: Make sure you're using `$PORT` (Render's dynamic port)

**Fix Start Command**:
1. Go to **Settings** tab
2. Find **Start Command**
3. Update to: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Click **Save Changes**

### Issue: Database Connection Failed

**Error**: `"database": "disconnected: ..."`

**Solutions**:

1. **Verify Supabase Credentials**:
   - Check `SUPABASE_URL` is correct (no trailing slash)
   - Check `SUPABASE_KEY` is the anon/public key (not service key)

2. **Test Credentials Locally**:
   ```bash
   # In your local .env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-key-here
   
   # Test connection
   python test_connection.py
   ```

3. **Update in Render**:
   - Go to **Environment** tab
   - Update the values
   - Service will auto-redeploy

### Issue: CORS Errors

**Error**: Frontend can't connect, CORS policy blocks requests

**Solutions**:

1. **Add Frontend URL to CORS**:
   ```python
   # app/main.py
   allow_origins=[
       "https://your-frontend.vercel.app",  # Add this
       # ...
   ]
   ```

2. **Remove Wildcards in Production**:
   - Remove `"*"` from `allow_origins`
   - List specific domains only

3. **Push Changes**:
   ```bash
   git add app/main.py
   git commit -m "Update CORS origins"
   git push
   ```

### Issue: Service Spins Down (Free Tier)

**Symptom**: First request takes 30-60 seconds (cold start)

**Explanation**: 
- Free tier services spin down after 15 minutes of inactivity
- First request "wakes" the service (slow)
- Subsequent requests are fast

**Solutions**:

1. **Upgrade to Starter Plan** ($7/mo):
   - Go to **Settings** → **Plan**
   - Select **Starter**
   - Services stay running 24/7

2. **Use a Ping Service** (Free tier workaround):
   - Use [cron-job.org](https://cron-job.org) to ping your health endpoint every 10 minutes
   - Add job: `https://your-service.onrender.com/health`
   - Keeps service awake

3. **Accept Cold Starts**: 
   - Fine for development/testing
   - Explain to users first load may be slow

### Issue: Custom Domain Not Working

**Setup Custom Domain**:

1. Go to **Settings** → **Custom Domain**
2. Click **Add Custom Domain**
3. Enter your domain (e.g., `api.yourdomain.com`)
4. Follow DNS setup instructions:
   - Add CNAME record in your domain registrar
   - Point to Render's URL
5. Wait for DNS propagation (can take up to 48 hours)

---

## 🔄 Updating Your Deployment

### Automatic Deployments (Recommended)

Render automatically deploys when you push to GitHub:

```bash
# Make changes to your code
git add .
git commit -m "Add new feature"
git push

# Render automatically detects and deploys! 🎉
```

**Monitor Deployment**:
- Watch **Logs** tab in Render dashboard
- Wait for "Deploy live" message
- Test your changes

### Manual Deployments

If automatic deployment is disabled:

1. Go to Render Dashboard → Your Service
2. Click **Manual Deploy** → **Deploy latest commit**

### Rollback to Previous Version

1. Go to **Events** tab
2. Find previous successful deploy
3. Click **Rollback**

---

## 💰 Cost & Free Tier

### Free Tier Limits

**What you get FREE**:
- ✅ 750 hours/month (enough for 24/7 if only one service)
- ✅ Automatic HTTPS
- ✅ Continuous deployment
- ✅ Global CDN
- ⚠️ Service spins down after 15 min inactivity
- ⚠️ 512 MB RAM, 0.1 CPU
- ⚠️ Shared IP address

**Perfect for**:
- Development & testing
- Personal projects
- Low-traffic apps
- MVP/prototypes

### Starter Plan ($7/month)

**What you get**:
- ✅ Always running (no spin down)
- ✅ 512 MB RAM, 0.5 CPU
- ✅ Faster performance
- ✅ Better for production

**Upgrade When**:
- Cold starts are annoying users
- You need 99.9% uptime
- Traffic increases
- Ready for production

### How to Upgrade

1. Go to **Settings** → **Plan**
2. Select **Starter** or **Standard**
3. Add payment method
4. Click **Change Plan**

---

## 📊 Monitoring & Logs

### View Logs

**Real-time**:
- Dashboard → Your Service → **Logs** tab
- Shows live stdout/stderr

**Useful Commands to Add to Your Code**:

```python
# app/main.py - Add logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/api/events/list")
def get_events():
    logger.info("Fetching events list")  # Will appear in Render logs
    # ... rest of code
```

### Monitor Performance

**Metrics Tab**:
- CPU usage
- Memory usage
- Request count
- Response times

**Health Check**:
- Render pings `/health` every 30 seconds
- If it fails, you'll get an alert

---

## 🔒 Security Best Practices

### 1. Environment Variables

✅ **DO**:
- Store all secrets in Render's Environment Variables
- Use strong Supabase keys
- Rotate keys periodically

❌ **DON'T**:
- Commit `.env` file to GitHub
- Hardcode credentials in code
- Share keys in public channels

### 2. CORS Configuration

```python
# Production - Specific origins only
allow_origins=[
    "https://your-frontend.vercel.app",
    "https://your-frontend.netlify.app",
]

# Development - Add localhost
allow_origins=[
    "http://localhost:3000",
    "https://your-frontend.vercel.app",
]
```

### 3. HTTPS Only

- Render provides free HTTPS automatically
- Never use `http://` in production
- Frontend should only call `https://` endpoints

### 4. Rate Limiting (Optional)

Consider adding rate limiting for production:

```python
# Add to requirements.txt
slowapi==0.1.9

# In app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/events/list")
@limiter.limit("100/minute")  # Max 100 requests per minute
def get_events():
    # ... your code
```

---

## 🎉 Success Checklist

Before going live, verify:

- [ ] Service deployed successfully
- [ ] `/health` endpoint returns 200 OK
- [ ] `/docs` shows interactive API documentation
- [ ] Database connection working (check health endpoint)
- [ ] Environment variables set correctly
- [ ] CORS includes production frontend URL
- [ ] `"*"` removed from CORS origins (security)
- [ ] Frontend updated to use production API URL
- [ ] All endpoints tested (create, read, update, delete)
- [ ] Error handling working correctly
- [ ] Logs show no errors
- [ ] Custom domain configured (if applicable)
- [ ] Team members have access to Render dashboard

---

## 📚 Additional Resources

### Render Documentation
- [Python Quickstart](https://render.com/docs/deploy-fastapi)
- [Environment Variables](https://render.com/docs/environment-variables)
- [Custom Domains](https://render.com/docs/custom-domains)

### Supabase Integration
- [Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Database Security](https://supabase.com/docs/guides/database/database-security)

### FastAPI Production
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Uvicorn Workers](https://www.uvicorn.org/deployment/)

---

## 🆘 Getting Help

**Render Issues**:
- [Render Community Forum](https://community.render.com/)
- [Render Status Page](https://status.render.com/)
- Email: support@render.com

**Backend Issues**:
- Check application logs in Render dashboard
- Test locally first: `python -m app.main`
- Verify Supabase connection

**Still Stuck?**:
1. Check **Logs** tab for specific errors
2. Compare with local development (does it work locally?)
3. Verify all environment variables are set
4. Test each endpoint individually via `/docs`

---

## 🚀 Quick Start Summary

```bash
# 1. Ensure code is on GitHub
git push origin main

# 2. Go to render.com
# 3. New → Web Service
# 4. Connect GitHub repo
# 5. Configure:
#    - Build: pip install -r requirements.txt
#    - Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
# 6. Add environment variables:
#    - SUPABASE_URL
#    - SUPABASE_KEY
# 7. Deploy!
# 8. Test: https://your-service.onrender.com/health
# 9. Update frontend API_URL
# 10. Celebrate! 🎉
```

---

**Last Updated**: December 10, 2025

**Questions?** Check Render docs or review logs in dashboard!

**Your API is now live!** 🌐 Share your URL with your frontend team! 🚀

