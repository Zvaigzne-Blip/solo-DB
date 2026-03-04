"""
SoloHub Django Models — Banking Hub (Module 4)
"""
import uuid
from django.db import models
from .core import Workspace, Company
from .integrations import BankConnection


class BankAccount(models.Model):
    """Individual bank accounts synced via Open Banking."""
    class AccountType(models.TextChoices):
        CHECKING = 'checking', 'Checking'
        SAVINGS = 'savings', 'Savings'
        CREDIT_CARD = 'credit_card', 'Credit Card'
        LOAN = 'loan', 'Loan'
        INVESTMENT = 'investment', 'Investment'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        CLOSED = 'closed', 'Closed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='bank_accounts')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_accounts')
    connection = models.ForeignKey(BankConnection, on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts')
    external_account_id = models.CharField(max_length=255, blank=True)
    account_name = models.CharField(max_length=255)
    institution_name = models.CharField(max_length=255, blank=True)
    institution_logo_url = models.URLField(blank=True)
    account_type = models.CharField(max_length=20, choices=AccountType.choices, default=AccountType.CHECKING)
    account_number_masked = models.CharField(max_length=20, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    available_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_updated_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    is_internal = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_accounts'

    def __str__(self):
        return f'{self.institution_name} — {self.account_name} ({self.account_number_masked})'


class BankTransaction(models.Model):
    """Bank statement lines synced via Open Banking. AI Matcher reconciles against invoices."""
    class TransactionType(models.TextChoices):
        CREDIT = 'credit', 'Credit'
        DEBIT = 'debit', 'Debit'

    class Category(models.TextChoices):
        INVOICE_PAYMENT = 'invoice_payment', 'Invoice Payment'
        VENDOR_PAYMENT = 'vendor_payment', 'Vendor Payment'
        INTERNAL_TRANSFER = 'internal_transfer', 'Internal Transfer'
        BANK_FEE = 'bank_fee', 'Bank Fee'
        INTEREST = 'interest', 'Interest'
        TAX_PAYMENT = 'tax_payment', 'Tax Payment'
        SALARY = 'salary', 'Salary'
        SUBSCRIPTION = 'subscription', 'Subscription'
        REFUND = 'refund', 'Refund'
        OTHER = 'other', 'Other'
        UNCATEGORIZED = 'uncategorized', 'Uncategorized'

    class ReconciliationStatus(models.TextChoices):
        MATCHED = 'matched', 'Matched'
        UNMATCHED = 'unmatched', 'Unmatched'
        MISSING_INVOICE = 'missing_invoice', 'Missing Invoice'
        INTERNAL_TRANSFER = 'internal_transfer', 'Internal Transfer'
        AUTO_CATEGORIZED = 'auto_categorized', 'Auto-Categorized'
        MANUALLY_RESOLVED = 'manually_resolved', 'Manually Resolved'
        PENDING = 'pending', 'Pending'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='bank_transactions')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_transactions')
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    external_transaction_id = models.CharField(max_length=255, blank=True)
    # Core fields
    transaction_date = models.DateField()
    posted_date = models.DateField(null=True, blank=True)
    value_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=255, blank=True)
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    running_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    # Auto-categorization
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.UNCATEGORIZED)
    category_confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    # Reconciliation (Matcher Agent)
    reconciliation_status = models.CharField(
        max_length=20, choices=ReconciliationStatus.choices, default=ReconciliationStatus.PENDING
    )
    linked_invoice = models.ForeignKey(
        'Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_transactions'
    )
    linked_transfer_account = models.ForeignKey(
        BankAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfer_transactions'
    )
    match_confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    matched_at = models.DateTimeField(null=True, blank=True)
    matched_by = models.CharField(max_length=50, blank=True)
    # Gap Analysis routing
    accountant_task = models.ForeignKey(
        'AccountantTask', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_transactions'
    )
    #
    counterparty_name = models.CharField(max_length=255, blank=True)
    counterparty_account = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_transactions'
        ordering = ['-transaction_date']

    def __str__(self):
        return f'{self.transaction_date} {self.get_transaction_type_display()} {self.currency} {self.amount}'


class PaymentTransaction(models.Model):
    """Records of payment initiations via PIS/payment-gateway."""
    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        CREDIT_CARD = 'credit_card', 'Credit Card'
        DEBIT_CARD = 'debit_card', 'Debit Card'
        CHECK = 'check', 'Check'
        CASH = 'cash', 'Cash'
        PAYPAL = 'paypal', 'PayPal'
        OTHER = 'other', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='payment_transactions')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payment_transactions')
    invoice = models.ForeignKey(
        'Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_executions'
    )
    gateway = models.CharField(max_length=100, blank=True)
    gateway_transaction_id = models.CharField(max_length=255, blank=True)
    gateway_status = models.CharField(max_length=50, blank=True)
    direction = models.CharField(max_length=10)  # 'outbound' or 'inbound'
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    fee_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, blank=True)
    initiated_by = models.UUIDField(null=True, blank=True)
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    linked_bank_transaction = models.ForeignKey(
        BankTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_executions'
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.direction} {self.currency} {self.amount} via {self.gateway}'
