from django.urls import path
from . import views

app_name = 'fatura'

urlpatterns = [
    path('', views.index, name='index'),
]

