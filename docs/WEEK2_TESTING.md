# Week 2 Testing Guide

## Overview

This guide covers testing the OAuth 2.0 flow and Microsoft Graph integration implemented in Week 2.

---

## Prerequisites

1. **Azure App Registration**
   - Follow [AZURE_SETUP.md](AZURE_SETUP.md) to create Azure AD app
   - Ensure redirect URI is configured: `http://localhost:3000/api/v1/auth/callback`
   - Required permissions: Files.Read.All, User.Read, offline_access

2. **Environment Configuration**
   - Copy `.env.example` to `.env`
   - Fill in Azure credentials (tenant ID, client ID, client secret)
   - Generate token encryption key:
     ```bash
     python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
     ```

3. **Database Setup**
   - Ensure Supabase Cloud_PMS database is accessible
   - Run migrations (see below)

---

## Setup Steps

### 1. Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Run Database Migrations

```bash
cd backend
export SUPABASE_URL=https://vzsohavtuotocgrfkfyd.supabase.co
export SUPABASE_SERVICE_KEY=<your-service-key>

alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial OneDrive tables
```

**Verify Tables Created:**
```sql
-- In Supabase SQL Editor
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'onedrive_%';
```

Should return:
- `onedrive_connections`
- `onedrive_sync_state`
- `onedrive_sync_jobs`

### 3. Start Services

**Option A: Docker Compose (Recommended)**
```bash
docker-compose up
```

**Option B: Local Development**

Terminal 1 (Backend):
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

**Services:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Testing OAuth Flow

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{
  "status": "healthy",
  "service": "onedrive-integration",
  "version": "0.1.0"
}
```

### Test 2: Initiate Connection

**API Test:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/connect \
  -H "Content-Type: application/json" \
  -d '{"yacht_id": "demo-yacht-001"}'
```

**Expected Response:**
```json
{
  "auth_url": "https://login.microsoftonline.com/...",
  "state": "demo-yacht-001"
}
```

**UI Test:**
1. Navigate to: http://localhost:3000
2. Click: "Go to Dashboard"
3. Click: "Connect OneDrive"
4. Should redirect to Microsoft login page

### Test 3: Complete OAuth Flow

1. **Click "Connect OneDrive" button**
   - Should redirect to Microsoft login page
   - URL should include your tenant ID and client ID

2. **Sign In with Microsoft 365**
   - Use valid Microsoft 365 account with OneDrive
   - Enter email and password

3. **Grant Permissions**
   - Consent screen should show:
     - Read all files that user can access
     - Sign in and read user profile
     - Maintain access to data
   - Click: **Accept**

4. **Callback Redirect**
   - Should redirect to: `http://localhost:3000/dashboard?connected=true&connection_id=<uuid>`
   - Green success message: "Successfully connected to OneDrive!"
   - Connection status shows your email

### Test 4: Verify Database

```sql
-- In Supabase SQL Editor
SELECT
    id,
    yacht_id,
    user_principal_name,
    sync_enabled,
    token_expires_at,
    created_at
FROM onedrive_connections
ORDER BY created_at DESC;
```

**Should see:**
- Your yacht ID
- Your Microsoft email
- Encrypted tokens (not readable)
- Future expiry time (1 hour from now)

### Test 5: Connection Status

```bash
curl "http://localhost:8000/api/v1/auth/status?yacht_id=demo-yacht-001"
```

**Expected (if connected):**
```json
{
  "connected": true,
  "user_principal_name": "your-email@domain.com",
  "connection_id": "uuid-here",
  "sync_enabled": true
}
```

### Test 6: Token Refresh Test

```bash
curl "http://localhost:8000/api/v1/auth/test-token?connection_id=<your-connection-id>"
```

**Expected:**
```json
{
  "success": true,
  "user": "Your Name",
  "email": "your-email@domain.com"
}
```

This confirms:
- Token is valid
- Can retrieve user profile from Microsoft Graph
- Automatic refresh works (if token expired)

### Test 7: Disconnect

**UI Test:**
1. Click: "Disconnect OneDrive" button
2. Status should change to "Not connected"
3. "Connect OneDrive" button reappears

**API Test:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/disconnect?connection_id=<your-connection-id>"
```

**Expected:**
```json
{
  "success": true,
  "message": "OneDrive disconnected successfully"
}
```

**Verify Database:**
```sql
SELECT COUNT(*) FROM onedrive_connections WHERE id = '<your-connection-id>';
-- Should return 0 (connection deleted)
```

---

## Troubleshooting

### Error: "Failed to generate authorization URL"

**Cause:** Invalid Azure credentials in `.env`

**Fix:**
- Verify `AZURE_TENANT_ID` matches Azure Portal
- Verify `AZURE_CLIENT_ID` matches Application (client) ID
- Ensure no extra spaces or quotes in `.env`

### Error: "redirect_uri mismatch"

**Cause:** Redirect URI not configured in Azure

**Fix:**
1. Go to: Azure Portal → App registrations → Your app → Authentication
2. Add: `http://localhost:3000/api/v1/auth/callback`
3. Save and retry

### Error: "Authentication failed: AADSTS650053"

**Cause:** User doesn't have OneDrive for Business

**Fix:**
- Ensure user has valid Microsoft 365 license with OneDrive
- Check in Microsoft 365 Admin Center

### Error: "Failed to decrypt token"

**Cause:** TOKEN_ENCRYPTION_KEY changed or invalid

**Fix:**
- Generate new key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- Update `.env` file
- Reconnect (old tokens will be invalid)

### Error: "Connection refused (database)"

**Cause:** Supabase connection failed

**Fix:**
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env`
- Check Supabase project status (not paused)
- Test connection: `psql "$DATABASE_URL" -c "SELECT 1;"`

### Frontend Shows "Loading..." Forever

**Cause:** Backend not running or CORS issue

**Fix:**
- Verify backend is running: `curl http://localhost:8000/health`
- Check browser console for CORS errors
- Verify `NEXT_PUBLIC_API_URL=http://localhost:8000` in frontend `.env`

---

## Success Criteria

Week 2 is complete when:

- [x] Backend health check returns 200
- [x] Can initiate OAuth connection (get auth URL)
- [x] Can complete OAuth flow (sign in with Microsoft)
- [x] Tokens stored encrypted in database
- [x] Connection status shows "Connected" with user email
- [x] Token refresh works (test-token endpoint succeeds)
- [x] Can disconnect and reconnect successfully
- [x] Frontend dashboard shows connection status
- [x] No errors in backend logs during OAuth flow

---

## API Documentation

Interactive API docs available at: http://localhost:8000/docs

**Endpoints Implemented (Week 2):**
- `POST /api/v1/auth/connect` - Initiate OAuth
- `GET /api/v1/auth/callback` - OAuth callback
- `GET /api/v1/auth/status` - Get connection status
- `POST /api/v1/auth/disconnect` - Revoke connection
- `GET /api/v1/auth/test-token` - Test token validity

**Coming in Week 3:**
- `GET /api/v1/files/browse` - Browse OneDrive files
- `POST /api/v1/sync/start` - Start sync job
- `GET /api/v1/sync/status` - Get sync progress

---

## Next Steps (Week 3)

After completing Week 2 testing:

1. **File Browser Implementation**
   - List OneDrive folders
   - Select folders to sync
   - Display folder hierarchy

2. **Sync Engine**
   - Enumerate files from selected folders
   - Download from OneDrive
   - Upload to Supabase Storage
   - Trigger document processing

3. **Real-time Progress**
   - WebSocket or polling for sync status
   - Progress bar showing files processed
   - Error handling and retry logic

---

## Support

For issues during testing:
1. Check backend logs for errors
2. Check browser console for frontend errors
3. Verify Azure app configuration
4. Test database connectivity
5. Review environment variables

**Common Logs to Check:**
```bash
# Backend logs (if using Docker)
docker logs celesteos-onedrive-backend

# Backend logs (local)
# Check terminal where uvicorn is running

# Database connection test
cd backend
python -c "from app.db.session import engine; print(engine.connect())"
```
