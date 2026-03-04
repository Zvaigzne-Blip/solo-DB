"""
SoloHub Django Admin — All 32 models registered with rich configuration.
Access: http://127.0.0.1:8000/admin/
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    # Core / IAM
    Profile, Workspace, Company, WorkspaceMember, RolePermission, WorkspacePreference,
    # Integrations
    ConnectedChannel, BankConnection, TaxAuthorityIntegration, GDriveConnection,
    # Counterparts
    Counterpart, CounterpartAuditLog,
    # Inbox
    InboxMessage, InboxAttachment,
    # Invoices
    Invoice, InvoiceLineItem, InvoiceStatusHistory, InvoiceCommunication, DunningRule,
    # Banking
    BankAccount, BankTransaction, PaymentTransaction,
    # Accountant
    AccountantTask, TaskDocument, ComplianceDeadline, ChatMessage, ChatAttachment,
    # Gmail & Dashboard
    GmailLabelMapping, GmailSyncLog, DashboardKPICache, Notification, AuditLog,
)


# ─────────────────────────────────────────────────────────────────────────────
# Admin site branding
# ─────────────────────────────────────────────────────────────────────────────
admin.site.site_header = 'SoloHub Administration'
admin.site.site_title = 'SoloHub Admin'
admin.site.index_title = 'SoloHub — Autonomous Business Engine'


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Core / IAM
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'display_name', 'phone', 'timezone', 'onboarding_completed', 'created_at')
    search_fields = ('full_name', 'display_name', 'phone')
    list_filter = ('onboarding_completed', 'timezone')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner_id', 'base_currency', 'timezone', 'is_active', 'created_at')
    search_fields = ('name', 'slug')
    list_filter = ('is_active', 'base_currency', 'timezone')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('legal_name', 'trade_name', 'workspace', 'tax_id', 'country_code', 'base_currency', 'is_default', 'is_individual')
    search_fields = ('legal_name', 'trade_name', 'tax_id', 'email')
    list_filter = ('is_default', 'is_individual', 'base_currency', 'country_code')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('workspace',)
    ordering = ('workspace', 'legal_name')


@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(admin.ModelAdmin):
    list_display = ('email', 'workspace', 'role', 'status', 'invited_at', 'joined_at')
    search_fields = ('email',)
    list_filter = ('role', 'status')
    readonly_fields = ('id', 'invited_at', 'created_at', 'updated_at')
    list_select_related = ('workspace',)
    ordering = ('workspace', 'role', 'email')


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'resource', 'action', 'is_allowed')
    search_fields = ('resource', 'action')
    list_filter = ('role', 'is_allowed')
    ordering = ('role', 'resource', 'action')


@admin.register(WorkspacePreference)
class WorkspacePreferenceAdmin(admin.ModelAdmin):
    list_display = ('workspace', 'key', 'value', 'updated_at')
    search_fields = ('key',)
    list_select_related = ('workspace',)
    ordering = ('workspace', 'key')


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Integrations
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(ConnectedChannel)
class ConnectedChannelAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'channel_type', 'workspace', 'company', 'account_identifier', 'status', 'last_sync_at')
    search_fields = ('display_name', 'account_identifier')
    list_filter = ('channel_type', 'status')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('workspace', 'company')
    ordering = ('workspace', 'channel_type')


@admin.register(BankConnection)
class BankConnectionAdmin(admin.ModelAdmin):
    list_display = ('institution_name', 'provider', 'company', 'status', 'supports_ais', 'supports_pis', 'consent_expires_at', 'last_sync_at')
    search_fields = ('institution_name', 'provider')
    list_filter = ('status', 'provider', 'supports_ais', 'supports_pis')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('workspace', 'company')


@admin.register(TaxAuthorityIntegration)
class TaxAuthorityIntegrationAdmin(admin.ModelAdmin):
    list_display = ('authority_name', 'authority_code', 'region', 'company', 'status', 'tax_reference')
    search_fields = ('authority_name', 'authority_code', 'tax_reference')
    list_filter = ('authority_code', 'status', 'region')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('company',)


@admin.register(GDriveConnection)
class GDriveConnectionAdmin(admin.ModelAdmin):
    list_display = ('company', 'workspace', 'status', 'source_folder_id', 'destination_folder_id', 'last_sync_at')
    list_filter = ('status',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('workspace', 'company')


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Counterparts
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Counterpart)
class CounterpartAdmin(admin.ModelAdmin):
    list_display = ('name', 'counterpart_type', 'company', 'email', 'phone', 'country_code',
                    'fraud_risk_score', 'credit_risk_score', 'total_invoices', 'total_paid', 'is_active')
    search_fields = ('name', 'legal_name', 'email', 'tax_id')
    list_filter = ('counterpart_type', 'is_active', 'country_code', 'fraud_risk_score', 'credit_risk_score')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('workspace', 'company')
    ordering = ('name',)
    fieldsets = (
        ('Identity', {'fields': ('name', 'legal_name', 'counterpart_type', 'workspace', 'company')}),
        ('Contact', {'fields': ('email', 'phone', 'tax_id')}),
        ('Address', {'fields': ('address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country_code')}),
        ('Bank Details', {'fields': ('bank_name', 'bank_account_number_encrypted', 'bank_routing_number_encrypted', 'bank_iban_encrypted', 'bank_swift', 'bank_currency'), 'classes': ('collapse',)}),
        ('Terms & Risk', {'fields': ('payment_terms_days', 'default_currency', 'fraud_risk_score', 'credit_risk_score')}),
        ('Statistics', {'fields': ('total_invoices', 'total_paid', 'avg_payment_days', 'last_invoice_date'), 'classes': ('collapse',)}),
        ('Meta', {'fields': ('notes', 'is_active', 'metadata', 'created_at', 'updated_at')}),
    )


@admin.register(CounterpartAuditLog)
class CounterpartAuditLogAdmin(admin.ModelAdmin):
    list_display = ('counterpart', 'field_name', 'old_value', 'new_value', 'changed_by', 'changed_at')
    search_fields = ('field_name', 'old_value', 'new_value')
    list_filter = ('field_name',)
    readonly_fields = ('id', 'changed_at')
    list_select_related = ('counterpart',)
    ordering = ('-changed_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — Smart Inbox
# ─────────────────────────────────────────────────────────────────────────────

class InboxAttachmentInline(admin.TabularInline):
    model = InboxAttachment
    extra = 0
    readonly_fields = ('id', 'ocr_status', 'ocr_confidence', 'ocr_processed_at', 'content_hash', 'is_duplicate', 'created_at')
    fields = ('filename', 'mime_type', 'file_size_bytes', 'ocr_status', 'ocr_confidence', 'is_duplicate')


@admin.register(InboxMessage)
class InboxMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'source', 'sender_email', 'classification', 'processing_status',
                    'linked_invoice', 'is_read', 'received_at')
    search_fields = ('subject', 'sender_email', 'sender_name', 'body_preview')
    list_filter = ('source', 'classification', 'processing_status', 'is_read', 'is_starred')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('workspace', 'company', 'linked_invoice', 'linked_counterpart')
    ordering = ('-received_at',)
    inlines = [InboxAttachmentInline]
    fieldsets = (
        ('Source', {'fields': ('workspace', 'company', 'channel', 'source', 'external_message_id', 'external_thread_id')}),
        ('Message', {'fields': ('sender_email', 'sender_name', 'sender_phone', 'subject', 'body_preview', 'received_at')}),
        ('Classification (AI)', {'fields': ('classification', 'classification_confidence', 'classified_at')}),
        ('Processing Pipeline', {'fields': ('processing_status', 'processing_error')}),
        ('Links', {'fields': ('linked_invoice', 'linked_counterpart')}),
        ('Gmail Sync', {'fields': ('gmail_label', 'gmail_label_synced_at')}),
        ('Flags', {'fields': ('is_read', 'is_starred', 'metadata')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(InboxAttachment)
class InboxAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'message', 'mime_type', 'file_size_bytes', 'ocr_status', 'ocr_confidence', 'is_duplicate')
    search_fields = ('filename', 'content_hash')
    list_filter = ('ocr_status', 'is_duplicate', 'mime_type')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('message',)
    ordering = ('-created_at',)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — Invoices (Modules 2 & 3)
# ─────────────────────────────────────────────────────────────────────────────

class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 1
    fields = ('position', 'description', 'quantity', 'unit_price', 'tax_rate', 'discount_percent', 'line_total')
    readonly_fields = ('line_total',)


class InvoiceStatusHistoryInline(admin.TabularInline):
    model = InvoiceStatusHistory
    extra = 0
    readonly_fields = ('id', 'old_status', 'new_status', 'changed_by', 'change_reason', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False


class InvoiceCommunicationInline(admin.TabularInline):
    model = InvoiceCommunication
    extra = 0
    readonly_fields = ('id', 'sent_at', 'delivered_at', 'read_at', 'created_at')
    fields = ('channel', 'recipient', 'status', 'is_dunning', 'dunning_level', 'sent_at', 'delivered_at', 'read_at')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'direction', 'contact_name', 'company',
                    'status', 'total_amount', 'amount_paid', 'amount_due_display',
                    'currency', 'issue_date', 'due_date', 'fraud_risk_score', 'credit_risk_score')
    search_fields = ('invoice_number', 'reference_number', 'contact_name', 'contact_email')
    list_filter = ('direction', 'status', 'source', 'currency', 'fraud_risk_score', 'credit_risk_score')
    readonly_fields = ('id', 'amount_due', 'created_at', 'updated_at')
    list_select_related = ('workspace', 'company', 'counterpart')
    ordering = ('-created_at',)
    inlines = [InvoiceLineItemInline, InvoiceStatusHistoryInline, InvoiceCommunicationInline]
    date_hierarchy = 'issue_date'
    fieldsets = (
        ('Type & Reference', {'fields': ('workspace', 'company', 'direction', 'source', 'invoice_number', 'reference_number')}),
        ('Parties', {'fields': ('counterpart', 'contact_name', 'contact_email', 'contact_address')}),
        ('Dates', {'fields': ('issue_date', 'due_date', 'payment_terms_days')}),
        ('Amounts', {'fields': ('currency', 'subtotal', 'tax_amount', 'tax_rate', 'discount_amount', 'total_amount', 'amount_paid', 'amount_due', 'fx_rate', 'base_currency_total')}),
        ('Status & Risk', {'fields': ('status', 'fraud_risk_score', 'fraud_risk_flags', 'credit_risk_score')}),
        ('Source Document', {'fields': ('source_message', 'original_file_url', 'original_file_bucket')}),
        ('Dispatch (Sales)', {'fields': ('dispatch_channel', 'dispatched_at', 'delivered_at', 'read_at')}),
        ('Reconciliation', {'fields': ('reconciled_at', 'reconciled_transaction', 'reconciliation_confidence')}),
        ('Payment (Purchase)', {'fields': ('payment_method', 'payment_reference', 'payment_executed_at', 'payment_gateway_id')}),
        ('GDrive Archive', {'fields': ('gdrive_file_id', 'gdrive_saved_at')}),
        ('Gmail Sync', {'fields': ('gmail_thread_id', 'gmail_label')}),
        ('Dunning (Sales)', {'fields': ('dunning_enabled', 'dunning_last_sent_at', 'dunning_count', 'dunning_next_at')}),
        ('Approval', {'fields': ('approved_by', 'approved_at')}),
        ('Notes & Meta', {'fields': ('notes', 'metadata', 'created_by', 'created_at', 'updated_at')}),
    )

    @admin.display(description='Amount Due')
    def amount_due_display(self, obj):
        due = obj.amount_due
        color = 'red' if due > 0 else 'green'
        return format_html('<span style="color:{}">{} {}</span>', color, obj.currency, due)


@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'position', 'description', 'quantity', 'unit_price', 'tax_rate', 'line_total')
    search_fields = ('description', 'category', 'account_code')
    list_filter = ('category',)
    list_select_related = ('invoice',)
    ordering = ('invoice', 'position')


@admin.register(InvoiceStatusHistory)
class InvoiceStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'old_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('old_status', 'new_status')
    readonly_fields = ('id', 'created_at')
    list_select_related = ('invoice',)
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(InvoiceCommunication)
class InvoiceCommunicationAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'channel', 'recipient', 'status', 'is_dunning', 'dunning_level', 'sent_at', 'delivered_at', 'read_at')
    search_fields = ('recipient', 'subject')
    list_filter = ('channel', 'status', 'is_dunning')
    readonly_fields = ('id', 'created_at')
    list_select_related = ('invoice',)
    ordering = ('-created_at',)


@admin.register(DunningRule)
class DunningRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'workspace', 'company', 'days_after_due', 'channel', 'dunning_level', 'is_active')
    search_fields = ('name',)
    list_filter = ('channel', 'dunning_level', 'is_active')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('days_after_due', 'dunning_level')


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — Banking Hub (Module 4)
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'institution_name', 'company', 'account_type',
                    'account_number_masked', 'currency', 'current_balance', 'available_balance',
                    'status', 'balance_updated_at')
    search_fields = ('account_name', 'institution_name', 'account_number_masked')
    list_filter = ('account_type', 'status', 'currency', 'is_internal')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('workspace', 'company', 'connection')
    ordering = ('company', 'institution_name')


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_date', 'description', 'account', 'transaction_type',
                    'amount', 'currency', 'category', 'reconciliation_status',
                    'linked_invoice', 'counterparty_name')
    search_fields = ('description', 'reference', 'counterparty_name', 'external_transaction_id')
    list_filter = ('transaction_type', 'category', 'reconciliation_status', 'currency', 'matched_by')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('account', 'company', 'linked_invoice', 'accountant_task')
    ordering = ('-transaction_date',)
    date_hierarchy = 'transaction_date'
    fieldsets = (
        ('Transaction', {'fields': ('workspace', 'company', 'account', 'external_transaction_id')}),
        ('Details', {'fields': ('transaction_date', 'posted_date', 'value_date', 'description', 'reference', 'transaction_type', 'amount', 'currency', 'running_balance')}),
        ('Auto-Categorization', {'fields': ('category', 'category_confidence')}),
        ('Reconciliation (Matcher)', {'fields': ('reconciliation_status', 'linked_invoice', 'linked_transfer_account', 'match_confidence', 'matched_at', 'matched_by')}),
        ('Gap Analysis', {'fields': ('accountant_task',)}),
        ('Counterparty', {'fields': ('counterparty_name', 'counterparty_account')}),
        ('Notes & Meta', {'fields': ('notes', 'metadata', 'created_at', 'updated_at')}),
    )


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'direction', 'gateway', 'amount', 'currency', 'fee_amount',
                    'payment_method', 'gateway_status', 'initiated_at', 'completed_at')
    search_fields = ('gateway_transaction_id', 'gateway')
    list_filter = ('direction', 'gateway', 'gateway_status', 'payment_method', 'currency')
    readonly_fields = ('id', 'initiated_at', 'created_at', 'updated_at')
    list_select_related = ('invoice', 'company', 'linked_bank_transaction')
    ordering = ('-initiated_at',)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — Accountant Hub (Module 5)
# ─────────────────────────────────────────────────────────────────────────────

class TaskDocumentInline(admin.TabularInline):
    model = TaskDocument
    extra = 0
    readonly_fields = ('id', 'ocr_processed', 'created_at')
    fields = ('filename', 'mime_type', 'file_size_bytes', 'storage_path', 'ocr_processed', 'linked_invoice')


@admin.register(AccountantTask)
class AccountantTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task_type', 'company', 'status', 'priority',
                    'linked_amount', 'linked_currency', 'assigned_to', 'due_date', 'created_by_system', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('task_type', 'status', 'priority', 'created_by_system')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('workspace', 'company', 'linked_transaction', 'linked_invoice')
    ordering = ('-created_at',)
    inlines = [TaskDocumentInline]
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Task', {'fields': ('workspace', 'company', 'task_type', 'title', 'description', 'status', 'priority')}),
        ('Linked Entities', {'fields': ('linked_transaction', 'linked_invoice', 'linked_amount', 'linked_currency')}),
        ('Assignment', {'fields': ('assigned_to', 'created_by_system')}),
        ('Resolution', {'fields': ('resolved_at', 'resolved_by', 'resolution_notes')}),
        ('Due & Meta', {'fields': ('due_date', 'metadata', 'created_at', 'updated_at')}),
    )


@admin.register(TaskDocument)
class TaskDocumentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'task', 'mime_type', 'file_size_bytes', 'ocr_processed', 'linked_invoice', 'created_at')
    search_fields = ('filename',)
    list_filter = ('ocr_processed', 'mime_type')
    readonly_fields = ('id', 'created_at')
    list_select_related = ('task', 'linked_invoice')


@admin.register(ComplianceDeadline)
class ComplianceDeadlineAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'deadline_type', 'due_date', 'status', 'recurrence',
                    'warning_days', 'filed_at', 'filing_reference')
    search_fields = ('title', 'deadline_type', 'filing_reference')
    list_filter = ('status', 'recurrence', 'deadline_type')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('workspace', 'company', 'linked_task')
    ordering = ('due_date',)
    date_hierarchy = 'due_date'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('thread_type', 'thread_ref_id', 'sender_id', 'workspace', 'company',
                    'is_read', 'has_attachments', 'created_at')
    search_fields = ('message_text',)
    list_filter = ('thread_type', 'is_read', 'has_attachments')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('workspace', 'company')
    ordering = ('-created_at',)


@admin.register(ChatAttachment)
class ChatAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'message', 'mime_type', 'file_size_bytes', 'created_at')
    search_fields = ('filename',)
    readonly_fields = ('id', 'created_at')
    list_select_related = ('message',)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — Gmail Add-on & Dashboard (Modules 7 & 8)
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(GmailLabelMapping)
class GmailLabelMappingAdmin(admin.ModelAdmin):
    list_display = ('workspace', 'channel', 'invoice_status', 'gmail_label_name', 'gmail_label_id', 'is_active')
    search_fields = ('gmail_label_name', 'gmail_label_id')
    list_filter = ('invoice_status', 'is_active')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('workspace', 'channel')


@admin.register(GmailSyncLog)
class GmailSyncLogAdmin(admin.ModelAdmin):
    list_display = ('channel', 'direction', 'gmail_thread_id', 'action', 'old_label', 'new_label',
                    'sync_status', 'linked_invoice', 'created_at')
    search_fields = ('gmail_thread_id', 'gmail_history_id', 'action', 'old_label', 'new_label')
    list_filter = ('direction', 'sync_status')
    readonly_fields = ('id', 'created_at')
    list_select_related = ('channel', 'linked_invoice')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DashboardKPICache)
class DashboardKPICacheAdmin(admin.ModelAdmin):
    list_display = ('workspace', 'company', 'metric_name', 'metric_value', 'period_start', 'period_end', 'calculated_at', 'expires_at')
    search_fields = ('metric_name',)
    list_filter = ('metric_name',)
    readonly_fields = ('id', 'calculated_at')
    list_select_related = ('workspace', 'company')
    ordering = ('-calculated_at',)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9 — Cross-cutting
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'workspace', 'user_id', 'entity_type',
                    'is_read', 'created_at')
    search_fields = ('title', 'body')
    list_filter = ('notification_type', 'is_read', 'entity_type')
    readonly_fields = ('id', 'created_at')
    list_select_related = ('workspace',)
    ordering = ('-created_at',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'entity_type', 'entity_id', 'workspace', 'user_id', 'ip_address', 'created_at')
    search_fields = ('action', 'entity_type', 'user_id')
    list_filter = ('action', 'entity_type')
    readonly_fields = ('id', 'created_at')
    list_select_related = ('workspace',)
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False  # immutable log
