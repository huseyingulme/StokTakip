from django.urls import path
from . import views

app_name = 'fatura'

urlpatterns = [
    path('', views.index, name='index'),
    path('ekle/', views.fatura_ekle, name='ekle'),
    path('<int:pk>/', views.fatura_detay, name='detay'),
    path('<int:pk>/duzenle/', views.fatura_duzenle, name='duzenle'),
    path('<int:pk>/sil/', views.fatura_sil, name='sil'),
    path('<int:fatura_pk>/kalem/ekle/', views.kalem_ekle, name='kalem_ekle'),
    path('kalem/<int:pk>/duzenle/', views.kalem_duzenle, name='kalem_duzenle'),
    path('kalem/<int:pk>/sil/', views.kalem_sil, name='kalem_sil'),
    path('api/urun/<int:urun_id>/', views.urun_bilgi_api, name='urun_bilgi_api'),
]
