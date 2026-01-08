# Azure App Registration Setup

## Overview

This document outlines the Azure Active Directory (Azure AD) app registration required for the CelesteOS OneDrive Integration to access OneDrive for Business files.

---

## Prerequisites

- Azure AD tenant (Microsoft 365 subscription)
- Global Administrator or Application Administrator role

---

## Step 1: Create App Registration

1. **Navigate to Azure Portal**
   - Go to: https://portal.azure.com
   - Sign in with admin account

2. **Create New App Registration**
   - Go to: **Azure Active Directory** → **App registrations** → **New registration**
   - **Name:** `CelesteOS OneDrive Integration`
   - **Supported account types:** `Accounts in this organizational directory only (Single tenant)`
   - **Redirect URI:**
     - Platform: `Web`
     - URI: `http://localhost:3000/api/v1/auth/callback` (development)
   - Click: **Register**

3. **Record Application Details**
   ```
   Application (client) ID: <copy this value>
   Directory (tenant) ID: <copy this value>
   ```

---

## Step 2: Configure API Permissions

1. **Go to API Permissions**
   - Navigate to: **App registrations** → **CelesteOS OneDrive Integration** → **API permissions**

2. **Add Microsoft Graph Permissions**
   - Click: **Add a permission** → **Microsoft Graph** → **Delegated permissions**
   - Select the following permissions:
     - ✅ **Files.Read.All** - Read all files that user can access
     - ✅ **User.Read** - Sign in and read user profile
     - ✅ **offline_access** - Maintain access to data you have given it access to

3. **Grant Admin Consent** (if required)
   - Click: **Grant admin consent for [Your Organization]**
   - Confirm: **Yes**

**Final Permissions List:**
```
Microsoft Graph (Delegated):
  - Files.Read.All
  - User.Read
  - offline_access
```

---

## Step 3: Create Client Secret

1. **Go to Certificates & Secrets**
   - Navigate to: **App registrations** → **CelesteOS OneDrive Integration** → **Certificates & secrets**

2. **Create New Client Secret**
   - Click: **New client secret**
   - **Description:** `CelesteOS OneDrive Backend`
   - **Expires:** `24 months` (recommended)
   - Click: **Add**

3. **Record Client Secret**
   ```
   Client Secret Value: <copy this value IMMEDIATELY>
   ```
   ⚠️ **IMPORTANT:** This value is only shown ONCE. Copy it now!

---

## Step 4: Configure Redirect URIs

1. **Go to Authentication**
   - Navigate to: **App registrations** → **CelesteOS OneDrive Integration** → **Authentication**

2. **Add Redirect URIs**
   - **Development:**
     - `http://localhost:3000/api/v1/auth/callback`
   - **Production:** (add when deployed)
     - `https://your-domain.com/api/v1/auth/callback`

3. **Configure Platform Settings**
   - **Supported account types:** Single tenant
   - **Allow public client flows:** No

---

## Step 5: Configure Environment Variables

1. **Generate Token Encryption Key**
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Create `.env` File**
   Copy `.env.example` to `.env` and fill in values:
   ```bash
   # Azure AD Configuration
   AZURE_TENANT_ID=<Directory (tenant) ID from Step 1>
   AZURE_CLIENT_ID=<Application (client) ID from Step 1>
   AZURE_CLIENT_SECRET=<Client Secret Value from Step 3>
   AZURE_REDIRECT_URI=http://localhost:3000/api/v1/auth/callback

   # Token Encryption
   TOKEN_ENCRYPTION_KEY=<Generated Fernet key from Step 5.1>

   # Supabase Configuration
   SUPABASE_URL=https://vzsohavtuotocgrfkfyd.supabase.co
   SUPABASE_SERVICE_KEY=<your-service-key>

   # Document Processing
   DIGEST_SERVICE_URL=https://celeste-digest-index.onrender.com
   YACHT_SALT=e49469e09cb6529e0bfef118370cf8425b006f0abbc77475da2e0cb479af8b18
   ```

---

## Step 6: Test Configuration

1. **Start Development Server**
   ```bash
   docker-compose up
   ```

2. **Navigate to Frontend**
   - Open: http://localhost:3000
   - Click: **Connect OneDrive**

3. **Expected OAuth Flow**
   - Redirect to Microsoft login page
   - User signs in with Microsoft 365 account
   - Consent screen shows requested permissions
   - Redirect back to application with authorization code
   - Backend exchanges code for access token
   - Token stored encrypted in database

---

## Troubleshooting

### Error: AADSTS700016 - Application not found
**Cause:** Application (client) ID is incorrect
**Fix:** Verify `AZURE_CLIENT_ID` matches Application ID from Azure Portal

### Error: AADSTS7000215 - Invalid client secret
**Cause:** Client secret is incorrect or expired
**Fix:** Generate new client secret in Azure Portal and update `AZURE_CLIENT_SECRET`

### Error: AADSTS650053 - Access denied
**Cause:** User does not have OneDrive for Business
**Fix:** Ensure user has valid Microsoft 365 license with OneDrive

### Error: Redirect URI mismatch
**Cause:** Redirect URI in request does not match Azure configuration
**Fix:** Add exact redirect URI to Azure Portal → Authentication → Redirect URIs

---

## Security Best Practices

1. **Client Secret Rotation**
   - Rotate client secrets every 6-12 months
   - Never commit secrets to version control
   - Use Azure Key Vault for production secrets

2. **Token Storage**
   - All tokens stored encrypted in database using Fernet encryption
   - Encryption key (`TOKEN_ENCRYPTION_KEY`) stored separately
   - Access tokens expire after 1 hour (automatically refreshed)

3. **Permissions**
   - Request minimum required permissions (Files.Read.All, not Files.ReadWrite.All)
   - Use delegated permissions (user context), not application permissions

4. **Monitoring**
   - Enable Azure AD sign-in logs
   - Monitor for unusual OAuth flows
   - Review consent grants regularly

---

## Production Deployment Checklist

- [ ] Create new client secret (separate from development)
- [ ] Add production redirect URI to Azure Portal
- [ ] Update `AZURE_REDIRECT_URI` in production environment
- [ ] Store secrets in secure vault (Azure Key Vault, AWS Secrets Manager)
- [ ] Enable Azure AD audit logs
- [ ] Configure conditional access policies
- [ ] Test OAuth flow end-to-end in production

---

## References

- [Microsoft Graph API Documentation](https://learn.microsoft.com/en-us/graph/overview)
- [OneDrive API Reference](https://learn.microsoft.com/en-us/graph/api/resources/onedrive)
- [Azure AD App Registration](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [OAuth 2.0 Authorization Code Flow](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)
