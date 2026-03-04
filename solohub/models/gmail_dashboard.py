"""
SoloHub Django Models — Gmail Add-on & Dashboard (Modules 7 & 8)
"""
import uuid
from django.db import models
from .core import Workspace, Company
from .integrations import ConnectedChannel


# ============================================================================
# Gmail Add-on (Module 8)
# ============================================================================

class GmailLabelMapping(models.Model):
    """Maps SoloHub invoice statuses to Gmail USER labels for bi-directional sync."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='gmail_label_mappings')
    channel = models.ForeignKey(ConnectedChannel, on_delete=models.CASCADE, related_name='label_mappings')
    invoice_status = models.CharField(max_length=20)  # matches invoice_status enum
    gmail_label_name = models.CharField(max_length=255)
    gmail_label_id = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gmail_label_mappings'
        unique_together = [('channel', 'invoice_status')]

    def __str__(self):
        return f'{self.invoice_status} → {self.gmail_label_name}'


class GmailSyncLog(models.Model):
    """Audit log for Gmail ↔ SoloHub label synchronization events."""
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]
    SYNC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('synced', 'Synced'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(ConnectedChannel, on_delete=models.CASCADE, related_name='sync_logs')
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    gmail_thread_id = models.CharField(max_length=255, blank=True)
    gmail_history_id = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=100, blank=True)
    old_label = models.CharField(max_length=255, blank=True)
    new_label = models.CharField(max_length=255, blank=True)
    linked_invoice = models.ForeignKey(
        'Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='gmail_sync_logs'
    )
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gmail_sync_log'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.direction} sync: {self.old_label} → {self.new_label}'


# ============================================================================
# Dashboard KPI Cache (Module 7)
# ============================================================================

class DashboardKPICache(models.Model):
    """Read-optimized cache for dashboard KPIs. Invalidated on state changes."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='kpi_cache')
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, null=True, blank=True, related_name='kpi_cache'
    )  # NULL = consolidated "All Companies"
    metric_name = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    metric_metadata = models.JSONField(default=dict, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    calculated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'dashboard_kpi_cache'
        unique_together = [('workspace', 'company', 'metric_name', 'period_start')]

    def __str__(self):
        return f'{self.metric_name}: {self.metric_value}'


# ============================================================================
# Notifications & Audit
# ============================================================================

class Notification(models.Model):
    """In-app notification feed with deep links to resolution workflows."""
    class NotificationType(models.TextChoices):
        INVOICE_RECEIVED = 'invoice_received', 'Invoice Received'
        INVOICE_PAID = 'invoice_paid', 'Invoice Paid'
        INVOICE_OVERDUE = 'invoice_overdue', 'Invoice Overdue'
        PAYMENT_CONFIRMED = 'payment_confirmed', 'Payment Confirmed'
        RISK_ALERT = 'risk_alert', 'Risk Alert'
        COMPLIANCE_DEADLINE = 'compliance_deadline', 'Compliance Deadline'
        MISSING_DOCUMENT = 'missing_document', 'Missing Document'
        RECONCILIATION_COMPLETE = 'reconciliation_complete', 'Reconciliation Complete'
        DUNNING_SENT = 'dunning_sent', 'Dunning Sent'
        TASK_ASSIGNED = 'task_assigned', 'Task Assigned'
        CHAT_MESSAGE = 'chat_message', 'Chat Message'
        SYSTEM_ALERT = 'system_alert', 'System Alert'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='notifications')
    user_id = models.UUIDField()
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    title = models.CharField(max_length=500)
    body = models.TextField(blank=True)
    entity_type = models.CharField(max_length=100, blank=True)
    entity_id = models.UUIDField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    action_url = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_notification_type_display()}: {self.title}'


class AuditLog(models.Model):
    """Global immutable audit trail for all data mutations."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='audit_logs')
    user_id = models.UUIDField(null=True, blank=True)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.UUIDField(null=True, blank=True)
    old_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_log'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} {self.entity_type} by {self.user_id}'
