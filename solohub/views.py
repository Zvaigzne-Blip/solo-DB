"""
SoloHub DRF Views — ModelViewSet for all 32 models with custom actions.
All views require authentication (IsAuthenticated by default in settings.py).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone

from .models import (
    Profile, Workspace, Company, WorkspaceMember, RolePermission, WorkspacePreference,
    ConnectedChannel, BankConnection, TaxAuthorityIntegration, GDriveConnection,
    Counterpart, CounterpartAuditLog,
    InboxMessage, InboxAttachment,
    Invoice, InvoiceLineItem, InvoiceStatusHistory, InvoiceCommunication, DunningRule,
    BankAccount, BankTransaction, PaymentTransaction,
    AccountantTask, TaskDocument, ComplianceDeadline, ChatMessage, ChatAttachment,
    GmailLabelMapping, GmailSyncLog, DashboardKPICache, Notification, AuditLog,
)
from .serializers import (
    ProfileSerializer, WorkspaceSerializer, CompanySerializer,
    WorkspaceMemberSerializer, RolePermissionSerializer, WorkspacePreferenceSerializer,
    ConnectedChannelSerializer, BankConnectionSerializer, TaxAuthorityIntegrationSerializer,
    GDriveConnectionSerializer,
    CounterpartSerializer, CounterpartAuditLogSerializer,
    InboxMessageSerializer, InboxMessageListSerializer, InboxAttachmentSerializer,
    InvoiceSerializer, InvoiceListSerializer, InvoiceLineItemSerializer,
    InvoiceStatusHistorySerializer, InvoiceCommunicationSerializer, DunningRuleSerializer,
    BankAccountSerializer, BankTransactionSerializer, BankTransactionListSerializer,
    PaymentTransactionSerializer,
    AccountantTaskSerializer, AccountantTaskListSerializer, TaskDocumentSerializer,
    ComplianceDeadlineSerializer, ChatMessageSerializer, ChatAttachmentSerializer,
    GmailLabelMappingSerializer, GmailSyncLogSerializer, DashboardKPICacheSerializer,
    NotificationSerializer, AuditLogSerializer,
)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Core / IAM
# ─────────────────────────────────────────────────────────────────────────────

class ProfileViewSet(viewsets.ModelViewSet):
    """User profiles — one per Supabase auth user."""
    queryset = Profile.objects.all().order_by('-created_at')
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['full_name', 'display_name', 'phone']
    ordering_fields = ['created_at', 'full_name']


class WorkspaceViewSet(viewsets.ModelViewSet):
    """Workspaces — top-level multi-tenancy unit."""
    queryset = Workspace.objects.all().order_by('-created_at')
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'slug']
    ordering_fields = ['created_at', 'name']
    filterset_fields = ['is_active', 'base_currency']


class CompanyViewSet(viewsets.ModelViewSet):
    """Trading entities / legal identities within a workspace."""
    queryset = Company.objects.select_related('workspace').order_by('legal_name')
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['legal_name', 'trade_name', 'tax_id']
    filterset_fields = ['workspace', 'is_active', 'is_default', 'base_currency', 'country_code']
    ordering_fields = ['legal_name', 'created_at']


class WorkspaceMemberViewSet(viewsets.ModelViewSet):
    """Members / invitees for a workspace."""
    queryset = WorkspaceMember.objects.select_related('workspace').order_by('workspace', 'role')
    serializer_class = WorkspaceMemberSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'role', 'status']
    search_fields = ['email']


class RolePermissionViewSet(viewsets.ModelViewSet):
    """Fine-grained RBAC matrix per workspace."""
    queryset = RolePermission.objects.all().order_by('role', 'resource', 'action')
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'role', 'action', 'is_allowed']
    search_fields = ['resource', 'action']


class WorkspacePreferenceViewSet(viewsets.ModelViewSet):
    """Key/value workspace settings store."""
    queryset = WorkspacePreference.objects.select_related('workspace').order_by('workspace', 'key')
    serializer_class = WorkspacePreferenceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace']
    search_fields = ['key']


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Integrations
# ─────────────────────────────────────────────────────────────────────────────

class ConnectedChannelViewSet(viewsets.ModelViewSet):
    """OAuth-connected channels (Gmail, Outlook, WhatsApp, Telegram, etc.)."""
    queryset = ConnectedChannel.objects.select_related('workspace', 'company').order_by('workspace', 'channel_type')
    serializer_class = ConnectedChannelSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'channel_type', 'status']
    search_fields = ['display_name', 'account_identifier']

    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """Revoke OAuth tokens and set status to disconnected."""
        channel = self.get_object()
        channel.status = 'disconnected'
        channel.access_token_encrypted = ''
        channel.refresh_token_encrypted = ''
        channel.save(update_fields=['status', 'access_token_encrypted', 'refresh_token_encrypted', 'updated_at'])
        return Response({'status': 'disconnected'})

    @action(detail=True, methods=['post'])
    def trigger_sync(self, request, pk=None):
        """Queue a sync job for this channel (stub — wire to Celery task)."""
        channel = self.get_object()
        # TODO: fire Celery task: sync_channel.delay(channel.id)
        return Response({'status': 'sync_queued', 'channel_id': str(channel.id)})


class BankConnectionViewSet(viewsets.ModelViewSet):
    """Open Banking connections (Plaid / TrueLayer)."""
    queryset = BankConnection.objects.select_related('workspace', 'company').order_by('institution_name')
    serializer_class = BankConnectionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'provider', 'status']
    search_fields = ['institution_name']

    @action(detail=True, methods=['post'])
    def refresh_consent(self, request, pk=None):
        """Re-trigger consent flow (stub)."""
        conn = self.get_object()
        return Response({'status': 'consent_refresh_initiated', 'connection_id': str(conn.id)})

    @action(detail=True, methods=['post'])
    def sync_transactions(self, request, pk=None):
        """Pull latest transactions from the bank (stub — wire to Celery)."""
        conn = self.get_object()
        # TODO: fire Celery task: sync_bank_transactions.delay(conn.id)
        return Response({'status': 'sync_queued', 'connection_id': str(conn.id)})


class TaxAuthorityIntegrationViewSet(viewsets.ModelViewSet):
    """MTD / HMRC and other tax authority integrations."""
    queryset = TaxAuthorityIntegration.objects.select_related('company').order_by('authority_name')
    serializer_class = TaxAuthorityIntegrationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'authority_code', 'status']
    search_fields = ['authority_name', 'tax_reference']


class GDriveConnectionViewSet(viewsets.ModelViewSet):
    """Google Drive integration for document archiving."""
    queryset = GDriveConnection.objects.select_related('workspace', 'company').order_by('company')
    serializer_class = GDriveConnectionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'status']


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Counterparts
# ─────────────────────────────────────────────────────────────────────────────

class CounterpartViewSet(viewsets.ModelViewSet):
    """Unified vendor + customer directory."""
    queryset = Counterpart.objects.select_related('workspace', 'company').order_by('name')
    serializer_class = CounterpartSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'counterpart_type', 'is_active', 'country_code',
                        'fraud_risk_score', 'credit_risk_score']
    search_fields = ['name', 'legal_name', 'email', 'tax_id']
    ordering_fields = ['name', 'total_invoices', 'total_paid', 'last_invoice_date']

    @action(detail=True, methods=['get'])
    def invoices(self, request, pk=None):
        """List all invoices for this counterpart."""
        counterpart = self.get_object()
        qs = counterpart.invoices.order_by('-created_at')
        serializer = InvoiceListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def audit_log(self, request, pk=None):
        """Return change history for this counterpart."""
        counterpart = self.get_object()
        qs = counterpart.audit_logs.order_by('-changed_at')
        serializer = CounterpartAuditLogSerializer(qs, many=True)
        return Response(serializer.data)


class CounterpartAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Immutable counterpart change history."""
    queryset = CounterpartAuditLog.objects.select_related('counterpart').order_by('-changed_at')
    serializer_class = CounterpartAuditLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['counterpart', 'field_name']
    search_fields = ['field_name', 'old_value', 'new_value']


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — Smart Inbox (Module 1)
# ─────────────────────────────────────────────────────────────────────────────

class InboxMessageViewSet(viewsets.ModelViewSet):
    """Unified message inbox from all connected channels."""
    queryset = InboxMessage.objects.select_related('workspace', 'company', 'linked_invoice', 'linked_counterpart').order_by('-received_at')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'source', 'classification', 'processing_status', 'is_read', 'is_starred']
    search_fields = ['subject', 'sender_email', 'sender_name', 'body_preview']
    ordering_fields = ['received_at', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return InboxMessageListSerializer
        return InboxMessageSerializer

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        msg = self.get_object()
        msg.is_read = True
        msg.save(update_fields=['is_read'])
        return Response({'status': 'marked_read'})

    @action(detail=True, methods=['post'])
    def mark_starred(self, request, pk=None):
        msg = self.get_object()
        msg.is_starred = not msg.is_starred
        msg.save(update_fields=['is_starred'])
        return Response({'is_starred': msg.is_starred})

    @action(detail=True, methods=['post'])
    def link_invoice(self, request, pk=None):
        """Manually link this message to an invoice."""
        msg = self.get_object()
        invoice_id = request.data.get('invoice_id')
        try:
            invoice = Invoice.objects.get(pk=invoice_id)
            msg.linked_invoice = invoice
            msg.save(update_fields=['linked_invoice', 'updated_at'])
            return Response({'status': 'linked', 'invoice_id': str(invoice_id)})
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        workspace_id = request.query_params.get('workspace')
        qs = self.get_queryset().filter(is_read=False)
        if workspace_id:
            qs = qs.filter(workspace_id=workspace_id)
        return Response({'unread_count': qs.count()})


class InboxAttachmentViewSet(viewsets.ModelViewSet):
    """File attachments with OCR status tracking."""
    queryset = InboxAttachment.objects.select_related('message').order_by('-created_at')
    serializer_class = InboxAttachmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['message', 'ocr_status', 'is_duplicate', 'mime_type']
    search_fields = ['filename']


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — Invoices (Modules 2 & 3)
# ─────────────────────────────────────────────────────────────────────────────

class InvoiceViewSet(viewsets.ModelViewSet):
    """Unified invoice store — both payables (purchase) and receivables (sale)."""
    queryset = Invoice.objects.select_related('workspace', 'company', 'counterpart').order_by('-created_at')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'direction', 'status', 'currency',
                        'fraud_risk_score', 'credit_risk_score', 'source']
    search_fields = ['invoice_number', 'reference_number', 'contact_name', 'contact_email']
    ordering_fields = ['created_at', 'issue_date', 'due_date', 'total_amount']

    def get_serializer_class(self):
        if self.action == 'list':
            return InvoiceListSerializer
        return InvoiceSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a purchase invoice for payment."""
        invoice = self.get_object()
        if invoice.direction != 'purchase':
            return Response({'error': 'Only purchase invoices can be approved'}, status=status.HTTP_400_BAD_REQUEST)
        invoice.status = 'approved'
        invoice.approved_by = str(request.user.id)
        invoice.approved_at = timezone.now()
        invoice.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        return Response({'status': 'approved', 'approved_at': invoice.approved_at})

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Record full payment on an invoice."""
        invoice = self.get_object()
        invoice.amount_paid = invoice.total_amount
        invoice.status = 'paid'
        invoice.save(update_fields=['amount_paid', 'status', 'updated_at'])
        return Response({'status': 'paid', 'amount_paid': str(invoice.amount_paid)})

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Dispatch a sales invoice via the configured channel (stub)."""
        invoice = self.get_object()
        if invoice.direction != 'sale':
            return Response({'error': 'Only sales invoices can be sent'}, status=status.HTTP_400_BAD_REQUEST)
        # TODO: fire Celery task: dispatch_invoice.delay(invoice.id)
        invoice.status = 'sent'
        invoice.dispatched_at = timezone.now()
        invoice.save(update_fields=['status', 'dispatched_at', 'updated_at'])
        return Response({'status': 'sent', 'dispatched_at': invoice.dispatched_at})

    @action(detail=True, methods=['get'])
    def line_items(self, request, pk=None):
        invoice = self.get_object()
        serializer = InvoiceLineItemSerializer(invoice.line_items.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Full status + communication timeline."""
        invoice = self.get_object()
        history = InvoiceStatusHistorySerializer(invoice.status_history.order_by('created_at'), many=True).data
        comms = InvoiceCommunicationSerializer(invoice.communications.order_by('created_at'), many=True).data
        return Response({'status_history': history, 'communications': comms})

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Return all overdue invoices."""
        today = timezone.now().date()
        qs = self.get_queryset().filter(due_date__lt=today, status__in=['sent', 'partially_paid', 'overdue'])
        serializer = InvoiceListSerializer(qs, many=True)
        return Response(serializer.data)


class InvoiceLineItemViewSet(viewsets.ModelViewSet):
    queryset = InvoiceLineItem.objects.select_related('invoice').order_by('invoice', 'position')
    serializer_class = InvoiceLineItemSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['invoice']
    search_fields = ['description', 'category']


class InvoiceStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Immutable invoice status change audit trail."""
    queryset = InvoiceStatusHistory.objects.select_related('invoice').order_by('-created_at')
    serializer_class = InvoiceStatusHistorySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['invoice', 'old_status', 'new_status']


class InvoiceCommunicationViewSet(viewsets.ModelViewSet):
    queryset = InvoiceCommunication.objects.select_related('invoice').order_by('-created_at')
    serializer_class = InvoiceCommunicationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['invoice', 'channel', 'status', 'is_dunning']


class DunningRuleViewSet(viewsets.ModelViewSet):
    queryset = DunningRule.objects.select_related('workspace', 'company').order_by('days_after_due')
    serializer_class = DunningRuleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'channel', 'is_active']


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — Banking Hub (Module 4)
# ─────────────────────────────────────────────────────────────────────────────

class BankAccountViewSet(viewsets.ModelViewSet):
    """Bank accounts synced from Open Banking connections."""
    queryset = BankAccount.objects.select_related('workspace', 'company', 'connection').order_by('company', 'institution_name')
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'connection', 'account_type', 'status', 'currency', 'is_internal']
    search_fields = ['account_name', 'institution_name', 'account_number_masked']

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        account = self.get_object()
        qs = account.transactions.order_by('-transaction_date')
        serializer = BankTransactionListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def balance_summary(self, request, pk=None):
        account = self.get_object()
        return Response({
            'account_id': str(account.id),
            'account_name': account.account_name,
            'currency': account.currency,
            'current_balance': str(account.current_balance),
            'available_balance': str(account.available_balance or 0),
            'balance_updated_at': account.balance_updated_at,
        })


class BankTransactionViewSet(viewsets.ModelViewSet):
    """Bank transactions with AI categorisation and reconciliation status."""
    queryset = BankTransaction.objects.select_related('account', 'company', 'linked_invoice', 'accountant_task').order_by('-transaction_date')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'account', 'transaction_type', 'category',
                        'reconciliation_status', 'currency', 'matched_by']
    search_fields = ['description', 'reference', 'counterparty_name', 'external_transaction_id']
    ordering_fields = ['transaction_date', 'amount', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return BankTransactionListSerializer
        return BankTransactionSerializer

    @action(detail=True, methods=['post'])
    def reconcile(self, request, pk=None):
        """Manually link transaction to an invoice and mark reconciled."""
        txn = self.get_object()
        invoice_id = request.data.get('invoice_id')
        try:
            invoice = Invoice.objects.get(pk=invoice_id)
            txn.linked_invoice = invoice
            txn.reconciliation_status = 'matched'
            txn.matched_by = 'manual'
            txn.matched_at = timezone.now()
            txn.match_confidence = 100
            txn.save(update_fields=['linked_invoice', 'reconciliation_status', 'matched_by', 'matched_at', 'match_confidence', 'updated_at'])
            return Response({'status': 'reconciled', 'invoice_id': str(invoice_id)})
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def flag_unmatched(self, request, pk=None):
        txn = self.get_object()
        txn.reconciliation_status = 'unmatched'
        txn.save(update_fields=['reconciliation_status', 'updated_at'])
        return Response({'status': 'flagged_unmatched'})

    @action(detail=False, methods=['get'])
    def unreconciled(self, request):
        workspace_id = request.query_params.get('workspace')
        qs = self.get_queryset().filter(reconciliation_status__in=['unmatched', 'pending'])
        if workspace_id:
            qs = qs.filter(workspace_id=workspace_id)
        serializer = BankTransactionListSerializer(qs, many=True)
        return Response(serializer.data)


class PaymentTransactionViewSet(viewsets.ModelViewSet):
    """Outbound payment execution log (Stripe, bank transfer, etc.)."""
    queryset = PaymentTransaction.objects.select_related('invoice', 'company', 'linked_bank_transaction').order_by('-initiated_at')
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'direction', 'gateway', 'gateway_status', 'payment_method', 'currency']
    search_fields = ['gateway_transaction_id']


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — Accountant Hub (Module 5)
# ─────────────────────────────────────────────────────────────────────────────

class AccountantTaskViewSet(viewsets.ModelViewSet):
    """AI-generated and manual accountant tasks with document support."""
    queryset = AccountantTask.objects.select_related('workspace', 'company', 'linked_transaction', 'linked_invoice').order_by('-created_at')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'task_type', 'status', 'priority', 'created_by_system', 'assigned_to']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority']

    def get_serializer_class(self):
        if self.action == 'list':
            return AccountantTaskListSerializer
        return AccountantTaskSerializer

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        task = self.get_object()
        task.status = 'resolved'
        task.resolved_at = timezone.now()
        task.resolved_by = str(request.user.id)
        task.resolution_notes = request.data.get('resolution_notes', '')
        task.save(update_fields=['status', 'resolved_at', 'resolved_by', 'resolution_notes', 'updated_at'])
        return Response({'status': 'resolved', 'resolved_at': task.resolved_at})

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        task = self.get_object()
        serializer = TaskDocumentSerializer(task.documents.all(), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def open_tasks(self, request):
        workspace_id = request.query_params.get('workspace')
        qs = self.get_queryset().filter(status__in=['open', 'in_progress'])
        if workspace_id:
            qs = qs.filter(workspace_id=workspace_id)
        serializer = AccountantTaskListSerializer(qs, many=True)
        return Response(serializer.data)


class TaskDocumentViewSet(viewsets.ModelViewSet):
    queryset = TaskDocument.objects.select_related('task', 'linked_invoice').order_by('-created_at')
    serializer_class = TaskDocumentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['task', 'linked_invoice', 'ocr_processed']
    search_fields = ['filename']


class ComplianceDeadlineViewSet(viewsets.ModelViewSet):
    """Tax and regulatory filing deadlines with reminders."""
    queryset = ComplianceDeadline.objects.select_related('workspace', 'company', 'linked_task').order_by('due_date')
    serializer_class = ComplianceDeadlineSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'status', 'recurrence', 'deadline_type']
    search_fields = ['title', 'deadline_type', 'filing_reference']
    ordering_fields = ['due_date', 'created_at']

    @action(detail=True, methods=['post'])
    def mark_filed(self, request, pk=None):
        deadline = self.get_object()
        deadline.status = 'filed'
        deadline.filed_at = timezone.now()
        deadline.filing_reference = request.data.get('filing_reference', '')
        deadline.save(update_fields=['status', 'filed_at', 'filing_reference', 'updated_at'])
        return Response({'status': 'filed', 'filed_at': deadline.filed_at})

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        from datetime import timedelta
        today = timezone.now().date()
        lookahead = today + timedelta(days=30)
        qs = self.get_queryset().filter(due_date__lte=lookahead, status__in=['pending', 'due_soon'])
        serializer = ComplianceDeadlineSerializer(qs, many=True)
        return Response(serializer.data)


class ChatMessageViewSet(viewsets.ModelViewSet):
    """AI + human chat messages in the Accountant Hub."""
    queryset = ChatMessage.objects.select_related('workspace', 'company').order_by('-created_at')
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'thread_type', 'is_read', 'has_attachments']
    search_fields = ['message_text']

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        msg = self.get_object()
        msg.is_read = True
        msg.save(update_fields=['is_read'])
        return Response({'status': 'marked_read'})


class ChatAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ChatAttachment.objects.select_related('message').order_by('-created_at')
    serializer_class = ChatAttachmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['message']
    search_fields = ['filename']


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — Gmail Add-on & Dashboard (Modules 7 & 8)
# ─────────────────────────────────────────────────────────────────────────────

class GmailLabelMappingViewSet(viewsets.ModelViewSet):
    """Invoice status → Gmail label mapping for the add-on."""
    queryset = GmailLabelMapping.objects.select_related('workspace', 'channel').order_by('workspace', 'invoice_status')
    serializer_class = GmailLabelMappingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'channel', 'invoice_status', 'is_active']
    search_fields = ['gmail_label_name']


class GmailSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Immutable Gmail label sync event log."""
    queryset = GmailSyncLog.objects.select_related('channel', 'linked_invoice').order_by('-created_at')
    serializer_class = GmailSyncLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['channel', 'direction', 'sync_status', 'linked_invoice']
    search_fields = ['gmail_thread_id', 'action']


class DashboardKPICacheViewSet(viewsets.ReadOnlyModelViewSet):
    """Pre-computed KPI metrics for the dashboard (read-only, populated by workers)."""
    queryset = DashboardKPICache.objects.select_related('workspace', 'company').order_by('-calculated_at')
    serializer_class = DashboardKPICacheSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'company', 'metric_name']
    search_fields = ['metric_name']

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Latest value for each metric for a workspace."""
        workspace_id = request.query_params.get('workspace')
        if not workspace_id:
            return Response({'error': 'workspace query param required'}, status=status.HTTP_400_BAD_REQUEST)
        qs = self.get_queryset().filter(workspace_id=workspace_id).order_by('metric_name', '-calculated_at').distinct('metric_name')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9 — Cross-cutting
# ─────────────────────────────────────────────────────────────────────────────

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.select_related('workspace').order_by('-created_at')
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['workspace', 'notification_type', 'is_read', 'entity_type']
    search_fields = ['title', 'body']

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.read_at = timezone.now()
        notif.save(update_fields=['is_read', 'read_at'])
        return Response({'status': 'marked_read'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        workspace_id = request.query_params.get('workspace')
        qs = self.get_queryset().filter(is_read=False)
        if workspace_id:
            qs = qs.filter(workspace_id=workspace_id)
        count = qs.update(is_read=True, read_at=timezone.now())
        return Response({'marked_read': count})


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Immutable global audit trail — admin-only."""
    queryset = AuditLog.objects.select_related('workspace').order_by('-created_at')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['workspace', 'action', 'entity_type', 'user_id']
    search_fields = ['action', 'entity_type', 'user_id']
