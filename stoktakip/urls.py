from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', views.custom_logout, name='logout'),
    path('stok/', include('stok.urls')),
    path('cari/', include('cari.urls')),
    path('fatura/', include('fatura.urls')),
    path('raporlar/', include('raporlar.urls')),
    path('masraf/', include('masraf.urls')),
    path('finans/', include('finans.urls')),
    path('kullanici-yonetimi/', include('kullanici_yonetimi.urls')),
    path('api/', include('api.urls')),
    path('', views.home, name='home'),
]

# API Documentation (drf-spectacular kullanılırsa)
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]
except ImportError:
    # drf-spectacular yoksa drf-yasg dene
    try:
        from drf_yasg.views import get_schema_view
        from drf_yasg import openapi
        from rest_framework import permissions
        
        schema_view = get_schema_view(
            openapi.Info(
                title="Stok Takip API",
                default_version='v1',
                description="Stok Takip Sistemi API Dokümantasyonu",
                terms_of_service="https://www.example.com/terms/",
                contact=openapi.Contact(email="contact@example.com"),
                license=openapi.License(name="BSD License"),
            ),
            public=True,
            permission_classes=(permissions.AllowAny,),
        )
        
        urlpatterns += [
            path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
            path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
            path('api/swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        ]
    except ImportError:
        # API documentation paketleri yoksa devam et
        pass

# Handler'ları ekle
handler404 = views.handler404
handler500 = views.handler500

# Media files (sadece development için)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
