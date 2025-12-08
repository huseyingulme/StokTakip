from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from .models import Urun, StokHareketi, Kategori
from .forms import UrunForm
from accounts.utils import log_action


@login_required
def index(request):
    """Stok listesi sayfası"""
    urun_list = Urun.objects.select_related('kategori').all().order_by('ad')
    
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
    from fatura.models import FaturaKalem
    urun = get_object_or_404(Urun, pk=pk)
    
    if request.method == 'POST':
        fatura_kalemleri = FaturaKalem.objects.filter(urun=urun)
        if fatura_kalemleri.exists():
            messages.error(request, 'Bu ürün fatura kalemlerinde kullanıldığı için silinemez!')
            return redirect('stok:index')
        
        stok_hareketleri = StokHareketi.objects.filter(urun=urun)
        if stok_hareketleri.exists():
            messages.error(request, 'Bu ürün stok hareketlerinde kullanıldığı için silinemez!')
            return redirect('stok:index')
        
        urun.delete()
        messages.success(request, 'Ürün başarıyla silindi.')
        return redirect('stok:index')
    
    fatura_kalemleri = FaturaKalem.objects.filter(urun=urun)
    stok_hareketleri = StokHareketi.objects.filter(urun=urun)
    
    return render(request, 'stok/urun_sil.html', {
        'urun': urun,
        'fatura_kalemleri': fatura_kalemleri,
        'stok_hareketleri': stok_hareketleri
    })


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
    hareketler = StokHareketi.objects.filter(urun=urun).select_related('olusturan').order_by('-tarih')
    
    paginator = Paginator(hareketler, 20)
    page_number = request.GET.get('page')
    hareketler_page = paginator.get_page(page_number)
    
    return render(request, 'stok/stok_hareketleri.html', {
        'urun': urun,
        'hareketler': hareketler_page
    })


@login_required
def toplu_stok_islem(request):
    if request.method == 'POST':
        urun_ids = request.POST.getlist('urun_ids')
        islem_turu = request.POST.get('islem_turu')
        miktar = int(request.POST.get('miktar', 0))
        aciklama = request.POST.get('aciklama', 'Toplu işlem')
        
        if not urun_ids:
            messages.error(request, 'Lütfen en az bir ürün seçin.')
            return redirect('stok:index')
        
        if miktar <= 0:
            messages.error(request, 'Miktar 0\'dan büyük olmalıdır.')
            return redirect('stok:index')
        
        islem_sayisi = 0
        for urun_id in urun_ids:
            try:
                urun = Urun.objects.get(pk=urun_id)
                StokHareketi.objects.create(
                    urun=urun,
                    islem_turu=islem_turu,
                    miktar=miktar,
                    aciklama=aciklama,
                    tarih=timezone.now(),
                    olusturan=request.user
                )
                islem_sayisi += 1
            except Urun.DoesNotExist:
                continue
        
        log_action(request.user, 'create', description=f'Toplu stok işlemi: {islem_turu} - {islem_sayisi} ürün')
        messages.success(request, f'{islem_sayisi} ürün için stok {islem_turu} işlemi başarıyla yapıldı.')
        return redirect('stok:index')
    
    urunler = Urun.objects.all().order_by('ad')
    return render(request, 'stok/toplu_stok_islem.html', {'urunler': urunler})


@login_required
def stok_sayim(request):
    if request.method == 'POST':
        sayim_verileri = {}
        for key, value in request.POST.items():
            if key.startswith('urun_') and key.endswith('_miktar'):
                urun_id = key.replace('urun_', '').replace('_miktar', '')
                try:
                    gercek_miktar = int(value)
                    sayim_verileri[int(urun_id)] = gercek_miktar
                except ValueError:
                    continue
        
        fark_sayisi = 0
        for urun_id, gercek_miktar in sayim_verileri.items():
            try:
                urun = Urun.objects.get(pk=urun_id)
                mevcut_stok = urun.mevcut_stok
                fark = gercek_miktar - mevcut_stok
                
                if fark != 0:
                    islem_turu = 'giriş' if fark > 0 else 'çıkış'
                    StokHareketi.objects.create(
                        urun=urun,
                        islem_turu=islem_turu,
                        miktar=abs(fark),
                        aciklama=f'Stok sayımı - Mevcut: {mevcut_stok}, Gerçek: {gercek_miktar}',
                        tarih=timezone.now(),
                        olusturan=request.user
                    )
                    fark_sayisi += 1
            except Urun.DoesNotExist:
                continue
        
        log_action(request.user, 'create', description=f'Stok sayımı tamamlandı - {fark_sayisi} fark bulundu')
        messages.success(request, f'Stok sayımı tamamlandı. {fark_sayisi} üründe fark bulundu ve düzeltildi.')
        return redirect('stok:index')
    
    urunler = Urun.objects.all().order_by('ad')
    return render(request, 'stok/stok_sayim.html', {'urunler': urunler})
