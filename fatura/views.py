from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Fatura, FaturaKalem
from .forms import FaturaForm, FaturaKalemForm


@login_required
def index(request):
    """Fatura listesi sayfası"""
    fatura_list = Fatura.objects.all().select_related('cari').order_by('-fatura_tarihi', '-olusturma_tarihi')
    
    # Arama
    search_query = request.GET.get('search', '')
    if search_query:
        fatura_list = fatura_list.filter(
            Q(fatura_no__icontains=search_query) |
            Q(cari__ad_soyad__icontains=search_query)
        )
    
    # Durum filtresi
    durum_filter = request.GET.get('durum', '')
    if durum_filter:
        fatura_list = fatura_list.filter(durum=durum_filter)
    
    # Tip filtresi
    tip_filter = request.GET.get('tip', '')
    if tip_filter:
        fatura_list = fatura_list.filter(fatura_tipi=tip_filter)
    
    # Sayfalama
    paginator = Paginator(fatura_list, 10)
    page_number = request.GET.get('page')
    faturalar = paginator.get_page(page_number)
    
    context = {
        'faturalar': faturalar,
        'search_query': search_query,
        'durum_filter': durum_filter,
        'tip_filter': tip_filter,
    }
    return render(request, 'fatura/index.html', context)


@login_required
def fatura_ekle(request):
    tip = request.GET.get('tip', 'Satis')
    if request.method == 'POST':
        form = FaturaForm(request.POST)
        if form.is_valid():
            fatura = form.save(commit=False)
            fatura.olusturan = request.user
            fatura.save()
            messages.success(request, f'Fatura {fatura.fatura_no} başarıyla oluşturuldu.')
            return redirect('fatura:detay', pk=fatura.pk)
    else:
        form = FaturaForm(initial={'fatura_tipi': tip})
    
    title = 'Yeni Alış Faturası' if tip == 'Alis' else 'Yeni Satış Faturası'
    return render(request, 'fatura/fatura_form.html', {'form': form, 'title': title, 'tip': tip})


@login_required
def fatura_detay(request, pk):
    """Fatura detay sayfası"""
    fatura = get_object_or_404(Fatura, pk=pk)
    kalemler = fatura.kalemler.all().order_by('sira_no')
    
    context = {
        'fatura': fatura,
        'kalemler': kalemler,
    }
    return render(request, 'fatura/fatura_detay.html', context)


@login_required
def fatura_duzenle(request, pk):
    """Fatura düzenleme"""
    fatura = get_object_or_404(Fatura, pk=pk)
    
    if request.method == 'POST':
        form = FaturaForm(request.POST, instance=fatura)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fatura başarıyla güncellendi.')
            return redirect('fatura:detay', pk=fatura.pk)
    else:
        form = FaturaForm(instance=fatura)
    
    return render(request, 'fatura/fatura_form.html', {'form': form, 'title': 'Fatura Düzenle', 'fatura': fatura})


@login_required
def fatura_sil(request, pk):
    fatura = get_object_or_404(Fatura, pk=pk)
    
    if request.method == 'POST':
        fatura_no = fatura.fatura_no
        fatura.delete()
        messages.success(request, f'Fatura {fatura_no} başarıyla silindi.')
        return redirect('fatura:index')
    
    return render(request, 'fatura/fatura_sil.html', {'fatura': fatura})


@login_required
def kalem_ekle(request, fatura_pk):
    fatura = get_object_or_404(Fatura, pk=fatura_pk)
    
    if request.method == 'POST':
        form = FaturaKalemForm(request.POST)
        if form.is_valid():
            kalem = form.save(commit=False)
            kalem.fatura = fatura
            if kalem.urun and not kalem.urun_adi:
                kalem.urun_adi = kalem.urun.ad
            kalem.save()
            messages.success(request, 'Fatura kalemi başarıyla eklendi.')
            return redirect('fatura:detay', pk=fatura_pk)
    else:
        form = FaturaKalemForm()
    
    return render(request, 'fatura/kalem_form.html', {'form': form, 'fatura': fatura, 'title': 'Yeni Kalem Ekle'})


@login_required
def kalem_duzenle(request, pk):
    kalem = get_object_or_404(FaturaKalem, pk=pk)
    fatura = kalem.fatura
    
    if request.method == 'POST':
        form = FaturaKalemForm(request.POST, instance=kalem)
        if form.is_valid():
            kalem = form.save(commit=False)
            if kalem.urun and not kalem.urun_adi:
                kalem.urun_adi = kalem.urun.ad
            kalem.save()
            messages.success(request, 'Fatura kalemi başarıyla güncellendi.')
            return redirect('fatura:detay', pk=fatura.pk)
    else:
        form = FaturaKalemForm(instance=kalem)
    
    return render(request, 'fatura/kalem_form.html', {'form': form, 'fatura': fatura, 'kalem': kalem, 'title': 'Kalem Düzenle'})


@login_required
def kalem_sil(request, pk):
    kalem = get_object_or_404(FaturaKalem, pk=pk)
    fatura_pk = kalem.fatura.pk
    
    if request.method == 'POST':
        kalem.delete()
        messages.success(request, 'Fatura kalemi başarıyla silindi.')
        return redirect('fatura:detay', pk=fatura_pk)
    
    return render(request, 'fatura/kalem_sil.html', {'kalem': kalem})
