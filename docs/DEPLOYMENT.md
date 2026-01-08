# Deployment Guide

## Overview

This guide covers deploying the CelesteOS OneDrive Integration to production on Render.com.

---

## Prerequisites

- Render account with payment method
- Azure AD app registration configured
- Supabase Cloud_PMS database access
- GitHub repository access

---

## Step 1: Prepare Production Environment

### 1.1 Azure Configuration

1. **Update Redirect URI**
   - Go to: Azure Portal → App registrations → CelesteOS OneDrive Integration → Authentication
   - Add production redirect URI:
     ```
     https://your-onedrive-portal.onrender.com/api/v1/auth/callback
     ```

2. **Create Production Client Secret**
   - Go to: Certificates & secrets → New client secret
   - Description: `Production - Render`
   - Expires: 24 months
   - Copy secret value

### 1.2 Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Store this key securely - it will be used to encrypt OAuth tokens.

---

## Step 2: Deploy Backend to Render

### 2.1 Create Web Service

1. **Navigate to Render Dashboard**
   - Go to: https://dashboard.render.com
   - Click: **New** → **Web Service**

2. **Connect Repository**
   - Select: **GitHub**
   - Choose: `shortalex12333/Cloud_DMG_Onedrive`
   - Branch: `main`

3. **Configure Service**
   ```
   Name: celesteos-onedrive-backend
   Region: Oregon (US West)
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Environment Variables**
   ```bash
   AZURE_TENANT_ID=<your_tenant_id>
   AZURE_CLIENT_ID=<your_client_id>
   AZURE_CLIENT_SECRET=<production_client_secret>
   AZURE_REDIRECT_URI=https://your-onedrive-portal.onrender.com/api/v1/auth/callback
   TOKEN_ENCRYPTION_KEY=<generated_fernet_key>
   SUPABASE_URL=https://vzsohavtuotocgrfkfyd.supabase.co
   SUPABASE_SERVICE_KEY=<service_key>
   DIGEST_SERVICE_URL=https://celeste-digest-index.onrender.com
   YACHT_SALT=e49469e09cb6529e0bfef118370cf8425b006f0abbc77475da2e0cb479af8b18
   REDIS_URL=<redis_connection_string>
   ```

5. **Select Plan**
   - Plan: **Starter** ($7/month) or higher
   - Click: **Create Web Service**

### 2.2 Deploy Database Migrations

**Option 1: Via Render Shell**
```bash
# In Render Dashboard → Shell
cd /opt/render/project/src
pip install alembic
alembic upgrade head
```

**Option 2: Local Deployment**
```bash
# Set DATABASE_URL to production Supabase
export SUPABASE_URL=https://vzsohavtuotocgrfkfyd.supabase.co
export SUPABASE_SERVICE_KEY=<production_service_key>

cd backend
alembic upgrade head
```

---

## Step 3: Deploy Frontend to Render

### 3.1 Create Web Service

1. **Create New Web Service**
   - Repository: `shortalex12333/Cloud_DMG_Onedrive`
   - Branch: `main`

2. **Configure Service**
   ```
   Name: celesteos-onedrive-portal
   Region: Oregon (US West)
   Branch: main
   Root Directory: frontend
   Runtime: Node
   Build Command: npm install && npm run build
   Start Command: npm start
   ```

3. **Add Environment Variables**
   ```bash
   NEXT_PUBLIC_API_URL=https://celesteos-onedrive-backend.onrender.com
   ```

4. **Select Plan**
   - Plan: **Starter** ($7/month) or higher
   - Click: **Create Web Service**

---

## Step 4: Deploy Redis Instance

### 4.1 Create Redis Service

1. **Create Redis Instance**
   - Click: **New** → **Redis**
   - Name: `celesteos-onedrive-redis`
   - Plan: **Free** or **Starter**

2. **Get Connection String**
   - Copy internal connection string (e.g., `redis://red-xxx.oregon-redis.render.com:6379`)

3. **Update Backend Environment**
   - Add `REDIS_URL` to backend service environment variables

---

## Step 5: Deploy Celery Worker

### 5.1 Create Background Worker

1. **Create Background Worker**
   - Repository: `shortalex12333/Cloud_DMG_Onedrive`
   - Branch: `main`

2. **Configure Worker**
   ```
   Name: celesteos-onedrive-worker
   Region: Oregon (US West)
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: celery -A app.tasks worker --loglevel=info
   ```

3. **Add Environment Variables**
   - Copy ALL environment variables from backend service
   - Ensure `REDIS_URL` matches Redis instance

4. **Select Plan**
   - Plan: **Starter** ($7/month) or higher

---

## Step 6: Configure CORS

### 6.1 Update Backend CORS Settings

Edit `backend/app/config.py`:
```python
cors_origins: list = [
    "https://celesteos-onedrive-portal.onrender.com",
    "http://localhost:3000",  # Keep for local development
]
```

Commit and push changes to trigger redeployment.

---

## Step 7: Verify Deployment

### 7.1 Health Checks

```bash
# Backend health check
curl https://celesteos-onedrive-backend.onrender.com/health

# Expected: {"status": "healthy", "service": "onedrive-integration", "version": "0.1.0"}
```

### 7.2 Frontend Access

Navigate to: `https://celesteos-onedrive-portal.onrender.com`

Expected:
- Landing page loads
- "Connect OneDrive" button visible

### 7.3 OAuth Flow Test

1. Click: **Connect OneDrive**
2. Redirect to Microsoft login
3. Sign in with Microsoft 365 account
4. Consent to permissions
5. Redirect back to application
6. Connection established

---

## Step 8: Monitoring

### 8.1 Enable Logging

**Render Dashboard:**
- Each service → Logs tab
- Real-time log streaming

**Key Logs to Monitor:**
- OAuth flow errors
- Token refresh failures
- Sync job failures
- Microsoft Graph API rate limits

### 8.2 Set Up Alerts

1. **Create Health Check Endpoints**
   - Already available at `/health`

2. **Configure Uptime Monitoring**
   - Use Render's built-in health checks
   - Or external: UptimeRobot, Pingdom

---

## Troubleshooting

### Backend Service Fails to Start

**Symptom:** Service shows "Deploy failed"
**Check:**
- Build logs for missing dependencies
- Ensure `requirements.txt` includes all packages
- Verify `uvicorn` command is correct

### Database Migration Fails

**Symptom:** `alembic upgrade head` fails
**Fix:**
```bash
# Check Supabase connection
psql "$DATABASE_URL" -c "SELECT 1;"

# Verify service_role key has permissions
# Run migration with verbose output
alembic upgrade head -v
```

### OAuth Redirect Fails

**Symptom:** "Redirect URI mismatch" error
**Fix:**
- Verify Azure redirect URI matches EXACTLY:
  - Azure Portal: `https://celesteos-onedrive-portal.onrender.com/api/v1/auth/callback`
  - Backend env: `AZURE_REDIRECT_URI` same value

### Redis Connection Fails

**Symptom:** Celery worker cannot connect
**Fix:**
- Verify `REDIS_URL` environment variable
- Check Redis instance is running (Render Dashboard)
- Ensure worker and Redis in same region

---

## Rollback Procedure

### Rollback to Previous Deployment

1. **Render Dashboard**
   - Service → Deploys tab
   - Find previous successful deploy
   - Click: **Redeploy**

### Rollback Database Migration

```bash
# Connect to production database
alembic downgrade -1

# Or specific revision
alembic downgrade <revision_id>
```

---

## Cost Estimate

**Monthly Costs (Render):**
- Backend (Starter): $7/month
- Frontend (Starter): $7/month
- Redis (Free tier): $0/month
- Celery Worker (Starter): $7/month

**Total:** ~$21/month (Starter plan)

**Scaling Options:**
- Upgrade to Standard ($25/month per service) for:
  - Auto-scaling
  - Zero-downtime deploys
  - Custom domains
  - SSL certificates

---

## Production Checklist

- [ ] Azure redirect URI updated
- [ ] Production client secret generated
- [ ] Token encryption key generated and stored securely
- [ ] Backend service deployed
- [ ] Database migrations applied
- [ ] Frontend service deployed
- [ ] Redis instance created
- [ ] Celery worker deployed
- [ ] CORS configured
- [ ] Health checks passing
- [ ] OAuth flow tested end-to-end
- [ ] Monitoring and alerts configured
- [ ] SSL certificates verified
- [ ] Custom domain configured (if applicable)

---

## Support

For deployment issues:
1. Check Render logs (Dashboard → Service → Logs)
2. Review environment variables
3. Verify Azure configuration
4. Check Supabase connectivity

---

## Related Documentation

- [Azure Setup](AZURE_SETUP.md) - Azure AD configuration
- [README](../README.md) - Development setup
- [Render Documentation](https://render.com/docs) - Platform documentation
