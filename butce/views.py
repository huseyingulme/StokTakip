from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from .models import ButceKategori, Butce
from .forms import ButceKategoriForm, ButceForm
from masraf.models import Masraf


@login_required
def index(request):
    butceler = Butce.objects.all().order_by('-baslangic_tarihi')
    kategoriler = ButceKategori.objects.all()
    
    # Filtreleme
    kategori_filter = request.GET.get('kategori', '')
    if kategori_filter:
        butceler = butceler.filter(kategori_id=kategori_filter)
    
    donem_filter = request.GET.get('donem', '')
    if donem_filter:
        butceler = butceler.filter(donem=donem_filter)
    
    # Toplam bütçe ve harcama
    toplam_butce = butceler.aggregate(toplam=Sum('butce_tutari'))['toplam'] or Decimal('0.00')
    
    paginator = Paginator(butceler, 20)
    page_number = request.GET.get('page')
    butceler_page = paginator.get_page(page_number)
    
    context = {
        'butceler': butceler_page,
        'kategoriler': kategoriler,
        'toplam_butce': toplam_butce,
        'kategori_filter': kategori_filter,
        'donem_filter': donem_filter,
    }
    return render(request, 'butce/index.html', context)


@login_required
def butce_ekle(request):
    if request.method == 'POST':
        form = ButceForm(request.POST)
        if form.is_valid():
            butce = form.save(commit=False)
            if not butce.olusturan:
                butce.olusturan = request.user
            butce.save()
            messages.success(request, 'Bütçe başarıyla eklendi.')
            return redirect('butce:index')
    else:
        form = ButceForm()
    
    return render(request, 'butce/butce_form.html', {'form': form, 'title': 'Yeni Bütçe Ekle'})


@login_required
def butce_duzenle(request, pk):
    butce = get_object_or_404(Butce, pk=pk)
    
    if request.method == 'POST':
        form = ButceForm(request.POST, instance=butce)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bütçe başarıyla güncellendi.')
            return redirect('butce:index')
    else:
        form = ButceForm(instance=butce)
    
    return render(request, 'butce/butce_form.html', {'form': form, 'title': 'Bütçe Düzenle', 'butce': butce})


@login_required
def butce_sil(request, pk):
    butce = get_object_or_404(Butce, pk=pk)
    
    if request.method == 'POST':
        butce.delete()
        messages.success(request, 'Bütçe başarıyla silindi.')
        return redirect('butce:index')
    
    return render(request, 'butce/butce_sil.html', {'butce': butce})


@login_required
def butce_detay(request, pk):
    butce = get_object_or_404(Butce, pk=pk)
    
    # Bütçe dönemindeki masraflar
    masraflar = Masraf.objects.filter(
        tarih__gte=butce.baslangic_tarihi,
        tarih__lte=butce.bitis_tarihi,
        durum='odendi'
    )
    
    harcanan = masraflar.aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
    kalan = butce.butce_tutari - harcanan
    kullanım_yuzdesi = (harcanan / butce.butce_tutari * 100) if butce.butce_tutari > 0 else Decimal('0.00')
    
    context = {
        'butce': butce,
        'masraflar': masraflar,
        'harcanan': harcanan,
        'kalan': kalan,
        'kullanım_yuzdesi': kullanım_yuzdesi,
    }
    return render(request, 'butce/butce_detay.html', context)
