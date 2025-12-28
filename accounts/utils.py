from django.contrib.contenttypes.models import ContentType
from .models import AuditLog

def log_action(user, action, obj, description, request=None):
    """
    Audit log kaydı oluşturur.
    
    Args:
        user: İşlemi yapan kullanıcı
        action: İşlem türü (create, update, delete, vs.)
        obj: İşlem yapılan obje (opsiyonel)
        description: İşlem açıklaması
        request: HTTP request (IP ve User-Agent için opsiyonel)
    """
    try:
        log_data = {
            'user': user if user and user.is_authenticated else None,
            'action': action,
            'description': description,
            'model_name': obj.__class__.__name__ if obj else 'System',
        }
        
        if obj:
            log_data['content_type'] = ContentType.objects.get_for_model(obj)
            log_data['object_id'] = obj.pk
            
        if request:
            log_data['ip_address'] = request.META.get('REMOTE_ADDR')
            log_data['user_agent'] = request.META.get('HTTP_USER_AGENT')
            
        return AuditLog.objects.create(**log_data)
    except Exception as e:
        # Loglama hatası ana akışı bozmamalı
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Audit log error: {str(e)}")
        return None
