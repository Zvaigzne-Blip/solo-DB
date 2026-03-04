# SoloHub Database Schema

## Overview

Complete database schema for **SoloHub — The Autonomous Business Engine for Solopreneurs**, designed for **Supabase** (PostgreSQL 15+) with **Django** ORM models.

## File Structure

```
database/
├── supabase_schema.sql    # Full DDL: tables, indexes, triggers, views
├── rls_policies.sql       # Supabase Row-Level Security policies
└── seed_data.sql          # RBAC permission matrix & default config

solohub/
└── models/
    ├── __init__.py        # Re-exports all models
    ├── core.py            # Workspace, Company, Profile, IAM
    ├── integrations.py    # Channels, Banking, Tax, GDrive connections
    ├── contacts.py        # Vendors & Customers + audit log
    ├── inbox.py           # Smart Multichannel Inbox
    ├── invoices.py        # Purchase (AP) & Sales (AR) invoices
    ├── banking.py         # Bank accounts, transactions, payments
    ├── accountant.py      # Tasks, compliance, chat
    └── gmail_dashboard.py # Gmail sync, KPI cache, notifications
```

## Module → Table Mapping

| Module | Tables |
|--------|--------|
| **6. Settings & Workspace** | `workspaces`, `companies`, `profiles`, `workspace_members`, `role_permissions`, `workspace_preferences`, `connected_channels`, `bank_connections`, `tax_authority_integrations`, `gdrive_connections` |
| **1. Smart Inbox** | `inbox_messages`, `inbox_attachments` |
| **2. Purchase Invoices (AP)** | `invoices` (direction=purchase), `invoice_line_items`, `invoice_status_history`, `invoice_communications` |
| **3. Sales Invoices (AR)** | `invoices` (direction=sale), `invoice_line_items`, `invoice_status_history`, `invoice_communications`, `dunning_rules` |
| **Shared** | `contacts`, `contact_audit_log` |
| **4. Banking Hub** | `bank_accounts`, `bank_transactions`, `payment_transactions` |
| **5. Accountant Hub** | `accountant_tasks`, `task_documents`, `compliance_deadlines`, `chat_messages`, `chat_attachments` |
| **7. Dashboard** | `dashboard_kpi_cache` |
| **8. Gmail Add-on** | `gmail_label_mappings`, `gmail_sync_log` |
| **Cross-cutting** | `notifications`, `audit_log` |

## Schema Diagram (Entity Relationships)

```
auth.users (Supabase)
    │
    ├─ 1:1 ─── profiles
    │
    └─ 1:N ─── workspaces (owner_id)
                    │
                    ├── companies (multi-entity)
                    │       ├── bank_connections
                    │       ├── tax_authority_integrations
                    │       ├── gdrive_connections
                    │       ├── contacts ──── contact_audit_log
                    │       ├── bank_accounts ──── bank_transactions
                    │       ├── invoices ──── invoice_line_items
                    │       │     ├── invoice_status_history
                    │       │     └── invoice_communications
                    │       ├── accountant_tasks ──── task_documents
                    │       ├── compliance_deadlines
                    │       └── chat_messages ──── chat_attachments
                    │
                    ├── workspace_members (RBAC)
                    ├── workspace_preferences
                    ├── connected_channels ──── gmail_label_mappings
                    │                     └── gmail_sync_log
                    ├── dunning_rules
                    ├── dashboard_kpi_cache
                    └── notifications
```

## Key Design Decisions

### 1. Multi-Tenant Isolation
- Every data table has `workspace_id` for tenant scoping
- `company_id` provides entity-level data isolation within a workspace
- RLS policies enforce isolation at the database level

### 2. Unified Invoice Table
- Single `invoices` table with `direction` field (`purchase` / `sale`)
- Avoids schema duplication between AP and AR
- Different fields activated by direction (fraud_risk for AP, dunning for AR)

### 3. Reconciliation Flow
```
bank_transactions.linked_invoice_id ←→ invoices.reconciled_transaction_id
```
The AI "Matcher" agent writes both sides when confidence threshold is met.

### 4. Missing Invoice Pipeline
```
bank_transaction (missing_invoice) → TRIGGER → accountant_tasks (auto-created)
task_documents (upload) → OCR → invoices (created) → bank_transaction (resolved)
```

### 5. Gmail Bi-Directional Sync
```
Invoice status change → gmail_label_mappings lookup → Gmail API threads.modify
Gmail label change → gmail_sync_log → SoloHub status update
```

### 6. Fraud Risk Assessment (Purchase Invoices)
Flags checked against `contact_audit_log`:
1. New unrecognized vendor (no prior invoices)
2. Vendor email recently changed
3. Source domain changed
4. Bank/routing details altered
5. Amount deviates from historical average

### 7. Credit Risk & Dunning (Sales Invoices)
- `contacts.credit_risk_score` (1-5) based on payment behavior
- `dunning_rules` table defines escalation schedule
- `invoice_communications` tracks all outbound dunning notices

## Deployment Steps

### 1. Run the schema migration
```sql
-- In Supabase SQL Editor (or via psql):
\i database/supabase_schema.sql
```

### 2. Apply RLS policies
```sql
\i database/rls_policies.sql
```

### 3. Seed default data
```sql
\i database/seed_data.sql
```

### 4. Create storage buckets
Via Supabase Dashboard → Storage:
- `inbox-attachments` (private)
- `invoice-documents` (private)
- `task-documents` (private)
- `chat-attachments` (private)
- `company-logos` (public)
- `user-avatars` (public)

### 5. Enable Realtime
Via Supabase Dashboard → Database → Replication:
- `chat_messages`
- `notifications`
- `accountant_tasks`
- `bank_transactions`
- `invoices`

### 6. Django configuration
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': '<your-supabase-db-password>',
        'HOST': '<your-project>.supabase.co',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

INSTALLED_APPS = [
    ...
    'solohub',
]
```

Since the schema is managed via raw SQL migrations on Supabase, set Django to **not** manage these tables:
```python
# In each model's Meta:
class Meta:
    managed = False  # Add this if Supabase owns the schema
    db_table = 'table_name'
```

## Table Count Summary

| Category | Count |
|----------|-------|
| Core / IAM | 6 |
| Integrations | 4 |
| Contacts | 2 |
| Inbox | 2 |
| Invoices | 5 |
| Banking | 3 |
| Accountant | 5 |
| Gmail | 2 |
| Dashboard | 1 |
| Cross-cutting | 2 |
| **Total** | **32 tables** |

## Custom PostgreSQL Types (Enums)

The schema defines 22 enum types for type safety:
`user_role`, `member_status`, `channel_type`, `integration_status`, `bank_connection_status`, `tax_integration_status`, `contact_type`, `message_source`, `message_classification`, `message_processing_status`, `invoice_direction`, `invoice_status`, `invoice_source`, `payment_method`, `comm_channel`, `comm_status`, `account_type`, `account_status`, `transaction_type`, `transaction_category`, `reconciliation_status`, `task_type`, `task_status`, `task_priority`, `deadline_status`, `deadline_recurrence`, `notification_type`
