# 🚀 Render Deployment Checklist

**Quick checklist for deploying SC Backend to Render**

For detailed instructions, see [z_Docs/RENDER_DEPLOYMENT.md](z_Docs/RENDER_DEPLOYMENT.md)

---

## ✅ Pre-Deployment

- [ ] Code is working locally (`python -m app.main`)
- [ ] All tests pass
- [ ] `.env` file is NOT committed to GitHub
- [ ] `.gitignore` includes `.env`
- [ ] `requirements.txt` is up to date
- [ ] Code is pushed to GitHub

**Supabase Setup:**
- [ ] Supabase project created
- [ ] Database schema (`supabase_schema.sql`) executed
- [ ] Have `SUPABASE_URL` ready
- [ ] Have `SUPABASE_KEY` ready

---

## 🌐 Render Setup

### 1. Create Account
- [ ] Go to [render.com](https://render.com)
- [ ] Sign up (use GitHub for easier integration)
- [ ] Verify email

### 2. Create Web Service
- [ ] Click "New +" → "Web Service"
- [ ] Connect GitHub account
- [ ] Select your repository
- [ ] Fill in configuration:

```
Name:            sc-backend
Region:          [Choose closest to users]
Branch:          main
Environment:     Python 3
Build Command:   pip install -r requirements.txt
Start Command:   uvicorn app.main:app --host 0.0.0.0 --port $PORT
Plan:            Free (or Starter for production)
```

- [ ] Advanced → Python Version: `3.11.0`
- [ ] Advanced → Health Check Path: `/health`
- [ ] Click "Create Web Service"

### 3. Add Environment Variables
- [ ] Go to "Environment" tab
- [ ] Add `SUPABASE_URL` = `[your-url]`
- [ ] Add `SUPABASE_KEY` = `[your-key]`
- [ ] Add `PYTHON_VERSION` = `3.11.0`
- [ ] Click "Save Changes" (triggers auto-deploy)

---

## 🧪 Post-Deployment Testing

### 4. Verify Deployment
- [ ] Wait for "Deploy live" in logs (5-10 minutes)
- [ ] Note your service URL: `https://[your-service].onrender.com`

### 5. Test Endpoints

**Health Check:**
- [ ] Visit: `https://[your-service].onrender.com/health`
- [ ] Should return: `{"status": "healthy", "database": "connected"}`

**Root Endpoint:**
- [ ] Visit: `https://[your-service].onrender.com/`
- [ ] Should return welcome message with version 2.0.0

**Interactive Docs:**
- [ ] Visit: `https://[your-service].onrender.com/docs`
- [ ] Can see all endpoints
- [ ] Try creating an event

**Events API:**
- [ ] Test: `https://[your-service].onrender.com/api/events/list`
- [ ] Should return events list

### 6. cURL Tests
```bash
# Health check
curl https://[your-service].onrender.com/health

# Get events
curl https://[your-service].onrender.com/api/events/list

# Create event
curl -X POST https://[your-service].onrender.com/api/events/create \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","date":"2025-12-25","time":"10:00","location":"Online"}'
```

- [ ] All tests pass

---

## 🔗 Frontend Integration

### 7. Update CORS (Backend)
- [ ] Open `app/main.py`
- [ ] Add production frontend URL to `allow_origins`
- [ ] Remove `"*"` from origins (security!)
- [ ] Example:
```python
allow_origins=[
    "http://localhost:3000",  # Keep for local dev
    "https://your-frontend.vercel.app",  # Add production
]
```
- [ ] Commit and push (Render auto-deploys)

### 8. Update Frontend
- [ ] Add production API URL to frontend env vars
- [ ] Example: `NEXT_PUBLIC_API_URL=https://[your-service].onrender.com`
- [ ] Test frontend connection
- [ ] Verify no CORS errors

---

## 🔧 Optional Enhancements

### 9. Custom Domain (Optional)
- [ ] Go to Settings → Custom Domain
- [ ] Add your domain (e.g., `api.yourdomain.com`)
- [ ] Update DNS records as instructed
- [ ] Wait for DNS propagation
- [ ] Update frontend to use custom domain

### 10. Monitoring
- [ ] Check "Metrics" tab for performance
- [ ] Set up alerts (if on paid plan)
- [ ] Monitor logs regularly

### 11. Upgrade to Starter (Optional but Recommended)
If you need:
- No cold starts (instant responses)
- Better performance
- 99.9% uptime

Then:
- [ ] Go to Settings → Plan
- [ ] Select "Starter" ($7/month)
- [ ] Add payment method
- [ ] Confirm upgrade

---

## 📊 Success Verification

### Final Checks
- [ ] Backend is accessible via HTTPS URL
- [ ] `/health` returns healthy status
- [ ] Database connection works
- [ ] Can create events via API
- [ ] Can retrieve events
- [ ] Frontend can connect successfully
- [ ] No CORS errors
- [ ] No errors in Render logs
- [ ] Team members have Render access

---

## 🎉 You're Live!

Your API is now deployed and accessible at:
```
https://[your-service].onrender.com
```

**Share with your team:**
- API URL: `https://[your-service].onrender.com`
- API Docs: `https://[your-service].onrender.com/docs`
- Health Check: `https://[your-service].onrender.com/health`

---

## 📝 Notes

**Free Tier Behavior:**
- Service spins down after 15 min of inactivity
- First request takes 30-60 seconds (cold start)
- Subsequent requests are fast
- 750 hours/month free (enough for 24/7)

**To avoid cold starts:**
- Upgrade to Starter plan, OR
- Use a ping service (cron-job.org) to ping `/health` every 10 minutes

---

## 🆘 Troubleshooting

**Build failed?**
- [ ] Check Logs tab for errors
- [ ] Verify `requirements.txt` is correct
- [ ] Test locally first

**Deploy succeeded but crashes?**
- [ ] Check environment variables are set
- [ ] Verify `SUPABASE_URL` and `SUPABASE_KEY`
- [ ] Check Start Command is correct
- [ ] Review logs for Python errors

**Database connection failed?**
- [ ] Verify Supabase credentials
- [ ] Test with local `.env` first
- [ ] Check Supabase project is active

**CORS errors from frontend?**
- [ ] Add frontend URL to `allow_origins` in `app/main.py`
- [ ] Remove `"*"` if present
- [ ] Push changes to trigger redeploy

**Need help?**
- See [z_Docs/RENDER_DEPLOYMENT.md](z_Docs/RENDER_DEPLOYMENT.md) for detailed troubleshooting
- Check Render logs
- Visit Render community forum

---

## 🔄 Next Steps

- [ ] Set up automatic backups (Supabase)
- [ ] Add monitoring/alerting
- [ ] Implement rate limiting
- [ ] Add authentication
- [ ] Set up CI/CD pipeline
- [ ] Create staging environment
- [ ] Document API changes
- [ ] Train team on deployment process

---

**Deployment Date:** _____________

**Deployed By:** _____________

**Service URL:** _____________

**Notes:** 

_____________________________________________

_____________________________________________

_____________________________________________

---

**🎊 Congratulations on your deployment! 🎊**

