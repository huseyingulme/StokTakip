from django.urls import path
from . import views

app_name = 'fatura'

urlpatterns = [
    path('', views.index, name='index'),
    path('ekle/', views.fatura_ekle, name='ekle'),
    path('<int:pk>/', views.fatura_detay, name='detay'),
    path('<int:pk>/duzenle/', views.fatura_duzenle, name='duzenle'),
    path('<int:pk>/sil/', views.fatura_sil, name='sil'),
]
