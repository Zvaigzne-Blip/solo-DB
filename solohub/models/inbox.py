"""
SoloHub Django Models — Smart Multichannel Inbox (Module 1)
"""
import uuid
from django.db import models
from .core import Workspace, Company
from .integrations import ConnectedChannel
from .contacts import Counterpart


class InboxMessage(models.Model):
    """Ingested messages from Gmail, Outlook, WhatsApp, Telegram, GDrive."""
    class Source(models.TextChoices):
        GMAIL = 'gmail', 'Gmail'
        OUTLOOK = 'outlook', 'Outlook'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        TELEGRAM = 'telegram', 'Telegram'
        GDRIVE = 'gdrive', 'GDrive'
        MANUAL = 'manual', 'Manual'

    class Classification(models.TextChoices):
        INVOICE = 'invoice', 'Invoice'
        RECEIPT = 'receipt', 'Receipt'
        CHECK = 'check', 'Check'
        REMITTANCE = 'remittance', 'Remittance'
        FINANCIAL_OTHER = 'financial_other', 'Financial (Other)'
        NON_FINANCIAL = 'non_financial', 'Non-Financial'
        UNCLASSIFIED = 'unclassified', 'Unclassified'

    class ProcessingStatus(models.TextChoices):
        RECEIVED = 'received', 'Received'
        CLASSIFYING = 'classifying', 'Classifying'
        CLASSIFIED = 'classified', 'Classified'
        EXTRACTING = 'extracting', 'Extracting'
        EXTRACTED = 'extracted', 'Extracted'
        SYNCED = 'synced', 'Synced'
        FAILED = 'failed', 'Failed'
        IGNORED = 'ignored', 'Ignored'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='inbox_messages')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='inbox_messages')
    channel = models.ForeignKey(ConnectedChannel, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    # Source metadata
    source = models.CharField(max_length=20, choices=Source.choices)
    external_message_id = models.CharField(max_length=500, blank=True)
    external_thread_id = models.CharField(max_length=500, blank=True)
    # Message content
    sender_email = models.EmailField(blank=True)
    sender_name = models.CharField(max_length=255, blank=True)
    sender_phone = models.CharField(max_length=50, blank=True)
    subject = models.TextField(blank=True)
    body_preview = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    received_at = models.DateTimeField()
    # Classification (Phase 2)
    classification = models.CharField(
        max_length=20, choices=Classification.choices, default=Classification.UNCLASSIFIED
    )
    classification_confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    classified_at = models.DateTimeField(null=True, blank=True)
    # Processing pipeline
    processing_status = models.CharField(
        max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.RECEIVED
    )
    processing_error = models.TextField(blank=True)
    # Linked entities
    linked_invoice = models.ForeignKey(
        'Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='source_messages'
    )
    linked_counterpart = models.ForeignKey(Counterpart, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    # Gmail sync
    gmail_label = models.CharField(max_length=100, blank=True)
    gmail_label_synced_at = models.DateTimeField(null=True, blank=True)
    #
    is_read = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inbox_messages'
        ordering = ['-received_at']

    def __str__(self):
        return f'{self.source}: {self.subject or self.sender_email}'


class InboxAttachment(models.Model):
    """Files attached to inbox messages. OCR extracts structured financial data."""
    OCR_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(InboxMessage, on_delete=models.CASCADE, related_name='attachments')
    filename = models.CharField(max_length=500)
    mime_type = models.CharField(max_length=100, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    storage_path = models.TextField(blank=True)
    storage_bucket = models.CharField(max_length=100, default='inbox-attachments')
    # OCR extraction (Phase 3)
    ocr_status = models.CharField(max_length=20, choices=OCR_STATUS_CHOICES, default='pending')
    ocr_extracted_text = models.TextField(blank=True)
    ocr_extracted_data = models.JSONField(null=True, blank=True)
    ocr_confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    ocr_model = models.CharField(max_length=50, blank=True)
    ocr_processed_at = models.DateTimeField(null=True, blank=True)
    # Deduplication
    content_hash = models.CharField(max_length=64, blank=True)
    is_duplicate = models.BooleanField(default=False)
    duplicate_of = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    #
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inbox_attachments'

    def __str__(self):
        return self.filename
