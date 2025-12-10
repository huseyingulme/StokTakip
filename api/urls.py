from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API versioning için router
router = DefaultRouter()
router.register(r'kategoriler', views.KategoriViewSet, basename='kategori')
router.register(r'urunler', views.UrunViewSet, basename='urun')
router.register(r'stok-hareketleri', views.StokHareketiViewSet, basename='stok-hareketi')
router.register(r'cariler', views.CariViewSet, basename='cari')
router.register(r'cari-hareketleri', views.CariHareketiViewSet, basename='cari-hareketi')
router.register(r'faturalar', views.FaturaViewSet, basename='fatura')

# API versioning: v1/ prefix ile
urlpatterns = [
    path('v1/', include(router.urls)),
    # Backward compatibility için eski URL'ler
    path('', include(router.urls)),
]

