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
    """Yeni fatura ekleme"""
    if request.method == 'POST':
        form = FaturaForm(request.POST)
        if form.is_valid():
            fatura = form.save()
            messages.success(request, f'Fatura {fatura.fatura_no} başarıyla oluşturuldu.')
            return redirect('fatura:detay', pk=fatura.pk)
    else:
        form = FaturaForm()
    
    return render(request, 'fatura/fatura_form.html', {'form': form, 'title': 'Yeni Fatura Oluştur'})


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
    """Fatura silme"""
    fatura = get_object_or_404(Fatura, pk=pk)
    
    if request.method == 'POST':
        fatura_no = fatura.fatura_no
        fatura.delete()
        messages.success(request, f'Fatura {fatura_no} başarıyla silindi.')
        return redirect('fatura:index')
    
    return render(request, 'fatura/fatura_sil.html', {'fatura': fatura})
