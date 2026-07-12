-- Migration: Add Multi-Tenant Columns
-- Description: Add organization and multi-tenant related columns for commercial features
-- Version: 001
-- Dependencies: base schema

-- This migration adds columns needed for multi-tenant support

-- Add org_id to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS org_id INTEGER;

-- Add shared_with_orgs for cross-organization sharing
ALTER TABLE documents ADD COLUMN IF NOT EXISTS shared_with_orgs JSONB;

-- Add org_id to conversations table
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS org_id INTEGER;

-- Add org_id to model_configs table
ALTER TABLE model_configs ADD COLUMN IF NOT EXISTS org_id INTEGER;

-- Add org_id to users table (for multi-tenant mode)
ALTER TABLE users ADD COLUMN IF NOT EXISTS org_id INTEGER;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_org_id ON documents(org_id);
CREATE INDEX IF NOT EXISTS idx_conversations_org_id ON conversations(org_id);
CREATE INDEX IF NOT EXISTS idx_model_configs_org_id ON model_configs(org_id);
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);

-- Comments
COMMENT ON COLUMN documents.org_id IS 'Organization ID for multi-tenant isolation';
COMMENT ON COLUMN documents.shared_with_orgs IS 'List of organization IDs that can access this document';
COMMENT ON COLUMN conversations.org_id IS 'Organization ID for multi-tenant isolation';
COMMENT ON COLUMN model_configs.org_id IS 'Organization ID for multi-tenant isolation';
