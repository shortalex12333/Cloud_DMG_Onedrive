# Azure App Configuration - CelesteOS.Read

## App Registration Details

**Display Name:** CelesteOS.Read
**Application (client) ID:** 41f6dc82-8127-4330-97e0-c6b26e6aa967
**Object ID:** c764c30f-640a-4e0c-bb8c-ccc0627fb69f
**Directory (tenant) ID:** 073af86c-74f3-422b-ad5c-a35d41fce4be
**Supported Account Types:** Multiple organizations

**Application ID URI:** api://41f6dc82-8127-4330-97e0-c6b26e6aa967

---

## Client Secret

**Description:** Read
**Expires:** 08/01/2028
**Value:** `<stored_in_Azure_Portal_and_local_env_file_only>`
**Secret ID:** 33319a37-560f-4091-ac1b-ecff92c7a904

⚠️ **IMPORTANT:**
- This secret expires on **August 1, 2028**. Set reminder to rotate before expiry.
- Secret value stored in `/Users/celeste7/Desktop/MS_APP_Documents.md` (local file only)
- For deployment, retrieve from Azure Portal → App registrations → CelesteOS.Read → Certificates & secrets

---

## Configured Permissions

All permissions have been **granted admin consent for CELESTE7 LTD**.

### Delegated Permissions (User Context)

| Permission | Description | Admin Consent Required |
|------------|-------------|----------------------|
| `email` | View users' email address | No |
| `Mail.Read` | Read user mail | No |
| `offline_access` | Maintain access to data you have given it access to | No |
| `openid` | Sign users in | No |
| `profile` | View users' basic profile | No |
| `User.Read` | Sign in and read user profile | No |

### Application Permissions (App-Only Context)

| Permission | Description | Admin Consent Required |
|------------|-------------|----------------------|
| `Files.Read.All` | Read files in all site collections | Yes ✅ |
| `Group.Read.All` | Read all groups | Yes ✅ |
| `Sites.Read.All` | Read items in all site collections | Yes ✅ |
| `User.Read.All` | Read all users' full profiles | Yes ✅ |

---

## Redirect URIs

**Configured:** 4 web, 1 spa, 0 public client

**Required for OneDrive Integration:**
- **Development:** `http://localhost:3000/api/v1/auth/callback`
- **Production:** `https://celesteos-onedrive-portal.onrender.com/api/v1/auth/callback` (update when deployed)

### Add Redirect URI

1. Go to Azure Portal → App registrations → CelesteOS.Read
2. Navigate to **Authentication**
3. Under **Platform configurations** → **Web**
4. Click **Add URI**
5. Enter: `http://localhost:3000/api/v1/auth/callback` (for development)
6. Enter: `https://your-production-url.onrender.com/api/v1/auth/callback` (for production)
7. Click **Save**

---

## Environment Configuration

### Development (.env)

```bash
# Azure AD (Get client secret from Azure Portal or /Users/celeste7/Desktop/MS_APP_Documents.md)
AZURE_TENANT_ID=073af86c-74f3-422b-ad5c-a35d41fce4be
AZURE_CLIENT_ID=41f6dc82-8127-4330-97e0-c6b26e6aa967
AZURE_CLIENT_SECRET=<get_from_Azure_Portal_Certificates_and_secrets>
AZURE_REDIRECT_URI=http://localhost:3000/api/v1/auth/callback

# Token Encryption
TOKEN_ENCRYPTION_KEY=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# Supabase (Cloud_PMS)
SUPABASE_URL=https://vzsohavtuotocgrfkfyd.supabase.co
SUPABASE_SERVICE_KEY=<your-service-key>

# Document Processing
DIGEST_SERVICE_URL=https://celeste-digest-index.onrender.com
YACHT_SALT=e49469e09cb6529e0bfef118370cf8425b006f0abbc77475da2e0cb479af8b18

# Backend
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Redis
REDIS_URL=redis://localhost:6379/0
```

---

## Security Notes

### Token Expiration
- **Access tokens:** Expire after 1 hour (automatically refreshed by token manager)
- **Refresh tokens:** Long-lived (maintained with `offline_access` permission)
- **Client secret:** Expires **August 1, 2028**

### Token Storage
- All tokens stored encrypted in database using Fernet symmetric encryption
- Encryption key stored separately in environment variable
- Token refresh happens automatically 5 minutes before expiry

### Permissions Breakdown

**Why Files.Read.All (Application)?**
- Allows backend to access OneDrive files on behalf of any authenticated user
- Required for server-side file enumeration and download
- Admin consent granted

**Why offline_access (Delegated)?**
- Enables refresh tokens
- Allows seamless re-authentication without user interaction
- Critical for background sync operations

**Why User.Read (Delegated)?**
- Get user profile (email, display name)
- Identify which Microsoft account connected
- Display in dashboard

---

## OAuth Flow Configuration

### Scopes Requested

```python
# app/config.py
azure_scopes: list = ["Files.Read.All", "User.Read", "offline_access"]
```

**Note:** Even though `Files.Read.All` has Application permission, we also request it as Delegated scope in OAuth flow for user-context access.

---

## Troubleshooting

### Error: AADSTS700016 - Application not found
**Cause:** Client ID incorrect
**Fix:** Verify `AZURE_CLIENT_ID=41f6dc82-8127-4330-97e0-c6b26e6aa967`

### Error: AADSTS7000215 - Invalid client secret
**Cause:** Secret expired or incorrect
**Fix:** Retrieve secret from Azure Portal → CelesteOS.Read → Certificates & secrets
**Expiry:** August 1, 2028
**Location:** `/Users/celeste7/Desktop/MS_APP_Documents.md` (local reference)

### Error: AADSTS650053 - Access denied
**Cause:** User missing OneDrive license
**Fix:** Ensure user has Microsoft 365 with OneDrive for Business

### Error: Redirect URI mismatch
**Cause:** Redirect URI not in Azure configuration
**Fix:** Add URI in Azure Portal → Authentication → Web → Add URI

---

## Production Deployment Checklist

- [ ] Update `AZURE_REDIRECT_URI` to production URL
- [ ] Add production redirect URI in Azure Portal
- [ ] Generate new `TOKEN_ENCRYPTION_KEY` for production
- [ ] Store secrets in secure vault (not in code)
- [ ] Verify all permissions still have admin consent
- [ ] Test OAuth flow end-to-end in production
- [ ] Set calendar reminder for secret rotation (July 2028)

---

## Admin Consent Status

✅ **All permissions have admin consent granted for CELESTE7 LTD**

No additional consent required. Users can immediately connect their OneDrive accounts.

---

## Related Documentation

- [AZURE_SETUP.md](AZURE_SETUP.md) - General Azure setup guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [WEEK2_TESTING.md](WEEK2_TESTING.md) - OAuth flow testing

---

## Quick Test

```bash
# Test OAuth URL generation
curl -X POST http://localhost:8000/api/v1/auth/connect \
  -H "Content-Type: application/json" \
  -d '{"yacht_id": "test-yacht-001"}'

# Expected response should include:
# auth_url: "https://login.microsoftonline.com/073af86c-74f3-422b-ad5c-a35d41fce4be/oauth2/v2.0/authorize?..."
```

---

## Contact

For Azure app configuration issues, contact CELESTE7 LTD IT admin with Global Administrator role.
