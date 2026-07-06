from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import AuditLog
from .middleware import get_current_user, get_current_ip


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    # Avoid recursive logging of AuditLog itself
    if sender == AuditLog:
        return

    # Introspect table existence and columns to avoid breaking migrations
    from django.db import connection
    if 'audit_auditlog' not in connection.introspection.table_names():
        return
    try:
        with connection.cursor() as cursor:
            columns = [col[0] for col in connection.introspection.get_table_description(cursor, 'audit_auditlog')]
        if 'user_id' not in columns:
            return
    except Exception:
        return

    # Check if this model is auditable (standard practice is to log almost all models)
    if not hasattr(instance, '_meta'):
        return

    user = get_current_user()
    ip = get_current_ip()
    action = 'CREATE' if created else 'UPDATE'
    
    # Try serialization of changes
    changes = {}
    if action == 'UPDATE':
        # Standard delta calculation could be complex, we log key details or a dump of current state
        # In a robust system, we serialize key attributes. Let's dump a standard representation.
        try:
            changes = {"detail": str(instance)}
        except Exception:
            pass
    else:
        try:
            changes = {"created": str(instance)}
        except Exception:
            pass

    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=sender.__name__,
            object_id=str(instance.pk),
            changes=changes,
            ip_address=ip
        )
    except Exception:
        pass


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    if sender == AuditLog:
        return

    # Introspect table existence and columns to avoid breaking migrations
    from django.db import connection
    if 'audit_auditlog' not in connection.introspection.table_names():
        return
    try:
        with connection.cursor() as cursor:
            columns = [col[0] for col in connection.introspection.get_table_description(cursor, 'audit_auditlog')]
        if 'user_id' not in columns:
            return
    except Exception:
        return

    user = get_current_user()
    ip = get_current_ip()

    try:
        AuditLog.objects.create(
            user=user,
            action='DELETE',
            model_name=sender.__name__,
            object_id=str(instance.pk),
            changes={"deleted": str(instance)},
            ip_address=ip
        )
    except Exception:
        pass
