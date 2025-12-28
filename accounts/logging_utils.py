import logging
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger('stoktakip')


def log_info(message, user=None, extra_data=None):
    """Info seviyesinde log kaydı"""
    log_data = {
        'level': 'INFO',
        'message': message,
        'user': str(user) if user else 'Anonymous',
        'timestamp': timezone.now().isoformat(),
        'extra': extra_data or {}
    }
    logger.info(message, extra=log_data)


def log_warning(message, user=None, extra_data=None):
    """Warning seviyesinde log kaydı"""
    log_data = {
        'level': 'WARNING',
        'message': message,
        'user': str(user) if user else 'Anonymous',
        'timestamp': timezone.now().isoformat(),
        'extra': extra_data or {}
    }
    logger.warning(message, extra=log_data)


def log_error(message, user=None, extra_data=None, exc_info=None):
    """Error seviyesinde log kaydı"""
    log_data = {
        'level': 'ERROR',
        'message': message,
        'user': str(user) if user else 'Anonymous',
        'timestamp': timezone.now().isoformat(),
        'extra': extra_data or {}
    }
    logger.error(message, extra=log_data, exc_info=exc_info)


def get_recent_logs(level=None, hours=24, limit=100):
    """Son log kayıtlarını getirir (cache'den)"""
    cache_key = f'recent_logs_{level}_{hours}'
    logs = cache.get(cache_key)
    
    if logs is None:
        # Bu basit bir implementasyon, gerçek uygulamada log dosyasından okunmalı
        logs = []
        cache.set(cache_key, logs, 300)  # 5 dakika cache
    
    return logs[:limit]