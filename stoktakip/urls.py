from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views
from accounts.views import CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', views.custom_logout, name='logout'),
    path('stok/', include('stok.urls')),
    path('cari/', include('cari.urls')),
    path('fatura/', include('fatura.urls')),
    path('raporlar/', include('raporlar.urls')),
    path('masraf/', include('masraf.urls')),
    path('finans/', include('finans.urls')),
    path('kullanici-yonetimi/', include('kullanici_yonetimi.urls')),
    path('musteri-paneli/', include('musteri_paneli.urls')),
    path('', views.home, name='home'),
]

# Handler'ları ekle
handler404 = views.handler404
handler500 = views.handler500

# Media files (sadece development için)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
