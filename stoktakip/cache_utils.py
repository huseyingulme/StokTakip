"""
Caching utility fonksiyonları.
View-level caching, query result caching için decorator'lar ve helper'lar.
"""
from functools import wraps
from typing import Callable, Any, Optional
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers


def cache_view_result(timeout: int = 300, key_prefix: Optional[str] = None):
    """
    View sonuçlarını cache'ler.
    
    Args:
        timeout: Cache süresi (saniye cinsinden, default: 5 dakika)
        key_prefix: Cache key prefix (None ise fonksiyon adı kullanılır)
    
    Usage:
        @cache_view_result(timeout=600, key_prefix='dashboard')
        def dashboard(request):
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            # Cache key oluştur
            prefix = key_prefix or view_func.__name__
            cache_key = f"{prefix}_{request.user.id if request.user.is_authenticated else 'anon'}"
            
            # Query parametrelerini cache key'e ekle
            if request.GET:
                query_string = '_'.join(f"{k}_{v}" for k, v in sorted(request.GET.items()))
                cache_key += f"_{query_string}"
            
            # Cache'den oku
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # View'ı çalıştır
            result = view_func(request, *args, **kwargs)
            
            # HttpResponse objelerini cache'leme (sadece render edilmiş içerik)
            # HttpResponse objeleri pickle edilemez, bu yüzden cache'lemiyoruz
            from django.http import HttpResponse
            if isinstance(result, HttpResponse):
                # HttpResponse'ları cache'leme, sadece return et
                return result
            
            # Cache'e yaz
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator


def cache_query_result(timeout: int = 300):
    """
    Query sonuçlarını cache'ler.
    Fonksiyonun return değerini cache'ler.
    
    Args:
        timeout: Cache süresi (saniye cinsinden)
    
    Usage:
        @cache_query_result(timeout=600)
        def get_dashboard_stats():
            return {...}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Cache key oluştur (fonksiyon adı + argümanlar)
            cache_key = f"{func.__name__}_{str(args)}_{str(sorted(kwargs.items()))}"
            
            # Cache'den oku
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Fonksiyonu çalıştır
            result = func(*args, **kwargs)
            
            # Cache'e yaz
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Belirli bir pattern'e uyan cache key'lerini siler.
    
    Args:
        pattern: Cache key pattern (örn: 'dashboard_*')
    
    Usage:
        invalidate_cache('dashboard_*')
    """
    # Django cache backend'ine göre değişir
    # Redis kullanılıyorsa pattern matching yapılabilir
    # LocMemCache için tüm cache'i temizlemek gerekebilir
    try:
        # Redis için pattern matching
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        keys = redis_conn.keys(f"stoktakip:{pattern}")
        if keys:
            redis_conn.delete(*keys)
    except Exception:
        # Redis yoksa veya hata varsa, cache'i temizle
        cache.clear()


def get_or_set_cache(key: str, callable_func: Callable, timeout: int = 300) -> Any:
    """
    Cache'den oku, yoksa fonksiyonu çalıştır ve cache'e yaz.
    
    Args:
        key: Cache key
        callable_func: Cache'de yoksa çalıştırılacak fonksiyon
        timeout: Cache süresi
    
    Returns:
        Cache'den veya fonksiyondan dönen değer
    
    Usage:
        stats = get_or_set_cache('dashboard_stats', lambda: calculate_stats(), timeout=600)
    """
    result = cache.get(key)
    if result is None:
        result = callable_func()
        cache.set(key, result, timeout)
    return result

