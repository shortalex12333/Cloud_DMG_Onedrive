# OneDrive 403 Error Diagnostic Checklist

## Error Message
```
403: You do not have access to create this personal site or you do not have a valid license
```

## Possible Causes & Solutions

### 1. **License Propagation Delay** ⏱️
**Timeframe**: 1-4 hours after license assignment

**What to check:**
- When was the Microsoft 365 Business Basic license assigned?
- Has it been at least 4 hours since assignment?

**Solution**: Wait 4 hours, then test again

---

### 2. **OneDrive Not Provisioned** 🏗️
**Most Common Cause**

Even with a valid license, OneDrive for Business needs first-time setup.

**Steps to provision:**
1. Have user go to **https://office.com**
2. Sign in with **x@alex-short.com**
3. Click the **OneDrive** icon/tile
4. Wait **10-15 minutes** for Microsoft to create the OneDrive site
5. Try browsing files in OneDrive web interface
6. Once files are visible at office.com, return to https://digest.celeste7.ai/dashboard

**How to verify:**
- Can the user see their OneDrive at office.com?
- Can they upload/download files there?
- If yes, provisioning is complete
- If no, wait longer or contact Microsoft support

---

### 3. **OneDrive Disabled at Organization Level** 🚫

**What to check (requires admin):**
1. Go to **https://admin.microsoft.com**
2. Navigate to **Settings** → **Org settings** → **Services**
3. Click **OneDrive**
4. Ensure "Let people in your organization use OneDrive" is **checked**

**Solution**: Enable OneDrive for the organization

---

### 4. **SharePoint Admin Settings** 📋

OneDrive for Business is built on SharePoint. Check SharePoint settings:

**What to check (requires admin):**
1. Go to **https://admin.microsoft.com**
2. Navigate to **Admin centers** → **SharePoint**
3. Go to **Settings**
4. Check if OneDrive creation is restricted
5. Verify x@alex-short.com is not blocked

**Solution**: Enable OneDrive creation for all users or specific user

---

### 5. **User Not Fully Synced to Microsoft 365** 👤

**What to check:**
1. Go to **https://admin.microsoft.com** → **Users** → **Active users**
2. Click on **x@alex-short.com**
3. Check if "Sign-in blocked" = **No**
4. Check if "Licenses and apps" shows **Microsoft 365 Business Basic** with checkmark
5. Specifically ensure these are checked:
   - ✅ SharePoint Online
   - ✅ OneDrive for Business

**Solution**:
- Ensure all licenses are checked
- If recently added, sign out and sign in again

---

### 6. **Conditional Access Policies** 🔐

**What to check (requires Azure AD Premium):**
1. Go to **https://portal.azure.com**
2. Navigate to **Azure Active Directory** → **Security** → **Conditional Access**
3. Check if any policies block OneDrive/SharePoint access
4. Check if any policies require device compliance

**Solution**: Adjust or exclude x@alex-short.com from blocking policies

---

### 7. **Azure App Permissions Issue** 🔑

**What to check:**
1. Go to **https://portal.azure.com**
2. Navigate to **Azure Active Directory** → **App registrations**
3. Find your app (ID: **41f6dc82-8127-4330-97e0-c6b26e6aa967**)
4. Go to **API permissions**
5. Verify these delegated permissions are granted:
   - ✅ Files.Read.All
   - ✅ User.Read
   - ✅ offline_access

**Solution**:
- Grant admin consent if not already done
- Add missing permissions

---

## Diagnostic Commands (for testing)

### Test 1: Check if user can access Microsoft Graph
```bash
curl "https://digest-cloud.int.celeste7.ai/api/v1/auth/test-token?connection_id=64666a06-dbee-43a0-838f-930a98e765c6"
```
**Expected**: Should return user profile
**If fails**: Token/authentication issue

### Test 2: Check connection health
```bash
curl "https://digest-cloud.int.celeste7.ai/api/v1/auth/health-check?connection_id=64666a06-dbee-43a0-838f-930a98e765c6"
```
**Expected**: `healthy: true`
**If fails**: Connection/token issue

### Test 3: Try browsing OneDrive
```bash
curl "https://digest-cloud.int.celeste7.ai/api/v1/files/browse?connection_id=64666a06-dbee-43a0-838f-930a98e765c6&path=/"
```
**Current**: 403 error
**Expected after fix**: List of files

---

## Recommended Next Steps

**Priority Order:**

1. ✅ **Verify license is actually assigned** (check in admin center)
2. ✅ **Have user visit office.com and click OneDrive** (triggers provisioning)
3. ⏱️ **Wait 15 minutes** (provisioning time)
4. 🔄 **Test at office.com first** (can user see OneDrive there?)
5. 🔄 **Then test dashboard** (https://digest.celeste7.ai/dashboard)

If still failing after all these steps:
- **Check organization-wide OneDrive settings**
- **Check SharePoint admin center**
- **Contact Microsoft support** (license/provisioning issues)

---

## Quick Test at Office.com

Have the user:
1. Go to **https://office.com**
2. Sign in with **x@alex-short.com**
3. Click **OneDrive** icon

**If they see:**
- ✅ "Welcome to OneDrive" setup wizard → Click through setup
- ✅ Their files/folders → OneDrive is working! Try dashboard again
- ❌ 403 error → Issue is with Microsoft 365 licensing/settings (not our code)
- ❌ "OneDrive is not available" → Disabled at org level

This test isolates whether the issue is:
- **Our code** (unlikely - auth is working)
- **Microsoft 365 configuration** (most likely)
