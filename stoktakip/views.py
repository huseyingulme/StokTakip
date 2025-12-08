from django.shortcuts import render, redirect
from django.http import HttpResponseNotFound, HttpResponseServerError
from django.contrib.auth.decorators import login_required


def handler404(request, exception):
    """404 hata sayfası"""
    return render(request, '404.html', status=404)


def handler500(request):
    """500 hata sayfası"""
    return render(request, '500.html', status=500)


def home(request):
    """Ana sayfa - Giriş yapmamış kullanıcıları login'e yönlendir"""
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect('raporlar:dashboard')
