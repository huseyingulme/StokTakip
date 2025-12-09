from django.urls import path
from . import views

app_name = 'kullanici_yonetimi'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:user_id>/', views.kullanici_detay, name='kullanici_detay'),
    path('<int:user_id>/rapor/', views.kullanici_rapor, name='kullanici_rapor'),
]

