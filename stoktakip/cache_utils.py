"""
Caching utility fonksiyonları.
View-level caching, query result caching için decorator'lar ve helper'lar.
"""
from functools import wraps
from typing import Callable, Any, Optional
from django.core.cache import cache


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



