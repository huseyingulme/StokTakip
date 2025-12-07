from django.urls import path
from . import views

app_name = 'finans'

urlpatterns = [
    path('', views.index, name='index'),
]

