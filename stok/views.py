from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Urun, StokHareketi
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
    urun = get_object_or_404(Urun, pk=pk)
    
    if request.method == 'POST':
        urun.delete()
        messages.success(request, 'Ürün başarıyla silindi.')
        return redirect('stok:index')
    
    return render(request, 'stok/urun_sil.html', {'urun': urun})


@login_required
def stok_duzenle(request, pk):
    urun = get_object_or_404(Urun, pk=pk)
    
    if request.method == 'POST':
        islem_turu = request.POST.get('islem_turu')
        miktar = int(request.POST.get('miktar', 0))
        aciklama = request.POST.get('aciklama', '')
        
        if miktar > 0:
            StokHareketi.objects.create(
                urun=urun,
                islem_turu=islem_turu,
                miktar=miktar,
                aciklama=aciklama,
                tarih=timezone.now(),
                olusturan=request.user
            )
            messages.success(request, f'Stok {islem_turu} işlemi başarıyla yapıldı.')
            return redirect('stok:index')
        else:
            messages.error(request, 'Miktar 0\'dan büyük olmalıdır.')
    
    return render(request, 'stok/stok_duzenle.html', {'urun': urun})


@login_required
def stok_hareketleri(request, pk):
    urun = get_object_or_404(Urun, pk=pk)
    hareketler = StokHareketi.objects.filter(urun=urun).order_by('-tarih')
    
    paginator = Paginator(hareketler, 20)
    page_number = request.GET.get('page')
    hareketler_page = paginator.get_page(page_number)
    
    return render(request, 'stok/stok_hareketleri.html', {
        'urun': urun,
        'hareketler': hareketler_page
    })
