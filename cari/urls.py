from django.urls import path
from . import views

app_name = 'cari'

urlpatterns = [
    path('', views.index, name='index'),
    path('ekle/', views.musteri_ekle, name='ekle'),
    path('<int:pk>/duzenle/', views.musteri_duzenle, name='duzenle'),
    path('<int:pk>/sil/', views.musteri_sil, name='sil'),
]
