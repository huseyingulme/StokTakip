from django.urls import path
from . import views

app_name = 'finans'

urlpatterns = [
    path('', views.index, name='index'),
    path('hesap/ekle/', views.hesap_ekle, name='hesap_ekle'),
    path('hesap/<int:pk>/duzenle/', views.hesap_duzenle, name='hesap_duzenle'),
    path('hesap/<int:pk>/sil/', views.hesap_sil, name='hesap_sil'),
    path('hareket/ekle/', views.hareket_ekle, name='hareket_ekle'),
    path('hareket/<int:pk>/duzenle/', views.hareket_duzenle, name='hareket_duzenle'),
    path('hareket/<int:pk>/sil/', views.hareket_sil, name='hareket_sil'),
]

