"""
SoloHub Django Models — Integrations (Module 6, Section 2)
Connected Channels, Bank Connections, Tax Authority, GDrive
"""
import uuid
from django.db import models
from .core import Workspace, Company


class ConnectedChannel(models.Model):
    """OAuth credentials and webhook config for email/messaging integrations."""
    class ChannelType(models.TextChoices):
        GMAIL = 'gmail', 'Gmail'
        OUTLOOK = 'outlook', 'Outlook'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        TELEGRAM = 'telegram', 'Telegram'
        SMS = 'sms', 'SMS'
        GDRIVE = 'gdrive', 'GDrive'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        ERROR = 'error', 'Error'
        PENDING_AUTH = 'pending_auth', 'Pending Auth'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='channels')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='channels')
    channel_type = models.CharField(max_length=20, choices=ChannelType.choices)
    display_name = models.CharField(max_length=255, blank=True)
    account_identifier = models.CharField(max_length=255, blank=True)
    access_token_encrypted = models.TextField(blank=True)
    refresh_token_encrypted = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    webhook_url = models.URLField(blank=True)
    webhook_secret_encrypted = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_AUTH)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_cursor = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'connected_channels'

    def __str__(self):
        return f'{self.get_channel_type_display()} — {self.display_name or self.account_identifier}'


class BankConnection(models.Model):
    """Open Banking (AIS/PIS) consent records per company entity."""
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRED = 'expired', 'Expired'
        REVOKED = 'revoked', 'Revoked'
        PENDING_AUTH = 'pending_auth', 'Pending Auth'
        ERROR = 'error', 'Error'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='bank_connections')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_connections')
    provider = models.CharField(max_length=100)  # 'plaid', 'truelayer', etc.
    institution_name = models.CharField(max_length=255, blank=True)
    institution_logo_url = models.URLField(blank=True)
    external_connection_id = models.CharField(max_length=255, blank=True)
    consent_token_encrypted = models.TextField(blank=True)
    consent_expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_AUTH)
    supports_ais = models.BooleanField(default=True)
    supports_pis = models.BooleanField(default=False)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_connections'

    def __str__(self):
        return f'{self.institution_name} ({self.provider})'


class TaxAuthorityIntegration(models.Model):
    """Credentials for regional tax authority APIs per company entity."""
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        ERROR = 'error', 'Error'
        PENDING_AUTH = 'pending_auth', 'Pending Auth'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='tax_integrations')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tax_integrations')
    authority_code = models.CharField(max_length=50)  # 'hmrc', 'irs', etc.
    authority_name = models.CharField(max_length=255, blank=True)
    region = models.CharField(max_length=100, blank=True)
    auth_type = models.CharField(max_length=50, blank=True)
    access_token_encrypted = models.TextField(blank=True)
    refresh_token_encrypted = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    tax_reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_AUTH)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tax_authority_integrations'

    def __str__(self):
        return f'{self.authority_name} ({self.authority_code})'


class GDriveConnection(models.Model):
    """GDrive source (new invoices) and destination (archive) folders per company."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='gdrive_connections')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='gdrive_connections')
    source_folder_id = models.CharField(max_length=255, blank=True)
    destination_folder_id = models.CharField(max_length=255, blank=True)
    access_token_encrypted = models.TextField(blank=True)
    refresh_token_encrypted = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ConnectedChannel.Status.choices,
        default=ConnectedChannel.Status.PENDING_AUTH,
    )
    last_sync_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gdrive_connections'

    def __str__(self):
        return f'GDrive for {self.company}'
