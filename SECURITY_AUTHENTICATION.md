# Authentication Security & Cache Clearing

## Problem
Microsoft OAuth can cache user credentials and auto-signin with previously used accounts, creating security risks where users accidentally connect the wrong OneDrive account.

## Solution: Multi-Layer Cache Clearing

We implement **nuclear-level** cache clearing to guarantee fresh authentication every time.

---

## Security Layers

### Layer 1: OAuth Prompt Parameter ✅
**Backend:** `prompt='login'` in OAuth URL

```python
# backend/app/api/v1/auth.py
auth_url = token_manager.client_app.get_authorization_request_url(
    scopes=scopes,
    redirect_uri=settings.azure_redirect_uri,
    state=request.yacht_id,
    prompt='login'  # Forces password entry - NO auto-signin
)
```

**Effect:**
- User MUST enter password every time
- Microsoft session cache is ignored
- No auto-selection of cached accounts

**Comparison:**
- `prompt='none'` → Silent auth (DANGEROUS - never use)
- `prompt='select_account'` → Shows picker but can auto-select (WEAK)
- `prompt='consent'` → Shows permissions but can cache account (WEAK)
- `prompt='login'` → Forces re-authentication (STRONG) ✅ **Using this**

---

### Layer 2: Database Connection Management ✅
**Backend:** Only ONE active connection per yacht

```python
# backend/app/core/token_manager.py
# Disable ALL old connections when new auth completes
supabase.table('onedrive_connections')\
    .update({'sync_enabled': False})\
    .eq('yacht_id', yacht_id)\
    .execute()
```

**Effect:**
- Old connection_id becomes invalid immediately
- Previous user's files cannot be accessed
- Only most recent connection is active

---

### Layer 3: API Endpoint Validation ✅
**Backend:** Validate connection before file access

```python
# backend/app/api/v1/files.py
connection_check = supabase.table('onedrive_connections')\
    .select('sync_enabled, user_principal_name')\
    .eq('id', connection_id)\
    .execute()

if not connection_check.data[0].get('sync_enabled', False):
    raise HTTPException(403, "Connection disabled. Please reconnect.")
```

**Effect:**
- Stale connection_id returns 403 error
- File access requires active connection
- Logs show which user's files are accessed

---

### Layer 4: Frontend State Clearing ✅
**Frontend:** Clear all browser cache on disconnect

```typescript
// frontend/src/lib/hooks/useConnection.ts
await apiClient.disconnect(status.connection_id);

// Clear browser storage
localStorage.removeItem('onedrive_connection');
localStorage.removeItem('connection_id');
sessionStorage.clear();

// Clear React state
setStatus(null);

// Refresh to get latest connection
refresh();
```

**Effect:**
- No cached connection_id in browser
- All local state cleared
- Forces fresh status fetch after disconnect

---

### Layer 5: Microsoft Session Logout (Optional) ✅
**Endpoint:** `GET /api/v1/auth/clear-microsoft-session`

**Nuclear Option** - Logs user out of ALL Microsoft services:
```
GET /api/v1/auth/clear-microsoft-session
→ Returns: { logout_url: "https://login.microsoftonline.com/common/oauth2/v2.0/logout?..." }
→ User redirects to logout_url
→ Clears ALL Microsoft cookies across ALL services
→ Redirects back to dashboard
```

**When to use:**
- User wants absolute guarantee of fresh auth
- Switching between many different Microsoft accounts
- Troubleshooting authentication issues

**Warning:** This logs user out of Outlook, Teams, Office, etc.

---

## Authentication Flow

### Normal Connection (with prompt='login')
```
1. User clicks "Connect OneDrive"
   ↓
2. Backend generates OAuth URL with prompt='login'
   ↓
3. User redirects to Microsoft login
   ↓
4. Microsoft FORCES password entry (ignores cache)
   ↓
5. User enters password + consents
   ↓
6. Callback with authorization code
   ↓
7. Backend disables ALL old connections
   ↓
8. Backend creates new connection (sync_enabled=true)
   ↓
9. Frontend refreshes connection status
   ↓
10. Dashboard shows NEW user's email and files
```

### Re-Authentication Flow
```
1. User clicks "Disconnect"
   ↓
2. Backend sets sync_enabled=false for connection
   ↓
3. Frontend clears localStorage, sessionStorage
   ↓
4. Frontend clears React state (setStatus(null))
   ↓
5. Frontend refreshes connection status
   ↓
6. Dashboard shows "Not connected"
   ↓
7. User clicks "Connect OneDrive" again
   ↓
8. prompt='login' FORCES fresh password entry
   ↓
9. User can choose ANY Microsoft account
   ↓
10. New connection created, old one stays disabled
```

---

## Security Guarantees

✅ **Password Required Every Time**
- `prompt='login'` forces password entry
- Microsoft session cache ignored
- No silent authentication possible

✅ **One Active Connection Per Yacht**
- Old connections auto-disabled on new auth
- Stale connection_id returns 403 error
- Only most recent connection works

✅ **No Browser Cache**
- localStorage cleared on disconnect
- sessionStorage cleared on disconnect
- React state fully reset

✅ **Connection Validation**
- Every API call checks sync_enabled=true
- Disabled connections rejected
- User principal name logged

✅ **No Stale Data**
- Frontend refreshes after disconnect
- Frontend refreshes after OAuth callback
- Always uses latest connection_id

---

## Testing Instructions

### Test 1: Basic Re-Authentication
1. Connect as User A (x@alex-short.com)
2. Note files visible in browser
3. Click "Disconnect"
4. Click "Connect OneDrive"
5. **Expected:** Microsoft login page (must enter password)
6. Sign in as User B (different account)
7. **Expected:** Dashboard shows User B's email and files
8. **Verify:** User A's files are NOT accessible

### Test 2: Stale Connection ID
1. Connect as User A
2. Copy connection_id from URL or browser console
3. Disconnect
4. Try to browse files with old connection_id:
   ```bash
   curl "https://digest-cloud.int.celeste7.ai/api/v1/files/browse?connection_id=<OLD_ID>&path=/"
   ```
5. **Expected:** 403 error "Connection disabled. Please reconnect."

### Test 3: Forced Password Entry
1. Connect and disconnect multiple times rapidly
2. **Expected:** EVERY connect requires password entry
3. **Verify:** No auto-signin, no cached credentials

---

## Troubleshooting

### Issue: Still seeing auto-signin
**Cause:** Microsoft session cookies persisting
**Solution:** Use nuclear option:
```
GET /api/v1/auth/clear-microsoft-session
→ Redirect user to returned logout_url
→ Clears ALL Microsoft sessions
→ Try connecting again
```

### Issue: Wrong user's files visible
**Cause:** Frontend using cached connection_id
**Solution:**
1. Check browser console for connection_id
2. Verify it matches latest in database
3. Clear browser storage manually
4. Refresh page

### Issue: Connection disabled error
**Cause:** Using old connection_id after re-auth
**Solution:**
1. Disconnect and reconnect
2. Frontend should automatically fetch new connection_id
3. Check `/status` endpoint returns latest connection

---

## Configuration

### Change OAuth Prompt Behavior
```python
# backend/app/api/v1/auth.py

# Current: Forces password every time (RECOMMENDED)
prompt='login'

# Alternative: Show account picker (WEAKER)
prompt='select_account'

# Alternative: Consent screen only (WEAKEST)
prompt='consent'

# Never use: Silent auth (DANGEROUS)
prompt='none'
```

### Adjust Connection Disable Behavior
```python
# backend/app/core/token_manager.py

# Current: Disable ALL old connections (RECOMMENDED)
supabase.table('onedrive_connections')\
    .update({'sync_enabled': False})\
    .eq('yacht_id', yacht_id)\
    .execute()

# Alternative: Delete old connections (AGGRESSIVE)
supabase.table('onedrive_connections')\
    .delete()\
    .eq('yacht_id', yacht_id)\
    .execute()
```

---

## API Endpoints

### Connect (with forced auth)
```
POST /api/v1/auth/connect
Body: { "yacht_id": "demo-yacht-001" }
Response: { "auth_url": "https://login.microsoftonline.com/...", "state": "..." }
```

### Clear Microsoft Session (nuclear option)
```
GET /api/v1/auth/clear-microsoft-session
Response: {
  "logout_url": "https://login.microsoftonline.com/common/oauth2/v2.0/logout?...",
  "message": "..."
}
```

### Connection Status (latest only)
```
GET /api/v1/auth/status?yacht_id=demo-yacht-001
Response: {
  "connected": true,
  "user_principal_name": "user@domain.com",
  "connection_id": "uuid",
  "sync_enabled": true
}
```

### Disconnect (clears connection)
```
POST /api/v1/auth/disconnect?connection_id=<uuid>
Response: { "success": true, "message": "OneDrive disconnected successfully" }
```

---

## Security Checklist

Before deployment, verify:

- [ ] OAuth uses `prompt='login'`
- [ ] Old connections disabled on new auth
- [ ] API validates `sync_enabled=true`
- [ ] Frontend clears localStorage on disconnect
- [ ] Frontend clears sessionStorage on disconnect
- [ ] Frontend refreshes after disconnect
- [ ] Frontend refreshes after OAuth callback
- [ ] Connection status returns latest only
- [ ] Stale connection_id returns 403
- [ ] User principal name logged on file access

---

## Audit Log

All authentication events are logged:

```
# New connection
"Generated auth URL for yacht demo-yacht-001 with prompt=login"
"Disabling all existing connections for yacht demo-yacht-001"
"Successfully connected OneDrive for yacht demo-yacht-001, user user@domain.com"

# File access
"Browsing files for user: user@domain.com"
"Active connection for yacht demo-yacht-001: user@domain.com (ID: uuid)"

# Disconnect
"Revoked connection uuid"
"No active connection found for yacht demo-yacht-001"
```

Check logs to verify correct user's files are accessed.

---

## References

- [Microsoft Identity Platform - prompt parameter](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow#request-an-authorization-code)
- [Microsoft logout endpoint](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-protocols-oidc#send-a-sign-out-request)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
