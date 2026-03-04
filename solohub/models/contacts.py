"""
SoloHub Django Models — Counterparts (Vendors & Customers)
"""
import uuid
from django.db import models
from .core import Workspace, Company


class Counterpart(models.Model):
    """Unified vendor/customer directory. Bank details encrypted at rest."""
    class CounterpartType(models.TextChoices):
        VENDOR = 'vendor', 'Vendor'
        CUSTOMER = 'customer', 'Customer'
        BOTH = 'both', 'Both'
        INDIVIDUAL = 'individual', 'Individual'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='counterparts')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='counterparts')
    counterpart_type = models.CharField(max_length=10, choices=CounterpartType.choices, default=CounterpartType.VENDOR)
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    # Bank details (encrypted columns)
    bank_name = models.CharField(max_length=255, blank=True)
    bank_account_number_encrypted = models.TextField(blank=True)
    bank_routing_number_encrypted = models.TextField(blank=True)
    bank_iban_encrypted = models.TextField(blank=True)
    bank_swift = models.CharField(max_length=20, blank=True)
    bank_currency = models.CharField(max_length=3, blank=True)
    # Terms
    payment_terms_days = models.IntegerField(default=30)
    default_currency = models.CharField(max_length=3, default='USD')
    # Risk scores
    credit_risk_score = models.SmallIntegerField(null=True, blank=True)  # 1-5
    fraud_risk_score = models.SmallIntegerField(null=True, blank=True)  # 1-5
    # Behavioral stats (denormalized)
    total_invoices = models.IntegerField(default=0)
    total_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    avg_payment_days = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    last_invoice_date = models.DateField(null=True, blank=True)
    #
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'counterparts'

    def __str__(self):
        return f'{self.name} ({self.get_counterpart_type_display()})'


class CounterpartAuditLog(models.Model):
    """Immutable log of vendor/customer field mutations for fraud detection."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    counterpart = models.ForeignKey(Counterpart, on_delete=models.CASCADE, related_name='audit_logs')
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    changed_by = models.UUIDField(null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'counterpart_audit_log'

    def __str__(self):
        return f'{self.counterpart.name}: {self.field_name} changed'
