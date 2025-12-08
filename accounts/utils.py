from django.contrib.contenttypes.models import ContentType
from .models import AuditLog


def log_action(user, action, obj=None, description='', request=None):
    if obj:
        content_type = ContentType.objects.get_for_model(obj)
        model_name = obj.__class__.__name__
        object_id = obj.pk
    else:
        content_type = None
        model_name = description.split('-')[0] if '-' in description else 'System'
        object_id = None

    ip_address = None
    user_agent = None
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

    AuditLog.objects.create(
        user=user,
        action=action,
        content_type=content_type,
        object_id=object_id,
        model_name=model_name,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent
    )


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

