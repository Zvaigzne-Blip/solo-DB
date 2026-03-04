# Hand-written migration: rename Contact → Counterpart and related models/fields
# Replacing the interactive autodetector which crashes on Django 6.0.3 when
# multiple renames (model + fields) are detected simultaneously.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('solohub', '0002_alter_profile_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── 1. Rename the two models ──────────────────────────────────────────
        migrations.RenameModel(
            old_name='Contact',
            new_name='Counterpart',
        ),
        migrations.RenameModel(
            old_name='ContactAuditLog',
            new_name='CounterpartAuditLog',
        ),

        # ── 2. Rename the FK field inside CounterpartAuditLog ─────────────────
        migrations.RenameField(
            model_name='counterpartauditlog',
            old_name='contact',
            new_name='counterpart',
        ),

        # ── 3. Rename the FK field on InboxMessage ────────────────────────────
        migrations.RenameField(
            model_name='inboxmessage',
            old_name='linked_contact',
            new_name='linked_counterpart',
        ),

        # ── 4. Rename the FK field on Invoice ────────────────────────────────
        migrations.RenameField(
            model_name='invoice',
            old_name='contact',
            new_name='counterpart',
        ),

        # ── 5. Rename the counterpart_type field (was contact_type) ───────────
        migrations.RenameField(
            model_name='counterpart',
            old_name='contact_type',
            new_name='counterpart_type',
        ),

        # ── 6. Update choices on the renamed field ────────────────────────────
        migrations.AlterField(
            model_name='counterpart',
            name='counterpart_type',
            field=models.CharField(
                choices=[
                    ('CLIENT', 'Client'),
                    ('SUPPLIER', 'Supplier'),
                    ('PARTNER', 'Partner'),
                    ('INDIVIDUAL', 'Individual'),
                    ('OTHER', 'Other'),
                ],
                default='CLIENT',
                max_length=10,
            ),
        ),

        # ── 7. Rename the DB tables ───────────────────────────────────────────
        migrations.AlterModelTable(
            name='counterpart',
            table='counterparts',
        ),
        migrations.AlterModelTable(
            name='counterpartauditlog',
            table='counterpart_audit_log',
        ),
    ]
