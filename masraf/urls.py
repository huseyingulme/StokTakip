from django.urls import path
from . import views

app_name = 'masraf'

urlpatterns = [
    path('', views.index, name='index'),
    path('ekle/', views.masraf_ekle, name='ekle'),
    path('<int:pk>/duzenle/', views.masraf_duzenle, name='duzenle'),
    path('<int:pk>/sil/', views.masraf_sil, name='sil'),
]

