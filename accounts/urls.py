from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('password-change/', views.password_change, name='password_change'),
    path('password-reset/', views.password_reset, name='password_reset'),
    path('audit-log/', views.audit_log_list, name='audit_log'),
]

