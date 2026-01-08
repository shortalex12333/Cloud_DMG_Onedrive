# CelesteOS OneDrive Integration

Cloud-to-cloud document ingestion from OneDrive for Business to CelesteOS document processing pipeline.

---

## Overview

This system provides a standalone alternative to the NAS-based document ingestion system for yacht clients who store their documentation in Microsoft OneDrive for Business instead of local network storage.

**Key Features:**
- OAuth 2.0 authentication with Microsoft 365
- Browse and select OneDrive folders for sync
- Automatic metadata extraction from folder hierarchy
- Cloud-to-cloud file transfer (OneDrive → Supabase Storage)
- Integration with existing CelesteOS document processing pipeline
- Real-time sync status tracking

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  CLOUD_DMG_ONEDRIVE                          │
│                                                              │
│  Next.js/React Portal                                       │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────┐      │
│  │  OAuth     │  │ File Browser │  │ Sync Status   │      │
│  │  Connect   │  │ (OneDrive)   │  │  Dashboard    │      │
│  └────────────┘  └──────────────┘  └───────────────┘      │
│         │                 │                  │              │
│         └─────────────────┼──────────────────┘              │
│                           │                                 │
│  FastAPI Backend          │                                 │
│  ┌────────────────────────┼───────────────────────┐        │
│  │  Graph API  Token Mgr  │  Sync Engine          │        │
│  │  Client     (refresh)  │  (orchestrator)       │        │
│  └────────────────────────┼───────────────────────┘        │
│         │                 │                  │              │
└─────────┼─────────────────┼──────────────────┼──────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
   Microsoft         Supabase           Existing Processing
   Graph API         Cloud_PMS          celeste-digest-index
   (OneDrive)        Database           .onrender.com
                     + Storage
```

---

## Tech Stack

**Frontend:**
- Next.js 14 (React, TypeScript)
- TailwindCSS + shadcn/ui
- OAuth 2.0 client

**Backend:**
- FastAPI (Python 3.11)
- SQLAlchemy + Alembic
- Microsoft Graph API (MSAL)
- Celery + Redis (background jobs)
- Fernet encryption (token storage)

**Database:**
- Supabase PostgreSQL (Cloud_PMS database)
- Tables: `onedrive_connections`, `onedrive_sync_state`, `onedrive_sync_jobs`

**Document Processing:**
- Same pipeline as NAS system (celeste-digest-index.onrender.com)
- No changes required to existing processing service

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Azure AD app registration (see [AZURE_SETUP.md](docs/AZURE_SETUP.md))
- Supabase Cloud_PMS database access

### 1. Clone Repository

```bash
git clone https://github.com/shortalex12333/Cloud_DMG_Onedrive.git
cd Cloud_DMG_Onedrive
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Azure and Supabase credentials
```

See [AZURE_SETUP.md](docs/AZURE_SETUP.md) for Azure app registration steps.

### 3. Run Database Migrations

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
cd ..
```

### 4. Start Services

```bash
docker-compose up
```

**Services:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Redis: localhost:6379

---

## Development

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## Project Structure

```
Cloud_DMG_Onedrive/
├── README.md
├── .env.example
├── docker-compose.yml
│
├── frontend/                      # Next.js portal
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx          # Landing page
│   │   │   ├── auth/
│   │   │   │   └── callback/page.tsx
│   │   │   └── dashboard/
│   │   │       ├── page.tsx      # Main dashboard
│   │   │       ├── browse/page.tsx
│   │   │       └── sync/page.tsx
│   │   ├── components/
│   │   │   ├── auth/ConnectButton.tsx
│   │   │   ├── files/FileBrowser.tsx
│   │   │   └── sync/SyncStatusCard.tsx
│   │   └── lib/
│   │       ├── api-client.ts
│   │       └── hooks/useConnection.ts
│   └── package.json
│
├── backend/                       # FastAPI app
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/v1/
│   │   │   ├── auth.py          # OAuth endpoints
│   │   │   ├── files.py         # File browser endpoints
│   │   │   └── sync.py          # Sync endpoints
│   │   ├── core/
│   │   │   ├── graph_client.py   # Microsoft Graph API wrapper
│   │   │   ├── token_manager.py  # Token encryption/refresh
│   │   │   ├── encryption.py     # Fernet encryption
│   │   │   ├── file_enumerator.py # OneDrive traversal
│   │   │   ├── metadata_extractor.py # Path → metadata
│   │   │   └── sync_manager.py   # Sync orchestration
│   │   ├── models/
│   │   │   ├── connection.py
│   │   │   ├── sync_state.py
│   │   │   └── sync_job.py
│   │   └── db/
│   │       ├── session.py
│   │       └── repositories/
│   ├── alembic/
│   │   └── versions/
│   │       └── 001_initial_onedrive_tables.py
│   └── requirements.txt
│
└── docs/
    ├── AZURE_SETUP.md
    └── DEPLOYMENT.md
```

---

## Database Schema

### `onedrive_connections`
Stores OAuth tokens and sync configuration per yacht.

```sql
- id (UUID, PK)
- yacht_id (TEXT)
- user_principal_name (TEXT)
- access_token_encrypted (TEXT)
- refresh_token_encrypted (TEXT)
- token_expires_at (TIMESTAMP)
- sync_enabled (BOOLEAN)
- selected_folders (JSONB)
- created_at, last_sync_at (TIMESTAMP)
```

### `onedrive_sync_state`
Tracks per-file sync status.

```sql
- id (UUID, PK)
- connection_id (UUID, FK)
- yacht_id (TEXT)
- onedrive_item_id (TEXT)
- onedrive_path (TEXT)
- file_name (TEXT)
- sync_status (TEXT)
- extracted_metadata (JSONB)
- created_at (TIMESTAMP)
```

### `onedrive_sync_jobs`
Tracks batch sync operations.

```sql
- id (UUID, PK)
- connection_id (UUID, FK)
- yacht_id (TEXT)
- job_status (TEXT)
- total_files_found, files_succeeded, files_failed (INTEGER)
- started_at, completed_at (TIMESTAMP)
```

---

## Implementation Timeline

### Week 1: Project Setup ✅ COMPLETE
- [x] Initialize Next.js app with TypeScript, TailwindCSS, shadcn/ui
- [x] Initialize FastAPI backend with SQLAlchemy
- [x] Create Docker Compose
- [x] Create Alembic migration for OneDrive tables
- [x] Document Azure app registration

### Week 2: OAuth & Microsoft Graph Integration ✅ COMPLETE
- [x] Implement OAuth 2.0 flow endpoints (connect, callback, disconnect)
- [x] Build token manager with Fernet encryption
- [x] Create Microsoft Graph API client wrapper
- [x] Implement automatic token refresh
- [x] Build frontend OAuth components (ConnectButton, useConnection hook)
- [x] Test OAuth flow end-to-end

### Week 3: File Browser & Sync Engine ✅ COMPLETE
- [x] Build OneDrive file enumeration endpoints
- [x] Port metadata extraction logic from NAS system
- [x] Create sync manager with document processing integration
- [x] Build file browser UI component
- [x] Integrate with existing document processing (celeste-digest-index)
- [x] Real-time sync progress tracking

---

## Environment Variables

```bash
# Azure AD
AZURE_TENANT_ID=<tenant_id>
AZURE_CLIENT_ID=<client_id>
AZURE_CLIENT_SECRET=<client_secret>
AZURE_REDIRECT_URI=http://localhost:3000/api/v1/auth/callback

# Token Encryption
TOKEN_ENCRYPTION_KEY=<fernet_key>

# Supabase
SUPABASE_URL=https://vzsohavtuotocgrfkfyd.supabase.co
SUPABASE_SERVICE_KEY=<service_key>

# Document Processing
DIGEST_SERVICE_URL=https://celeste-digest-index.onrender.com
YACHT_SALT=e49469e09cb6529e0bfef118370cf8425b006f0abbc77475da2e0cb479af8b18
```

---

## Testing

### Manual Testing

1. **Start services:** `docker-compose up`
2. **Navigate to:** http://localhost:3000
3. **Click:** "Connect OneDrive"
4. **Sign in** with Microsoft 365 account
5. **Browse** OneDrive folders
6. **Select** folders to sync
7. **Trigger** manual sync
8. **Verify** files uploaded to Supabase Storage

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Get OAuth authorization URL (Week 2)
curl http://localhost:8000/api/v1/auth/connect?yacht_id=test-yacht-123
```

---

## Security

- OAuth 2.0 with PKCE for authorization
- All tokens encrypted at rest using Fernet
- Service role authentication for Supabase operations
- HTTPS/TLS 1.2+ for all external communication
- Yacht signature authentication (HMAC-SHA256) for document processing

---

## Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment instructions.

---

## Related Documentation

- [Azure App Registration](docs/AZURE_SETUP.md) - Setup guide for Azure AD
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [RENDER_SERVICES_MAP.md](../Cloud_PMS_render/RENDER_SERVICES_MAP.md) - Existing Render services

---

## Contributing

This is an internal CelesteOS project. For questions or issues, contact the development team.

---

## License

Proprietary - CelesteOS
