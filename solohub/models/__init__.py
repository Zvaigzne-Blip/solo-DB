"""
SoloHub Django Models — Package Init
Imports all models from submodules for Django's app registry.
"""

# Core & IAM (Module 6, Section 1)
from .core import (
    Profile,
    Workspace,
    Company,
    WorkspaceMember,
    RolePermission,
    WorkspacePreference,
)

# Integrations (Module 6, Section 2)
from .integrations import (
    ConnectedChannel,
    BankConnection,
    TaxAuthorityIntegration,
    GDriveConnection,
)

# Counterparts (formerly Contacts)
from .contacts import (
    Counterpart,
    CounterpartAuditLog,
)

# Smart Inbox (Module 1)
from .inbox import (
    InboxMessage,
    InboxAttachment,
)

# Invoices — Purchase AP & Sales AR (Modules 2 & 3)
from .invoices import (
    Invoice,
    InvoiceLineItem,
    InvoiceStatusHistory,
    InvoiceCommunication,
    DunningRule,
)

# Banking Hub (Module 4)
from .banking import (
    BankAccount,
    BankTransaction,
    PaymentTransaction,
)

# Accountant Hub (Module 5)
from .accountant import (
    AccountantTask,
    TaskDocument,
    ComplianceDeadline,
    ChatMessage,
    ChatAttachment,
)

# Gmail Add-on (Module 8) & Dashboard (Module 7)
from .gmail_dashboard import (
    GmailLabelMapping,
    GmailSyncLog,
    DashboardKPICache,
    Notification,
    AuditLog,
)

__all__ = [
    # Core
    'Profile', 'Workspace', 'Company', 'WorkspaceMember',
    'RolePermission', 'WorkspacePreference',
    # Integrations
    'ConnectedChannel', 'BankConnection', 'TaxAuthorityIntegration',
    'GDriveConnection',
    # Contacts
    'Contact', 'ContactAuditLog',
    # Inbox
    'InboxMessage', 'InboxAttachment',
    # Invoices
    'Invoice', 'InvoiceLineItem', 'InvoiceStatusHistory',
    'InvoiceCommunication', 'DunningRule',
    # Banking
    'BankAccount', 'BankTransaction', 'PaymentTransaction',
    # Accountant
    'AccountantTask', 'TaskDocument', 'ComplianceDeadline',
    'ChatMessage', 'ChatAttachment',
    # Gmail & Dashboard
    'GmailLabelMapping', 'GmailSyncLog', 'DashboardKPICache',
    'Notification', 'AuditLog',
]
