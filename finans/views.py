from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import HesapKart, FinansHareketi


@login_required
def index(request):
    hesaplar = HesapKart.objects.filter(durum=True)
    hareketler = FinansHareketi.objects.all().order_by('-tarih', '-id')[:50]
    
    context = {
        'hesaplar': hesaplar,
        'hareketler': hareketler,
    }
    return render(request, 'finans/index.html', context)
