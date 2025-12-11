from django.urls import path
from . import views

app_name = 'cari'

urlpatterns = [
    path('', views.index, name='index'),
    path('ekle/', views.cari_ekle, name='ekle'),
    path('<int:pk>/', views.cari_detay, name='detay'),
    path('<int:pk>/duzenle/', views.cari_duzenle, name='duzenle'),
    path('<int:pk>/sil/', views.cari_sil, name='sil'),
    path('<int:pk>/ekstre/', views.cari_ekstre, name='ekstre'),
    path('hareketler/', views.hareket_listesi, name='hareket_listesi'),
    path('hareket/ekle/', views.hareket_ekle, name='hareket_ekle'),
    path('hareket/<int:cari_pk>/ekle/', views.hareket_ekle, name='hareket_cari_ekle'),
    path('hareket/<int:pk>/duzenle/', views.hareket_duzenle, name='hareket_duzenle'),
    path('hareket/<int:pk>/sil/', views.hareket_sil, name='hareket_sil'),
    path('<int:cari_pk>/not/ekle/', views.not_ekle, name='not_ekle'),
    path('not/<int:pk>/duzenle/', views.not_duzenle, name='not_duzenle'),
    path('not/<int:pk>/sil/', views.not_sil, name='not_sil'),
    path('tahsilat/ekle/', views.tahsilat_makbuzu_ekle, name='tahsilat_ekle'),
    path('tahsilat/<int:cari_pk>/ekle/', views.tahsilat_makbuzu_ekle, name='tahsilat_cari_ekle'),
    path('tahsilat/', views.tahsilat_makbuzu_listesi, name='tahsilat_listesi'),
    path('tediye/ekle/', views.tediye_makbuzu_ekle, name='tediye_ekle'),
    path('tediye/<int:cari_pk>/ekle/', views.tediye_makbuzu_ekle, name='tediye_cari_ekle'),
    path('tediye/', views.tediye_makbuzu_listesi, name='tediye_listesi'),
]
