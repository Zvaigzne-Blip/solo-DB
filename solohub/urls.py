"""
SoloHub API URL configuration.
All endpoints available under /api/ (see config/urls.py).

Module routing:
  /api/profiles/               — user profiles
  /api/workspaces/             — multi-tenant workspaces
  /api/companies/              — legal entities
  /api/members/                — workspace members
  /api/permissions/            — RBAC role permissions
  /api/preferences/            — workspace key/value settings
  /api/channels/               — OAuth connected channels (Gmail, WhatsApp…)
  /api/bank-connections/       — Open Banking connections (Plaid/TrueLayer)
  /api/tax-integrations/       — HMRC / MTD integrations
  /api/gdrive/                 — Google Drive connections
  /api/counterparts/          — unified vendor + customer directory
  /api/counterpart-audit/     — counterpart change history
  /api/inbox/                  — smart unified inbox
  /api/attachments/            — inbox attachments + OCR
  /api/invoices/               — unified AP + AR invoices
  /api/line-items/             — invoice line items
  /api/invoice-history/        — invoice status history
  /api/communications/         — invoice dispatch / dunning log
  /api/dunning-rules/          — automated dunning rule templates
  /api/bank-accounts/          — bank accounts
  /api/transactions/           — bank transactions + reconciliation
  /api/payments/               — payment execution log
  /api/tasks/                  — accountant tasks
  /api/task-documents/         — documents attached to tasks
  /api/deadlines/              — compliance deadlines
  /api/chat/                   — accountant AI chat messages
  /api/chat-attachments/       — chat message attachments
  /api/gmail-labels/           — Gmail label ↔ invoice status mapping
  /api/gmail-sync-log/         — Gmail sync event log
  /api/kpi/                    — dashboard KPI cache
  /api/notifications/          — user notifications
  /api/audit/                  — global audit log (admin only)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    # Core / IAM
    ProfileViewSet, WorkspaceViewSet, CompanyViewSet,
    WorkspaceMemberViewSet, RolePermissionViewSet, WorkspacePreferenceViewSet,
    # Integrations
    ConnectedChannelViewSet, BankConnectionViewSet, TaxAuthorityIntegrationViewSet,
    GDriveConnectionViewSet,
    # Counterparts
    CounterpartViewSet, CounterpartAuditLogViewSet,
    # Inbox
    InboxMessageViewSet, InboxAttachmentViewSet,
    # Invoices
    InvoiceViewSet, InvoiceLineItemViewSet, InvoiceStatusHistoryViewSet,
    InvoiceCommunicationViewSet, DunningRuleViewSet,
    # Banking
    BankAccountViewSet, BankTransactionViewSet, PaymentTransactionViewSet,
    # Accountant
    AccountantTaskViewSet, TaskDocumentViewSet, ComplianceDeadlineViewSet,
    ChatMessageViewSet, ChatAttachmentViewSet,
    # Gmail & Dashboard
    GmailLabelMappingViewSet, GmailSyncLogViewSet, DashboardKPICacheViewSet,
    # Cross-cutting
    NotificationViewSet, AuditLogViewSet,
)

router = DefaultRouter()

# Core / IAM
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'members', WorkspaceMemberViewSet, basename='workspacemember')
router.register(r'permissions', RolePermissionViewSet, basename='rolepermission')
router.register(r'preferences', WorkspacePreferenceViewSet, basename='workspacepreference')

# Integrations
router.register(r'channels', ConnectedChannelViewSet, basename='connectedchannel')
router.register(r'bank-connections', BankConnectionViewSet, basename='bankconnection')
router.register(r'tax-integrations', TaxAuthorityIntegrationViewSet, basename='taxauthorityintegration')
router.register(r'gdrive', GDriveConnectionViewSet, basename='gdriveconnection')

# Counterparts
router.register(r'counterparts', CounterpartViewSet, basename='counterpart')
router.register(r'counterpart-audit', CounterpartAuditLogViewSet, basename='counterpartauditlog')

# Inbox
router.register(r'inbox', InboxMessageViewSet, basename='inboxmessage')
router.register(r'attachments', InboxAttachmentViewSet, basename='inboxattachment')

# Invoices
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'line-items', InvoiceLineItemViewSet, basename='invoicelineitem')
router.register(r'invoice-history', InvoiceStatusHistoryViewSet, basename='invoicestatushistory')
router.register(r'communications', InvoiceCommunicationViewSet, basename='invoicecommunication')
router.register(r'dunning-rules', DunningRuleViewSet, basename='dunningrule')

# Banking
router.register(r'bank-accounts', BankAccountViewSet, basename='bankaccount')
router.register(r'transactions', BankTransactionViewSet, basename='banktransaction')
router.register(r'payments', PaymentTransactionViewSet, basename='paymenttransaction')

# Accountant Hub
router.register(r'tasks', AccountantTaskViewSet, basename='accountanttask')
router.register(r'task-documents', TaskDocumentViewSet, basename='taskdocument')
router.register(r'deadlines', ComplianceDeadlineViewSet, basename='compliancedeadline')
router.register(r'chat', ChatMessageViewSet, basename='chatmessage')
router.register(r'chat-attachments', ChatAttachmentViewSet, basename='chatattachment')

# Gmail & Dashboard
router.register(r'gmail-labels', GmailLabelMappingViewSet, basename='gmaillabelmapping')
router.register(r'gmail-sync-log', GmailSyncLogViewSet, basename='gmailsynclog')
router.register(r'kpi', DashboardKPICacheViewSet, basename='dashboardkpicache')

# Cross-cutting
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'audit', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('', include(router.urls)),
]
