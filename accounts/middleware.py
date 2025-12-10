from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import time


class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Rate limiting sadece API ve login sayfaları için
        if request.path.startswith('/api/') or request.path.startswith('/accounts/login/'):
            try:
                ip = self.get_client_ip(request)
                cache_key = f'ratelimit_{ip}_{request.path}'
                
                # 1 dakikada 60 istek limiti
                requests = cache.get(cache_key, 0)
                if requests >= 60:
                    return HttpResponse('Rate limit exceeded. Please try again later.', status=429)
                
                cache.set(cache_key, requests + 1, 60)  # 60 saniye TTL
            except Exception:
                # Cache hatası durumunda rate limiting'i atla
                pass
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware:
    """Security headers ekler"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
