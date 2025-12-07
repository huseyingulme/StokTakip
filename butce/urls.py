from django.urls import path
from . import views

app_name = 'butce'

urlpatterns = [
    path('', views.index, name='index'),
]

