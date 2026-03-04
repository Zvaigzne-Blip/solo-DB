-- ============================================================================
-- SoloHub Seed Data — RBAC Permission Matrix & Default Label Mappings
-- ============================================================================

-- ============================================================================
-- RBAC: Role-Permission Matrix
-- ============================================================================
-- Resources: company_settings, integrations, tax_integrations,
--            bank_connections, bank_accounts, contacts, invoices,
--            accountant_tasks, compliance_deadlines, chat
-- Actions:   create, read, update, delete, approve, pay

INSERT INTO role_permissions (role, resource, action, is_allowed) VALUES
-- ── OWNER: Full access ──
('owner', 'company_settings',     'create',  TRUE),
('owner', 'company_settings',     'read',    TRUE),
('owner', 'company_settings',     'update',  TRUE),
('owner', 'company_settings',     'delete',  TRUE),
('owner', 'integrations',         'create',  TRUE),
('owner', 'integrations',         'read',    TRUE),
('owner', 'integrations',         'update',  TRUE),
('owner', 'integrations',         'delete',  TRUE),
('owner', 'tax_integrations',     'create',  TRUE),
('owner', 'tax_integrations',     'read',    TRUE),
('owner', 'tax_integrations',     'update',  TRUE),
('owner', 'tax_integrations',     'delete',  TRUE),
('owner', 'bank_connections',     'create',  TRUE),
('owner', 'bank_connections',     'read',    TRUE),
('owner', 'bank_connections',     'update',  TRUE),
('owner', 'bank_connections',     'delete',  TRUE),
('owner', 'bank_accounts',        'read',    TRUE),
('owner', 'bank_accounts',        'update',  TRUE),
('owner', 'contacts',             'create',  TRUE),
('owner', 'contacts',             'read',    TRUE),
('owner', 'contacts',             'update',  TRUE),
('owner', 'contacts',             'delete',  TRUE),
('owner', 'invoices',             'create',  TRUE),
('owner', 'invoices',             'read',    TRUE),
('owner', 'invoices',             'update',  TRUE),
('owner', 'invoices',             'delete',  TRUE),
('owner', 'invoices',             'approve', TRUE),
('owner', 'invoices',             'pay',     TRUE),
('owner', 'accountant_tasks',     'create',  TRUE),
('owner', 'accountant_tasks',     'read',    TRUE),
('owner', 'accountant_tasks',     'update',  TRUE),
('owner', 'compliance_deadlines', 'create',  TRUE),
('owner', 'compliance_deadlines', 'read',    TRUE),
('owner', 'compliance_deadlines', 'update',  TRUE),
('owner', 'chat',                 'create',  TRUE),
('owner', 'chat',                 'read',    TRUE),

-- ── ADMIN: Nearly full access, cannot delete company ──
('admin', 'company_settings',     'create',  TRUE),
('admin', 'company_settings',     'read',    TRUE),
('admin', 'company_settings',     'update',  TRUE),
('admin', 'company_settings',     'delete',  FALSE),
('admin', 'integrations',         'create',  TRUE),
('admin', 'integrations',         'read',    TRUE),
('admin', 'integrations',         'update',  TRUE),
('admin', 'integrations',         'delete',  TRUE),
('admin', 'tax_integrations',     'create',  TRUE),
('admin', 'tax_integrations',     'read',    TRUE),
('admin', 'tax_integrations',     'update',  TRUE),
('admin', 'tax_integrations',     'delete',  TRUE),
('admin', 'bank_connections',     'create',  TRUE),
('admin', 'bank_connections',     'read',    TRUE),
('admin', 'bank_connections',     'update',  TRUE),
('admin', 'bank_connections',     'delete',  TRUE),
('admin', 'bank_accounts',        'read',    TRUE),
('admin', 'bank_accounts',        'update',  TRUE),
('admin', 'contacts',             'create',  TRUE),
('admin', 'contacts',             'read',    TRUE),
('admin', 'contacts',             'update',  TRUE),
('admin', 'contacts',             'delete',  TRUE),
('admin', 'invoices',             'create',  TRUE),
('admin', 'invoices',             'read',    TRUE),
('admin', 'invoices',             'update',  TRUE),
('admin', 'invoices',             'delete',  TRUE),
('admin', 'invoices',             'approve', TRUE),
('admin', 'invoices',             'pay',     TRUE),
('admin', 'accountant_tasks',     'create',  TRUE),
('admin', 'accountant_tasks',     'read',    TRUE),
('admin', 'accountant_tasks',     'update',  TRUE),
('admin', 'compliance_deadlines', 'create',  TRUE),
('admin', 'compliance_deadlines', 'read',    TRUE),
('admin', 'compliance_deadlines', 'update',  TRUE),
('admin', 'chat',                 'create',  TRUE),
('admin', 'chat',                 'read',    TRUE),

-- ── ACCOUNTANT: Financial data access, no settings/integrations ──
('accountant', 'company_settings',     'read',    TRUE),
('accountant', 'integrations',         'read',    TRUE),
('accountant', 'tax_integrations',     'read',    TRUE),
('accountant', 'bank_connections',     'read',    TRUE),
('accountant', 'bank_accounts',        'read',    TRUE),
('accountant', 'contacts',             'create',  TRUE),
('accountant', 'contacts',             'read',    TRUE),
('accountant', 'contacts',             'update',  TRUE),
('accountant', 'invoices',             'create',  TRUE),
('accountant', 'invoices',             'read',    TRUE),
('accountant', 'invoices',             'update',  TRUE),
('accountant', 'invoices',             'approve', TRUE),
('accountant', 'invoices',             'pay',     FALSE),
('accountant', 'accountant_tasks',     'create',  TRUE),
('accountant', 'accountant_tasks',     'read',    TRUE),
('accountant', 'accountant_tasks',     'update',  TRUE),
('accountant', 'compliance_deadlines', 'create',  TRUE),
('accountant', 'compliance_deadlines', 'read',    TRUE),
('accountant', 'compliance_deadlines', 'update',  TRUE),
('accountant', 'chat',                 'create',  TRUE),
('accountant', 'chat',                 'read',    TRUE),

-- ── MEMBER: Day-to-day operations, no settings, no approval/pay ──
('member', 'company_settings',     'read',    TRUE),
('member', 'bank_accounts',        'read',    TRUE),
('member', 'contacts',             'create',  TRUE),
('member', 'contacts',             'read',    TRUE),
('member', 'contacts',             'update',  TRUE),
('member', 'invoices',             'create',  TRUE),
('member', 'invoices',             'read',    TRUE),
('member', 'invoices',             'update',  TRUE),
('member', 'invoices',             'approve', FALSE),
('member', 'invoices',             'pay',     FALSE),
('member', 'accountant_tasks',     'read',    TRUE),
('member', 'accountant_tasks',     'update',  TRUE),
('member', 'compliance_deadlines', 'read',    TRUE),
('member', 'chat',                 'create',  TRUE),
('member', 'chat',                 'read',    TRUE),

-- ── VIEWER: Read-only across the board ──
('viewer', 'company_settings',     'read',    TRUE),
('viewer', 'bank_accounts',        'read',    TRUE),
('viewer', 'contacts',             'read',    TRUE),
('viewer', 'invoices',             'read',    TRUE),
('viewer', 'accountant_tasks',     'read',    TRUE),
('viewer', 'compliance_deadlines', 'read',    TRUE),
('viewer', 'chat',                 'read',    TRUE);


-- ============================================================================
-- Default Gmail Label Mappings (template — applied per channel on connect)
-- ============================================================================
-- These are reference values. Actual rows are created in gmail_label_mappings
-- when a Gmail channel is connected.
--
-- Status             → Gmail Label
-- ─────────────────────────────────
-- in_progress        → $invoice/1_in_progress
-- pending            → $invoice/2_pending
-- approved           → $invoice/3_approved
-- payment_submitted  → $invoice/4_payment_submitted
-- paid               → $invoice/5_paid
-- overdue            → $invoice/6_overdue
-- disputed           → $invoice/7_disputed
-- voided             → $invoice/8_voided


-- ============================================================================
-- Default Dunning Rules (template)
-- ============================================================================
-- These are inserted per-workspace on creation. workspace_id placeholder = '00000000-0000-0000-0000-000000000000'
-- Replace with actual workspace_id during provisioning.

-- INSERT INTO dunning_rules (workspace_id, name, days_after_due, channel, subject_template, body_template, dunning_level) VALUES
-- ('{ws_id}', 'Gentle Reminder',       3,  'email', 'Payment Reminder: Invoice #{invoice_number}',     'Hi {contact_name},\n\nThis is a friendly reminder that invoice #{invoice_number} for {currency} {total_amount} was due on {due_date}.\n\nPlease let us know if you have any questions.\n\nBest regards', 1),
-- ('{ws_id}', 'Second Notice',         10, 'email', 'Second Notice: Invoice #{invoice_number} Overdue', 'Hi {contact_name},\n\nOur records show that invoice #{invoice_number} for {currency} {total_amount} remains unpaid. It was due on {due_date}.\n\nPlease arrange payment at your earliest convenience.\n\nRegards', 2),
-- ('{ws_id}', 'Final Notice',          21, 'email', 'Final Notice: Invoice #{invoice_number}',          'Hi {contact_name},\n\nThis is our final reminder regarding invoice #{invoice_number} for {currency} {total_amount}, which has been overdue since {due_date}.\n\nPlease settle this balance immediately to avoid further action.\n\nRegards', 3);


-- ============================================================================
-- Default Compliance Deadline Types (reference)
-- ============================================================================
-- deadline_type values used by the system:
--   'income_tax_installment'
--   'vat_return'
--   'sales_tax_return'
--   'payroll_filing'
--   'corporate_tax_return'
--   'annual_accounts'
--   '1099_filing'
--   'w2_filing'
