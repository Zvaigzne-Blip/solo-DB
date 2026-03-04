"""
SoloHub Django Models — Accountant Hub (Module 5)
Tasks, Compliance Deadlines, Chat
"""
import uuid
from django.db import models
from .core import Workspace, Company


class AccountantTask(models.Model):
    """Task queue for the CPA / Accountant Hub."""
    class TaskType(models.TextChoices):
        MISSING_INVOICE = 'missing_invoice', 'Missing Invoice'
        MISSING_RECEIPT = 'missing_receipt', 'Missing Receipt'
        CLARIFY_TRANSACTION = 'clarify_transaction', 'Clarify Transaction'
        APPROVE_VAT_RETURN = 'approve_vat_return', 'Approve VAT Return'
        APPROVE_TAX_FILING = 'approve_tax_filing', 'Approve Tax Filing'
        UPLOAD_DOCUMENT = 'upload_document', 'Upload Document'
        GENERAL_REQUEST = 'general_request', 'General Request'
        COMPLIANCE_DEADLINE = 'compliance_deadline', 'Compliance Deadline'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        WAITING_CLIENT = 'waiting_client', 'Waiting on Client'
        WAITING_CPA = 'waiting_cpa', 'Waiting on CPA'
        RESOLVED = 'resolved', 'Resolved'
        CANCELLED = 'cancelled', 'Cancelled'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='accountant_tasks')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='accountant_tasks')
    task_type = models.CharField(max_length=30, choices=TaskType.choices)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    # Linked entities
    linked_transaction = models.ForeignKey(
        'BankTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='accountant_tasks_linked'
    )
    linked_invoice = models.ForeignKey(
        'Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='accountant_tasks'
    )
    linked_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    linked_currency = models.CharField(max_length=3, blank=True)
    # Assignment
    assigned_to = models.UUIDField(null=True, blank=True)
    created_by_system = models.BooleanField(default=False)
    # Resolution
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.UUIDField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    #
    due_date = models.DateField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accountant_tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_task_type_display()}] {self.title}'


class TaskDocument(models.Model):
    """Files uploaded to resolve accountant tasks."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(AccountantTask, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.UUIDField(null=True, blank=True)
    filename = models.CharField(max_length=500)
    mime_type = models.CharField(max_length=100, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    storage_path = models.TextField(blank=True)
    storage_bucket = models.CharField(max_length=100, default='task-documents')
    ocr_processed = models.BooleanField(default=False)
    linked_invoice = models.ForeignKey(
        'Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='task_documents'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'task_documents'

    def __str__(self):
        return self.filename


class ComplianceDeadline(models.Model):
    """Statutory calendar for tax/filing deadlines."""
    class Status(models.TextChoices):
        UPCOMING = 'upcoming', 'Upcoming'
        DUE_SOON = 'due_soon', 'Due Soon'
        OVERDUE = 'overdue', 'Overdue'
        COMPLETED = 'completed', 'Completed'
        FILED = 'filed', 'Filed'

    class Recurrence(models.TextChoices):
        ONE_TIME = 'one_time', 'One-Time'
        MONTHLY = 'monthly', 'Monthly'
        QUARTERLY = 'quarterly', 'Quarterly'
        ANNUALLY = 'annually', 'Annually'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='compliance_deadlines')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='compliance_deadlines')
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    deadline_type = models.CharField(max_length=100, blank=True)
    due_date = models.DateField()
    warning_days = models.IntegerField(default=14)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.UPCOMING)
    recurrence = models.CharField(max_length=15, choices=Recurrence.choices, default=Recurrence.ONE_TIME)
    filed_at = models.DateTimeField(null=True, blank=True)
    filed_by = models.UUIDField(null=True, blank=True)
    filing_reference = models.CharField(max_length=255, blank=True)
    linked_task = models.ForeignKey(AccountantTask, on_delete=models.SET_NULL, null=True, blank=True, related_name='deadlines')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compliance_deadlines'
        ordering = ['due_date']

    def __str__(self):
        return f'{self.title} — due {self.due_date}'


class ChatMessage(models.Model):
    """WebSocket-driven contextual messaging between client and CPA."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='chat_messages')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='chat_messages')
    thread_type = models.CharField(max_length=50, blank=True)  # 'task', 'invoice', 'transaction', 'general'
    thread_ref_id = models.UUIDField(null=True, blank=True)
    sender_id = models.UUIDField()
    message_text = models.TextField()
    has_attachments = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']

    def __str__(self):
        return f'Chat [{self.thread_type}]: {self.message_text[:60]}'


class ChatAttachment(models.Model):
    """File attachments on chat messages."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='attachments')
    filename = models.CharField(max_length=500)
    mime_type = models.CharField(max_length=100, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    storage_path = models.TextField(blank=True)
    storage_bucket = models.CharField(max_length=100, default='chat-attachments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_attachments'

    def __str__(self):
        return self.filename
