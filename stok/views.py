from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Urun
from .forms import UrunForm


@login_required
def index(request):
    """Stok listesi sayfası"""
    urun_list = Urun.objects.all().order_by('ad')
    
    # Arama
    search_query = request.GET.get('search', '')
    if search_query:
        urun_list = urun_list.filter(ad__icontains=search_query) | \
                   urun_list.filter(barkod__icontains=search_query)
    
    # Sayfalama
    paginator = Paginator(urun_list, 10)
    page_number = request.GET.get('page')
    urunler = paginator.get_page(page_number)
    
    context = {
        'urunler': urunler,
        'search_query': search_query,
    }
    return render(request, 'stok/index.html', context)


@login_required
def urun_ekle(request):
    """Yeni ürün ekleme"""
    if request.method == 'POST':
        form = UrunForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ürün başarıyla eklendi.')
            return redirect('stok:index')
    else:
        form = UrunForm()
    
    return render(request, 'stok/urun_form.html', {'form': form, 'title': 'Yeni Ürün Ekle'})


@login_required
def urun_duzenle(request, pk):
    """Ürün düzenleme"""
    urun = get_object_or_404(Urun, pk=pk)
    
    if request.method == 'POST':
        form = UrunForm(request.POST, instance=urun)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ürün başarıyla güncellendi.')
            return redirect('stok:index')
    else:
        form = UrunForm(instance=urun)
    
    return render(request, 'stok/urun_form.html', {'form': form, 'title': 'Ürün Düzenle', 'urun': urun})


@login_required
def urun_sil(request, pk):
    """Ürün silme"""
    urun = get_object_or_404(Urun, pk=pk)
    
    if request.method == 'POST':
        urun.delete()
        messages.success(request, 'Ürün başarıyla silindi.')
        return redirect('stok:index')
    
    return render(request, 'stok/urun_sil.html', {'urun': urun})
