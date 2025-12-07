from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ButceKategori, Butce


@login_required
def index(request):
    butceler = Butce.objects.all().order_by('-baslangic_tarihi')
    kategoriler = ButceKategori.objects.all()
    
    context = {
        'butceler': butceler,
        'kategoriler': kategoriler,
    }
    return render(request, 'butce/index.html', context)
