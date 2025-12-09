from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
import secrets
import string
from .utils import log_action
from .models import AuditLog


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            log_action(user, 'create', description='Yeni kullanıcı kaydı')
            messages.success(request, 'Kayıt başarılı!')
            return redirect('raporlar:dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def password_change(request):
    """Şifre değiştirme sayfası"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_action(request.user, 'update', description='Şifre değiştirildi')
            messages.success(request, 'Şifreniz başarıyla değiştirildi!')
            return redirect('accounts:password_change')
        else:
            messages.error(request, 'Lütfen hataları düzeltin.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/password_change.html', {'form': form})


def password_reset(request):
    """Şifre sıfırlama - E-posta kontrolü ve rastgele şifre oluşturma"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Lütfen e-posta adresinizi girin.')
            return render(request, 'registration/password_reset.html')
        
        try:
            # Veritabanında e-posta ile kullanıcı ara
            user = User.objects.get(email=email)
            
            # Rastgele şifre oluştur (12 karakter: büyük harf, küçük harf, rakam, özel karakter)
            alphabet = string.ascii_letters + string.digits + "!@#$%&*"
            new_password = ''.join(secrets.choice(alphabet) for i in range(12))
            
            # Şifreyi kaydet
            user.set_password(new_password)
            user.save()
            
            # Audit log
            log_action(user, 'update', description=f'Şifre sıfırlandı (e-posta: {email})')
            
            # Başarılı sayfasına yönlendir ve şifreyi göster
            return render(request, 'registration/password_reset_success.html', {
                'new_password': new_password,
                'email': email,
                'username': user.username
            })
            
        except User.DoesNotExist:
            messages.error(request, 'Bu e-posta adresi ile kayıtlı kullanıcı bulunamadı.')
        except Exception as e:
            messages.error(request, f'Bir hata oluştu: {str(e)}')
    
    return render(request, 'registration/password_reset.html')


@login_required
def profile(request):
    """Kullanıcı profil sayfası"""
    from .models import UserProfile
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def audit_log_list(request):
    """Audit log görüntüleme sayfası"""
    log_list = AuditLog.objects.select_related('user', 'content_type').all()
    
    # Arama
    search_query = request.GET.get('search', '')
    if search_query:
        log_list = log_list.filter(
            Q(description__icontains=search_query) |
            Q(model_name__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    # Filtreler
    action_filter = request.GET.get('action', '')
    if action_filter:
        log_list = log_list.filter(action=action_filter)
    
    user_filter = request.GET.get('user', '')
    if user_filter:
        log_list = log_list.filter(user_id=user_filter)
    
    # Tarih filtresi
    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    if tarih_baslangic:
        log_list = log_list.filter(timestamp__date__gte=tarih_baslangic)
    if tarih_bitis:
        log_list = log_list.filter(timestamp__date__lte=tarih_bitis)
    
    # Sayfalama
    paginator = Paginator(log_list, 50)
    page_number = request.GET.get('page')
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

