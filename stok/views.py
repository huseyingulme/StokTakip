from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction
from typing import Any
import logging
from .models import Urun, StokHareketi, Kategori
from .forms import UrunForm
from accounts.utils import log_action
from stoktakip.template_helpers import (
    generate_pagination_html, prepare_urun_table_data, generate_table_html
)
from stoktakip.error_handling import handle_view_errors, database_transaction
from stoktakip.cache_utils import cache_view_result
from stoktakip.security_utils import sanitize_integer, sanitize_string, validate_search_query, sanitize_decimal

logger = logging.getLogger(__name__)


@cache_view_result(timeout=300, key_prefix='stok_index')
@handle_view_errors(error_message="Stok listesi yüklenirken bir hata oluştu.")
@login_required
def index(request: Any) -> Any:
    """
    Stok listesi sayfası.
    
    ürün listesini gösterir. Input validation ve error handling ile güvenli hale getirilmiştir.
    """
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

    
    # Prepare table data in Python
    table_data = prepare_urun_table_data(urunler)
    headers = ['Kod', 'Ürün Adı', 'Kategori', 'Barkod', 'Birim', 'Satış Fiyatı', 'Mevcut Stok', 'İşlemler']
    rows = [[
        data['kod'], data['ad'], data['kategori'], data['barkod'],
        data['birim'], data['fiyat'], data['stok'], data['actions']
    ] for data in table_data]
    table_html = generate_table_html(headers, rows) if rows else None
    
    # Generate pagination HTML
    request_params = {
        'search': search_query,
        'kategori': kategori_filter,
        'stok_durumu': stok_durumu,
        'fiyat_min': fiyat_min,
        'fiyat_max': fiyat_max
    }
    pagination_html = generate_pagination_html(urunler, request_params, request.path) if urunler.has_other_pages() else None
    
    context = {
        'urunler': urunler,
        'search_query': search_query,
        'kategori_filter': kategori_filter,
        'stok_durumu': stok_durumu,
        'fiyat_min': fiyat_min,
        'fiyat_max': fiyat_max,
        'kategoriler': Kategori.objects.all().order_by('ad'),
        'table_html': table_html,
        'pagination_html': pagination_html,
        'has_data': len(table_data) > 0,
    }
    return render(request, 'stok/index.html', context)


@handle_view_errors(
    error_message="Ürün eklenirken bir hata oluştu.",
    redirect_url="stok:index"
)
@database_transaction
@login_required
def urun_ekle(request: Any) -> Any:
    """
    Yeni ürün ekler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    from django.core.exceptions import ValidationError
    
    if request.method == 'POST':
        try:
            form = UrunForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    urun = form.save(commit=False)
                    
                    # Fiyat validation
                    if urun.fiyat and urun.fiyat < 0:
                        raise ValidationError("Fiyat negatif olamaz.")
                    
                    urun.save()
                    
                    log_action(request.user, 'create', urun, 
                             f'Ürün eklendi: {urun.ad}', request)
                    messages.success(request, 'Ürün başarıyla eklendi.')
                    return redirect('stok:index')
            else:
                messages.error(request, 'Lütfen form hatalarını düzeltin.')
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Ürün ekleme hatası: {str(e)}", exc_info=True)
            raise
    else:
        form = UrunForm()
    
    return render(request, 'stok/urun_form.html', {'form': form, 'title': 'Yeni Ürün Ekle'})


@handle_view_errors(
    error_message="Ürün güncellenirken bir hata oluştu.",
    redirect_url="stok:index"
)
@login_required
def urun_duzenle(request: Any, pk: int) -> Any:
    """
    Ürün düzenler.
    
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    from django.core.exceptions import ValidationError
    
    try:
        urun = get_object_or_404(Urun, pk=pk)
        
        if request.method == 'POST':
            try:
                form = UrunForm(request.POST, instance=urun)
                if form.is_valid():
                    # Fiyat validation
                    if form.cleaned_data.get('fiyat', 0) < 0:
                        raise ValidationError("Fiyat negatif olamaz.")
                    
                    form.save()
                    
                    log_action(request.user, 'update', urun, 
                             f'Ürün güncellendi: {urun.ad}', request)
                    messages.success(request, 'Ürün başarıyla güncellendi.')
                    return redirect('stok:index')
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Ürün düzenleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = UrunForm(instance=urun)
        
        return render(request, 'stok/urun_form.html', {'form': form, 'title': 'Ürün Düzenle', 'urun': urun})
    except Exception as e:
        logger.error(f"Ürün düzenleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Ürün silinirken bir hata oluştu.",
    redirect_url="stok:index"
)
@login_required
def urun_sil(request: Any, pk: int) -> Any:
    """
    Ürün siler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    İlişkili kayıtlar varsa uyarı gösterir ancak silmeye izin verir.
    """
    from fatura.models import FaturaKalem
    
    try:
        urun = get_object_or_404(Urun, pk=pk)
        
        if request.method == 'POST':
            try:
                action = request.POST.get('action', 'sil')  # 'sil' veya 'iptal'
                
                if action == 'iptal':
                    return redirect('stok:index')
                
                # Ürün bilgilerini silmeden önce al
                urun_ad = urun.ad
                urun_id = urun.pk
                
                # İlişkili kayıt sayıları (bilgi amaçlı)
                fatura_kalem_sayisi = FaturaKalem.objects.filter(urun=urun).count()
                stok_hareket_sayisi = StokHareketi.objects.filter(urun=urun).count()
                
                # Transaction içinde silme işlemi
                with transaction.atomic():
                    # Önce fatura kalemlerindeki urun referanslarını NULL yap
                    # (SET_NULL constraint'i veritabanında düzgün çalışmıyorsa manuel yapıyoruz)
                    if fatura_kalem_sayisi > 0:
                        FaturaKalem.objects.filter(urun=urun).update(urun=None)
                    
                    # Ürünü sil (CASCADE ile stok hareketleri otomatik silinecek)
                    urun.delete()
                    
                    # Log kaydı (ürün silindikten sonra)
                    try:
                        log_action(request.user, 'delete', None, 
                                    f'Ürün silindi: {urun_ad} (ID: {urun_id}, Fatura kalemleri: {fatura_kalem_sayisi}, Stok hareketleri: {stok_hareket_sayisi})', request)
                    except Exception as log_error:
                        logger.warning(f"Log kaydı oluşturulamadı: {str(log_error)}")
                    
                    messages.success(request, f'Ürün "{urun_ad}" başarıyla silindi.')
                    if fatura_kalem_sayisi > 0 or stok_hareket_sayisi > 0:
                        messages.info(request, f'İlişkili {fatura_kalem_sayisi + stok_hareket_sayisi} kayıt da silindi.')
                    
                return redirect('stok:index')
            except Exception as e:
                logger.error(f"Ürün silme hatası: {str(e)}", exc_info=True)
                messages.error(request, f'Ürün silinirken bir hata oluştu: {str(e)}')
                return redirect('stok:index')
        else:
            # GET isteği - bilgilendirme sayfası
            fatura_kalemleri = FaturaKalem.objects.filter(urun=urun)
            stok_hareketleri = StokHareketi.objects.filter(urun=urun)
            
            fatura_kalem_sayisi = fatura_kalemleri.count()
            stok_hareket_sayisi = stok_hareketleri.count()
            toplam_iliskili_kayit = fatura_kalem_sayisi + stok_hareket_sayisi
            
            return render(request, 'stok/urun_sil.html', {
                'urun': urun,
                'fatura_kalemleri': fatura_kalemleri,
                'stok_hareketleri': stok_hareketleri,
                'fatura_kalem_sayisi': fatura_kalem_sayisi,
                'stok_hareket_sayisi': stok_hareket_sayisi,
                'toplam_iliskili_kayit': toplam_iliskili_kayit,
            })
    except Exception as e:
        logger.error(f"Ürün silme hatası: {str(e)}", exc_info=True)
        messages.error(request, f'Ürün silinirken bir hata oluştu: {str(e)}')
        return redirect('stok:index')


@handle_view_errors(
    error_message="Stok işlemi yapılırken bir hata oluştu.",
    redirect_url="stok:index"
)
@database_transaction
@login_required
def stok_duzenle(request: Any, pk: int) -> Any:
    """
    Stok giriş/çıkış işlemi yapar.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Input validation ve error handling ile güvenli hale getirilmiştir.

    """
    from django.core.exceptions import ValidationError
    
    urun = get_object_or_404(Urun, pk=pk)
    
    if request.method == 'POST':
        try:
            # Input validation
            islem_turu = sanitize_string(request.POST.get('islem_turu', ''), max_length=20)
            if islem_turu not in ['giriş', 'çıkış']:
                raise ValidationError("Geçersiz işlem türü")
            
            miktar = sanitize_integer(request.POST.get('miktar', 0), min_value=1, max_value=1000000)
            aciklama = sanitize_string(request.POST.get('aciklama', ''), max_length=500)
            
            # Transaction içinde stok hareketi oluştur
            with transaction.atomic():
                # Stok kontrolü kaldırıldı - negatif stok olabilir
                
                StokHareketi.objects.create(
                    urun=urun,
                    islem_turu=islem_turu,
                    miktar=miktar,
                    aciklama=aciklama,
                    tarih=timezone.now(),
                    olusturan=request.user
                )
                
                log_action(request.user, 'update', urun, 
                         f'Stok {islem_turu} işlemi: {miktar} {urun.birim}', request)
                messages.success(request, f'Stok {islem_turu} işlemi başarıyla yapıldı.')
                return redirect('stok:index')
                
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Stok düzenleme hatası: {str(e)}", exc_info=True)
            raise  # handle_view_errors decorator'ı yakalayacak
    
    return render(request, 'stok/stok_duzenle.html', {'urun': urun})


@handle_view_errors(error_message="Stok hareketleri yüklenirken bir hata oluştu.")
@login_required
def stok_hareketleri(request: Any, pk: int) -> Any:
    """
    Stok hareketleri listesi.

    """
    try:
        urun = get_object_or_404(Urun, pk=pk)
        hareketler = StokHareketi.objects.filter(urun=urun).select_related('olusturan').order_by('-tarih')
        
        # Sayfalama - Input validation
        try:
            page_number = request.GET.get('page', '1')
            page_number = sanitize_integer(page_number, min_value=1)
        except Exception:
            page_number = 1
        
        paginator = Paginator(hareketler, 20)
        hareketler_page = paginator.get_page(page_number)
        
        return render(request, 'stok/stok_hareketleri.html', {
            'urun': urun,
            'hareketler': hareketler_page
        })
    except Exception as e:
        logger.error(f"Stok hareketleri hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Toplu stok işlemi yapılırken bir hata oluştu.",
    redirect_url="stok:index"
)
@database_transaction
@login_required
def toplu_stok_islem(request: Any) -> Any:
    """
    Toplu stok işlemi yapar.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Birden fazla ürün için aynı anda stok giriş/çıkış işlemi yapar.
    """
    from django.core.exceptions import ValidationError
    
    if request.method == 'POST':
        try:
            # Input validation
            urun_ids = request.POST.getlist('urun_ids')
            if not urun_ids:
                raise ValidationError('Lütfen en az bir ürün seçin.')
            
            islem_turu = sanitize_string(request.POST.get('islem_turu', '').strip(), max_length=20)
            if not islem_turu or islem_turu not in ['giriş', 'çıkış']:
                raise ValidationError('Geçerli bir işlem türü seçin.')
            
            miktar = sanitize_integer(request.POST.get('miktar', '0'), min_value=1, max_value=1000000)
            aciklama = sanitize_string(
                request.POST.get('aciklama', 'Toplu işlem').strip() or 'Toplu işlem',
                max_length=500
            )
        
            # Transaction içinde toplu işlem
            with transaction.atomic():
                # Çıkış işleminde stok kontrolü
                if islem_turu == 'çıkış':
                    yetersiz_stok_urunler = []
                    for urun_id in urun_ids:
                        try:
                            urun_id_int = sanitize_integer(urun_id, min_value=1)
                            urun = Urun.objects.get(pk=urun_id_int)
                            if urun.mevcut_stok < miktar:
                                yetersiz_stok_urunler.append(urun.ad)
                        except (Urun.DoesNotExist, ValidationError):
                            continue
                    
                    if yetersiz_stok_urunler:
                        messages.warning(request, 
                                       f'Bazı ürünlerde yetersiz stok var: {", ".join(yetersiz_stok_urunler[:5])}')
                
                islem_sayisi = 0
                hata_sayisi = 0
                
                for urun_id in urun_ids:
                    try:
                        urun_id_int = sanitize_integer(urun_id, min_value=1)
                        urun = Urun.objects.get(pk=urun_id_int)
                        
                        # Çıkış işleminde stok kontrolü
                        if islem_turu == 'çıkış' and urun.mevcut_stok < miktar:
                            hata_sayisi += 1
                            continue
                        
                        StokHareketi.objects.create(
                            urun=urun,
                            islem_turu=islem_turu,
                            miktar=miktar,
                            aciklama=aciklama,
                            tarih=timezone.now(),
                            olusturan=request.user
                        )
                        islem_sayisi += 1
                        log_action(request.user, 'create', urun, 
                                 f'Toplu stok işlemi: {islem_turu} - {miktar} {urun.birim}', request)
                    except (Urun.DoesNotExist, ValidationError):
                        hata_sayisi += 1
                        continue
                    except Exception as e:
                        logger.warning(f"Toplu stok işlemi hatası (ürün {urun_id}): {str(e)}")
                        hata_sayisi += 1
                        continue
                
                if islem_sayisi > 0:
                    log_action(request.user, 'create', None, 
                             f'Toplu stok işlemi: {islem_turu} - {islem_sayisi} ürün', request)
                    messages.success(request, f'{islem_sayisi} ürün için stok {islem_turu} işlemi başarıyla yapıldı.')
                if hata_sayisi > 0:
                    messages.warning(request, f'{hata_sayisi} ürün için işlem yapılamadı.')
                
                if islem_sayisi == 0:
                    raise ValidationError('Hiçbir ürün için işlem yapılamadı.')
                
                return redirect('stok:index')
                
        except ValidationError as e:
            messages.error(request, str(e))
            urunler = Urun.objects.all().order_by('ad')
            return render(request, 'stok/toplu_stok_islem.html', {'urunler': urunler})
        except Exception as e:
            logger.error(f"Toplu stok işlemi hatası: {str(e)}", exc_info=True)
            raise
    
    urunler = Urun.objects.all().order_by('ad')
    return render(request, 'stok/toplu_stok_islem.html', {'urunler': urunler})


@handle_view_errors(
    error_message="Stok sayımı yapılırken bir hata oluştu.",
    redirect_url="stok:index"
)
@database_transaction
@login_required
def stok_sayim(request: Any) -> Any:
    """
    Stok sayımı yapar.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Gerçek stok ile mevcut stok arasındaki farkları düzeltir.
    """
    from django.core.exceptions import ValidationError
    
    if request.method == 'POST':
        try:
            sayim_verileri = {}
            for key, value in request.POST.items():
                if key.startswith('urun_') and key.endswith('_miktar'):
                    urun_id_str = key.replace('urun_', '').replace('_miktar', '')
                    # Boş değerleri atla
                    if not value or value.strip() == '':
                        continue
                    try:
                        urun_id = sanitize_integer(urun_id_str, min_value=1)
                        gercek_miktar = sanitize_integer(value, min_value=0, max_value=10000000)
                        sayim_verileri[urun_id] = gercek_miktar
                    except (ValueError, TypeError, ValidationError):
                        continue
        
            if not sayim_verileri:
                raise ValidationError('Hiçbir ürün için sayım miktarı girilmedi.')
            
            # Transaction içinde stok sayımı
            with transaction.atomic():
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
                                aciklama=sanitize_string(
                                    f'Stok sayımı - Mevcut: {mevcut_stok}, Gerçek: {gercek_miktar}',
                                    max_length=500
                                ),
                                tarih=timezone.now(),
                                olusturan=request.user
                            )
                            fark_sayisi += 1
                        islem_sayisi += 1
                    except Urun.DoesNotExist:
                        continue
                    except Exception as e:
                        logger.warning(f"Stok sayımı hatası (ürün {urun_id}): {str(e)}")
                        continue
                
                if fark_sayisi > 0:
                    log_action(request.user, 'create', None, 
                             f'Stok sayımı tamamlandı - {fark_sayisi} fark bulundu', request)
                    messages.success(request, 
                                   f'Stok sayımı tamamlandı. {islem_sayisi} ürün sayıldı, {fark_sayisi} üründe fark bulundu ve düzeltildi.')
                else:
                    messages.info(request, 
                                f'Stok sayımı tamamlandı. {islem_sayisi} ürün sayıldı, fark bulunmadı.')
                
                return redirect('stok:index')
                
        except ValidationError as e:
            messages.error(request, str(e))
            urunler = Urun.objects.all().order_by('ad')
            return render(request, 'stok/stok_sayim.html', {'urunler': urunler})
        except Exception as e:
            logger.error(f"Stok sayımı hatası: {str(e)}", exc_info=True)
            raise
    
    urunler = Urun.objects.all().order_by('ad')
    return render(request, 'stok/stok_sayim.html', {'urunler': urunler})

