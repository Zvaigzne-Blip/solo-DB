-- ============================================================================
-- SoloHub Database Schema for Supabase (PostgreSQL)
-- The Autonomous Business Engine for Solopreneurs
-- ============================================================================
-- Generated: 2026-03-03
-- Platform:  Supabase (PostgreSQL 15+)
-- Backend:   Python Django
-- ============================================================================
-- Module Map:
--   1. Smart Multichannel Inbox
--   2. Purchase Invoices (AP)
--   3. Sales Invoices (AR)
--   4. Banking Hub
--   5. Accountant Hub
--   6. Settings & Workspace Management
--   7. Main Dashboard
--   8. Gmail Add-on & Workspace Synchronization
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- fuzzy text matching


-- ============================================================================
-- SECTION 0: CUSTOM ENUM TYPES
-- ============================================================================

-- Core / IAM
CREATE TYPE user_role AS ENUM (
    'owner', 'admin', 'accountant', 'member', 'viewer'
);
CREATE TYPE member_status AS ENUM (
    'pending', 'active', 'suspended', 'removed'
);

-- Channels & Integrations
CREATE TYPE channel_type AS ENUM (
    'gmail', 'outlook', 'whatsapp', 'telegram', 'sms', 'gdrive'
);
CREATE TYPE integration_status AS ENUM (
    'active', 'inactive', 'error', 'pending_auth'
);
CREATE TYPE bank_connection_status AS ENUM (
    'active', 'expired', 'revoked', 'pending_auth', 'error'
);
CREATE TYPE tax_integration_status AS ENUM (
    'active', 'inactive', 'error', 'pending_auth'
);

-- Contacts
CREATE TYPE contact_type AS ENUM (
    'vendor', 'customer', 'both'
);

-- Smart Inbox
CREATE TYPE message_source AS ENUM (
    'gmail', 'outlook', 'whatsapp', 'telegram', 'gdrive', 'manual'
);
CREATE TYPE message_classification AS ENUM (
    'invoice', 'receipt', 'check', 'remittance',
    'financial_other', 'non_financial', 'unclassified'
);
CREATE TYPE message_processing_status AS ENUM (
    'received', 'classifying', 'classified', 'extracting',
    'extracted', 'synced', 'failed', 'ignored'
);

-- Invoices
CREATE TYPE invoice_direction AS ENUM (
    'purchase', 'sale'
);
CREATE TYPE invoice_status AS ENUM (
    'draft', 'pending', 'approved', 'sent', 'delivered', 'read',
    'partially_paid', 'paid', 'overdue', 'voided', 'cancelled',
    'disputed', 'in_progress', 'payment_submitted'
);
CREATE TYPE invoice_source AS ENUM (
    'smart_inbox', 'manual', 'scan', 'api',
    'quote_conversion', 'gmail_addon'
);
CREATE TYPE payment_method AS ENUM (
    'bank_transfer', 'credit_card', 'debit_card',
    'check', 'cash', 'paypal', 'other'
);

-- Communications
CREATE TYPE comm_channel AS ENUM (
    'email', 'whatsapp', 'telegram', 'sms', 'in_app'
);
CREATE TYPE comm_status AS ENUM (
    'queued', 'sent', 'delivered', 'read', 'failed', 'bounced'
);

-- Banking
CREATE TYPE account_type AS ENUM (
    'checking', 'savings', 'credit_card', 'loan', 'investment', 'other'
);
CREATE TYPE account_status AS ENUM (
    'active', 'inactive', 'closed'
);
CREATE TYPE transaction_type AS ENUM (
    'credit', 'debit'
);
CREATE TYPE transaction_category AS ENUM (
    'invoice_payment', 'vendor_payment', 'internal_transfer',
    'bank_fee', 'interest', 'tax_payment', 'salary',
    'subscription', 'refund', 'other', 'uncategorized'
);
CREATE TYPE reconciliation_status AS ENUM (
    'matched', 'unmatched', 'missing_invoice', 'internal_transfer',
    'auto_categorized', 'manually_resolved', 'pending'
);

-- Accountant Hub
CREATE TYPE task_type AS ENUM (
    'missing_invoice', 'missing_receipt', 'clarify_transaction',
    'approve_vat_return', 'approve_tax_filing', 'upload_document',
    'general_request', 'compliance_deadline'
);
CREATE TYPE task_status AS ENUM (
    'open', 'in_progress', 'waiting_client', 'waiting_cpa',
    'resolved', 'cancelled'
);
CREATE TYPE task_priority AS ENUM (
    'low', 'medium', 'high', 'urgent'
);
CREATE TYPE deadline_status AS ENUM (
    'upcoming', 'due_soon', 'overdue', 'completed', 'filed'
);
CREATE TYPE deadline_recurrence AS ENUM (
    'one_time', 'monthly', 'quarterly', 'annually'
);

-- Notifications
CREATE TYPE notification_type AS ENUM (
    'invoice_received', 'invoice_paid', 'invoice_overdue',
    'payment_confirmed', 'risk_alert', 'compliance_deadline',
    'missing_document', 'reconciliation_complete', 'dunning_sent',
    'task_assigned', 'chat_message', 'system_alert'
);


-- ============================================================================
-- SECTION 1: FOUNDATION — Workspaces, Companies, Profiles, IAM (Module 6)
-- ============================================================================

-- 1a. User profiles (extends Supabase auth.users)
CREATE TABLE profiles (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name       VARCHAR(255),
    display_name    VARCHAR(100),
    avatar_url      TEXT,
    phone           VARCHAR(50),
    timezone        VARCHAR(50) DEFAULT 'UTC',
    onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE profiles IS 'Extended user profile data; linked 1:1 with Supabase auth.users.';

-- 1b. Workspaces (top-level tenant container)
CREATE TABLE workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(100) NOT NULL UNIQUE,
    owner_id        UUID NOT NULL REFERENCES auth.users(id),
    base_currency   VARCHAR(3) NOT NULL DEFAULT 'USD',
    timezone        VARCHAR(50) NOT NULL DEFAULT 'UTC',
    logo_url        TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE workspaces IS 'Top-level tenant. A user may own/belong to multiple workspaces.';

-- 1c. Companies / Entities within a workspace
CREATE TABLE companies (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    legal_name          VARCHAR(255) NOT NULL,
    trade_name          VARCHAR(255),
    tax_id              VARCHAR(100),
    registration_number VARCHAR(100),
    address_line1       VARCHAR(255),
    address_line2       VARCHAR(255),
    city                VARCHAR(100),
    state_province      VARCHAR(100),
    postal_code         VARCHAR(20),
    country_code        VARCHAR(2),
    phone               VARCHAR(50),
    email               VARCHAR(255),
    website             VARCHAR(255),
    logo_url            TEXT,
    is_default          BOOLEAN DEFAULT FALSE,
    is_individual       BOOLEAN DEFAULT FALSE,
    base_currency       VARCHAR(3) DEFAULT 'USD',
    fiscal_year_start   INTEGER DEFAULT 1,  -- month (1-12)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE companies IS 'Corporate entities within a workspace. The default entity is auto-provisioned on workspace creation.';

-- 1d. Workspace members (IAM)
CREATE TABLE workspace_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    email           VARCHAR(255) NOT NULL,
    role            user_role NOT NULL DEFAULT 'member',
    status          member_status NOT NULL DEFAULT 'pending',
    invited_by      UUID REFERENCES auth.users(id),
    invited_at      TIMESTAMPTZ DEFAULT NOW(),
    joined_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(workspace_id, email)
);
COMMENT ON TABLE workspace_members IS 'Maps users to workspaces with role-based access. Tracks invitation lifecycle (PENDING → ACTIVE).';

-- 1e. Role-permission matrix (RBAC enforcement)
CREATE TABLE role_permissions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role        user_role NOT NULL,
    resource    VARCHAR(100) NOT NULL,
    action      VARCHAR(50) NOT NULL,
    is_allowed  BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(role, resource, action)
);
COMMENT ON TABLE role_permissions IS 'Fine-grained RBAC permission matrix. Resources: invoices, bank_accounts, company_settings, etc. Actions: create, read, update, delete, approve, pay.';

-- 1f. Workspace preferences (global variables)
CREATE TABLE workspace_preferences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    key             VARCHAR(100) NOT NULL,
    value           JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(workspace_id, key)
);
COMMENT ON TABLE workspace_preferences IS 'System-wide environment variables: base_currency, default_payment_terms, etc.';


-- ============================================================================
-- SECTION 2: INTEGRATIONS — Channels, Banking, Tax, GDrive (Module 6)
-- ============================================================================

-- 2a. Connected channels (Gmail, Outlook, WhatsApp, Telegram)
CREATE TABLE connected_channels (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id            UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id              UUID REFERENCES companies(id) ON DELETE CASCADE,
    channel_type            channel_type NOT NULL,
    display_name            VARCHAR(255),
    account_identifier      VARCHAR(255),
    access_token_encrypted  TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at        TIMESTAMPTZ,
    webhook_url             TEXT,
    webhook_secret_encrypted TEXT,
    status                  integration_status DEFAULT 'pending_auth',
    last_sync_at            TIMESTAMPTZ,
    sync_cursor             TEXT,   -- Gmail historyId, Telegram offset, etc.
    metadata                JSONB DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE connected_channels IS 'OAuth credentials and webhook config for email/messaging integrations that feed the Smart Inbox.';

-- 2b. Bank connections (Open Banking AIS/PIS)
CREATE TABLE bank_connections (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id            UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id              UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    provider                VARCHAR(100) NOT NULL,
    institution_name        VARCHAR(255),
    institution_logo_url    TEXT,
    external_connection_id  VARCHAR(255),
    consent_token_encrypted TEXT,
    consent_expires_at      TIMESTAMPTZ,
    status                  bank_connection_status DEFAULT 'pending_auth',
    supports_ais            BOOLEAN DEFAULT TRUE,
    supports_pis            BOOLEAN DEFAULT FALSE,
    last_sync_at            TIMESTAMPTZ,
    metadata                JSONB DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE bank_connections IS 'Open Banking (AIS/PIS) consent records. Each entity-level connection feeds bank accounts and transactions.';

-- 2c. Tax authority integrations
CREATE TABLE tax_authority_integrations (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id            UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id              UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    authority_code          VARCHAR(50) NOT NULL,
    authority_name          VARCHAR(255),
    region                  VARCHAR(100),
    auth_type               VARCHAR(50),
    access_token_encrypted  TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at        TIMESTAMPTZ,
    tax_reference           VARCHAR(100),
    status                  tax_integration_status DEFAULT 'pending_auth',
    metadata                JSONB DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE tax_authority_integrations IS 'Credentials for regional tax authority APIs (HMRC, IRS, e-invoicing portals) at the company entity level.';

-- 2d. GDrive connections
CREATE TABLE gdrive_connections (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id            UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id              UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    source_folder_id        VARCHAR(255),
    destination_folder_id   VARCHAR(255),
    access_token_encrypted  TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at        TIMESTAMPTZ,
    status                  integration_status DEFAULT 'pending_auth',
    last_sync_at            TIMESTAMPTZ,
    metadata                JSONB DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE gdrive_connections IS 'GDrive source folder (new invoices) and destination folder (archive) per company entity.';


-- ============================================================================
-- SECTION 3: CONTACTS — Vendors & Customers
-- ============================================================================

CREATE TABLE contacts (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id                UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id                  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    contact_type                contact_type NOT NULL DEFAULT 'vendor',
    name                        VARCHAR(255) NOT NULL,
    legal_name                  VARCHAR(255),
    email                       VARCHAR(255),
    phone                       VARCHAR(50),
    tax_id                      VARCHAR(100),
    address_line1               VARCHAR(255),
    address_line2               VARCHAR(255),
    city                        VARCHAR(100),
    state_province              VARCHAR(100),
    postal_code                 VARCHAR(20),
    country_code                VARCHAR(2),
    -- Bank details (encrypted at rest)
    bank_name                   VARCHAR(255),
    bank_account_number_encrypted TEXT,
    bank_routing_number_encrypted TEXT,
    bank_iban_encrypted         TEXT,
    bank_swift                  VARCHAR(20),
    bank_currency               VARCHAR(3),
    -- Terms
    payment_terms_days          INTEGER DEFAULT 30,
    default_currency            VARCHAR(3) DEFAULT 'USD',
    -- Risk
    credit_risk_score           SMALLINT CHECK (credit_risk_score BETWEEN 1 AND 5),
    fraud_risk_score            SMALLINT CHECK (fraud_risk_score BETWEEN 1 AND 5),
    -- Behavioral stats (denormalized, updated by triggers/cron)
    total_invoices              INTEGER DEFAULT 0,
    total_paid                  DECIMAL(15,2) DEFAULT 0,
    avg_payment_days            DECIMAL(5,1),
    last_invoice_date           DATE,
    --
    notes                       TEXT,
    is_active                   BOOLEAN DEFAULT TRUE,
    metadata                    JSONB DEFAULT '{}',
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE contacts IS 'Unified vendor/customer directory. Bank details are encrypted. Behavioral stats power risk scoring.';

-- Contact audit log (tracks field changes for fraud detection)
CREATE TABLE contact_audit_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id  UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    field_name  VARCHAR(100) NOT NULL,
    old_value   TEXT,
    new_value   TEXT,
    changed_by  UUID REFERENCES auth.users(id),
    changed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE contact_audit_log IS 'Immutable log of vendor/customer field mutations. Powers fraud risk flags (email changed, bank details altered, etc.).';


-- ============================================================================
-- SECTION 4: SMART MULTICHANNEL INBOX (Module 1)
-- ============================================================================

CREATE TABLE inbox_messages (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id            UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id              UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    channel_id              UUID REFERENCES connected_channels(id) ON DELETE SET NULL,
    -- Source metadata
    source                  message_source NOT NULL,
    external_message_id     VARCHAR(500),
    external_thread_id      VARCHAR(500),
    -- Message content
    sender_email            VARCHAR(255),
    sender_name             VARCHAR(255),
    sender_phone            VARCHAR(50),
    subject                 TEXT,
    body_preview            TEXT,
    body_html               TEXT,
    received_at             TIMESTAMPTZ NOT NULL,
    -- Classification (Phase 2 – "Accountant" AI layer)
    classification          message_classification DEFAULT 'unclassified',
    classification_confidence DECIMAL(5,4),
    classified_at           TIMESTAMPTZ,
    -- Processing pipeline status
    processing_status       message_processing_status DEFAULT 'received',
    processing_error        TEXT,
    -- Linked entities (populated after extraction/sync)
    linked_invoice_id       UUID,   -- FK added after invoices table
    linked_contact_id       UUID REFERENCES contacts(id) ON DELETE SET NULL,
    -- Gmail label sync (Phase 4)
    gmail_label             VARCHAR(100),
    gmail_label_synced_at   TIMESTAMPTZ,
    --
    is_read                 BOOLEAN DEFAULT FALSE,
    is_starred              BOOLEAN DEFAULT FALSE,
    metadata                JSONB DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE inbox_messages IS 'All ingested messages from Gmail, Outlook, WhatsApp, Telegram, GDrive. Classified by the AI "Accountant" agent.';

CREATE TABLE inbox_attachments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id          UUID NOT NULL REFERENCES inbox_messages(id) ON DELETE CASCADE,
    filename            VARCHAR(500) NOT NULL,
    mime_type           VARCHAR(100),
    file_size_bytes     BIGINT,
    storage_path        TEXT,
    storage_bucket      VARCHAR(100) DEFAULT 'inbox-attachments',
    -- OCR extraction (Phase 3 – Vision-Language Model)
    ocr_status          VARCHAR(20) DEFAULT 'pending'
                        CHECK (ocr_status IN ('pending','processing','completed','failed')),
    ocr_extracted_text  TEXT,
    ocr_extracted_data  JSONB,      -- {vendor_name, date, tax_amount, total_amount, line_items[], ...}
    ocr_confidence      DECIMAL(5,4),
    ocr_model           VARCHAR(50),
    ocr_processed_at    TIMESTAMPTZ,
    -- Deduplication (Phase 3 – Validation)
    content_hash        VARCHAR(64),    -- SHA-256 of file bytes
    is_duplicate        BOOLEAN DEFAULT FALSE,
    duplicate_of_id     UUID REFERENCES inbox_attachments(id),
    --
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE inbox_attachments IS 'Files attached to inbox messages. OCR engine extracts structured financial data.';


-- ============================================================================
-- SECTION 5: INVOICES — Purchase (AP) & Sales (AR) (Modules 2 & 3)
-- ============================================================================

-- Unified invoice table (direction distinguishes AP vs AR)
CREATE TABLE invoices (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id            UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id              UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- === Type & Source ===
    direction               invoice_direction NOT NULL,
    source                  invoice_source NOT NULL DEFAULT 'manual',

    -- === Reference ===
    invoice_number          VARCHAR(100),
    reference_number        VARCHAR(100),       -- PO number, contract reference

    -- === Parties ===
    contact_id              UUID REFERENCES contacts(id) ON DELETE SET NULL,
    contact_name            VARCHAR(255),       -- denormalized snapshot at creation
    contact_email           VARCHAR(255),
    contact_address         TEXT,

    -- === Dates ===
    issue_date              DATE NOT NULL,
    due_date                DATE,
    payment_terms_days      INTEGER,

    -- === Amounts ===
    currency                VARCHAR(3) DEFAULT 'USD',
    subtotal                DECIMAL(15,2) DEFAULT 0,
    tax_amount              DECIMAL(15,2) DEFAULT 0,
    tax_rate                DECIMAL(5,2),
    discount_amount         DECIMAL(15,2) DEFAULT 0,
    total_amount            DECIMAL(15,2) NOT NULL DEFAULT 0,
    amount_paid             DECIMAL(15,2) DEFAULT 0,
    amount_due              DECIMAL(15,2) GENERATED ALWAYS AS (total_amount - amount_paid) STORED,
    fx_rate                 DECIMAL(12,6),
    base_currency_total     DECIMAL(15,2),

    -- === Status & Risk ===
    status                  invoice_status DEFAULT 'draft',
    -- Fraud risk (Purchase – Module 2, Phase 3)
    fraud_risk_score        SMALLINT CHECK (fraud_risk_score BETWEEN 1 AND 5),
    fraud_risk_flags        JSONB DEFAULT '[]',
    -- Credit risk (Sales – Module 3, Phase 3)
    credit_risk_score       SMALLINT CHECK (credit_risk_score BETWEEN 1 AND 5),

    -- === Source Document ===
    source_message_id       UUID REFERENCES inbox_messages(id) ON DELETE SET NULL,
    original_file_url       TEXT,
    original_file_bucket    VARCHAR(100),

    -- === Dispatch Tracking (Sales – Module 3, Phase 1) ===
    dispatch_channel        VARCHAR(50),
    dispatched_at           TIMESTAMPTZ,
    delivered_at            TIMESTAMPTZ,
    read_at                 TIMESTAMPTZ,

    -- === Reconciliation (Modules 2 & 3, Phase 2/4) ===
    reconciled_at           TIMESTAMPTZ,
    reconciled_transaction_id UUID,             -- FK added after bank_transactions
    reconciliation_confidence DECIMAL(5,4),

    -- === Payment Execution (Module 2, Phase 4) ===
    payment_method          payment_method,
    payment_reference       VARCHAR(255),
    payment_executed_at     TIMESTAMPTZ,
    payment_gateway_id      VARCHAR(255),

    -- === GDrive Archive (Module 2, Phase 5) ===
    gdrive_file_id          VARCHAR(255),
    gdrive_saved_at         TIMESTAMPTZ,

    -- === Gmail Sync (Module 8) ===
    gmail_thread_id         VARCHAR(255),
    gmail_label             VARCHAR(100),

    -- === Dunning Engine (Sales – Module 3, Phase 3) ===
    dunning_enabled         BOOLEAN DEFAULT TRUE,
    dunning_last_sent_at    TIMESTAMPTZ,
    dunning_count           INTEGER DEFAULT 0,
    dunning_next_at         TIMESTAMPTZ,

    -- === Approval ===
    approved_by             UUID REFERENCES auth.users(id),
    approved_at             TIMESTAMPTZ,

    notes                   TEXT,
    metadata                JSONB DEFAULT '{}',
    created_by              UUID REFERENCES auth.users(id),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE invoices IS 'Unified invoice ledger. direction=purchase → AP (Module 2), direction=sale → AR (Module 3).';

-- Back-link: inbox_messages → invoices
ALTER TABLE inbox_messages
    ADD CONSTRAINT fk_inbox_linked_invoice
    FOREIGN KEY (linked_invoice_id) REFERENCES invoices(id) ON DELETE SET NULL;

-- Invoice line items
CREATE TABLE invoice_line_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id      UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    position        INTEGER NOT NULL DEFAULT 0,
    description     TEXT NOT NULL,
    quantity        DECIMAL(12,4) DEFAULT 1,
    unit_price      DECIMAL(15,2) NOT NULL DEFAULT 0,
    tax_rate        DECIMAL(5,2) DEFAULT 0,
    tax_amount      DECIMAL(15,2) DEFAULT 0,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    line_total      DECIMAL(15,2) NOT NULL DEFAULT 0,
    category        VARCHAR(100),
    account_code    VARCHAR(50),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE invoice_line_items IS 'Individual line items on an invoice. Supports categorization via account_code (chart of accounts).';

-- Invoice status change history
CREATE TABLE invoice_status_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id      UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    old_status      invoice_status,
    new_status      invoice_status NOT NULL,
    changed_by      UUID REFERENCES auth.users(id),
    change_reason   TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE invoice_status_history IS 'Immutable audit trail for every invoice status transition.';

-- Invoice dispatch / communication log
CREATE TABLE invoice_communications (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id          UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    channel             comm_channel NOT NULL,
    recipient           VARCHAR(255) NOT NULL,
    subject             TEXT,
    body_preview        TEXT,
    status              comm_status DEFAULT 'queued',
    sent_at             TIMESTAMPTZ,
    delivered_at        TIMESTAMPTZ,
    read_at             TIMESTAMPTZ,
    error_message       TEXT,
    external_message_id VARCHAR(500),
    -- Dunning
    is_dunning          BOOLEAN DEFAULT FALSE,
    dunning_level       INTEGER,
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE invoice_communications IS 'Outbound message log for invoice dispatch and dunning notices across all channels.';

-- Dunning rules configuration (Sales – Module 3)
CREATE TABLE dunning_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    days_after_due  INTEGER NOT NULL,
    channel         comm_channel NOT NULL DEFAULT 'email',
    subject_template TEXT,
    body_template   TEXT,
    dunning_level   INTEGER NOT NULL DEFAULT 1,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE dunning_rules IS 'Configurable escalation rules for automated payment reminders (Module 3 dunning engine).';


-- ============================================================================
-- SECTION 6: BANKING HUB (Module 4)
-- ============================================================================

CREATE TABLE bank_accounts (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id            UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id              UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    connection_id           UUID REFERENCES bank_connections(id) ON DELETE SET NULL,
    external_account_id     VARCHAR(255),
    account_name            VARCHAR(255) NOT NULL,
    institution_name        VARCHAR(255),
    institution_logo_url    TEXT,
    account_type            account_type DEFAULT 'checking',
    account_number_masked   VARCHAR(20),
    currency                VARCHAR(3) DEFAULT 'USD',
    current_balance         DECIMAL(15,2) DEFAULT 0,
    available_balance       DECIMAL(15,2) DEFAULT 0,
    balance_updated_at      TIMESTAMPTZ,
    status                  account_status DEFAULT 'active',
    is_internal             BOOLEAN DEFAULT TRUE,
    metadata                JSONB DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE bank_accounts IS 'Individual bank accounts synced via Open Banking. Balances refreshed by AIS polling.';

CREATE TABLE bank_transactions (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id                UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id                  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    account_id                  UUID NOT NULL REFERENCES bank_accounts(id) ON DELETE CASCADE,
    external_transaction_id     VARCHAR(255),
    -- Core fields
    transaction_date            DATE NOT NULL,
    posted_date                 DATE,
    value_date                  DATE,
    description                 TEXT,
    reference                   VARCHAR(255),
    transaction_type            transaction_type NOT NULL,
    amount                      DECIMAL(15,2) NOT NULL,
    currency                    VARCHAR(3) DEFAULT 'USD',
    running_balance             DECIMAL(15,2),
    -- Auto-categorization (Phase 3)
    category                    transaction_category DEFAULT 'uncategorized',
    category_confidence         DECIMAL(5,4),
    -- Reconciliation (Phase 3 "Matcher" Agent)
    reconciliation_status       reconciliation_status DEFAULT 'pending',
    linked_invoice_id           UUID REFERENCES invoices(id) ON DELETE SET NULL,
    linked_transfer_account_id  UUID REFERENCES bank_accounts(id),
    match_confidence            DECIMAL(5,4),
    matched_at                  TIMESTAMPTZ,
    matched_by                  VARCHAR(50),    -- 'ai_agent', 'manual', 'rule'
    -- Gap Analysis routing (Phase 4)
    accountant_task_id          UUID,           -- FK added after accountant_tasks
    --
    counterparty_name           VARCHAR(255),
    counterparty_account        VARCHAR(100),
    notes                       TEXT,
    metadata                    JSONB DEFAULT '{}',
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE bank_transactions IS 'Bank statement lines synced via Open Banking. The AI "Matcher" agent reconciles these against invoices.';

-- Back-link: invoices.reconciled_transaction_id → bank_transactions
ALTER TABLE invoices
    ADD CONSTRAINT fk_invoice_reconciled_transaction
    FOREIGN KEY (reconciled_transaction_id) REFERENCES bank_transactions(id) ON DELETE SET NULL;

-- Payment execution records
CREATE TABLE payment_transactions (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id                UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id                  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    invoice_id                  UUID REFERENCES invoices(id) ON DELETE SET NULL,
    gateway                     VARCHAR(100),
    gateway_transaction_id      VARCHAR(255),
    gateway_status              VARCHAR(50),
    direction                   VARCHAR(10) NOT NULL CHECK (direction IN ('outbound','inbound')),
    amount                      DECIMAL(15,2) NOT NULL,
    currency                    VARCHAR(3) DEFAULT 'USD',
    fee_amount                  DECIMAL(15,2) DEFAULT 0,
    payment_method              payment_method,
    initiated_by                UUID REFERENCES auth.users(id),
    initiated_at                TIMESTAMPTZ DEFAULT NOW(),
    completed_at                TIMESTAMPTZ,
    failed_at                   TIMESTAMPTZ,
    failure_reason              TEXT,
    linked_bank_transaction_id  UUID REFERENCES bank_transactions(id) ON DELETE SET NULL,
    metadata                    JSONB DEFAULT '{}',
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE payment_transactions IS 'Records of payment initiations via PIS/payment-gateway. Links invoice → bank_transaction once settled.';


-- ============================================================================
-- SECTION 7: ACCOUNTANT HUB (Module 5)
-- ============================================================================

CREATE TABLE accountant_tasks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id          UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    task_type           task_type NOT NULL,
    title               VARCHAR(500) NOT NULL,
    description         TEXT,
    status              task_status DEFAULT 'open',
    priority            task_priority DEFAULT 'medium',
    -- Linked entities
    linked_transaction_id UUID REFERENCES bank_transactions(id) ON DELETE SET NULL,
    linked_invoice_id   UUID REFERENCES invoices(id) ON DELETE SET NULL,
    linked_amount       DECIMAL(15,2),
    linked_currency     VARCHAR(3),
    -- Assignment
    assigned_to         UUID REFERENCES auth.users(id),
    created_by_system   BOOLEAN DEFAULT FALSE,
    -- Resolution
    resolved_at         TIMESTAMPTZ,
    resolved_by         UUID REFERENCES auth.users(id),
    resolution_notes    TEXT,
    --
    due_date            DATE,
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE accountant_tasks IS 'Task queue for the CPA / Accountant Hub. Auto-generated by Missing Invoice pipeline or manually by CPA.';

-- Back-link: bank_transactions.accountant_task_id → accountant_tasks
ALTER TABLE bank_transactions
    ADD CONSTRAINT fk_txn_accountant_task
    FOREIGN KEY (accountant_task_id) REFERENCES accountant_tasks(id) ON DELETE SET NULL;

-- Documents uploaded against tasks
CREATE TABLE task_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID NOT NULL REFERENCES accountant_tasks(id) ON DELETE CASCADE,
    uploaded_by     UUID REFERENCES auth.users(id),
    filename        VARCHAR(500) NOT NULL,
    mime_type       VARCHAR(100),
    file_size_bytes BIGINT,
    storage_path    TEXT,
    storage_bucket  VARCHAR(100) DEFAULT 'task-documents',
    ocr_processed   BOOLEAN DEFAULT FALSE,
    linked_invoice_id UUID REFERENCES invoices(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE task_documents IS 'Files uploaded to resolve accountant tasks. OCR pipeline reuses the Purchase Invoice extraction flow.';

-- Compliance deadlines
CREATE TABLE compliance_deadlines (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    deadline_type   VARCHAR(100),
    due_date        DATE NOT NULL,
    warning_days    INTEGER DEFAULT 14,
    status          deadline_status DEFAULT 'upcoming',
    recurrence      deadline_recurrence DEFAULT 'one_time',
    filed_at        TIMESTAMPTZ,
    filed_by        UUID REFERENCES auth.users(id),
    filing_reference VARCHAR(255),
    linked_task_id  UUID REFERENCES accountant_tasks(id) ON DELETE SET NULL,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE compliance_deadlines IS 'Statutory calendar for tax/filing deadlines. Auto-transitions: UPCOMING → DUE_SOON → OVERDUE.';

-- Real-time accountant ↔ client chat
CREATE TABLE chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    thread_type     VARCHAR(50),    -- 'task', 'invoice', 'transaction', 'general'
    thread_ref_id   UUID,
    sender_id       UUID NOT NULL REFERENCES auth.users(id),
    message_text    TEXT NOT NULL,
    has_attachments BOOLEAN DEFAULT FALSE,
    is_read         BOOLEAN DEFAULT FALSE,
    read_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE chat_messages IS 'WebSocket-driven contextual messaging between client and CPA within the financial ecosystem.';

CREATE TABLE chat_attachments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id      UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    filename        VARCHAR(500) NOT NULL,
    mime_type       VARCHAR(100),
    file_size_bytes BIGINT,
    storage_path    TEXT,
    storage_bucket  VARCHAR(100) DEFAULT 'chat-attachments',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================================
-- SECTION 8: GMAIL ADD-ON & SYNC (Module 8)
-- ============================================================================

CREATE TABLE gmail_label_mappings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    channel_id      UUID NOT NULL REFERENCES connected_channels(id) ON DELETE CASCADE,
    invoice_status  invoice_status NOT NULL,
    gmail_label_name VARCHAR(255) NOT NULL,
    gmail_label_id  VARCHAR(255),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(channel_id, invoice_status)
);
COMMENT ON TABLE gmail_label_mappings IS 'Maps SoloHub invoice statuses to Gmail USER labels for bi-directional sync.';

CREATE TABLE gmail_sync_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id      UUID NOT NULL REFERENCES connected_channels(id) ON DELETE CASCADE,
    direction       VARCHAR(10) NOT NULL CHECK (direction IN ('inbound','outbound')),
    gmail_thread_id VARCHAR(255),
    gmail_history_id VARCHAR(255),
    action          VARCHAR(100),
    old_label       VARCHAR(255),
    new_label       VARCHAR(255),
    linked_invoice_id UUID REFERENCES invoices(id) ON DELETE SET NULL,
    sync_status     VARCHAR(20) DEFAULT 'pending'
                    CHECK (sync_status IN ('pending','synced','failed')),
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE gmail_sync_log IS 'Audit log for every Gmail ↔ SoloHub label synchronization event.';


-- ============================================================================
-- SECTION 9: DASHBOARD KPI CACHE (Module 7)
-- ============================================================================

CREATE TABLE dashboard_kpi_cache (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,   -- NULL = consolidated
    metric_name     VARCHAR(100) NOT NULL,
    metric_value    DECIMAL(15,2),
    metric_metadata JSONB DEFAULT '{}',
    period_start    DATE,
    period_end      DATE,
    calculated_at   TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,
    UNIQUE(workspace_id, company_id, metric_name, period_start)
);
COMMENT ON TABLE dashboard_kpi_cache IS 'Read-optimized cache for dashboard KPIs. Invalidated on invoice/transaction state changes.';


-- ============================================================================
-- SECTION 10: NOTIFICATIONS & AUDIT
-- ============================================================================

CREATE TABLE notifications (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    notification_type   notification_type NOT NULL,
    title               VARCHAR(500) NOT NULL,
    body                TEXT,
    entity_type         VARCHAR(100),
    entity_id           UUID,
    is_read             BOOLEAN DEFAULT FALSE,
    read_at             TIMESTAMPTZ,
    action_url          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE notifications IS 'In-app notification feed. Deep links route users to the relevant resolution workflow.';

CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES auth.users(id),
    action          VARCHAR(100) NOT NULL,
    entity_type     VARCHAR(100) NOT NULL,
    entity_id       UUID,
    old_data        JSONB,
    new_data        JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE audit_log IS 'Global immutable audit trail for all data mutations across every module.';


-- ============================================================================
-- SECTION 11: INDEXES
-- ============================================================================

-- Profiles
CREATE INDEX idx_profiles_full_name ON profiles USING GIN (full_name gin_trgm_ops);

-- Workspaces
CREATE INDEX idx_workspaces_owner ON workspaces(owner_id);

-- Companies
CREATE INDEX idx_companies_workspace ON companies(workspace_id);
CREATE INDEX idx_companies_default ON companies(workspace_id) WHERE is_default = TRUE;

-- Workspace members
CREATE INDEX idx_members_workspace ON workspace_members(workspace_id);
CREATE INDEX idx_members_user ON workspace_members(user_id);
CREATE INDEX idx_members_status ON workspace_members(workspace_id, status);

-- Connected channels
CREATE INDEX idx_channels_workspace ON connected_channels(workspace_id);
CREATE INDEX idx_channels_type ON connected_channels(workspace_id, channel_type);

-- Bank connections
CREATE INDEX idx_bank_conn_company ON bank_connections(company_id);

-- Contacts
CREATE INDEX idx_contacts_company ON contacts(company_id);
CREATE INDEX idx_contacts_type ON contacts(workspace_id, contact_type);
CREATE INDEX idx_contacts_name ON contacts USING GIN (name gin_trgm_ops);
CREATE INDEX idx_contacts_email ON contacts(email);

-- Inbox messages
CREATE INDEX idx_inbox_company ON inbox_messages(company_id);
CREATE INDEX idx_inbox_source ON inbox_messages(workspace_id, source);
CREATE INDEX idx_inbox_classification ON inbox_messages(workspace_id, classification);
CREATE INDEX idx_inbox_processing ON inbox_messages(workspace_id, processing_status);
CREATE INDEX idx_inbox_received ON inbox_messages(received_at DESC);
CREATE INDEX idx_inbox_external_msg ON inbox_messages(external_message_id);
CREATE INDEX idx_inbox_sender ON inbox_messages(sender_email);

-- Inbox attachments
CREATE INDEX idx_attachments_message ON inbox_attachments(message_id);
CREATE INDEX idx_attachments_hash ON inbox_attachments(content_hash);
CREATE INDEX idx_attachments_ocr ON inbox_attachments(ocr_status);

-- Invoices (critical – most queried table)
CREATE INDEX idx_invoices_company ON invoices(company_id);
CREATE INDEX idx_invoices_direction ON invoices(workspace_id, direction);
CREATE INDEX idx_invoices_status ON invoices(workspace_id, direction, status);
CREATE INDEX idx_invoices_contact ON invoices(contact_id);
CREATE INDEX idx_invoices_due_date ON invoices(due_date) WHERE status NOT IN ('paid','voided','cancelled');
CREATE INDEX idx_invoices_overdue ON invoices(due_date) WHERE status = 'overdue';
CREATE INDEX idx_invoices_number ON invoices(workspace_id, invoice_number);
CREATE INDEX idx_invoices_gmail_thread ON invoices(gmail_thread_id) WHERE gmail_thread_id IS NOT NULL;
CREATE INDEX idx_invoices_reconciled ON invoices(reconciled_transaction_id) WHERE reconciled_transaction_id IS NOT NULL;
CREATE INDEX idx_invoices_created ON invoices(created_at DESC);
CREATE INDEX idx_invoices_dunning ON invoices(dunning_next_at)
    WHERE direction = 'sale' AND status IN ('pending','sent','delivered','overdue') AND dunning_enabled = TRUE;

-- Invoice line items
CREATE INDEX idx_line_items_invoice ON invoice_line_items(invoice_id);

-- Invoice status history
CREATE INDEX idx_status_history_invoice ON invoice_status_history(invoice_id, created_at DESC);

-- Invoice communications
CREATE INDEX idx_comms_invoice ON invoice_communications(invoice_id);
CREATE INDEX idx_comms_dunning ON invoice_communications(invoice_id) WHERE is_dunning = TRUE;

-- Bank accounts
CREATE INDEX idx_bank_acct_company ON bank_accounts(company_id);
CREATE INDEX idx_bank_acct_connection ON bank_accounts(connection_id);

-- Bank transactions
CREATE INDEX idx_bank_txn_account ON bank_transactions(account_id);
CREATE INDEX idx_bank_txn_company ON bank_transactions(company_id);
CREATE INDEX idx_bank_txn_date ON bank_transactions(transaction_date DESC);
CREATE INDEX idx_bank_txn_recon ON bank_transactions(workspace_id, reconciliation_status);
CREATE INDEX idx_bank_txn_missing ON bank_transactions(workspace_id)
    WHERE reconciliation_status = 'missing_invoice';
CREATE INDEX idx_bank_txn_unmatched ON bank_transactions(workspace_id)
    WHERE reconciliation_status IN ('unmatched','pending');
CREATE INDEX idx_bank_txn_external ON bank_transactions(external_transaction_id);
CREATE INDEX idx_bank_txn_counterparty ON bank_transactions USING GIN (counterparty_name gin_trgm_ops);

-- Payment transactions
CREATE INDEX idx_pay_txn_invoice ON payment_transactions(invoice_id);
CREATE INDEX idx_pay_txn_company ON payment_transactions(company_id);

-- Accountant tasks
CREATE INDEX idx_tasks_company ON accountant_tasks(company_id);
CREATE INDEX idx_tasks_status ON accountant_tasks(workspace_id, status);
CREATE INDEX idx_tasks_assigned ON accountant_tasks(assigned_to, status);
CREATE INDEX idx_tasks_type ON accountant_tasks(workspace_id, task_type);
CREATE INDEX idx_tasks_due ON accountant_tasks(due_date) WHERE status NOT IN ('resolved','cancelled');

-- Compliance deadlines
CREATE INDEX idx_deadlines_company ON compliance_deadlines(company_id);
CREATE INDEX idx_deadlines_due ON compliance_deadlines(due_date) WHERE status NOT IN ('completed','filed');
CREATE INDEX idx_deadlines_status ON compliance_deadlines(workspace_id, status);

-- Chat
CREATE INDEX idx_chat_workspace ON chat_messages(workspace_id, created_at DESC);
CREATE INDEX idx_chat_thread ON chat_messages(thread_type, thread_ref_id, created_at);
CREATE INDEX idx_chat_unread ON chat_messages(workspace_id) WHERE is_read = FALSE;

-- Gmail sync
CREATE INDEX idx_gmail_sync_channel ON gmail_sync_log(channel_id, created_at DESC);
CREATE INDEX idx_gmail_sync_thread ON gmail_sync_log(gmail_thread_id);

-- Dashboard cache
CREATE INDEX idx_kpi_cache_lookup ON dashboard_kpi_cache(workspace_id, company_id, metric_name);

-- Notifications
CREATE INDEX idx_notifications_user ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_unread ON notifications(user_id) WHERE is_read = FALSE;

-- Audit log
CREATE INDEX idx_audit_workspace ON audit_log(workspace_id, created_at DESC);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);


-- ============================================================================
-- SECTION 12: TRIGGERS & FUNCTIONS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN
        SELECT table_name FROM information_schema.columns
        WHERE column_name = 'updated_at'
          AND table_schema = 'public'
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%I_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at()',
            t, t
        );
    END LOOP;
END;
$$;

-- Auto-create default company on workspace creation
CREATE OR REPLACE FUNCTION create_default_company()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO companies (workspace_id, legal_name, is_default, is_individual, base_currency)
    VALUES (NEW.id, 'My Business', TRUE, TRUE, NEW.base_currency);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_workspace_default_company
    AFTER INSERT ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION create_default_company();

-- Auto-add owner as workspace member
CREATE OR REPLACE FUNCTION add_owner_as_member()
RETURNS TRIGGER AS $$
DECLARE
    owner_email TEXT;
BEGIN
    SELECT email INTO owner_email FROM auth.users WHERE id = NEW.owner_id;
    INSERT INTO workspace_members (workspace_id, user_id, email, role, status, joined_at)
    VALUES (NEW.id, NEW.owner_id, COALESCE(owner_email, ''), 'owner', 'active', NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_workspace_add_owner
    AFTER INSERT ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION add_owner_as_member();

-- Log invoice status transitions
CREATE OR REPLACE FUNCTION log_invoice_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO invoice_status_history (invoice_id, old_status, new_status)
        VALUES (NEW.id, OLD.status, NEW.status);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_invoice_status_change
    AFTER UPDATE OF status ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION log_invoice_status_change();

-- Auto-update compliance deadline status based on date proximity
CREATE OR REPLACE FUNCTION update_deadline_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status NOT IN ('completed', 'filed') THEN
        IF NEW.due_date < CURRENT_DATE THEN
            NEW.status = 'overdue';
        ELSIF NEW.due_date <= CURRENT_DATE + (NEW.warning_days || ' days')::INTERVAL THEN
            NEW.status = 'due_soon';
        ELSE
            NEW.status = 'upcoming';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_deadline_status
    BEFORE INSERT OR UPDATE ON compliance_deadlines
    FOR EACH ROW
    EXECUTE FUNCTION update_deadline_status();

-- Auto-generate accountant task when bank transaction flagged as missing_invoice
CREATE OR REPLACE FUNCTION route_missing_invoice_task()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.reconciliation_status = 'missing_invoice'
       AND (OLD.reconciliation_status IS NULL OR OLD.reconciliation_status != 'missing_invoice')
       AND NEW.accountant_task_id IS NULL THEN

        INSERT INTO accountant_tasks (
            workspace_id, company_id, task_type, title, description,
            linked_transaction_id, linked_amount, linked_currency,
            status, priority, created_by_system
        ) VALUES (
            NEW.workspace_id, NEW.company_id, 'missing_invoice',
            'Missing Invoice: ' || COALESCE(NEW.counterparty_name, NEW.description, 'Unknown'),
            'Bank transaction on ' || NEW.transaction_date::TEXT || ' for ' || NEW.currency || ' ' || ABS(NEW.amount)::TEXT || ' has no linked invoice.',
            NEW.id, ABS(NEW.amount), NEW.currency,
            'open', 'high', TRUE
        )
        RETURNING id INTO NEW.accountant_task_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_missing_invoice_task
    BEFORE INSERT OR UPDATE OF reconciliation_status ON bank_transactions
    FOR EACH ROW
    EXECUTE FUNCTION route_missing_invoice_task();

-- Track contact field changes for fraud detection
CREATE OR REPLACE FUNCTION track_contact_changes()
RETURNS TRIGGER AS $$
DECLARE
    fields TEXT[] := ARRAY['email', 'bank_name', 'bank_account_number_encrypted',
                           'bank_routing_number_encrypted', 'bank_iban_encrypted',
                           'bank_swift', 'name', 'legal_name'];
    f TEXT;
    old_val TEXT;
    new_val TEXT;
BEGIN
    FOREACH f IN ARRAY fields LOOP
        EXECUTE format('SELECT ($1).%I::TEXT, ($2).%I::TEXT', f, f)
            INTO old_val, new_val
            USING OLD, NEW;
        IF old_val IS DISTINCT FROM new_val THEN
            INSERT INTO contact_audit_log (contact_id, field_name, old_value, new_value)
            VALUES (NEW.id, f, old_val, new_val);
        END IF;
    END LOOP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_contact_audit
    AFTER UPDATE ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION track_contact_changes();


-- ============================================================================
-- SECTION 13: VIEWS (Dashboard convenience)
-- ============================================================================

-- Open purchase invoices (AP)
CREATE OR REPLACE VIEW v_open_purchase_invoices AS
SELECT
    i.*,
    c.name AS vendor_name,
    c.credit_risk_score AS vendor_risk,
    CURRENT_DATE - i.due_date AS days_overdue
FROM invoices i
LEFT JOIN contacts c ON i.contact_id = c.id
WHERE i.direction = 'purchase'
  AND i.status NOT IN ('paid', 'voided', 'cancelled');

-- Open sales invoices (AR)
CREATE OR REPLACE VIEW v_open_sales_invoices AS
SELECT
    i.*,
    c.name AS customer_name,
    c.credit_risk_score AS customer_risk,
    CURRENT_DATE - i.due_date AS days_overdue
FROM invoices i
LEFT JOIN contacts c ON i.contact_id = c.id
WHERE i.direction = 'sale'
  AND i.status NOT IN ('paid', 'voided', 'cancelled');

-- Unreconciled bank transactions
CREATE OR REPLACE VIEW v_unreconciled_transactions AS
SELECT
    bt.*,
    ba.account_name,
    ba.institution_name
FROM bank_transactions bt
JOIN bank_accounts ba ON bt.account_id = ba.id
WHERE bt.reconciliation_status IN ('pending', 'unmatched', 'missing_invoice');

-- Net cash position per company
CREATE OR REPLACE VIEW v_net_cash_position AS
SELECT
    ba.workspace_id,
    ba.company_id,
    SUM(ba.available_balance) AS net_cash_balance,
    COUNT(*) AS account_count,
    MAX(ba.balance_updated_at) AS last_updated
FROM bank_accounts ba
WHERE ba.status = 'active'
GROUP BY ba.workspace_id, ba.company_id;

-- Active compliance deadlines
CREATE OR REPLACE VIEW v_active_deadlines AS
SELECT
    cd.*,
    CURRENT_DATE - cd.due_date AS days_until_due,
    CASE
        WHEN cd.due_date < CURRENT_DATE THEN 'overdue'
        WHEN cd.due_date <= CURRENT_DATE + (cd.warning_days || ' days')::INTERVAL THEN 'due_soon'
        ELSE 'upcoming'
    END AS computed_status
FROM compliance_deadlines cd
WHERE cd.status NOT IN ('completed', 'filed');

-- Accountant hub pending tasks summary
CREATE OR REPLACE VIEW v_pending_accountant_tasks AS
SELECT
    at.workspace_id,
    at.company_id,
    COUNT(*) FILTER (WHERE at.status = 'open') AS open_count,
    COUNT(*) FILTER (WHERE at.status = 'in_progress') AS in_progress_count,
    COUNT(*) FILTER (WHERE at.status IN ('waiting_client', 'waiting_cpa')) AS waiting_count,
    COUNT(*) AS total_pending,
    MIN(at.due_date) FILTER (WHERE at.status != 'resolved') AS next_deadline
FROM accountant_tasks at
WHERE at.status NOT IN ('resolved', 'cancelled')
GROUP BY at.workspace_id, at.company_id;


-- ============================================================================
-- SECTION 14: SUPABASE STORAGE BUCKETS
-- ============================================================================
-- Run these via Supabase Dashboard or Management API:
--
-- INSERT INTO storage.buckets (id, name, public) VALUES
--   ('inbox-attachments',  'inbox-attachments',  FALSE),
--   ('invoice-documents',  'invoice-documents',  FALSE),
--   ('task-documents',     'task-documents',      FALSE),
--   ('chat-attachments',   'chat-attachments',    FALSE),
--   ('company-logos',      'company-logos',       TRUE),
--   ('user-avatars',       'user-avatars',        TRUE);


-- ============================================================================
-- SECTION 15: SUPABASE REALTIME SUBSCRIPTIONS
-- ============================================================================
-- Enable realtime for chat and notifications (run via Supabase Dashboard):
--
-- ALTER PUBLICATION supabase_realtime ADD TABLE chat_messages;
-- ALTER PUBLICATION supabase_realtime ADD TABLE notifications;
-- ALTER PUBLICATION supabase_realtime ADD TABLE accountant_tasks;
-- ALTER PUBLICATION supabase_realtime ADD TABLE bank_transactions;
-- ALTER PUBLICATION supabase_realtime ADD TABLE invoices;
