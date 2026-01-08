# Deployment Guide - OneDrive Integration

## One-Click Deploy to Render (Free Tier)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/shortalex12333/Cloud_DMG_Onedrive)

Click the button above to deploy both services to Render's free tier.

### What Gets Deployed

**Backend Service:** `celesteos-onedrive-api`
- FastAPI application
- OAuth 2.0 flow with Microsoft
- File sync engine
- Automatic metadata extraction

**Frontend Service:** `celesteos-onedrive-portal`
- Next.js web portal
- File browser interface
- Sync dashboard

### Environment Variables Required

When deploying, you'll need to provide:

#### Backend
**Note:** Get actual values from `.env` file or `docs/AZURE_APP_CONFIG.md`

- `AZURE_TENANT_ID`: `073af86c-74f3-422b-ad5c-a35d41fce4be`
- `AZURE_CLIENT_ID`: `41f6dc82-8127-4330-97e0-c6b26e6aa967`
- `AZURE_CLIENT_SECRET`: See `docs/AZURE_APP_CONFIG.md` (expires Aug 2028)
- `AZURE_REDIRECT_URI`: `https://celesteos-onedrive-portal.onrender.com/api/v1/auth/callback`
- `TOKEN_ENCRYPTION_KEY`: See `.env` file (Fernet key)
- `SUPABASE_URL`: `https://vzsohavtuotocgrfkfyd.supabase.co`
- `SUPABASE_SERVICE_KEY`: See `/Users/celeste7/Documents/3B_ENTITY_PRODUCTION/supabase_credentials.md`

#### Frontend
- `NEXT_PUBLIC_API_URL`: Will be set to your backend URL after deployment

### After Deployment

1. **Get Your Backend URL** from Render dashboard
2. **Update Frontend env var:**
   - Go to Frontend service → Environment
   - Set `NEXT_PUBLIC_API_URL` to your backend URL
   - Example: `https://celesteos-onedrive-api.onrender.com`

3. **Update Azure Redirect URI:**
   - Go to Azure Portal → App registrations → CelesteOS.Read
   - Add redirect URI: `https://YOUR-FRONTEND-URL.onrender.com/api/v1/auth/callback`
   - Update `AZURE_REDIRECT_URI` env var in backend service

4. **Test the deployment:**
   - Visit your frontend URL
   - Click "Go to Dashboard"
   - Test OAuth connection

---

## Manual Deployment (Alternative)

If the button doesn't work, deploy manually:

### Backend Service

1. Go to https://dashboard.render.com/create?type=web
2. Select "Build and deploy from a Git repository"
3. Connect repository: `https://github.com/shortalex12333/Cloud_DMG_Onedrive`
4. Configure:
   - **Name:** `celesteos-onedrive-api`
   - **Region:** Oregon
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
5. Add environment variables (see list above)
6. Click "Create Web Service"

### Frontend Service

1. Go to https://dashboard.render.com/create?type=web
2. Select same repository
3. Configure:
   - **Name:** `celesteos-onedrive-portal`
   - **Region:** Oregon
   - **Branch:** `main`
   - **Root Directory:** `frontend`
   - **Runtime:** Node
   - **Build Command:** `npm install && npm run build`
   - **Start Command:** `npm start`
   - **Instance Type:** Free
4. Add environment variable: `NEXT_PUBLIC_API_URL` (get from backend service)
5. Click "Create Web Service"

---

## Deployment Checklist

- [ ] Backend service deployed
- [ ] Frontend service deployed
- [ ] Frontend `NEXT_PUBLIC_API_URL` updated with backend URL
- [ ] Azure redirect URI updated in Azure Portal
- [ ] Backend `AZURE_REDIRECT_URI` updated with production URL
- [ ] Test OAuth flow end-to-end
- [ ] Test file browsing
- [ ] Test sync functionality

---

## Troubleshooting

### Build Failures

**Backend:** Check that `requirements.txt` exists in `/backend` directory
**Frontend:** Check that `package.json` exists in `/frontend` directory

### OAuth Errors

- Verify Azure redirect URI matches production URL
- Check that `AZURE_CLIENT_SECRET` hasn't expired (expires Aug 2028)
- Ensure all Azure env vars are correctly set

### Database Connection Issues

- Verify `SUPABASE_SERVICE_KEY` is the service role JWT, not personal access token
- Check that tables exist (run `migrations_manual.sql` in Supabase SQL Editor)

---

## Auto-Deploy

Both services are configured for auto-deploy:
- Push to `main` branch triggers automatic redeployment
- Build logs available in Render dashboard
- Health check endpoint: `/health`

---

## Support

For issues, check:
- Render logs: Dashboard → Service → Logs
- Backend health: `https://your-backend-url.onrender.com/health`
- GitHub repo: https://github.com/shortalex12333/Cloud_DMG_Onedrive
