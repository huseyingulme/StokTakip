from django.urls import path
from . import views

app_name = 'butce'

urlpatterns = [
    path('', views.index, name='index'),
    path('ekle/', views.butce_ekle, name='ekle'),
    path('<int:pk>/duzenle/', views.butce_duzenle, name='duzenle'),
    path('<int:pk>/sil/', views.butce_sil, name='sil'),
    path('<int:pk>/detay/', views.butce_detay, name='detay'),
]

