from django.urls import path
from . import views

app_name = 'raporlar'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('kar-maliyet/', views.kar_maliyet_raporu, name='kar_maliyet_raporu'),
    path('alis/', views.alis_raporu, name='alis_raporu'),
    path('alis/excel/', views.alis_raporu_excel, name='alis_raporu_excel'),
    path('satis/', views.satis_raporu, name='satis_raporu'),
    path('satis/excel/', views.satis_raporu_excel, name='satis_raporu_excel'),
]


