from django.urls import path
from . import views

app_name = 'musteri_paneli'

urlpatterns = [
    path('', views.index, name='index'),
    path('faturalar/', views.fatura_listesi, name='fatura_listesi'),
    path('faturalar/<int:pk>/', views.fatura_detay, name='fatura_detay'),
    path('ekstre/', views.ekstre, name='ekstre'),
    path('tahsilatlar/', views.tahsilat_listesi, name='tahsilat_listesi'),
    path('siparisler/', views.siparis_listesi, name='siparis_listesi'),
    path('siparisler/yeni/', views.siparis_olustur, name='siparis_olustur'),
    path('siparisler/<int:pk>/', views.siparis_detay, name='siparis_detay'),
    path('profil/', views.profil, name='profil'),
    
    # Admin Yolları
    path('yonetim/siparisler/', views.admin_siparis_listesi, name='admin_siparis_listesi'),
    path('yonetim/siparisler/<int:pk>/', views.admin_siparis_detay, name='admin_siparis_detay'),
    path('yonetim/siparisler/<int:pk>/<str:islem>/', views.admin_siparis_islem, name='admin_siparis_islem'),
]
