from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from .models import HesapKart, FinansHareketi
from .forms import HesapKartForm, FinansHareketiForm


@login_required
def index(request):
    hesaplar = HesapKart.objects.filter(durum=True)
    hareketler = FinansHareketi.objects.all().order_by('-tarih', '-id')
    
    # Filtreleme
    hesap_filter = request.GET.get('hesap', '')
    if hesap_filter:
        hareketler = hareketler.filter(hesap_id=hesap_filter)
    
    hareket_tipi_filter = request.GET.get('hareket_tipi', '')
    if hareket_tipi_filter:
        hareketler = hareketler.filter(hareket_tipi=hareket_tipi_filter)
    
    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    if tarih_baslangic:
        hareketler = hareketler.filter(tarih__gte=tarih_baslangic)
    if tarih_bitis:
        hareketler = hareketler.filter(tarih__lte=tarih_bitis)
    
    # Toplamlar
    toplam_gelir = hareketler.filter(hareket_tipi='gelir').aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
    toplam_gider = hareketler.filter(hareket_tipi='gider').aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
    toplam_transfer = hareketler.filter(hareket_tipi='transfer').aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
    net_bakiye = toplam_gelir - toplam_gider
    
    paginator = Paginator(hareketler, 20)
    page_number = request.GET.get('page')
    hareketler_page = paginator.get_page(page_number)
    
    context = {
        'hesaplar': hesaplar,
        'hareketler': hareketler_page,
        'toplam_gelir': toplam_gelir,
        'toplam_gider': toplam_gider,
        'toplam_transfer': toplam_transfer,
        'net_bakiye': net_bakiye,
        'hesap_filter': hesap_filter,
        'hareket_tipi_filter': hareket_tipi_filter,
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
    }
    return render(request, 'finans/index.html', context)


@login_required
def hesap_ekle(request):
    if request.method == 'POST':
        form = HesapKartForm(request.POST)
        if form.is_valid():
            hesap = form.save()
            messages.success(request, 'Hesap kartı başarıyla eklendi.')
            return redirect('finans:index')
    else:
        form = HesapKartForm()
    
    return render(request, 'finans/hesap_form.html', {'form': form, 'title': 'Yeni Hesap Ekle'})


@login_required
def hesap_duzenle(request, pk):
    hesap = get_object_or_404(HesapKart, pk=pk)
    
    if request.method == 'POST':
        form = HesapKartForm(request.POST, instance=hesap)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hesap kartı başarıyla güncellendi.')
            return redirect('finans:index')
    else:
        form = HesapKartForm(instance=hesap)
    
    return render(request, 'finans/hesap_form.html', {'form': form, 'title': 'Hesap Düzenle', 'hesap': hesap})


@login_required
def hesap_sil(request, pk):
    hesap = get_object_or_404(HesapKart, pk=pk)
    
    if request.method == 'POST':
        hesap.delete()
        messages.success(request, 'Hesap kartı başarıyla silindi.')
        return redirect('finans:index')
    
    return render(request, 'finans/hesap_sil.html', {'hesap': hesap})


@login_required
def hareket_ekle(request):
    if request.method == 'POST':
        form = FinansHareketiForm(request.POST)
        if form.is_valid():
            hareket = form.save(commit=False)
            if not hareket.olusturan:
                hareket.olusturan = request.user
            hareket.save()
            messages.success(request, 'Finans hareketi başarıyla eklendi.')
            return redirect('finans:index')
    else:
        form = FinansHareketiForm()
    
    return render(request, 'finans/hareket_form.html', {'form': form, 'title': 'Yeni Finans Hareketi Ekle'})


@login_required
def hareket_duzenle(request, pk):
    hareket = get_object_or_404(FinansHareketi, pk=pk)
    
    if request.method == 'POST':
        form = FinansHareketiForm(request.POST, instance=hareket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Finans hareketi başarıyla güncellendi.')
            return redirect('finans:index')
    else:
        form = FinansHareketiForm(instance=hareket)
    
    return render(request, 'finans/hareket_form.html', {'form': form, 'title': 'Finans Hareketi Düzenle', 'hareket': hareket})


@login_required
def hareket_sil(request, pk):
    hareket = get_object_or_404(FinansHareketi, pk=pk)
    
    if request.method == 'POST':
        hareket.delete()
        messages.success(request, 'Finans hareketi başarıyla silindi.')
        return redirect('finans:index')
    
    return render(request, 'finans/hareket_sil.html', {'hareket': hareket})
