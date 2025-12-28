import logging
from functools import wraps
from typing import Callable, Any, Optional
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.core.exceptions import ValidationError, PermissionDenied
from accounts.utils import log_action

logger = logging.getLogger(__name__)


def handle_view_errors(
    error_message: str = "Bir hata oluştu. Lütfen tekrar deneyin.",
    redirect_url: Optional[str] = None,
    log_error: bool = False 
):
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                return view_func(request, *args, **kwargs)
            except ValidationError as e:
                # Validation hataları için özel mesaj
                messages.error(request, str(e))
                if log_error:
                    logger.warning(f"Validation error in {view_func.__name__}: {str(e)}", 
                                 extra={'user': request.user.username if hasattr(request, 'user') else None})
                if redirect_url:
                    return redirect(redirect_url)
                # Form hatalarını göstermek için aynı sayfada kal
                return view_func(request, *args, **kwargs)
            except PermissionDenied as e:
                error_msg = str(e) if str(e) else "Bu işlem için yetkiniz yok."
                messages.error(request, error_msg)
                if log_error:
                    logger.warning(f"Permission denied in {view_func.__name__}: {error_msg}",
                                 extra={'user': request.user.username if hasattr(request, 'user') else None})
                
                # JSON response için
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg}, status=403)
                
                # Eğer redirect_url varsa ve dashboard/home değilse kullan
                if redirect_url and 'dashboard' not in redirect_url and 'home' not in redirect_url and 'raporlar' not in redirect_url:
                    return redirect(redirect_url)
                
                # Ana sayfaya yönlendir (daha iyi UX)
                from django.shortcuts import render
                try:
                    # Önce home sayfasına yönlendirmeyi dene
                    return redirect('home')
                except:
                    try:
                        # Eğer home yoksa dashboard'a yönlendir
                        return redirect('raporlar:dashboard')
                    except:
                        # Eğer hiçbiri yoksa 403 sayfası göster
                        return render(request, '403.html', {
                            'error': error_msg,
                        }, status=403)
            except Exception as e:
                # Genel exception handling
                import traceback
                import sys
                
                if log_error:
                    logger.error(f"Error in {view_func.__name__}: {str(e)}", 
                               exc_info=True,
                               extra={'user': request.user.username if hasattr(request, 'user') else None})
                    # Audit log'a da kaydet
                    if hasattr(request, 'user') and request.user.is_authenticated:
                        try:
                            log_action(request.user, 'error', None, 
                                     f'Hata: {view_func.__name__} - {str(e)}', request)
                        except Exception:
                            pass  # Log action hatası görmezden gel
                
                messages.error(request, error_message)
                
                if redirect_url:
                    return redirect(redirect_url)
                
                # JSON response için
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'success': False, 'error': error_message}, status=500)
                
                # Normal HTML response için - Her zaman detaylı hata göster (DEBUG modunda)
                from django.shortcuts import render
                from django.conf import settings
                error_context = {
                    'error': error_message,
                    'exception': str(e),
                    'traceback': traceback.format_exc()
                }
                return render(request, '500.html', error_context, status=500)
        
        return wrapper
    return decorator


def handle_api_errors(
    error_message: str = "API request failed",
    status_code: int = 500
):
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return view_func(*args, **kwargs)
            except ValidationError as e:
                logger.warning(f"API validation error in {view_func.__name__}: {str(e)}")
                # DRF Response için
                try:
                    from rest_framework.response import Response
                    from rest_framework import status as drf_status
                    return Response({'detail': str(e)}, status=drf_status.HTTP_400_BAD_REQUEST)
                except ImportError:
                    # Django JsonResponse için
                    return JsonResponse({'success': False, 'error': str(e)}, status=400)
            except PermissionDenied:
                logger.warning(f"API permission denied in {view_func.__name__}")
                try:
                    from rest_framework.response import Response
                    from rest_framework import status as drf_status
                    return Response({'detail': 'Yetkiniz yok'}, status=drf_status.HTTP_403_FORBIDDEN)
                except ImportError:
                    return JsonResponse({'success': False, 'error': 'Yetkiniz yok'}, status=403)
            except Exception as e:
                logger.error(f"API error in {view_func.__name__}: {str(e)}", exc_info=True)
                try:
                    from rest_framework.response import Response
                    from rest_framework import status as drf_status
                    return Response({'detail': error_message}, status=status_code)
                except ImportError:
                    return JsonResponse({'success': False, 'error': error_message}, status=status_code)
        
        return wrapper
    return decorator


def database_transaction(view_func: Callable) -> Callable:

    @wraps(view_func)
    def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            # Transaction zaten rollback olacak ama loglama yapalım
            logger.error(f"Database transaction error in {view_func.__name__}: {str(e)}", 
                        exc_info=True)
            raise  # Exception'ı yukarı fırlat
    
    return wrapper


