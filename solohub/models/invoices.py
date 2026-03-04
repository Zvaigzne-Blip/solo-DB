"""
SoloHub Django Models — Invoices (Modules 2 & 3)
Unified Purchase (AP) and Sales (AR) invoice ledger.
"""
import uuid
from django.db import models
from .core import Workspace, Company
from .contacts import Counterpart


class Invoice(models.Model):
    """
    Unified invoice ledger.
    direction='purchase' → Accounts Payable (Module 2)
    direction='sale' → Accounts Receivable (Module 3)
    """
    class Direction(models.TextChoices):
        PURCHASE = 'purchase', 'Purchase (AP)'
        SALE = 'sale', 'Sale (AR)'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        READ = 'read', 'Read'
        PARTIALLY_PAID = 'partially_paid', 'Partially Paid'
        PAID = 'paid', 'Paid'
        OVERDUE = 'overdue', 'Overdue'
        VOIDED = 'voided', 'Voided'
        CANCELLED = 'cancelled', 'Cancelled'
        DISPUTED = 'disputed', 'Disputed'
        IN_PROGRESS = 'in_progress', 'In Progress'
        PAYMENT_SUBMITTED = 'payment_submitted', 'Payment Submitted'

    class Source(models.TextChoices):
        SMART_INBOX = 'smart_inbox', 'Smart Inbox'
        MANUAL = 'manual', 'Manual'
        SCAN = 'scan', 'Scan'
        API = 'api', 'API'
        QUOTE_CONVERSION = 'quote_conversion', 'Quote Conversion'
        GMAIL_ADDON = 'gmail_addon', 'Gmail Add-on'

    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        CREDIT_CARD = 'credit_card', 'Credit Card'
        DEBIT_CARD = 'debit_card', 'Debit Card'
        CHECK = 'check', 'Check'
        CASH = 'cash', 'Cash'
        PAYPAL = 'paypal', 'PayPal'
        OTHER = 'other', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='invoices')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')

    # Type & Source
    direction = models.CharField(max_length=10, choices=Direction.choices)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)

    # Reference
    invoice_number = models.CharField(max_length=100, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)

    # Parties
    counterpart = models.ForeignKey(Counterpart, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_address = models.TextField(blank=True)

    # Dates
    issue_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    payment_terms_days = models.IntegerField(null=True, blank=True)

    # Amounts
    currency = models.CharField(max_length=3, default='USD')
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    fx_rate = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    base_currency_total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    @property
    def amount_due(self):
        return self.total_amount - self.amount_paid

    # Status & Risk
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    fraud_risk_score = models.SmallIntegerField(null=True, blank=True)  # 1-5 (Purchase)
    fraud_risk_flags = models.JSONField(default=list, blank=True)
    credit_risk_score = models.SmallIntegerField(null=True, blank=True)  # 1-5 (Sales)

    # Source document
    source_message = models.ForeignKey(
        'InboxMessage', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_invoices'
    )
    original_file_url = models.TextField(blank=True)
    original_file_bucket = models.CharField(max_length=100, blank=True)

    # Dispatch tracking (Sales)
    dispatch_channel = models.CharField(max_length=50, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Reconciliation
    reconciled_at = models.DateTimeField(null=True, blank=True)
    reconciled_transaction = models.ForeignKey(
        'BankTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='reconciled_invoices'
    )
    reconciliation_confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)

    # Payment execution (Purchase)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, blank=True)
    payment_reference = models.CharField(max_length=255, blank=True)
    payment_executed_at = models.DateTimeField(null=True, blank=True)
    payment_gateway_id = models.CharField(max_length=255, blank=True)

    # GDrive archive
    gdrive_file_id = models.CharField(max_length=255, blank=True)
    gdrive_saved_at = models.DateTimeField(null=True, blank=True)

    # Gmail sync
    gmail_thread_id = models.CharField(max_length=255, blank=True)
    gmail_label = models.CharField(max_length=100, blank=True)

    # Dunning engine (Sales)
    dunning_enabled = models.BooleanField(default=True)
    dunning_last_sent_at = models.DateTimeField(null=True, blank=True)
    dunning_count = models.IntegerField(default=0)
    dunning_next_at = models.DateTimeField(null=True, blank=True)

    # Approval
    approved_by = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_direction_display()} #{self.invoice_number} — {self.contact_name}'


class InvoiceLineItem(models.Model):
    """Individual line items on an invoice."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    position = models.IntegerField(default=0)
    description = models.TextField()
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    category = models.CharField(max_length=100, blank=True)
    account_code = models.CharField(max_length=50, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invoice_line_items'
        ordering = ['position']

    def __str__(self):
        return f'Line {self.position}: {self.description[:60]}'


class InvoiceStatusHistory(models.Model):
    """Immutable audit trail for invoice status transitions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, choices=Invoice.Status.choices, blank=True)
    new_status = models.CharField(max_length=20, choices=Invoice.Status.choices)
    changed_by = models.UUIDField(null=True, blank=True)
    change_reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoice_status_history'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.invoice}: {self.old_status} → {self.new_status}'


class InvoiceCommunication(models.Model):
    """Outbound message log for invoice dispatch and dunning notices."""
    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        TELEGRAM = 'telegram', 'Telegram'
        SMS = 'sms', 'SMS'
        IN_APP = 'in_app', 'In-App'

    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        READ = 'read', 'Read'
        FAILED = 'failed', 'Failed'
        BOUNCED = 'bounced', 'Bounced'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='communications')
    channel = models.CharField(max_length=20, choices=Channel.choices)
    recipient = models.CharField(max_length=255)
    subject = models.TextField(blank=True)
    body_preview = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    external_message_id = models.CharField(max_length=500, blank=True)
    is_dunning = models.BooleanField(default=False)
    dunning_level = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoice_communications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_channel_display()} to {self.recipient}: {self.get_status_display()}'


class DunningRule(models.Model):
    """Configurable escalation rules for automated payment reminders (Sales)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='dunning_rules')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='dunning_rules')
    name = models.CharField(max_length=255)
    days_after_due = models.IntegerField()
    channel = models.CharField(
        max_length=20,
        choices=InvoiceCommunication.Channel.choices,
        default=InvoiceCommunication.Channel.EMAIL,
    )
    subject_template = models.TextField(blank=True)
    body_template = models.TextField(blank=True)
    dunning_level = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dunning_rules'
        ordering = ['days_after_due']

    def __str__(self):
        return f'{self.name} (Level {self.dunning_level}, +{self.days_after_due}d)'
