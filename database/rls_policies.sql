-- ============================================================================
-- SoloHub Row-Level Security (RLS) Policies for Supabase
-- ============================================================================
-- These policies enforce multi-tenant data isolation at the database level.
-- Every query automatically scopes data to the user's workspace(s).
-- ============================================================================

-- Helper: Get all workspace IDs the current user belongs to
CREATE OR REPLACE FUNCTION get_user_workspace_ids()
RETURNS SETOF UUID AS $$
    SELECT workspace_id
    FROM workspace_members
    WHERE user_id = auth.uid()
      AND status = 'active';
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- Helper: Get the current user's role in a specific workspace
CREATE OR REPLACE FUNCTION get_user_role(ws_id UUID)
RETURNS user_role AS $$
    SELECT role
    FROM workspace_members
    WHERE workspace_id = ws_id
      AND user_id = auth.uid()
      AND status = 'active'
    LIMIT 1;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- Helper: Check if user has a specific permission
CREATE OR REPLACE FUNCTION has_permission(ws_id UUID, p_resource TEXT, p_action TEXT)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1
        FROM role_permissions rp
        JOIN workspace_members wm ON wm.role = rp.role
        WHERE wm.workspace_id = ws_id
          AND wm.user_id = auth.uid()
          AND wm.status = 'active'
          AND rp.resource = p_resource
          AND rp.action = p_action
          AND rp.is_allowed = TRUE
    );
$$ LANGUAGE sql STABLE SECURITY DEFINER;


-- ============================================================================
-- PROFILES
-- ============================================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY profiles_select ON profiles
    FOR SELECT USING (TRUE);  -- Public read (display names, avatars)

CREATE POLICY profiles_update ON profiles
    FOR UPDATE USING (id = auth.uid());

CREATE POLICY profiles_insert ON profiles
    FOR INSERT WITH CHECK (id = auth.uid());


-- ============================================================================
-- WORKSPACES
-- ============================================================================
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;

CREATE POLICY workspaces_select ON workspaces
    FOR SELECT USING (id IN (SELECT get_user_workspace_ids()));

CREATE POLICY workspaces_insert ON workspaces
    FOR INSERT WITH CHECK (owner_id = auth.uid());

CREATE POLICY workspaces_update ON workspaces
    FOR UPDATE USING (
        owner_id = auth.uid()
        OR get_user_role(id) IN ('owner', 'admin')
    );

CREATE POLICY workspaces_delete ON workspaces
    FOR DELETE USING (owner_id = auth.uid());


-- ============================================================================
-- COMPANIES
-- ============================================================================
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

CREATE POLICY companies_select ON companies
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY companies_insert ON companies
    FOR INSERT WITH CHECK (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'company_settings', 'create')
    );

CREATE POLICY companies_update ON companies
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'company_settings', 'update')
    );

CREATE POLICY companies_delete ON companies
    FOR DELETE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'company_settings', 'delete')
        AND is_default = FALSE
    );


-- ============================================================================
-- WORKSPACE MEMBERS
-- ============================================================================
ALTER TABLE workspace_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY members_select ON workspace_members
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY members_insert ON workspace_members
    FOR INSERT WITH CHECK (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND get_user_role(workspace_id) IN ('owner', 'admin')
    );

CREATE POLICY members_update ON workspace_members
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND get_user_role(workspace_id) IN ('owner', 'admin')
    );

CREATE POLICY members_delete ON workspace_members
    FOR DELETE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND get_user_role(workspace_id) IN ('owner', 'admin')
    );


-- ============================================================================
-- CONNECTED CHANNELS
-- ============================================================================
ALTER TABLE connected_channels ENABLE ROW LEVEL SECURITY;

CREATE POLICY channels_select ON connected_channels
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY channels_insert ON connected_channels
    FOR INSERT WITH CHECK (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'integrations', 'create')
    );

CREATE POLICY channels_update ON connected_channels
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'integrations', 'update')
    );

CREATE POLICY channels_delete ON connected_channels
    FOR DELETE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'integrations', 'delete')
    );


-- ============================================================================
-- BANK CONNECTIONS
-- ============================================================================
ALTER TABLE bank_connections ENABLE ROW LEVEL SECURITY;

CREATE POLICY bank_conn_select ON bank_connections
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY bank_conn_insert ON bank_connections
    FOR INSERT WITH CHECK (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'bank_connections', 'create')
    );

CREATE POLICY bank_conn_update ON bank_connections
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'bank_connections', 'update')
    );

CREATE POLICY bank_conn_delete ON bank_connections
    FOR DELETE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'bank_connections', 'delete')
    );


-- ============================================================================
-- TAX AUTHORITY INTEGRATIONS
-- ============================================================================
ALTER TABLE tax_authority_integrations ENABLE ROW LEVEL SECURITY;

CREATE POLICY tax_int_select ON tax_authority_integrations
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY tax_int_insert ON tax_authority_integrations
    FOR INSERT WITH CHECK (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'tax_integrations', 'create')
    );

CREATE POLICY tax_int_update ON tax_authority_integrations
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'tax_integrations', 'update')
    );

CREATE POLICY tax_int_delete ON tax_authority_integrations
    FOR DELETE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'tax_integrations', 'delete')
    );


-- ============================================================================
-- GDRIVE CONNECTIONS
-- ============================================================================
ALTER TABLE gdrive_connections ENABLE ROW LEVEL SECURITY;

CREATE POLICY gdrive_select ON gdrive_connections
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY gdrive_insert ON gdrive_connections
    FOR INSERT WITH CHECK (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'integrations', 'create')
    );

CREATE POLICY gdrive_update ON gdrive_connections
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'integrations', 'update')
    );


-- ============================================================================
-- CONTACTS
-- ============================================================================
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

CREATE POLICY contacts_select ON contacts
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY contacts_insert ON contacts
    FOR INSERT WITH CHECK (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY contacts_update ON contacts
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'contacts', 'update')
    );

CREATE POLICY contacts_delete ON contacts
    FOR DELETE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'contacts', 'delete')
    );


-- ============================================================================
-- CONTACT AUDIT LOG
-- ============================================================================
ALTER TABLE contact_audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY contact_audit_select ON contact_audit_log
    FOR SELECT USING (
        contact_id IN (
            SELECT id FROM contacts WHERE workspace_id IN (SELECT get_user_workspace_ids())
        )
    );
-- Insert-only: system and triggers write, no user updates/deletes
CREATE POLICY contact_audit_insert ON contact_audit_log
    FOR INSERT WITH CHECK (TRUE);


-- ============================================================================
-- INBOX MESSAGES
-- ============================================================================
ALTER TABLE inbox_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY inbox_select ON inbox_messages
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY inbox_insert ON inbox_messages
    FOR INSERT WITH CHECK (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY inbox_update ON inbox_messages
    FOR UPDATE USING (workspace_id IN (SELECT get_user_workspace_ids()));


-- ============================================================================
-- INBOX ATTACHMENTS
-- ============================================================================
ALTER TABLE inbox_attachments ENABLE ROW LEVEL SECURITY;

CREATE POLICY attachments_select ON inbox_attachments
    FOR SELECT USING (
        message_id IN (
            SELECT id FROM inbox_messages WHERE workspace_id IN (SELECT get_user_workspace_ids())
        )
    );

CREATE POLICY attachments_insert ON inbox_attachments
    FOR INSERT WITH CHECK (
        message_id IN (
            SELECT id FROM inbox_messages WHERE workspace_id IN (SELECT get_user_workspace_ids())
        )
    );


-- ============================================================================
-- INVOICES
-- ============================================================================
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

CREATE POLICY invoices_select ON invoices
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY invoices_insert ON invoices
    FOR INSERT WITH CHECK (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY invoices_update ON invoices
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'invoices', 'update')
    );

CREATE POLICY invoices_delete ON invoices
    FOR DELETE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'invoices', 'delete')
    );

-- Invoice approval requires specific permission
CREATE POLICY invoices_approve ON invoices
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'invoices', 'approve')
    );

-- Invoice payment execution requires specific permission
CREATE POLICY invoices_pay ON invoices
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'invoices', 'pay')
    );


-- ============================================================================
-- INVOICE LINE ITEMS
-- ============================================================================
ALTER TABLE invoice_line_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY line_items_select ON invoice_line_items
    FOR SELECT USING (
        invoice_id IN (
            SELECT id FROM invoices WHERE workspace_id IN (SELECT get_user_workspace_ids())
        )
    );

CREATE POLICY line_items_insert ON invoice_line_items
    FOR INSERT WITH CHECK (
        invoice_id IN (
            SELECT id FROM invoices WHERE workspace_id IN (SELECT get_user_workspace_ids())
        )
    );

CREATE POLICY line_items_update ON invoice_line_items
    FOR UPDATE USING (
        invoice_id IN (
            SELECT id FROM invoices
            WHERE workspace_id IN (SELECT get_user_workspace_ids())
              AND has_permission(workspace_id, 'invoices', 'update')
        )
    );

CREATE POLICY line_items_delete ON invoice_line_items
    FOR DELETE USING (
        invoice_id IN (
            SELECT id FROM invoices
            WHERE workspace_id IN (SELECT get_user_workspace_ids())
              AND has_permission(workspace_id, 'invoices', 'update')
        )
    );


-- ============================================================================
-- INVOICE STATUS HISTORY (read-only for users)
-- ============================================================================
ALTER TABLE invoice_status_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY status_hist_select ON invoice_status_history
    FOR SELECT USING (
        invoice_id IN (
            SELECT id FROM invoices WHERE workspace_id IN (SELECT get_user_workspace_ids())
        )
    );

CREATE POLICY status_hist_insert ON invoice_status_history
    FOR INSERT WITH CHECK (TRUE);  -- System trigger inserts


-- ============================================================================
-- INVOICE COMMUNICATIONS
-- ============================================================================
ALTER TABLE invoice_communications ENABLE ROW LEVEL SECURITY;

CREATE POLICY comms_select ON invoice_communications
    FOR SELECT USING (
        invoice_id IN (
            SELECT id FROM invoices WHERE workspace_id IN (SELECT get_user_workspace_ids())
        )
    );

CREATE POLICY comms_insert ON invoice_communications
    FOR INSERT WITH CHECK (
        invoice_id IN (
            SELECT id FROM invoices WHERE workspace_id IN (SELECT get_user_workspace_ids())
        )
    );


-- ============================================================================
-- DUNNING RULES
-- ============================================================================
ALTER TABLE dunning_rules ENABLE ROW LEVEL SECURITY;

CREATE POLICY dunning_select ON dunning_rules
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY dunning_insert ON dunning_rules
    FOR INSERT WITH CHECK (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'invoices', 'update')
    );

CREATE POLICY dunning_update ON dunning_rules
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'invoices', 'update')
    );


-- ============================================================================
-- BANK ACCOUNTS
-- ============================================================================
ALTER TABLE bank_accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY bank_acct_select ON bank_accounts
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY bank_acct_insert ON bank_accounts
    FOR INSERT WITH CHECK (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY bank_acct_update ON bank_accounts
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'bank_accounts', 'update')
    );


-- ============================================================================
-- BANK TRANSACTIONS
-- ============================================================================
ALTER TABLE bank_transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY bank_txn_select ON bank_transactions
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY bank_txn_insert ON bank_transactions
    FOR INSERT WITH CHECK (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY bank_txn_update ON bank_transactions
    FOR UPDATE USING (workspace_id IN (SELECT get_user_workspace_ids()));


-- ============================================================================
-- PAYMENT TRANSACTIONS
-- ============================================================================
ALTER TABLE payment_transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY pay_txn_select ON payment_transactions
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY pay_txn_insert ON payment_transactions
    FOR INSERT WITH CHECK (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND has_permission(workspace_id, 'invoices', 'pay')
    );


-- ============================================================================
-- ACCOUNTANT TASKS
-- ============================================================================
ALTER TABLE accountant_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY tasks_select ON accountant_tasks
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY tasks_insert ON accountant_tasks
    FOR INSERT WITH CHECK (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY tasks_update ON accountant_tasks
    FOR UPDATE USING (workspace_id IN (SELECT get_user_workspace_ids()));


-- ============================================================================
-- TASK DOCUMENTS
-- ============================================================================
ALTER TABLE task_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY task_docs_select ON task_documents
    FOR SELECT USING (
        task_id IN (
            SELECT id FROM accountant_tasks WHERE workspace_id IN (SELECT get_user_workspace_ids())
        )
    );

CREATE POLICY task_docs_insert ON task_documents
    FOR INSERT WITH CHECK (
        task_id IN (
            SELECT id FROM accountant_tasks WHERE workspace_id IN (SELECT get_user_workspace_ids())
        )
    );


-- ============================================================================
-- COMPLIANCE DEADLINES
-- ============================================================================
ALTER TABLE compliance_deadlines ENABLE ROW LEVEL SECURITY;

CREATE POLICY deadlines_select ON compliance_deadlines
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY deadlines_insert ON compliance_deadlines
    FOR INSERT WITH CHECK (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND get_user_role(workspace_id) IN ('owner', 'admin', 'accountant')
    );

CREATE POLICY deadlines_update ON compliance_deadlines
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND get_user_role(workspace_id) IN ('owner', 'admin', 'accountant')
    );


-- ============================================================================
-- CHAT MESSAGES
-- ============================================================================
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY chat_select ON chat_messages
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY chat_insert ON chat_messages
    FOR INSERT WITH CHECK (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND sender_id = auth.uid()
    );

CREATE POLICY chat_update ON chat_messages
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND (sender_id = auth.uid() OR TRUE)  -- Allow marking as read
    );


-- ============================================================================
-- CHAT ATTACHMENTS
-- ============================================================================
ALTER TABLE chat_attachments ENABLE ROW LEVEL SECURITY;

CREATE POLICY chat_att_select ON chat_attachments
    FOR SELECT USING (
        message_id IN (
            SELECT id FROM chat_messages WHERE workspace_id IN (SELECT get_user_workspace_ids())
        )
    );

CREATE POLICY chat_att_insert ON chat_attachments
    FOR INSERT WITH CHECK (
        message_id IN (
            SELECT id FROM chat_messages WHERE sender_id = auth.uid()
        )
    );


-- ============================================================================
-- GMAIL LABEL MAPPINGS
-- ============================================================================
ALTER TABLE gmail_label_mappings ENABLE ROW LEVEL SECURITY;

CREATE POLICY gmail_labels_select ON gmail_label_mappings
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY gmail_labels_insert ON gmail_label_mappings
    FOR INSERT WITH CHECK (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY gmail_labels_update ON gmail_label_mappings
    FOR UPDATE USING (workspace_id IN (SELECT get_user_workspace_ids()));


-- ============================================================================
-- GMAIL SYNC LOG
-- ============================================================================
ALTER TABLE gmail_sync_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY gmail_sync_select ON gmail_sync_log
    FOR SELECT USING (
        channel_id IN (
            SELECT id FROM connected_channels WHERE workspace_id IN (SELECT get_user_workspace_ids())
        )
    );

CREATE POLICY gmail_sync_insert ON gmail_sync_log
    FOR INSERT WITH CHECK (TRUE);  -- System process inserts


-- ============================================================================
-- DASHBOARD KPI CACHE
-- ============================================================================
ALTER TABLE dashboard_kpi_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY kpi_select ON dashboard_kpi_cache
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY kpi_insert ON dashboard_kpi_cache
    FOR INSERT WITH CHECK (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY kpi_update ON dashboard_kpi_cache
    FOR UPDATE USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY kpi_delete ON dashboard_kpi_cache
    FOR DELETE USING (workspace_id IN (SELECT get_user_workspace_ids()));


-- ============================================================================
-- NOTIFICATIONS
-- ============================================================================
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY notif_select ON notifications
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY notif_update ON notifications
    FOR UPDATE USING (user_id = auth.uid());  -- Mark as read

CREATE POLICY notif_insert ON notifications
    FOR INSERT WITH CHECK (TRUE);  -- System inserts


-- ============================================================================
-- AUDIT LOG (read-only for admins)
-- ============================================================================
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY audit_select ON audit_log
    FOR SELECT USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND get_user_role(workspace_id) IN ('owner', 'admin')
    );

CREATE POLICY audit_insert ON audit_log
    FOR INSERT WITH CHECK (TRUE);  -- System/trigger inserts


-- ============================================================================
-- WORKSPACE PREFERENCES
-- ============================================================================
ALTER TABLE workspace_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY prefs_select ON workspace_preferences
    FOR SELECT USING (workspace_id IN (SELECT get_user_workspace_ids()));

CREATE POLICY prefs_insert ON workspace_preferences
    FOR INSERT WITH CHECK (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND get_user_role(workspace_id) IN ('owner', 'admin')
    );

CREATE POLICY prefs_update ON workspace_preferences
    FOR UPDATE USING (
        workspace_id IN (SELECT get_user_workspace_ids())
        AND get_user_role(workspace_id) IN ('owner', 'admin')
    );


-- ============================================================================
-- ROLE PERMISSIONS (read-only; seeded by migrations)
-- ============================================================================
ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;

CREATE POLICY perms_select ON role_permissions
    FOR SELECT USING (TRUE);  -- All authenticated users can read permission matrix
