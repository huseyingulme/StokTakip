from django.urls import path
from . import views

app_name = 'stok'

urlpatterns = [
    path('', views.index, name='index'),
    path('ekle/', views.urun_ekle, name='ekle'),
    path('<int:pk>/duzenle/', views.urun_duzenle, name='duzenle'),
    path('<int:pk>/sil/', views.urun_sil, name='sil'),
    path('<int:pk>/stok-duzenle/', views.stok_duzenle, name='stok_duzenle'),
    path('<int:pk>/hareketler/', views.stok_hareketleri, name='hareketler'),
    path('toplu-islem/', views.toplu_stok_islem, name='toplu_islem'),
    path('sayim/', views.stok_sayim, name='sayim'),
]
