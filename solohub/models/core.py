"""
SoloHub Django Models — Core & IAM (Module 6, Section 1)
Workspaces, Companies, Profiles, Workspace Members, RBAC
"""
import uuid
from django.db import models
from django.conf import settings


class Profile(models.Model):
    """Extended user profile — 1:1 with Django's built-in User."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        null=True, blank=True,
    )
    full_name = models.CharField(max_length=255, blank=True)
    display_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles'

    def __str__(self):
        return self.display_name or self.full_name or str(self.id)


class Workspace(models.Model):
    """Top-level tenant container."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='owned_workspaces',
    )
    base_currency = models.CharField(max_length=3, default='USD')
    timezone = models.CharField(max_length=50, default='UTC')
    logo_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workspaces'

    def __str__(self):
        return self.name


class Company(models.Model):
    """Corporate entity within a workspace. Default entity auto-provisioned on workspace creation."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='companies')
    legal_name = models.CharField(max_length=255)
    trade_name = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    logo_url = models.URLField(blank=True)
    is_default = models.BooleanField(default=False)
    is_individual = models.BooleanField(default=False)
    base_currency = models.CharField(max_length=3, default='USD')
    fiscal_year_start = models.IntegerField(default=1)  # month 1-12
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'companies'

    def __str__(self):
        return self.legal_name


class WorkspaceMember(models.Model):
    """Maps users to workspaces with RBAC. Tracks invitation lifecycle."""
    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'
        ACCOUNTANT = 'accountant', 'Accountant'
        MEMBER = 'member', 'Member'
        VIEWER = 'viewer', 'Viewer'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACTIVE = 'active', 'Active'
        SUSPENDED = 'suspended', 'Suspended'
        REMOVED = 'removed', 'Removed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='workspace_memberships',
    )
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sent_invitations',
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workspace_members'
        unique_together = [('workspace', 'email')]

    def __str__(self):
        return f'{self.email} ({self.role}) in {self.workspace}'


class RolePermission(models.Model):
    """Fine-grained RBAC permission matrix."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=WorkspaceMember.Role.choices)
    resource = models.CharField(max_length=100)  # 'invoices', 'bank_accounts', etc.
    action = models.CharField(max_length=50)  # 'create', 'read', 'update', 'delete', 'approve', 'pay'
    is_allowed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'role_permissions'
        unique_together = [('role', 'resource', 'action')]

    def __str__(self):
        return f'{self.role} can {"" if self.is_allowed else "NOT "}{self.action} {self.resource}'


class WorkspacePreference(models.Model):
    """System-wide environment variables (base_currency, default_payment_terms, etc.)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='preferences')
    key = models.CharField(max_length=100)
    value = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workspace_preferences'
        unique_together = [('workspace', 'key')]

    def __str__(self):
        return f'{self.workspace.name}: {self.key}'
