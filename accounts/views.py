from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from django.core.cache import cache
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from typing import Any
import logging
from .utils import log_action
from .models import AuditLog
from stoktakip.error_handling import handle_view_errors, database_transaction
from stoktakip.security_utils import validate_search_query
from .services.email_service import EmailService

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    """Özel login view'i.

    - Template: templates/registration/login.html
    - "Beni hatırla" (remember_me) checkbox'una göre session süresini ayarlar.
    """

    template_name = "registration/login.html"

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'cari_account'):
            return reverse('musteri_paneli:index')
        return reverse('raporlar:dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)

        remember_me = self.request.POST.get("remember_me")
        if remember_me:
            # 2 hafta boyunca oturum açık kalsın
            self.request.session.set_expiry(60 * 60 * 24 * 14)
        else:
            # Tarayıcı kapanınca oturum sonlansın
            self.request.session.set_expiry(0)

        return response


@handle_view_errors(
    error_message="Kayıt işlemi sırasında bir hata oluştu.",
    redirect_url="accounts:register"
)
@database_transaction
def register(request: Any) -> Any:
    """Kullanıcı kayıt sayfası.

    Rate limiting ve transaction yönetimi ile güvenli hale getirilmiştir.
    """
    # Rate limiting - IP bazlı
    ip_address = request.META.get('REMOTE_ADDR', '')
    cache_key = f'register_rate_limit_{ip_address}'
    attempts = cache.get(cache_key, 0)

    if attempts >= 5:  # 5 dakikada 5 kayıt denemesi
        messages.error(request, 'Çok fazla kayıt denemesi yaptınız. Lütfen 5 dakika sonra tekrar deneyin.')
        return render(request, 'registration/register.html', {'form': UserCreationForm()})

    if request.method == 'POST':
        try:
            form = UserCreationForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    user = form.save()
                    login(request, user)

                    # Rate limiting cache'e kaydet
                    cache.set(cache_key, attempts + 1, 300)  # 5 dakika

                    log_action(user, 'create', None, 'Yeni kullanıcı kaydı', request)
                    messages.success(request, 'Kayıt başarılı!')
                    return redirect('raporlar:dashboard')
            else:
                # Rate limiting cache'e kaydet
                cache.set(cache_key, attempts + 1, 300)
        except Exception as e:
            logger.error(f"Kayıt hatası: {str(e)}", exc_info=True)
            raise
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


@handle_view_errors(
    error_message="Şifre değiştirme işlemi sırasında bir hata oluştu."
)
@login_required
def password_change(request: Any) -> Any:
    """Şifre değiştirme sayfası.

    Error handling ile güvenli hale getirilmiştir.
    """
    try:
        if request.method == 'POST':
            try:
                form = PasswordChangeForm(request.user, request.POST)
                if form.is_valid():
                    user = form.save()
                    update_session_auth_hash(request, user)
                    log_action(request.user, 'update', None, 'Şifre değiştirildi', request)
                    messages.success(request, 'Şifreniz başarıyla değiştirildi!')
                    return redirect('accounts:password_change')
                else:
                    messages.error(request, 'Lütfen hataları düzeltin.')
            except Exception as e:
                logger.error(f"Şifre değiştirme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = PasswordChangeForm(request.user)

        return render(request, 'accounts/password_change.html', {'form': form})
    except Exception as e:
        logger.error(f"Şifre değiştirme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Şifre sıfırlama işlemi sırasında bir hata oluştu."
)
def forgot_password(request: Any) -> Any:
    """Token tabanlı şifre sıfırlama e-postası gönderir.

    EmailService ile mail mantığı merkezi tutulur.
    """
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        user = User.objects.filter(email=email).first()

        # Güvenlik: kullanıcı bulunmasa bile aynı cevap
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = request.build_absolute_uri(
                reverse("accounts:password_reset_confirm", args=[uid, token])
            )

            html_content = f"""
                <h2>Şifre Sıfırlama</h2>
                <p>Şifrenizi sıfırlamak için aşağıdaki linke tıklayın:</p>
                <a href="{reset_link}">Şifreyi Sıfırla</a>
                <br><br>
                <small>Eğer bu isteği siz yapmadıysanız, bu maili yok sayabilirsiniz.</small>
            """

            EmailService.send_email(
                subject="Şifre Sıfırlama Talebi",
                to_email=email,
                html_content=html_content,
            )

        return render(request, "accounts/forgot_password_done.html")

    return render(request, "accounts/forgot_password.html")


@handle_view_errors(error_message="Profil sayfası yüklenirken bir hata oluştu.")
@login_required
def profile(request: Any) -> Any:
    """Kullanıcı profil sayfası.

    Error handling ile güvenli hale getirilmiştir.
    """
    try:
        from .models import UserProfile

        profile, created = UserProfile.objects.get_or_create(user=request.user)

        context = {
            'profile': profile,
            'user': request.user,
        }
        return render(request, 'accounts/profile.html', context)
    except Exception as e:
        logger.error(f"Profil yükleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(error_message="Audit log listesi yüklenirken bir hata oluştu.")
@login_required
def audit_log_list(request: Any) -> Any:
    """Audit log görüntüleme sayfası.

    Admin yetkisi gerektirir. Filtreleme, arama ve sayfalama desteği ile
    audit log listesini gösterir. Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    try:
        log_list = AuditLog.objects.select_related('user', 'content_type').all()

        # Arama - Input validation ile
        search_query = request.GET.get('search', '')
        if search_query:
            try:
                search_query = validate_search_query(search_query, max_length=100)
                log_list = log_list.filter(
                    Q(description__icontains=search_query) |
                    Q(model_name__icontains=search_query) |
                    Q(user__username__icontains=search_query)
                )
            except Exception as e:
                logger.warning(f"Geçersiz arama sorgusu: {str(e)}")
                messages.warning(request, "Geçersiz arama sorgusu.")
                search_query = ''

        # Filtreler - Input validation
        action_filter = request.GET.get('action', '')
        if action_filter:
            valid_actions = [choice[0] for choice in AuditLog.ACTION_CHOICES]
            if action_filter in valid_actions:
                log_list = log_list.filter(action=action_filter)
            else:
                action_filter = ''

        user_filter = request.GET.get('user', '')
        if user_filter:
            try:
                from stoktakip.security_utils import sanitize_integer
                user_id = sanitize_integer(user_filter, min_value=1)
                from django.contrib.auth.models import User
                if User.objects.filter(pk=user_id).exists():
                    log_list = log_list.filter(user_id=user_id)
                else:
                    user_filter = ''
            except Exception:
                user_filter = ''

        # Tarih filtresi - Input validation
        tarih_baslangic = request.GET.get('tarih_baslangic', '')
        tarih_bitis = request.GET.get('tarih_bitis', '')
        if tarih_baslangic and tarih_bitis:
            try:
                from stoktakip.security_utils import validate_date_range
                tarih_baslangic, tarih_bitis = validate_date_range(tarih_baslangic, tarih_bitis)
                log_list = log_list.filter(
                    timestamp__date__gte=tarih_baslangic,
                    timestamp__date__lte=tarih_bitis
                )
            except Exception as e:
                logger.warning(f"Geçersiz tarih aralığı: {str(e)}")
                messages.warning(request, "Geçersiz tarih aralığı.")
                tarih_baslangic = ''
                tarih_bitis = ''
        elif tarih_baslangic:
            log_list = log_list.filter(timestamp__date__gte=tarih_baslangic)
        elif tarih_bitis:
            log_list = log_list.filter(timestamp__date__lte=tarih_bitis)

        # Sayfalama - Input validation
        try:
            from stoktakip.security_utils import sanitize_integer
            page_number = request.GET.get('page', '1')
            page_number = sanitize_integer(page_number, min_value=1)
        except Exception:
            page_number = 1

        paginator = Paginator(log_list, 50)
        logs = paginator.get_page(page_number)

        from django.contrib.auth.models import User

        context = {
            'logs': logs,
            'search_query': search_query,
            'action_filter': action_filter,
            'user_filter': user_filter,
            'tarih_baslangic': tarih_baslangic,
            'tarih_bitis': tarih_bitis,
            'users': User.objects.all().order_by('username'),
            'action_choices': AuditLog.ACTION_CHOICES,
        }
        return render(request, 'accounts/audit_log.html', context)
    except Exception as e:
        logger.error(f"Audit log listesi hatası: {str(e)}", exc_info=True)
        raise
