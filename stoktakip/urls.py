from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('stok/', include('stok.urls')),
    path('cari/', include('cari.urls')),
    path('fatura/', include('fatura.urls')),
    path('raporlar/', include('raporlar.urls')),
    path('masraf/', include('masraf.urls')),
    path('finans/', include('finans.urls')),
    path('butce/', include('butce.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]
