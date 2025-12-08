from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def role_required(*role_names):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            
            user_groups = request.user.groups.values_list('name', flat=True)
            if not any(role in user_groups for role in role_names):
                raise PermissionDenied("Bu işlem için yetkiniz yok.")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    return role_required('Admin')(view_func)


def muhasebe_required(view_func):
    return role_required('Admin', 'Muhasebe')(view_func)


def satis_required(view_func):
    return role_required('Admin', 'Satış')(view_func)


def depo_required(view_func):
    return role_required('Admin', 'Depo')(view_func)

