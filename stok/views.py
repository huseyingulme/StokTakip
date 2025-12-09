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
        urun_list = urun_list.filter(
            Q(ad__icontains=search_query) |
            Q(barkod__icontains=search_query) |
            Q(kategori__ad__icontains=search_query)
        )
    
    # Kategori filtresi
    kategori_filter = request.GET.get('kategori', '')
    if kategori_filter:
        urun_list = urun_list.filter(kategori_id=kategori_filter)
    
    # Stok durumu filtresi
    stok_durumu = request.GET.get('stok_durumu', '')
    if stok_durumu == 'dusuk':
        # Düşük stoklu ürünler
        urun_list = [u for u in urun_list if u.mevcut_stok < u.min_stok_adedi]
    elif stok_durumu == 'stoksuz':
        # Stoksuz ürünler
        urun_list = [u for u in urun_list if u.mevcut_stok == 0]
    elif stok_durumu == 'normal':
        # Normal stoklu ürünler
        urun_list = [u for u in urun_list if u.mevcut_stok >= u.min_stok_adedi]
    
    # Fiyat aralığı filtresi
    fiyat_min = request.GET.get('fiyat_min', '')
    fiyat_max = request.GET.get('fiyat_max', '')
    if fiyat_min:
        try:
            urun_list = urun_list.filter(fiyat__gte=float(fiyat_min))
        except ValueError:
            pass
    if fiyat_max:
        try:
            urun_list = urun_list.filter(fiyat__lte=float(fiyat_max))
        except ValueError:
            pass
    
    # Sayfalama
    paginator = Paginator(urun_list, 20)
    page_number = request.GET.get('page')
    urunler = paginator.get_page(page_number)
    
    # Stok uyarıları - Sadece stoksuz ürünler
    stoksuz_urunler = [u for u in Urun.objects.all() if u.mevcut_stok == 0]
    
    context = {
        'urunler': urunler,
        'search_query': search_query,
        'kategori_filter': kategori_filter,
        'stok_durumu': stok_durumu,
        'fiyat_min': fiyat_min,
        'fiyat_max': fiyat_max,
        'kategoriler': Kategori.objects.all().order_by('ad'),
        'stoksuz_urunler': stoksuz_urunler[:10],
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
        islem_turu = request.POST.get('islem_turu', '').strip()
        miktar_str = request.POST.get('miktar', '0').strip()
        aciklama = request.POST.get('aciklama', 'Toplu işlem').strip() or 'Toplu işlem'
        
        # Validasyon
        if not urun_ids:
            messages.error(request, 'Lütfen en az bir ürün seçin.')
            urunler = Urun.objects.all().order_by('ad')
            return render(request, 'stok/toplu_stok_islem.html', {'urunler': urunler})
        
        if not islem_turu:
            messages.error(request, 'Lütfen işlem türü seçin.')
            urunler = Urun.objects.all().order_by('ad')
            return render(request, 'stok/toplu_stok_islem.html', {'urunler': urunler})
        
        try:
            miktar = int(miktar_str)
            if miktar <= 0:
                messages.error(request, 'Miktar 0\'dan büyük olmalıdır.')
                urunler = Urun.objects.all().order_by('ad')
                return render(request, 'stok/toplu_stok_islem.html', {'urunler': urunler})
        except (ValueError, TypeError):
            messages.error(request, 'Geçerli bir miktar girin.')
            urunler = Urun.objects.all().order_by('ad')
            return render(request, 'stok/toplu_stok_islem.html', {'urunler': urunler})
        
        # Çıkış işleminde stok kontrolü
        if islem_turu == 'çıkış':
            yetersiz_stok_urunler = []
            for urun_id in urun_ids:
                try:
                    urun = Urun.objects.get(pk=urun_id)
                    if urun.mevcut_stok < miktar:
                        yetersiz_stok_urunler.append(urun.ad)
                except Urun.DoesNotExist:
                    continue
            
            if yetersiz_stok_urunler:
                messages.warning(request, f'Bazı ürünlerde yetersiz stok var: {", ".join(yetersiz_stok_urunler[:5])}')
                # Yine de işlemi yap, kullanıcı bilgilendirildi
        
        islem_sayisi = 0
        hata_sayisi = 0
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
                log_action(request.user, 'create', urun, f'Toplu stok işlemi: {islem_turu} - {miktar} {urun.birim}')
            except Urun.DoesNotExist:
                hata_sayisi += 1
                continue
            except Exception as e:
                hata_sayisi += 1
                continue
        
        if islem_sayisi > 0:
            log_action(request.user, 'create', description=f'Toplu stok işlemi: {islem_turu} - {islem_sayisi} ürün')
            messages.success(request, f'{islem_sayisi} ürün için stok {islem_turu} işlemi başarıyla yapıldı.')
        if hata_sayisi > 0:
            messages.warning(request, f'{hata_sayisi} ürün için işlem yapılamadı.')
        
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
                # Boş değerleri atla
                if not value or value.strip() == '':
                    continue
                try:
                    gercek_miktar = int(value)
                    if gercek_miktar >= 0:  # Negatif değerleri kabul etme
                        sayim_verileri[int(urun_id)] = gercek_miktar
                except (ValueError, TypeError):
                    continue
        
        if not sayim_verileri:
            messages.warning(request, 'Hiçbir ürün için sayım miktarı girilmedi.')
            urunler = Urun.objects.all().order_by('ad')
            return render(request, 'stok/stok_sayim.html', {'urunler': urunler})
        
        fark_sayisi = 0
        islem_sayisi = 0
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
                islem_sayisi += 1
            except Urun.DoesNotExist:
                continue
        
        if fark_sayisi > 0:
            log_action(request.user, 'create', description=f'Stok sayımı tamamlandı - {fark_sayisi} fark bulundu')
            messages.success(request, f'Stok sayımı tamamlandı. {islem_sayisi} ürün sayıldı, {fark_sayisi} üründe fark bulundu ve düzeltildi.')
        else:
            messages.info(request, f'Stok sayımı tamamlandı. {islem_sayisi} ürün sayıldı, fark bulunmadı.')
        return redirect('stok:index')
    
    urunler = Urun.objects.all().order_by('ad')
    return render(request, 'stok/stok_sayim.html', {'urunler': urunler})


@login_required
def urun_import(request):
    """CSV/Excel ile ürün import"""
    import csv
    from decimal import Decimal
    
    if request.method == 'POST' and request.FILES.get('import_file'):
        import_file = request.FILES['import_file']
        
        # Dosya uzantısına göre işle
        file_extension = import_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            # CSV import
            try:
                decoded_file = import_file.read().decode('utf-8-sig')
                csv_reader = csv.DictReader(decoded_file.splitlines())
                
                basarili = 0
                hatali = 0
                hatalar = []
                
                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        # Gerekli alanları kontrol et
                        if not row.get('ad'):
                            hatali += 1
                            hatalar.append(f'Satır {row_num}: Ürün adı boş olamaz')
                            continue
                        
                        # Kategori varsa al, yoksa None
                        kategori = None
                        if row.get('kategori'):
                            kategori, created = Kategori.objects.get_or_create(ad=row['kategori'])
                        
                        # Ürün oluştur veya güncelle
                        urun, created = Urun.objects.update_or_create(
                            barkod=row.get('barkod') or None,
                            defaults={
                                'ad': row['ad'],
                                'kategori': kategori,
                                'birim': row.get('birim', 'Adet'),
                                'fiyat': Decimal(row.get('fiyat', '0').replace(',', '.')),
                                # min_stok_adedi her zaman 0 olacak (model save metodunda)
                            }
                        )
                        
                        # Eğer stok miktarı belirtilmişse stok hareketi oluştur
                        if row.get('stok_miktari'):
                            try:
                                stok_miktari = int(row['stok_miktari'])
                                if stok_miktari > 0:
                                    StokHareketi.objects.create(
                                        urun=urun,
                                        islem_turu='giriş',
                                        miktar=stok_miktari,
                                        aciklama='CSV import ile eklenen stok',
                                        tarih=timezone.now(),
                                        olusturan=request.user
                                    )
                            except ValueError:
                                pass
                        
                        basarili += 1
                        if created:
                            log_action(request.user, 'create', urun, f'CSV import ile ürün oluşturuldu: {urun.ad}')
                        else:
                            log_action(request.user, 'update', urun, f'CSV import ile ürün güncellendi: {urun.ad}')
                            
                    except Exception as e:
                        hatali += 1
                        hatalar.append(f'Satır {row_num}: {str(e)}')
                
                if basarili > 0:
                    messages.success(request, f'{basarili} ürün başarıyla import edildi.')
                if hatali > 0:
                    messages.warning(request, f'{hatali} satırda hata oluştu. Detaylar: {", ".join(hatalar[:5])}')
                
                return redirect('stok:index')
                
            except Exception as e:
                messages.error(request, f'Import hatası: {str(e)}')
        else:
            messages.error(request, 'Sadece CSV dosyası desteklenmektedir.')
    
    return render(request, 'stok/urun_import.html')
