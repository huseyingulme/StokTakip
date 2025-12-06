from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Musteri
from .forms import MusteriForm


@login_required
def index(request):
    """Müşteri listesi sayfası"""
    musteri_list = Musteri.objects.all().order_by('ad_soyad')
    
    # Arama
    search_query = request.GET.get('search', '')
    if search_query:
        musteri_list = musteri_list.filter(ad_soyad__icontains=search_query) | \
                      musteri_list.filter(tc_vkn__icontains=search_query) | \
                      musteri_list.filter(telefon__icontains=search_query)
    
    # Tip filtresi
    tip_filter = request.GET.get('tip', '')
    if tip_filter:
        musteri_list = musteri_list.filter(tip=tip_filter)
    
    # Sayfalama
    paginator = Paginator(musteri_list, 10)
    page_number = request.GET.get('page')
    musteriler = paginator.get_page(page_number)
    
    context = {
        'musteriler': musteriler,
        'search_query': search_query,
        'tip_filter': tip_filter,
    }
    return render(request, 'cari/index.html', context)


@login_required
def musteri_ekle(request):
    """Yeni müşteri ekleme"""
    if request.method == 'POST':
        form = MusteriForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Müşteri başarıyla eklendi.')
            return redirect('cari:index')
    else:
        form = MusteriForm()
    
    return render(request, 'cari/musteri_form.html', {'form': form, 'title': 'Yeni Müşteri Ekle'})


@login_required
def musteri_duzenle(request, pk):
    """Müşteri düzenleme"""
    musteri = get_object_or_404(Musteri, pk=pk)
    
    if request.method == 'POST':
        form = MusteriForm(request.POST, instance=musteri)
        if form.is_valid():
            form.save()
            messages.success(request, 'Müşteri başarıyla güncellendi.')
            return redirect('cari:index')
    else:
        form = MusteriForm(instance=musteri)
    
    return render(request, 'cari/musteri_form.html', {'form': form, 'title': 'Müşteri Düzenle', 'musteri': musteri})


@login_required
def musteri_sil(request, pk):
    """Müşteri silme"""
    musteri = get_object_or_404(Musteri, pk=pk)
    
    if request.method == 'POST':
        musteri.delete()
        messages.success(request, 'Müşteri başarıyla silindi.')
        return redirect('cari:index')
    
    return render(request, 'cari/musteri_sil.html', {'musteri': musteri})
