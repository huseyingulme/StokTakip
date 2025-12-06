from django.urls import path
from . import views

app_name = 'stok'

urlpatterns = [
    path('', views.index, name='index'),
    path('ekle/', views.urun_ekle, name='ekle'),
    path('<int:pk>/duzenle/', views.urun_duzenle, name='duzenle'),
    path('<int:pk>/sil/', views.urun_sil, name='sil'),
]
