"""
SoloHub Database Schema — Visual PDF Generator
Produces: database/SoloHub_Database_Schema.pdf

Run: python generate_schema_pdf.py
"""
import os
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ──────────────────────────────────────────────────────────────────────────────
# COLOUR PALETTE (one per module)
# ──────────────────────────────────────────────────────────────────────────────
C = {
    "core":        HexColor("#4A90D9"),   # blue
    "integrations":HexColor("#7B68EE"),   # medium slate blue
    "counterparts": HexColor("#27AE60"),   # green
    "inbox":       HexColor("#E67E22"),   # orange
    "invoices":    HexColor("#E74C3C"),   # red
    "banking":     HexColor("#2ECC71"),   # emerald
    "accountant":  HexColor("#8E44AD"),   # purple
    "gmail":       HexColor("#C0392B"),   # dark red
    "cross":       HexColor("#555555"),   # dark grey
    "bg":          HexColor("#F8F9FA"),
    "header_text": colors.white,
    "field_text":  HexColor("#2C3E50"),
    "pk_text":     HexColor("#C0392B"),
    "fk_text":     HexColor("#2980B9"),
    "border":      HexColor("#BDC3C7"),
    "title_bg":    HexColor("#1A1A2E"),
    "subtitle":    HexColor("#E8E8E8"),
}

# ──────────────────────────────────────────────────────────────────────────────
# SCHEMA DATA  — (table_name, module_key, [(field, type, notes), ...])
# notes: "PK" / "FK→Table" / "" / "encrypted" / "JSON"
# ──────────────────────────────────────────────────────────────────────────────
TABLES = [
    # ── CORE / IAM ──────────────────────────────────────────────────────────
    ("Profile", "core", [
        ("id",                   "UUID",         "PK · default=uuid4"),
        ("full_name",            "VARCHAR(255)",  ""),
        ("display_name",         "VARCHAR(100)",  ""),
        ("phone",                "VARCHAR(50)",   "nullable"),
        ("timezone",             "VARCHAR(64)",   ""),
        ("avatar_url",           "TEXT",          "nullable"),
        ("onboarding_completed", "BOOLEAN",       "default False"),
        ("metadata",             "JSONB",         "JSON"),
        ("created_at",           "TIMESTAMPTZ",  "auto"),
        ("updated_at",           "TIMESTAMPTZ",  "auto"),
    ]),
    ("Workspace", "core", [
        ("id",            "UUID",        "PK · default=uuid4"),
        ("owner_id",      "UUID",        "FK→Profile"),
        ("name",          "VARCHAR(255)",""),
        ("slug",          "VARCHAR(100)","unique"),
        ("base_currency", "VARCHAR(3)",  "default GBP"),
        ("timezone",      "VARCHAR(64)", ""),
        ("is_active",     "BOOLEAN",     "default True"),
        ("logo_url",      "TEXT",        "nullable"),
        ("settings",      "JSONB",       "JSON"),
        ("created_at",    "TIMESTAMPTZ", "auto"),
        ("updated_at",    "TIMESTAMPTZ", "auto"),
    ]),
    ("Company", "core", [
        ("id",            "UUID",        "PK · default=uuid4"),
        ("workspace",     "UUID",        "FK→Workspace"),
        ("legal_name",    "VARCHAR(255)",""),
        ("trade_name",    "VARCHAR(255)","nullable"),
        ("tax_id",        "VARCHAR(100)","nullable"),
        ("email",         "EMAIL",       "nullable"),
        ("phone",         "VARCHAR(50)", "nullable"),
        ("address_line1", "VARCHAR(255)","nullable"),
        ("city",          "VARCHAR(100)","nullable"),
        ("country_code",  "VARCHAR(2)",  ""),
        ("base_currency", "VARCHAR(3)",  ""),
        ("is_default",    "BOOLEAN",     "default False"),
        ("is_individual", "BOOLEAN",     "default False"),
        ("logo_url",      "TEXT",        "nullable"),
        ("created_at",    "TIMESTAMPTZ", "auto"),
        ("updated_at",    "TIMESTAMPTZ", "auto"),
    ]),
    ("WorkspaceMember", "core", [
        ("id",         "UUID",        "PK · default=uuid4"),
        ("workspace",  "UUID",        "FK→Workspace"),
        ("user_id",    "UUID",        "FK→Profile · nullable"),
        ("email",      "EMAIL",       ""),
        ("role",       "ENUM",        "owner/admin/accountant/member/viewer"),
        ("status",     "ENUM",        "invited/active/deactivated"),
        ("invited_at", "TIMESTAMPTZ", "auto"),
        ("joined_at",  "TIMESTAMPTZ", "nullable"),
        ("created_at", "TIMESTAMPTZ", "auto"),
        ("updated_at", "TIMESTAMPTZ", "auto"),
    ]),
    ("RolePermission", "core", [
        ("id",         "BIGINT",      "PK auto"),
        ("workspace",  "UUID",        "FK→Workspace"),
        ("role",       "ENUM",        "owner/admin/accountant/member/viewer"),
        ("resource",   "VARCHAR(100)",""),
        ("action",     "VARCHAR(50)", ""),
        ("is_allowed", "BOOLEAN",     ""),
    ]),
    ("WorkspacePreference", "core", [
        ("id",         "BIGINT",      "PK auto"),
        ("workspace",  "UUID",        "FK→Workspace"),
        ("key",        "VARCHAR(100)",""),
        ("value",      "TEXT",        ""),
        ("updated_at", "TIMESTAMPTZ", "auto"),
    ]),

    # ── INTEGRATIONS ────────────────────────────────────────────────────────
    ("ConnectedChannel", "integrations", [
        ("id",                      "UUID",        "PK"),
        ("workspace",               "UUID",        "FK→Workspace"),
        ("company",                 "UUID",        "FK→Company · nullable"),
        ("channel_type",            "ENUM",        "gmail/outlook/whatsapp/telegram/…"),
        ("display_name",            "VARCHAR(255)",""),
        ("account_identifier",      "VARCHAR(255)","nullable"),
        ("access_token_encrypted",  "TEXT",        "encrypted"),
        ("refresh_token_encrypted", "TEXT",        "encrypted"),
        ("token_expires_at",        "TIMESTAMPTZ", "nullable"),
        ("status",                  "ENUM",        "active/error/disconnected"),
        ("last_sync_at",            "TIMESTAMPTZ", "nullable"),
        ("sync_cursor",             "TEXT",        "nullable"),
        ("created_at",              "TIMESTAMPTZ", "auto"),
        ("updated_at",              "TIMESTAMPTZ", "auto"),
    ]),
    ("BankConnection", "integrations", [
        ("id",                       "UUID",   "PK"),
        ("workspace",                "UUID",   "FK→Workspace"),
        ("company",                  "UUID",   "FK→Company"),
        ("provider",                 "ENUM",   "plaid/truelayer/…"),
        ("institution_name",         "VARCHAR(255)", ""),
        ("access_token_encrypted",   "TEXT",   "encrypted"),
        ("refresh_token_encrypted",  "TEXT",   "encrypted"),
        ("consent_token_encrypted",  "TEXT",   "encrypted"),
        ("status",                   "ENUM",   "active/expired/revoked/error"),
        ("supports_ais",             "BOOLEAN",""),
        ("supports_pis",             "BOOLEAN",""),
        ("consent_expires_at",       "TIMESTAMPTZ","nullable"),
        ("last_sync_at",             "TIMESTAMPTZ","nullable"),
        ("created_at",               "TIMESTAMPTZ","auto"),
        ("updated_at",               "TIMESTAMPTZ","auto"),
    ]),
    ("TaxAuthorityIntegration", "integrations", [
        ("id",                      "UUID",   "PK"),
        ("workspace",               "UUID",   "FK→Workspace"),
        ("company",                 "UUID",   "FK→Company"),
        ("authority_name",          "VARCHAR(255)",""),
        ("authority_code",          "ENUM",   "hmrc/irs/…"),
        ("region",                  "VARCHAR(10)","nullable"),
        ("tax_reference",           "VARCHAR(100)","nullable"),
        ("access_token_encrypted",  "TEXT",   "encrypted"),
        ("refresh_token_encrypted", "TEXT",   "encrypted"),
        ("status",                  "ENUM",   "active/expired/error/disconnected"),
        ("created_at",              "TIMESTAMPTZ","auto"),
        ("updated_at",              "TIMESTAMPTZ","auto"),
    ]),
    ("GDriveConnection", "integrations", [
        ("id",                      "UUID",   "PK"),
        ("workspace",               "UUID",   "FK→Workspace"),
        ("company",                 "UUID",   "FK→Company"),
        ("access_token_encrypted",  "TEXT",   "encrypted"),
        ("refresh_token_encrypted", "TEXT",   "encrypted"),
        ("status",                  "ENUM",   "active/error/disconnected"),
        ("source_folder_id",        "TEXT",   "nullable"),
        ("destination_folder_id",   "TEXT",   "nullable"),
        ("last_sync_at",            "TIMESTAMPTZ","nullable"),
        ("created_at",              "TIMESTAMPTZ","auto"),
        ("updated_at",              "TIMESTAMPTZ","auto"),
    ]),

    # ── COUNTERPARTS ──────────────────────────────────────────────────────────
    ("Counterpart", "counterparts", [
        ("id",                           "UUID",    "PK"),
        ("workspace",                    "UUID",    "FK→Workspace"),
        ("company",                      "UUID",    "FK→Company"),
        ("name",                         "VARCHAR(255)",""),
        ("legal_name",                   "VARCHAR(255)","nullable"),
        ("counterpart_type",              "ENUM",    "CLIENT/SUPPLIER/PARTNER/INDIVIDUAL/OTHER"),
        ("email",                        "EMAIL",   "nullable"),
        ("phone",                        "VARCHAR(50)","nullable"),
        ("tax_id",                       "VARCHAR(100)","nullable"),
        ("address_line1",                "VARCHAR(255)","nullable"),
        ("city",                         "VARCHAR(100)","nullable"),
        ("country_code",                 "VARCHAR(2)","nullable"),
        ("bank_account_number_encrypted","TEXT",    "encrypted"),
        ("bank_iban_encrypted",          "TEXT",    "encrypted"),
        ("bank_swift",                   "VARCHAR(20)","nullable"),
        ("bank_currency",                "VARCHAR(3)","nullable"),
        ("payment_terms_days",           "INTEGER", "default 30"),
        ("default_currency",             "VARCHAR(3)",""),
        ("fraud_risk_score",             "SMALLINT","1–5"),
        ("credit_risk_score",            "SMALLINT","1–5"),
        ("total_invoices",               "DECIMAL(15,2)","default 0"),
        ("total_paid",                   "DECIMAL(15,2)","default 0"),
        ("avg_payment_days",             "DECIMAL(6,1)","nullable"),
        ("last_invoice_date",            "DATE",    "nullable"),
        ("is_active",                    "BOOLEAN", "default True"),
        ("metadata",                     "JSONB",   "JSON"),
        ("created_at",                   "TIMESTAMPTZ","auto"),
        ("updated_at",                   "TIMESTAMPTZ","auto"),
    ]),
    ("CounterpartAuditLog", "counterparts", [
        ("id",            "UUID",  "PK"),
        ("counterpart",   "UUID",  "FK→Counterpart"),
        ("field_name", "VARCHAR(100)",""),
        ("old_value",  "TEXT",  "nullable"),
        ("new_value",  "TEXT",  "nullable"),
        ("changed_by", "UUID",  "nullable"),
        ("changed_at", "TIMESTAMPTZ","auto"),
    ]),

    # ── INBOX ────────────────────────────────────────────────────────────────
    ("InboxMessage", "inbox", [
        ("id",                      "UUID",   "PK"),
        ("workspace",               "UUID",   "FK→Workspace"),
        ("company",                 "UUID",   "FK→Company · nullable"),
        ("channel",                 "UUID",   "FK→ConnectedChannel · nullable"),
        ("source",                  "ENUM",   "gmail/outlook/whatsapp/telegram/…"),
        ("external_message_id",     "TEXT",   "nullable"),
        ("sender_email",            "EMAIL",  "nullable"),
        ("sender_name",             "VARCHAR(255)","nullable"),
        ("subject",                 "TEXT",   "nullable"),
        ("body_preview",            "TEXT",   "nullable"),
        ("received_at",             "TIMESTAMPTZ",""),
        ("classification",          "ENUM",   "invoice/payment/query/spam/other"),
        ("classification_confidence","DECIMAL(5,2)","nullable"),
        ("classified_at",           "TIMESTAMPTZ","nullable"),
        ("processing_status",       "ENUM",   "pending/processing/done/failed"),
        ("linked_invoice",          "UUID",   "FK→Invoice · nullable"),
        ("linked_counterpart",       "UUID",   "FK→Counterpart · nullable"),
        ("gmail_label",             "TEXT",   "nullable"),
        ("is_read",                 "BOOLEAN","default False"),
        ("is_starred",              "BOOLEAN","default False"),
        ("metadata",                "JSONB",  "JSON"),
        ("created_at",              "TIMESTAMPTZ","auto"),
        ("updated_at",              "TIMESTAMPTZ","auto"),
    ]),
    ("InboxAttachment", "inbox", [
        ("id",                 "UUID",  "PK"),
        ("message",            "UUID",  "FK→InboxMessage"),
        ("filename",           "TEXT",  ""),
        ("mime_type",          "VARCHAR(100)",""),
        ("file_size_bytes",    "BIGINT","nullable"),
        ("storage_path",       "TEXT",  ""),
        ("content_hash",       "VARCHAR(64)","nullable · dedup"),
        ("is_duplicate",       "BOOLEAN","default False"),
        ("ocr_status",         "ENUM",  "pending/processing/done/failed/skipped"),
        ("ocr_extracted_data", "JSONB", "JSON"),
        ("ocr_confidence",     "DECIMAL(5,2)","nullable"),
        ("ocr_processed_at",   "TIMESTAMPTZ","nullable"),
        ("created_at",         "TIMESTAMPTZ","auto"),
        ("updated_at",         "TIMESTAMPTZ","auto"),
    ]),

    # ── INVOICES ─────────────────────────────────────────────────────────────
    ("Invoice", "invoices", [
        ("id",                     "UUID",   "PK"),
        ("workspace",              "UUID",   "FK→Workspace"),
        ("company",                "UUID",   "FK→Company"),
        ("direction",              "ENUM",   "purchase / sale"),
        ("source",                 "ENUM",   "email/manual/gdrive/api/…"),
        ("invoice_number",         "VARCHAR(100)",""),
        ("reference_number",       "VARCHAR(100)","nullable"),
        ("counterpart",             "UUID",   "FK→Counterpart · nullable"),
        ("contact_name",           "TEXT",   "snapshot · denormalized"),
        ("issue_date",             "DATE",   ""),
        ("due_date",               "DATE",   "nullable"),
        ("payment_terms_days",     "INTEGER","nullable"),
        ("currency",               "VARCHAR(3)",""),
        ("subtotal",               "DECIMAL(15,2)",""),
        ("tax_amount",             "DECIMAL(15,2)","default 0"),
        ("tax_rate",               "DECIMAL(6,4)","nullable"),
        ("discount_amount",        "DECIMAL(15,2)","default 0"),
        ("total_amount",           "DECIMAL(15,2)",""),
        ("amount_paid",            "DECIMAL(15,2)","default 0"),
        ("amount_due",             "@property","total_amount − amount_paid"),
        ("fx_rate",                "DECIMAL(12,6)","nullable"),
        ("base_currency_total",    "DECIMAL(15,2)","nullable"),
        ("status",                 "ENUM",   "draft/pending/approved/sent/paid/…"),
        ("fraud_risk_score",       "SMALLINT","1–5"),
        ("fraud_risk_flags",       "JSONB",  "JSON"),
        ("credit_risk_score",      "SMALLINT","1–5"),
        ("source_message",         "UUID",   "FK→InboxMessage · nullable"),
        ("reconciled_transaction", "UUID",   "FK→BankTransaction · nullable"),
        ("reconciliation_confidence","DECIMAL(5,2)","nullable"),
        ("dispatch_channel",       "ENUM",   "email/whatsapp/portal/…"),
        ("payment_method",         "ENUM",   "bank_transfer/card/stripe/…"),
        ("gdrive_file_id",         "TEXT",   "nullable"),
        ("gmail_thread_id",        "TEXT",   "nullable"),
        ("dunning_enabled",        "BOOLEAN","default False"),
        ("dunning_count",          "INTEGER","default 0"),
        ("approved_by",            "TEXT",   "nullable"),
        ("notes",                  "TEXT",   "nullable"),
        ("metadata",               "JSONB",  "JSON"),
        ("created_at",             "TIMESTAMPTZ","auto"),
        ("updated_at",             "TIMESTAMPTZ","auto"),
    ]),
    ("InvoiceLineItem", "invoices", [
        ("id",               "BIGINT",  "PK auto"),
        ("invoice",          "UUID",    "FK→Invoice"),
        ("position",         "INTEGER", ""),
        ("description",      "TEXT",    ""),
        ("quantity",         "DECIMAL(12,4)",""),
        ("unit_price",       "DECIMAL(15,2)",""),
        ("tax_rate",         "DECIMAL(6,4)", "default 0"),
        ("discount_percent", "DECIMAL(6,2)", "default 0"),
        ("line_total",       "DECIMAL(15,2)","computed"),
        ("category",         "VARCHAR(100)", "nullable"),
        ("account_code",     "VARCHAR(50)",  "nullable"),
        ("metadata",         "JSONB",        "JSON"),
    ]),
    ("InvoiceStatusHistory", "invoices", [
        ("id",           "UUID",   "PK"),
        ("invoice",      "UUID",   "FK→Invoice"),
        ("old_status",   "ENUM",   ""),
        ("new_status",   "ENUM",   ""),
        ("changed_by",   "UUID",   "nullable"),
        ("change_reason","TEXT",   "nullable"),
        ("created_at",   "TIMESTAMPTZ","auto"),
    ]),
    ("InvoiceCommunication", "invoices", [
        ("id",            "UUID",   "PK"),
        ("invoice",       "UUID",   "FK→Invoice"),
        ("channel",       "ENUM",   "email/whatsapp/sms/…"),
        ("recipient",     "VARCHAR(255)",""),
        ("subject",       "TEXT",   "nullable"),
        ("status",        "ENUM",   "queued/sent/delivered/read/failed"),
        ("is_dunning",    "BOOLEAN","default False"),
        ("dunning_level", "INTEGER","nullable"),
        ("sent_at",       "TIMESTAMPTZ","nullable"),
        ("delivered_at",  "TIMESTAMPTZ","nullable"),
        ("read_at",       "TIMESTAMPTZ","nullable"),
        ("created_at",    "TIMESTAMPTZ","auto"),
    ]),
    ("DunningRule", "invoices", [
        ("id",               "UUID",   "PK"),
        ("workspace",        "UUID",   "FK→Workspace"),
        ("company",          "UUID",   "FK→Company · nullable"),
        ("name",             "VARCHAR(255)",""),
        ("days_after_due",   "INTEGER",""),
        ("channel",          "ENUM",   "email/whatsapp/sms/…"),
        ("dunning_level",    "INTEGER",""),
        ("subject_template", "TEXT",   ""),
        ("body_template",    "TEXT",   ""),
        ("is_active",        "BOOLEAN","default True"),
        ("created_at",       "TIMESTAMPTZ","auto"),
        ("updated_at",       "TIMESTAMPTZ","auto"),
    ]),

    # ── BANKING ──────────────────────────────────────────────────────────────
    ("BankAccount", "banking", [
        ("id",                      "UUID",   "PK"),
        ("workspace",               "UUID",   "FK→Workspace"),
        ("company",                 "UUID",   "FK→Company"),
        ("connection",              "UUID",   "FK→BankConnection · nullable"),
        ("account_name",            "VARCHAR(255)",""),
        ("institution_name",        "VARCHAR(255)",""),
        ("account_type",            "ENUM",   "current/savings/credit/loan/…"),
        ("account_number_masked",   "VARCHAR(50)",""),
        ("account_number_encrypted","TEXT",   "encrypted"),
        ("sort_code_encrypted",     "TEXT",   "encrypted"),
        ("iban_encrypted",          "TEXT",   "encrypted"),
        ("currency",                "VARCHAR(3)",""),
        ("current_balance",         "DECIMAL(15,2)","default 0"),
        ("available_balance",       "DECIMAL(15,2)","nullable"),
        ("balance_updated_at",      "TIMESTAMPTZ","nullable"),
        ("status",                  "ENUM",   "active/inactive/closed/error"),
        ("is_internal",             "BOOLEAN","default False"),
        ("created_at",              "TIMESTAMPTZ","auto"),
        ("updated_at",              "TIMESTAMPTZ","auto"),
    ]),
    ("BankTransaction", "banking", [
        ("id",                    "UUID",   "PK"),
        ("workspace",             "UUID",   "FK→Workspace"),
        ("company",               "UUID",   "FK→Company"),
        ("account",               "UUID",   "FK→BankAccount"),
        ("external_transaction_id","TEXT",  "nullable · unique per account"),
        ("transaction_date",      "DATE",   ""),
        ("posted_date",           "DATE",   "nullable"),
        ("description",           "TEXT",   ""),
        ("reference",             "TEXT",   "nullable"),
        ("transaction_type",      "ENUM",   "debit/credit"),
        ("amount",                "DECIMAL(15,2)",""),
        ("currency",              "VARCHAR(3)",""),
        ("running_balance",       "DECIMAL(15,2)","nullable"),
        ("category",              "VARCHAR(100)","nullable · AI"),
        ("category_confidence",   "DECIMAL(5,2)","nullable"),
        ("reconciliation_status", "ENUM",   "pending/matched/unmatched/ignored"),
        ("linked_invoice",        "UUID",   "FK→Invoice · nullable"),
        ("linked_transfer_account","UUID",  "FK→BankAccount · nullable"),
        ("match_confidence",      "DECIMAL(5,2)","nullable"),
        ("matched_at",            "TIMESTAMPTZ","nullable"),
        ("matched_by",            "ENUM",   "auto/manual · nullable"),
        ("accountant_task",       "UUID",   "FK→AccountantTask · nullable"),
        ("counterparty_name",     "TEXT",   "nullable"),
        ("counterparty_account",  "TEXT",   "nullable"),
        ("notes",                 "TEXT",   "nullable"),
        ("metadata",              "JSONB",  "JSON"),
        ("created_at",            "TIMESTAMPTZ","auto"),
        ("updated_at",            "TIMESTAMPTZ","auto"),
    ]),
    ("PaymentTransaction", "banking", [
        ("id",                      "UUID",   "PK"),
        ("workspace",               "UUID",   "FK→Workspace"),
        ("company",                 "UUID",   "FK→Company"),
        ("invoice",                 "UUID",   "FK→Invoice"),
        ("direction",               "ENUM",   "inbound/outbound"),
        ("gateway",                 "VARCHAR(100)","stripe/bank_transfer/…"),
        ("gateway_transaction_id",  "TEXT",   "nullable"),
        ("gateway_status",          "ENUM",   "pending/succeeded/failed/…"),
        ("amount",                  "DECIMAL(15,2)",""),
        ("currency",                "VARCHAR(3)",""),
        ("fee_amount",              "DECIMAL(15,2)","nullable"),
        ("payment_method",          "ENUM",   "bank_transfer/card/stripe/…"),
        ("initiated_at",            "TIMESTAMPTZ","auto"),
        ("completed_at",            "TIMESTAMPTZ","nullable"),
        ("failed_at",               "TIMESTAMPTZ","nullable"),
        ("failure_reason",          "TEXT",   "nullable"),
        ("linked_bank_transaction", "UUID",   "FK→BankTransaction · nullable"),
        ("metadata",                "JSONB",  "JSON"),
        ("created_at",              "TIMESTAMPTZ","auto"),
        ("updated_at",              "TIMESTAMPTZ","auto"),
    ]),

    # ── ACCOUNTANT ───────────────────────────────────────────────────────────
    ("AccountantTask", "accountant", [
        ("id",               "UUID",   "PK"),
        ("workspace",        "UUID",   "FK→Workspace"),
        ("company",          "UUID",   "FK→Company"),
        ("task_type",        "ENUM",   "missing_invoice/unreconciled/vat_filing/…"),
        ("title",            "TEXT",   ""),
        ("description",      "TEXT",   "nullable"),
        ("status",           "ENUM",   "open/in_progress/resolved/closed"),
        ("priority",         "ENUM",   "low/medium/high/urgent"),
        ("linked_transaction","UUID",  "FK→BankTransaction · nullable"),
        ("linked_invoice",   "UUID",   "FK→Invoice · nullable"),
        ("linked_amount",    "DECIMAL(15,2)","nullable"),
        ("linked_currency",  "VARCHAR(3)","nullable"),
        ("assigned_to",      "UUID",   "nullable"),
        ("created_by_system","BOOLEAN","default False"),
        ("resolved_at",      "TIMESTAMPTZ","nullable"),
        ("resolved_by",      "TEXT",   "nullable"),
        ("resolution_notes", "TEXT",   "nullable"),
        ("due_date",         "DATE",   "nullable"),
        ("metadata",         "JSONB",  "JSON"),
        ("created_at",       "TIMESTAMPTZ","auto"),
        ("updated_at",       "TIMESTAMPTZ","auto"),
    ]),
    ("TaskDocument", "accountant", [
        ("id",             "UUID",   "PK"),
        ("task",           "UUID",   "FK→AccountantTask"),
        ("filename",       "TEXT",   ""),
        ("mime_type",      "VARCHAR(100)",""),
        ("file_size_bytes","BIGINT", "nullable"),
        ("storage_path",   "TEXT",   ""),
        ("ocr_processed",  "BOOLEAN","default False"),
        ("linked_invoice", "UUID",   "FK→Invoice · nullable"),
        ("created_at",     "TIMESTAMPTZ","auto"),
    ]),
    ("ComplianceDeadline", "accountant", [
        ("id",              "UUID",   "PK"),
        ("workspace",       "UUID",   "FK→Workspace"),
        ("company",         "UUID",   "FK→Company"),
        ("deadline_type",   "VARCHAR(100)","vat/corporation_tax/paye/…"),
        ("title",           "TEXT",   ""),
        ("due_date",        "DATE",   ""),
        ("status",          "ENUM",   "pending/due_soon/overdue/filed/cancelled"),
        ("recurrence",      "ENUM",   "none/monthly/quarterly/annually"),
        ("warning_days",    "INTEGER","default 14"),
        ("filed_at",        "TIMESTAMPTZ","nullable"),
        ("filing_reference","TEXT",   "nullable"),
        ("linked_task",     "UUID",   "FK→AccountantTask · nullable"),
        ("created_at",      "TIMESTAMPTZ","auto"),
        ("updated_at",      "TIMESTAMPTZ","auto"),
    ]),
    ("ChatMessage", "accountant", [
        ("id",              "UUID",   "PK"),
        ("workspace",       "UUID",   "FK→Workspace"),
        ("company",         "UUID",   "FK→Company · nullable"),
        ("thread_type",     "ENUM",   "task/invoice/general/…"),
        ("thread_ref_id",   "UUID",   "nullable"),
        ("sender_id",       "UUID",   ""),
        ("message_text",    "TEXT",   ""),
        ("is_read",         "BOOLEAN","default False"),
        ("has_attachments", "BOOLEAN","default False"),
        ("metadata",        "JSONB",  "JSON"),
        ("created_at",      "TIMESTAMPTZ","auto"),
        ("updated_at",      "TIMESTAMPTZ","auto"),
    ]),
    ("ChatAttachment", "accountant", [
        ("id",             "UUID",  "PK"),
        ("message",        "UUID",  "FK→ChatMessage"),
        ("filename",       "TEXT",  ""),
        ("mime_type",      "VARCHAR(100)",""),
        ("file_size_bytes","BIGINT","nullable"),
        ("storage_path",   "TEXT",  ""),
        ("created_at",     "TIMESTAMPTZ","auto"),
    ]),

    # ── GMAIL & DASHBOARD ────────────────────────────────────────────────────
    ("GmailLabelMapping", "gmail", [
        ("id",              "UUID",   "PK"),
        ("workspace",       "UUID",   "FK→Workspace"),
        ("channel",         "UUID",   "FK→ConnectedChannel"),
        ("invoice_status",  "ENUM",   "draft/pending/sent/paid/…"),
        ("gmail_label_name","TEXT",   ""),
        ("gmail_label_id",  "TEXT",   "nullable"),
        ("is_active",       "BOOLEAN","default True"),
        ("created_at",      "TIMESTAMPTZ","auto"),
        ("updated_at",      "TIMESTAMPTZ","auto"),
    ]),
    ("GmailSyncLog", "gmail", [
        ("id",               "UUID",  "PK"),
        ("channel",          "UUID",  "FK→ConnectedChannel"),
        ("direction",        "ENUM",  "invoice_to_label/label_to_invoice"),
        ("gmail_thread_id",  "TEXT",  ""),
        ("gmail_history_id", "TEXT",  "nullable"),
        ("action",           "TEXT",  ""),
        ("old_label",        "TEXT",  "nullable"),
        ("new_label",        "TEXT",  "nullable"),
        ("sync_status",      "ENUM",  "success/failed/skipped"),
        ("linked_invoice",   "UUID",  "FK→Invoice · nullable"),
        ("created_at",       "TIMESTAMPTZ","auto"),
    ]),
    ("DashboardKPICache", "gmail", [
        ("id",            "UUID",   "PK"),
        ("workspace",     "UUID",   "FK→Workspace"),
        ("company",       "UUID",   "FK→Company · nullable"),
        ("metric_name",   "VARCHAR(100)",""),
        ("metric_value",  "DECIMAL(20,4)","nullable"),
        ("metric_data",   "JSONB",  "JSON"),
        ("period_start",  "DATE",   "nullable"),
        ("period_end",    "DATE",   "nullable"),
        ("calculated_at", "TIMESTAMPTZ","auto"),
        ("expires_at",    "TIMESTAMPTZ","nullable"),
    ]),

    # ── CROSS-CUTTING ────────────────────────────────────────────────────────
    ("Notification", "cross", [
        ("id",                "UUID",   "PK"),
        ("workspace",         "UUID",   "FK→Workspace"),
        ("user_id",           "UUID",   ""),
        ("notification_type", "ENUM",   "invoice_due/payment_received/…"),
        ("title",             "VARCHAR(255)",""),
        ("body",              "TEXT",   ""),
        ("entity_type",       "VARCHAR(100)","nullable"),
        ("entity_id",         "UUID",   "nullable"),
        ("is_read",           "BOOLEAN","default False"),
        ("read_at",           "TIMESTAMPTZ","nullable"),
        ("created_at",        "TIMESTAMPTZ","auto"),
    ]),
    ("AuditLog", "cross", [
        ("id",          "UUID",   "PK"),
        ("workspace",   "UUID",   "FK→Workspace"),
        ("user_id",     "UUID",   "nullable"),
        ("action",      "VARCHAR(100)",""),
        ("entity_type", "VARCHAR(100)",""),
        ("entity_id",   "UUID",   "nullable"),
        ("old_values",  "JSONB",  "JSON"),
        ("new_values",  "JSONB",  "JSON"),
        ("ip_address",  "INET",   "nullable"),
        ("user_agent",  "TEXT",   "nullable"),
        ("created_at",  "TIMESTAMPTZ","auto"),
    ]),
]

# ──────────────────────────────────────────────────────────────────────────────
# MODULE METADATA  — display order, title, description
# ──────────────────────────────────────────────────────────────────────────────
MODULES = [
    ("core",         "Core / IAM",           "Profiles, Workspaces, Companies, Members, RBAC"),
    ("integrations", "Integrations",          "OAuth channels, Open Banking, Tax Authorities, Google Drive"),
    ("counterparts", "Counterparts",           "Unified vendor & customer directory with risk scoring"),
    ("inbox",        "Smart Inbox",           "Unified multi-channel inbox with AI classification & OCR"),
    ("invoices",     "Invoices (AP & AR)",    "Purchase payables + Sales receivables, dunning, dispatch"),
    ("banking",      "Banking Hub",           "Bank accounts, transactions, reconciliation, payments"),
    ("accountant",   "Accountant Hub",        "Tasks, documents, compliance, AI chat"),
    ("gmail",        "Gmail & Dashboard",     "Gmail add-on label sync, KPI cache"),
    ("cross",        "Cross-cutting",         "Notifications, immutable audit log"),
]

# ──────────────────────────────────────────────────────────────────────────────
# KEY CROSS-TABLE RELATIONSHIPS  (for the relationships reference page)
# ──────────────────────────────────────────────────────────────────────────────
RELATIONSHIPS = [
    ("Profile",          "Workspace",         "owner_id",                    "1:N"),
    ("Workspace",        "Company",           "workspace",                   "1:N"),
    ("Workspace",        "WorkspaceMember",   "workspace",                   "1:N"),
    ("Workspace",        "RolePermission",    "workspace",                   "1:N"),
    ("Workspace",        "WorkspacePreference","workspace",                  "1:N"),
    ("Company",          "ConnectedChannel",  "company",                     "1:N"),
    ("Company",          "BankConnection",    "company",                     "1:N"),
    ("Company",          "TaxAuthorityIntegration","company",                "1:N"),
    ("Company",          "GDriveConnection",  "company",                     "1:N"),
    ("Company",          "Counterpart",       "company",                     "1:N"),
    ("Company",          "Invoice",           "company",                     "1:N"),
    ("Company",          "BankAccount",       "company",                     "1:N"),
    ("Company",          "AccountantTask",    "company",                     "1:N"),
    ("Counterpart",      "Invoice",           "counterpart",                 "1:N"),
    ("Counterpart",      "CounterpartAuditLog","counterpart",                "1:N"),
    ("ConnectedChannel", "InboxMessage",      "channel",                     "1:N"),
    ("ConnectedChannel", "GmailLabelMapping", "channel",                     "1:N"),
    ("ConnectedChannel", "GmailSyncLog",      "channel",                     "1:N"),
    ("InboxMessage",     "InboxAttachment",   "message",                     "1:N"),
    ("InboxMessage",     "Invoice",           "source_message",              "1:N"),
    ("Invoice",          "InvoiceLineItem",   "invoice",                     "1:N"),
    ("Invoice",          "InvoiceStatusHistory","invoice",                   "1:N"),
    ("Invoice",          "InvoiceCommunication","invoice",                   "1:N"),
    ("Invoice",          "BankTransaction",   "linked_invoice",              "1:N"),
    ("Invoice",          "PaymentTransaction","invoice",                     "1:N"),
    ("Invoice",          "GmailSyncLog",      "linked_invoice",              "1:N"),
    ("BankConnection",   "BankAccount",       "connection",                  "1:N"),
    ("BankAccount",      "BankTransaction",   "account",                     "1:N"),
    ("BankTransaction",  "AccountantTask",    "accountant_task",             "N:1"),
    ("AccountantTask",   "TaskDocument",      "task",                        "1:N"),
    ("AccountantTask",   "ComplianceDeadline","linked_task",                 "1:1"),
    ("ChatMessage",      "ChatAttachment",    "message",                     "1:N"),
]

# ──────────────────────────────────────────────────────────────────────────────
# PDF DRAWING HELPERS
# ──────────────────────────────────────────────────────────────────────────────

PAGE_W, PAGE_H = landscape(A3)   # 420 × 297 mm in points  → ~1191 × 842 pt
MARGIN = 20 * mm
FONT_BOLD   = "Helvetica-Bold"
FONT_NORMAL = "Helvetica"
FONT_SMALL  = "Helvetica-Oblique"

def note_color(note: str) -> HexColor:
    if "PK" in note:        return C["pk_text"]
    if "FK→" in note:       return C["fk_text"]
    if "encrypted" in note: return HexColor("#E67E22")
    if "JSON" in note:      return HexColor("#27AE60")
    if "@property" in note: return HexColor("#8E44AD")
    return C["field_text"]

def draw_table_box(c, x, y, width, name, module_key, fields, max_height=None):
    """
    Draw a single ER table box at (x, y) [bottom-left].
    Returns the actual height used.
    """
    header_h = 14
    row_h    = 10
    pad      = 3

    total_h = header_h + len(fields) * row_h + pad * 2

    # clamp if needed
    if max_height and total_h > max_height:
        max_fields = int((max_height - header_h - pad * 2) / row_h)
        fields     = fields[:max_fields] + [("…", "", f"({len(fields) - max_fields} more fields)")]
        total_h    = height = header_h + len(fields) * row_h + pad * 2
    else:
        height = total_h

    col_color = C[module_key]

    # shadow
    c.setFillColor(HexColor("#CCCCCC"))
    c.setStrokeColor(HexColor("#CCCCCC"))
    c.roundRect(x + 2, y - height - 2, width, height, 4, fill=1, stroke=0)

    # body background
    c.setFillColor(colors.white)
    c.setStrokeColor(C["border"])
    c.setLineWidth(0.5)
    c.roundRect(x, y - height, width, height, 4, fill=1, stroke=1)

    # header band
    c.setFillColor(col_color)
    c.roundRect(x, y - header_h, width, header_h, 4, fill=1, stroke=0)
    # square off bottom corners of header
    c.rect(x, y - header_h, width, header_h / 2, fill=1, stroke=0)

    # table name
    c.setFillColor(C["header_text"])
    c.setFont(FONT_BOLD, 7)
    c.drawCentredString(x + width / 2, y - header_h + 4, name)

    # fields
    fy = y - header_h - pad
    name_w   = width * 0.38
    type_w   = width * 0.30
    note_w   = width * 0.32

    for fname, ftype, fnote in fields:
        fy -= row_h
        # zebra stripe
        if fields.index((fname, ftype, fnote)) % 2 == 0:
            c.setFillColor(HexColor("#F0F4F8"))
            c.rect(x + 1, fy, width - 2, row_h, fill=1, stroke=0)

        txt_y = fy + 2.5
        # field name
        fc = note_color(fnote)
        c.setFillColor(fc)
        c.setFont(FONT_BOLD if ("PK" in fnote or "FK" in fnote) else FONT_NORMAL, 5.5)
        c.drawString(x + 4, txt_y, fname[:22])
        # type
        c.setFillColor(HexColor("#555555"))
        c.setFont(FONT_NORMAL, 5)
        c.drawString(x + 4 + name_w, txt_y, ftype[:16])
        # note
        c.setFillColor(note_color(fnote))
        c.setFont(FONT_SMALL, 4.5)
        c.drawString(x + 4 + name_w + type_w, txt_y, fnote[:24])

    # bottom border line
    c.setStrokeColor(C["border"])
    c.setLineWidth(0.5)
    c.line(x, y - height, x + width, y - height)

    return height

def draw_title_page(c):
    c.setPageSize(landscape(A3))
    w, h = PAGE_W, PAGE_H

    # Background
    c.setFillColor(C["title_bg"])
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Accent stripe
    c.setFillColor(C["core"])
    c.rect(0, h * 0.52, w, 6, fill=1, stroke=0)

    # Title
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 48)
    c.drawCentredString(w / 2, h * 0.62, "SOLOHUB")
    c.setFont(FONT_NORMAL, 22)
    c.setFillColor(C["subtitle"])
    c.drawCentredString(w / 2, h * 0.56, "Database Schema — Visual Reference")
    c.setFont(FONT_NORMAL, 12)
    c.setFillColor(HexColor("#888888"))
    c.drawCentredString(w / 2, h * 0.51, "AI-Native Business Engine for Solopreneurs")

    # Stats row
    stats = [
        ("32", "Tables"),
        ("9",  "Modules"),
        ("22", "Enum Types"),
        ("60+","Indexes"),
        ("7",  "DB Triggers"),
        ("6",  "Views"),
    ]
    sw = w / len(stats)
    sy = h * 0.38
    for i, (num, label) in enumerate(stats):
        sx = i * sw + sw / 2
        c.setFillColor(C[list(C.keys())[i]])
        c.setFont(FONT_BOLD, 28)
        c.drawCentredString(sx, sy, num)
        c.setFillColor(C["subtitle"])
        c.setFont(FONT_NORMAL, 10)
        c.drawCentredString(sx, sy - 16, label)

    # Module list
    c.setFillColor(C["subtitle"])
    c.setFont(FONT_BOLD, 11)
    c.drawCentredString(w / 2, h * 0.30, "MODULES")
    c.setStrokeColor(HexColor("#444444"))
    c.setLineWidth(0.5)
    c.line(w * 0.2, h * 0.285, w * 0.8, h * 0.285)

    row_y = h * 0.265
    col_keys = list(C.keys())
    for idx, (key, title, desc) in enumerate(MODULES):
        dot_x = MARGIN + (idx % 3) * (w - MARGIN * 2) / 3 + 10
        dot_y = row_y - (idx // 3) * 18 + 5
        num_lt = len([t for t in TABLES if t[1] == key])
        c.setFillColor(C[key])
        c.circle(dot_x - 6, dot_y + 2, 4, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont(FONT_BOLD, 7)
        c.drawString(dot_x - 9, dot_y + 4 - 3, str(num_lt))
        c.setFillColor(C["subtitle"])
        c.setFont(FONT_BOLD, 9)
        c.drawString(dot_x + 2, dot_y + 1, title)
        c.setFillColor(HexColor("#666666"))
        c.setFont(FONT_NORMAL, 7.5)
        c.drawString(dot_x + 2, dot_y - 9, desc)

    # Footer
    c.setFillColor(HexColor("#333333"))
    c.setFont(FONT_NORMAL, 8)
    c.drawCentredString(w / 2, 18, "Generated: March 2026  ·  Supabase PostgreSQL + Django ORM  ·  SoloHub v1.0")

    c.showPage()

def draw_module_page(c, module_key, module_title, module_desc, tables_in_module):
    """Lay out all tables for one module across the A3 landscape page."""
    c.setPageSize(landscape(A3))
    w, h = PAGE_W, PAGE_H

    # Page background
    c.setFillColor(C["bg"])
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Top header bar
    bar_h = 32
    c.setFillColor(C[module_key])
    c.rect(0, h - bar_h, w, bar_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 16)
    c.drawString(MARGIN, h - 22, module_title)
    c.setFont(FONT_NORMAL, 9)
    c.setFillColor(HexColor("#DDDDDD"))
    c.drawString(MARGIN, h - 30, module_desc)
    # table count badge
    badge_txt = f"{len(tables_in_module)} table{'s' if len(tables_in_module) != 1 else ''}"
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 9)
    c.drawRightString(w - MARGIN, h - 22, badge_txt)

    # Grid layout
    usable_w = w - MARGIN * 2
    usable_h = h - bar_h - MARGIN * 2 - 12

    n = len(tables_in_module)
    # choose columns to keep tables reasonably wide
    cols = min(n, 4) if n > 2 else n
    rows = (n + cols - 1) // cols

    cell_w  = (usable_w - (cols - 1) * 8) / cols
    cell_h  = (usable_h - (rows - 1) * 8) / rows

    start_y = h - bar_h - MARGIN

    for idx, (tname, tmod, tfields) in enumerate(tables_in_module):
        col = idx % cols
        row = idx // cols
        tx = MARGIN + col * (cell_w + 8)
        ty = start_y - row * (cell_h + 8)
        draw_table_box(c, tx, ty, cell_w, tname, tmod, tfields, max_height=cell_h)

    # footer
    c.setFillColor(HexColor("#AAAAAA"))
    c.setFont(FONT_NORMAL, 7)
    c.drawCentredString(w / 2, 10, f"SoloHub DB Schema  ·  {module_title}")

    c.showPage()

def draw_relationships_page(c):
    """One page listing all key FK relationships."""
    c.setPageSize(landscape(A3))
    w, h = PAGE_W, PAGE_H

    c.setFillColor(C["bg"])
    c.rect(0, 0, w, h, fill=1, stroke=0)

    bar_h = 32
    c.setFillColor(C["cross"])
    c.rect(0, h - bar_h, w, bar_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 16)
    c.drawString(MARGIN, h - 22, "Foreign Key Relationships")
    c.setFont(FONT_NORMAL, 9)
    c.setFillColor(HexColor("#DDDDDD"))
    c.drawString(MARGIN, h - 30, "All cross-table references in the SoloHub schema")

    # column headers
    col_x = [MARGIN, MARGIN + 110, MARGIN + 220, MARGIN + 340, MARGIN + 430]
    hy = h - bar_h - 18
    for hd, cx in zip(["Parent Table", "Child Table", "FK Column", "Cardinality", "Module"], col_x):
        c.setFillColor(HexColor("#2C3E50"))
        c.setFont(FONT_BOLD, 8)
        c.drawString(cx, hy, hd)
    c.setStrokeColor(HexColor("#BDC3C7"))
    c.setLineWidth(0.7)
    c.line(MARGIN, hy - 3, w - MARGIN, hy - 3)

    ry = hy - 14
    for i, (parent, child, fk_col, card) in enumerate(RELATIONSHIPS):
        if ry < MARGIN + 20:
            break  # prevent overflow (could paginate if needed)
        # find module of child
        mod = next((t[1] for t in TABLES if t[0] == child), "cross")
        if i % 2 == 0:
            c.setFillColor(HexColor("#EDF2F7"))
            c.rect(MARGIN, ry - 2, w - MARGIN * 2, 11, fill=1, stroke=0)

        c.setFillColor(C["pk_text"])
        c.setFont(FONT_BOLD, 7.5)
        c.drawString(col_x[0], ry, parent)
        c.setFillColor(C["fk_text"])
        c.drawString(col_x[1], ry, child)
        c.setFillColor(HexColor("#444444"))
        c.setFont(FONT_NORMAL, 7.5)
        c.drawString(col_x[2], ry, fk_col)
        c.setFillColor(HexColor("#888888"))
        c.drawString(col_x[3], ry, card)
        c.setFillColor(C[mod])
        c.setFont(FONT_BOLD, 7)
        mod_label = next((m[1] for m in MODULES if m[0] == mod), mod)
        c.drawString(col_x[4], ry, mod_label)
        ry -= 13

    # ── Second column if list is long ──────────────────────────────────────
    # (already handled by stopping at MARGIN, single column is fine for ~32 rows)

    # Legend
    lx = w * 0.56
    c.setFillColor(HexColor("#2C3E50"))
    c.setFont(FONT_BOLD, 9)
    c.drawString(lx, h - bar_h - 18, "Legend")
    c.setStrokeColor(HexColor("#BDC3C7"))
    c.line(lx, h - bar_h - 21, lx + 200, h - bar_h - 21)
    legend_items = [
        (C["pk_text"],         "Primary Key  (PK)"),
        (C["fk_text"],         "Foreign Key  (FK→Table)"),
        (HexColor("#E67E22"),  "Encrypted field  (write-only over API)"),
        (HexColor("#27AE60"),  "JSONB / JSON column"),
        (HexColor("#8E44AD"),  "@property  (computed, not stored)"),
    ]
    for ii, (col, label) in enumerate(legend_items):
        ly = h - bar_h - 35 - ii * 16
        c.setFillColor(col)
        c.roundRect(lx, ly, 10, 9, 2, fill=1, stroke=0)
        c.setFillColor(HexColor("#2C3E50"))
        c.setFont(FONT_NORMAL, 8)
        c.drawString(lx + 14, ly + 1, label)

    # Module colour key
    c.setFont(FONT_BOLD, 9)
    c.drawString(lx, h - bar_h - 130, "Module Colours")
    c.setStrokeColor(HexColor("#BDC3C7"))
    c.line(lx, h - bar_h - 133, lx + 200, h - bar_h - 133)
    for ii, (key, title, _) in enumerate(MODULES):
        my = h - bar_h - 148 - ii * 14
        c.setFillColor(C[key])
        c.roundRect(lx, my, 10, 9, 2, fill=1, stroke=0)
        c.setFillColor(HexColor("#2C3E50"))
        c.setFont(FONT_NORMAL, 8)
        c.drawString(lx + 14, my + 1, title)

    c.setFillColor(HexColor("#AAAAAA"))
    c.setFont(FONT_NORMAL, 7)
    c.drawCentredString(w / 2, 10, "SoloHub DB Schema  ·  Foreign Key Relationships")
    c.showPage()

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def generate():
    os.makedirs("database", exist_ok=True)
    output = "database/SoloHub_Database_Schema.pdf"
    cv = canvas.Canvas(output, pagesize=landscape(A3))
    cv.setTitle("SoloHub Database Schema")
    cv.setAuthor("SoloHub")
    cv.setSubject("Visual Database Schema — 32 Tables, 9 Modules")

    # 1 — Title page
    draw_title_page(cv)

    # 2 — One page per module
    for mod_key, mod_title, mod_desc in MODULES:
        tables_in_mod = [(n, m, f) for n, m, f in TABLES if m == mod_key]
        if tables_in_mod:
            draw_module_page(cv, mod_key, mod_title, mod_desc, tables_in_mod)

    # 3 — FK Relationships reference page
    draw_relationships_page(cv)

    cv.save()
    print(f"✅  PDF generated → {os.path.abspath(output)}")
    print(f"   Pages: {len(MODULES) + 2}  (title + {len(MODULES)} modules + relationships)")
    print(f"   Tables: {len(TABLES)}  across {len(MODULES)} modules")

if __name__ == "__main__":
    generate()
