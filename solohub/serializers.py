"""
SoloHub DRF Serializers — ModelSerializer for all 32 models, grouped by module.
Nested read serializers expose related objects; write serializers accept PKs.
"""
from rest_framework import serializers

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
# SECTION 1 — Core / IAM
# ─────────────────────────────────────────────────────────────────────────────

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class CompanySerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)

    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = '__all__'
        read_only_fields = ('id', 'invited_at', 'created_at', 'updated_at')


class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = '__all__'


class WorkspacePreferenceSerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)

    class Meta:
        model = WorkspacePreference
        fields = '__all__'
        read_only_fields = ('updated_at',)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Integrations
# ─────────────────────────────────────────────────────────────────────────────

class ConnectedChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectedChannel
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        # Never expose OAuth tokens over API
        extra_kwargs = {
            'access_token_encrypted': {'write_only': True},
            'refresh_token_encrypted': {'write_only': True},
        }


class BankConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankConnection
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'access_token_encrypted': {'write_only': True},
            'refresh_token_encrypted': {'write_only': True},
            'consent_token_encrypted': {'write_only': True},
        }


class TaxAuthorityIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxAuthorityIntegration
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'access_token_encrypted': {'write_only': True},
            'refresh_token_encrypted': {'write_only': True},
        }


class GDriveConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GDriveConnection
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'access_token_encrypted': {'write_only': True},
            'refresh_token_encrypted': {'write_only': True},
        }


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Counterparts
# ─────────────────────────────────────────────────────────────────────────────

class CounterpartSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.legal_name', read_only=True)
    amount_due_total = serializers.SerializerMethodField()

    class Meta:
        model = Counterpart
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'bank_account_number_encrypted': {'write_only': True},
            'bank_routing_number_encrypted': {'write_only': True},
            'bank_iban_encrypted': {'write_only': True},
        }

    def get_amount_due_total(self, obj):
        """Sum of outstanding balances across all linked invoices."""
        return obj.total_invoices - obj.total_paid if obj.total_invoices else 0


class CounterpartAuditLogSerializer(serializers.ModelSerializer):
    counterpart_name = serializers.CharField(source='counterpart.name', read_only=True)

    class Meta:
        model = CounterpartAuditLog
        fields = '__all__'
        read_only_fields = ('id', 'changed_at')


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — Smart Inbox
# ─────────────────────────────────────────────────────────────────────────────

class InboxAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InboxAttachment
        fields = '__all__'
        read_only_fields = ('id', 'content_hash', 'is_duplicate', 'ocr_status', 'ocr_extracted_data', 'ocr_confidence', 'ocr_processed_at', 'created_at', 'updated_at')


class InboxMessageSerializer(serializers.ModelSerializer):
    attachments = InboxAttachmentSerializer(many=True, read_only=True)
    linked_invoice_number = serializers.CharField(source='linked_invoice.invoice_number', read_only=True)

    class Meta:
        model = InboxMessage
        fields = '__all__'
        read_only_fields = ('id', 'classification', 'classification_confidence', 'classified_at', 'created_at', 'updated_at')


class InboxMessageListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views — no nested attachments."""
    class Meta:
        model = InboxMessage
        fields = ('id', 'source', 'classification', 'processing_status', 'subject',
                  'sender_email', 'sender_name', 'body_preview', 'is_read', 'is_starred',
                  'received_at', 'linked_invoice', 'created_at')
        read_only_fields = fields


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — Invoices
# ─────────────────────────────────────────────────────────────────────────────

class InvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLineItem
        fields = '__all__'
        read_only_fields = ('id', 'line_total')


class InvoiceStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceStatusHistory
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class InvoiceCommunicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceCommunication
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class InvoiceSerializer(serializers.ModelSerializer):
    amount_due = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    status_history = InvoiceStatusHistorySerializer(many=True, read_only=True)
    communications = InvoiceCommunicationSerializer(many=True, read_only=True)
    counterpart_name = serializers.CharField(source='counterpart.name', read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('id', 'amount_due', 'created_at', 'updated_at',
                            'dispatched_at', 'delivered_at', 'read_at',
                            'reconciled_at', 'reconciliation_confidence',
                            'payment_executed_at', 'gdrive_saved_at',
                            'dunning_last_sent_at', 'dunning_count', 'dunning_next_at')


class InvoiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    amount_due = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = ('id', 'invoice_number', 'direction', 'status', 'contact_name',
                  'total_amount', 'amount_paid', 'amount_due', 'currency',
                  'issue_date', 'due_date', 'fraud_risk_score', 'credit_risk_score', 'created_at')
        read_only_fields = fields


class DunningRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DunningRule
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — Banking Hub
# ─────────────────────────────────────────────────────────────────────────────

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'
        read_only_fields = ('id', 'account_number_masked', 'current_balance', 'available_balance', 'balance_updated_at', 'created_at', 'updated_at')
        extra_kwargs = {
            'account_number_encrypted': {'write_only': True},
            'sort_code_encrypted': {'write_only': True},
            'iban_encrypted': {'write_only': True},
        }


class BankTransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.account_name', read_only=True)
    linked_invoice_number = serializers.CharField(source='linked_invoice.invoice_number', read_only=True)

    class Meta:
        model = BankTransaction
        fields = '__all__'
        read_only_fields = ('id', 'category', 'category_confidence', 'matched_at', 'matched_by',
                            'match_confidence', 'created_at', 'updated_at')


class BankTransactionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankTransaction
        fields = ('id', 'transaction_date', 'description', 'transaction_type', 'amount',
                  'currency', 'category', 'reconciliation_status', 'counterparty_name',
                  'linked_invoice', 'created_at')
        read_only_fields = fields


class PaymentTransactionSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = '__all__'
        read_only_fields = ('id', 'initiated_at', 'created_at', 'updated_at')


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — Accountant Hub
# ─────────────────────────────────────────────────────────────────────────────

class TaskDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskDocument
        fields = '__all__'
        read_only_fields = ('id', 'ocr_processed', 'created_at')


class AccountantTaskSerializer(serializers.ModelSerializer):
    documents = TaskDocumentSerializer(many=True, read_only=True)
    linked_invoice_number = serializers.CharField(source='linked_invoice.invoice_number', read_only=True)

    class Meta:
        model = AccountantTask
        fields = '__all__'
        read_only_fields = ('id', 'created_by_system', 'resolved_at', 'resolved_by', 'created_at', 'updated_at')


class AccountantTaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountantTask
        fields = ('id', 'task_type', 'title', 'status', 'priority', 'linked_amount',
                  'linked_currency', 'due_date', 'assigned_to', 'created_by_system', 'created_at')
        read_only_fields = fields


class ComplianceDeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceDeadline
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class ChatAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatAttachment
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class ChatMessageSerializer(serializers.ModelSerializer):
    attachments = ChatAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = ChatMessage
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — Gmail & Dashboard
# ─────────────────────────────────────────────────────────────────────────────

class GmailLabelMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GmailLabelMapping
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class GmailSyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GmailSyncLog
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class DashboardKPICacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardKPICache
        fields = '__all__'
        read_only_fields = ('id', 'calculated_at')


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
