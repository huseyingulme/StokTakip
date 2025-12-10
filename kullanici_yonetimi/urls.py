from django.urls import path
from . import views

app_name = 'kullanici_yonetimi'

urlpatterns = [
    path('', views.index, name='index'),
    path('liste/', views.kullanici_listesi, name='kullanici_listesi'),
    path('ekle/', views.kullanici_ekle, name='kullanici_ekle'),
    path('<int:user_id>/', views.kullanici_detay, name='kullanici_detay'),
    path('<int:user_id>/duzenle/', views.kullanici_duzenle, name='kullanici_duzenle'),
    path('<int:user_id>/sil/', views.kullanici_sil, name='kullanici_sil'),
    path('<int:user_id>/rapor/', views.kullanici_rapor, name='kullanici_rapor'),
]

