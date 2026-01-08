-- Manual migration SQL for OneDrive Integration Tables
-- Run this in Supabase SQL Editor if Alembic migrations can't connect

-- Create onedrive_connections table
CREATE TABLE IF NOT EXISTS onedrive_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    yacht_id TEXT NOT NULL,
    user_principal_name TEXT NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    sync_enabled BOOLEAN DEFAULT true,
    selected_folders JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uq_yacht_user UNIQUE (yacht_id, user_principal_name)
);

CREATE INDEX IF NOT EXISTS ix_onedrive_connections_yacht_id ON onedrive_connections(yacht_id);

-- Create onedrive_sync_state table
CREATE TABLE IF NOT EXISTS onedrive_sync_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID NOT NULL REFERENCES onedrive_connections(id) ON DELETE CASCADE,
    yacht_id TEXT NOT NULL,
    onedrive_item_id TEXT NOT NULL,
    onedrive_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size BIGINT,
    onedrive_etag TEXT,
    sync_status TEXT NOT NULL DEFAULT 'pending',
    supabase_doc_id UUID,
    extracted_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_connection_item UNIQUE (connection_id, onedrive_item_id)
);

CREATE INDEX IF NOT EXISTS ix_onedrive_sync_state_yacht_id ON onedrive_sync_state(yacht_id);

-- Create onedrive_sync_jobs table
CREATE TABLE IF NOT EXISTS onedrive_sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID NOT NULL REFERENCES onedrive_connections(id) ON DELETE CASCADE,
    yacht_id TEXT NOT NULL,
    job_status TEXT NOT NULL DEFAULT 'pending',
    total_files_found INTEGER DEFAULT 0,
    files_succeeded INTEGER DEFAULT 0,
    files_failed INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_onedrive_sync_jobs_yacht_id ON onedrive_sync_jobs(yacht_id);
