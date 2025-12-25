from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def musteri_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Kullanıcının Cari kaydı var mı kontrol et
        if hasattr(request.user, 'cari_account'):
            return view_func(request, *args, **kwargs)
        
        # Eğer personelse dashboard'a gönder, aksi halde hata ver
        if request.user.is_staff:
            messages.info(request, "Müşteri paneli sadece müşteriler içindir.")
            return redirect('raporlar:dashboard')
        
        messages.error(request, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")
        return redirect('login')
        
    return _wrapped_view
