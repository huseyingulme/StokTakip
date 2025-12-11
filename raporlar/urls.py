from django.urls import path
from . import views

app_name = 'raporlar'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('kar-maliyet/', views.kar_maliyet_raporu, name='kar_maliyet_raporu'),
    path('alis/', views.alis_raporu, name='alis_raporu'),
    path('satis/', views.satis_raporu, name='satis_raporu'),
]


