from .utils import log_action
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    log_action(user, 'login', description=f'Kullanıcı giriş yaptı: {user.username}')


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        log_action(user, 'logout', description=f'Kullanıcı çıkış yaptı: {user.username}')


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

