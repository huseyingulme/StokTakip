from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.http import JsonResponse, HttpResponse
# Transaction yönetimi artık servis katmanında yapılıyor
from datetime import datetime
from django.utils import timezone
from typing import Any
import logging
from .models import Fatura, FaturaKalem
from django.db import models
from .forms import FaturaForm, FaturaKalemForm
from accounts.utils import log_action
from stok.models import Urun
from stoktakip.template_helpers import (
    generate_pagination_html,
    prepare_fatura_table_data,
    generate_table_html,
)
from stoktakip.error_handling import (
    handle_view_errors,
    handle_api_errors,
    database_transaction,
)
from stoktakip.cache_utils import cache_view_result
from django.core.exceptions import ValidationError
from stoktakip.security_utils import (
    sanitize_string,
    sanitize_integer,
    sanitize_decimal,
    validate_search_query,
)
from stoktakip.services.fatura_service import create_fatura, update_fatura, delete_fatura, copy_fatura
from stoktakip.services.fatura_kalem_service import (
    add_fatura_kalem, 
    update_fatura_kalem, 
    delete_fatura_kalem,
    add_fatura_kalemler_from_post_data
)
from stoktakip.services.stok_service import create_stok_hareketleri_from_fatura
from stoktakip.services.cari_service import create_or_update_cari_hareketi_from_fatura


logger = logging.getLogger(__name__)


@cache_view_result(timeout=300, key_prefix='fatura_index')
@handle_view_errors(error_message="Fatura listesi yüklenirken bir hata oluştu.")
@login_required
def index(request: Any) -> Any:
    """
    Fatura listesi sayfası.
    
    Filtreleme, arama ve sayfalama desteği ile fatura listesini gösterir.
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    try:
        fatura_list = Fatura.objects.all().select_related('cari').order_by('-fatura_tarihi', '-olusturma_tarihi')
        
        # Arama - Input validation ile
        search_query = request.GET.get('search', '')
        if search_query:
            try:
                search_query = validate_search_query(search_query, max_length=100)
                fatura_list = fatura_list.filter(
                    Q(fatura_no__icontains=search_query) |
                    Q(cari__ad_soyad__icontains=search_query)
                )
            except Exception as e:
                logger.warning(f"Geçersiz arama sorgusu: {str(e)}")
                messages.warning(request, "Geçersiz arama sorgusu.")
                search_query = ''
        
        # Durum filtresi - Input validation
        durum_filter = request.GET.get('durum', '')
        if durum_filter:
            if durum_filter in ['AcikHesap', 'KasadanKapanacak']:
                fatura_list = fatura_list.filter(durum=durum_filter)
            else:
                durum_filter = ''
        
        # Tip filtresi - Input validation
        tip_filter = request.GET.get('tip', '')
        if tip_filter:
            if tip_filter in ['Alis', 'Satis']:
                fatura_list = fatura_list.filter(fatura_tipi=tip_filter)
            else:
                tip_filter = ''
        
        # Tarih aralığı filtresi - Input validation
        tarih_baslangic = request.GET.get('tarih_baslangic', '')
        tarih_bitis = request.GET.get('tarih_bitis', '')
        if tarih_baslangic and tarih_bitis:
            try:
                from stoktakip.security_utils import validate_date_range
                tarih_baslangic, tarih_bitis = validate_date_range(tarih_baslangic, tarih_bitis)
                fatura_list = fatura_list.filter(
                    fatura_tarihi__gte=tarih_baslangic,
                    fatura_tarihi__lte=tarih_bitis
                )
            except Exception as e:
                logger.warning(f"Geçersiz tarih aralığı: {str(e)}")
                messages.warning(request, "Geçersiz tarih aralığı.")
                tarih_baslangic = ''
                tarih_bitis = ''
        elif tarih_baslangic:
            fatura_list = fatura_list.filter(fatura_tarihi__gte=tarih_baslangic)
        elif tarih_bitis:
            fatura_list = fatura_list.filter(fatura_tarihi__lte=tarih_bitis)
        
        # Tutar aralığı filtresi - Input validation
        tutar_min = request.GET.get('tutar_min', '')
        tutar_max = request.GET.get('tutar_max', '')
        if tutar_min:
            try:
                tutar_min = sanitize_decimal(tutar_min, min_value=0)
                fatura_list = fatura_list.filter(genel_toplam__gte=tutar_min)
            except Exception:
                tutar_min = ''
        if tutar_max:
            try:
                tutar_max = sanitize_decimal(tutar_max, min_value=0)
                fatura_list = fatura_list.filter(genel_toplam__lte=tutar_max)
            except Exception:
                tutar_max = ''
        
        # Sayfalama
        try:
            page_number = request.GET.get('page', '1')
            page_number = sanitize_integer(page_number, min_value=1)
        except Exception:
            page_number = 1
        
        paginator = Paginator(fatura_list, 20)
        faturalar = paginator.get_page(page_number)
        
        # Prepare table data in Python
        table_data = prepare_fatura_table_data(faturalar)
        headers = ['Fatura No', 'Tarih', 'Cari', 'Tip', 'Genel Toplam', 'Durum', 'İşlemler']
        rows = [[
            data['fatura_no'], data['tarih'], data['cari'], data['tip'],
            data['genel_toplam'], data['durum'], data['actions']
        ] for data in table_data]
        table_html = generate_table_html(headers, rows) if rows else None
        
        # Generate pagination HTML
        request_params = {
            'search': search_query,
            'durum': durum_filter,
            'tip': tip_filter,
            'tarih_baslangic': tarih_baslangic,
            'tarih_bitis': tarih_bitis,
            'tutar_min': tutar_min,
            'tutar_max': tutar_max
        }
        pagination_html = generate_pagination_html(faturalar, request_params, request.path) if faturalar.has_other_pages() else None
        
        context = {
            'faturalar': faturalar,
            'search_query': search_query,
            'durum_filter': durum_filter,
            'tip_filter': tip_filter,
            'tarih_baslangic': tarih_baslangic,
            'tarih_bitis': tarih_bitis,
            'tutar_min': tutar_min,
            'tutar_max': tutar_max,
            'table_html': table_html,
            'pagination_html': pagination_html,
            'has_data': len(table_data) > 0,
        }
        return render(request, 'fatura/index.html', context)
    except Exception as e:
        logger.error(f"Fatura index hatası: {str(e)}", exc_info=True)
        raise  # handle_view_errors decorator'ı yakalayacak


@handle_view_errors(
    error_message="Fatura oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.",
    redirect_url="fatura:index"
)
@login_required
def fatura_ekle(request: Any) -> Any:
    """
    Yeni fatura oluşturur.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    from decimal import Decimal, ROUND_HALF_UP
    from django.utils import timezone
    from datetime import timedelta
    from django.core.exceptions import ValidationError
    
    try:
        tip = sanitize_string(request.GET.get('tip', 'Satis'), max_length=10)
        if tip not in ['Satis', 'Alis']:
            tip = 'Satis'
    except Exception:
        tip = 'Satis'
    
    if request.method == 'POST':
        try:
            # Input validation
            post_data = request.POST.copy()
            if 'fatura_tipi' not in post_data:
                post_data['fatura_tipi'] = tip
            
            fatura_form = FaturaForm(post_data)
            
            if fatura_form.is_valid():
                # Servis katmanını kullanarak fatura oluştur
                fatura = create_fatura(fatura_form, request.user, request)
                    
                    # Servis katmanını kullanarak kalemleri ekle
                    try:
                        kalem_sayisi, hata_sayisi = add_fatura_kalemler_from_post_data(
                            fatura, request.POST, request.user, request
                        )
                    except ValidationError as ve:
                        # En az bir kalem eklenemezse faturayı sil ve hata göster
                        fatura.delete()
                        messages.error(request, str(ve))
                        urunler = Urun.objects.all().order_by('ad')
                        title = 'Yeni Alış Faturası' if tip == 'Alis' else 'Yeni Satış Faturası'
                        return render(request, 'fatura/fatura_form.html', {
                            'form': fatura_form,
                            'title': title,
                            'tip': tip,
                            'urunler': urunler
                        })
                    
                    # Eski kalem ekleme kodu kaldırıldı - servis katmanı kullanılıyor
                            # Input validation - Basitleştirilmiş
                            logger.info(f"Kalem işleniyor: {kalem_data}")
                            
                            # Ürün ID - Direkt int'e çevir
                            try:
                                urun_id = int(str(kalem_data['urun_id']).strip())
                                if urun_id <= 0:
                                    raise ValueError("Ürün ID pozitif olmalı")
                            except (ValueError, TypeError) as ve:
                                logger.error(f"Geçersiz ürün ID: {kalem_data['urun_id']}, hata: {ve}")
                                hata_sayisi += 1
                                continue
                            
                            # Ürün kontrolü - Önce ürünü al
                            try:
                                urun = Urun.objects.get(pk=urun_id)
                            except Urun.DoesNotExist:
                                logger.error(f"Ürün bulunamadı: ID={urun_id}")
                                hata_sayisi += 1
                                continue
                            
                            # Miktar - Basit dönüşüm
                            try:
                                miktar_str = str(kalem_data['miktar']).replace(',', '.').strip()
                                miktar_float = float(miktar_str)
                                miktar = int(miktar_float)
                                if miktar <= 0:
                                    raise ValueError("Miktar pozitif olmalı")
                            except (ValueError, TypeError) as ve:
                                logger.error(f"Geçersiz miktar: {kalem_data['miktar']}, hata: {ve}")
                                hata_sayisi += 1
                                continue
                            
                            # KDV oranı - Sabit %20
                            kdv_orani = 20
                            
                            # Fiyat hesaplama - Fatura tipine göre varsayılan fiyat
                            birim_fiyat = None
                            try:
                                # Önce KDV dahil fiyat kontrolü
                                kdv_dahil_str = str(kalem_data.get('kdv_dahil_fiyat', '')).strip().replace(',', '.')
                                if kdv_dahil_str and kdv_dahil_str != '0' and kdv_dahil_str != '0.00':
                                    try:
                                        kdv_dahil_float = float(kdv_dahil_str)
                                        if kdv_dahil_float > 0:
                                            # sanitize_decimal float döndürür, Decimal'e çevir
                                            kdv_dahil_float_sanitized = sanitize_decimal(kdv_dahil_str, min_value=0)
                                            kdv_dahil = Decimal(str(kdv_dahil_float_sanitized))
                                            # birim_fiyat = kdv_dahil / (1 + kdv_orani / 100)
                                            if kdv_orani == 0:
                                                # KDV yoksa, birim_fiyat = kdv_dahil_fiyat
                                                birim_fiyat = kdv_dahil
                                            else:
                                                birim_fiyat = kdv_dahil / (Decimal('1') + Decimal(str(kdv_orani)) / Decimal('100'))
                                            # 2 ondalık basamağa yuvarla
                                            birim_fiyat = birim_fiyat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                                    except (ValueError, TypeError, ValidationError) as ve:
                                        logger.warning(f"KDV dahil fiyat hesaplama hatası: {ve}")
                                
                                # Eğer KDV dahil fiyat yoksa, birim fiyat kontrolü
                                if birim_fiyat is None:
                                    birim_fiyat_str = str(kalem_data.get('birim_fiyat', '')).strip().replace(',', '.')
                                    if birim_fiyat_str and birim_fiyat_str != '0' and birim_fiyat_str != '0.00':
                                        try:
                                            birim_fiyat_float = float(birim_fiyat_str)
                                            if birim_fiyat_float > 0:
                                                birim_fiyat = Decimal(str(sanitize_decimal(birim_fiyat_str, min_value=0)))
                                        except (ValueError, TypeError, ValidationError) as ve:
                                            logger.warning(f"Birim fiyat hesaplama hatası: {ve}")
                                
                                # Eğer hala fiyat yoksa, varsayılan fiyat (KDV dahil olarak geliyor)
                                if birim_fiyat is None:
                                    kdv_dahil_fiyat = None
                                    if fatura.fatura_tipi == 'Alis':
                                        kdv_dahil_fiyat = Decimal(str(urun.alis_fiyati)) if urun.alis_fiyati and urun.alis_fiyati > 0 else (Decimal(str(urun.fiyat)) if urun.fiyat else Decimal('0.00'))
                                    else:
                                        kdv_dahil_fiyat = Decimal(str(urun.fiyat)) if urun.fiyat else Decimal('0.00')
                                    
                                    if kdv_dahil_fiyat and kdv_dahil_fiyat > 0:
                                        # KDV dahil fiyattan KDV hariç fiyatı hesapla
                                        birim_fiyat = kdv_dahil_fiyat / (Decimal('1') + Decimal('20') / Decimal('100'))
                                        birim_fiyat = birim_fiyat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                                    else:
                                        birim_fiyat = Decimal('0.00')
                                        
                            except Exception as ve:
                                logger.warning(f"Fiyat hesaplama genel hatası: {ve}, varsayılan fiyat kullanılıyor")
                                # Varsayılan fiyat (KDV dahil olarak geliyor)
                                kdv_dahil_fiyat = None
                                if fatura.fatura_tipi == 'Alis':
                                    kdv_dahil_fiyat = Decimal(str(urun.alis_fiyati)) if urun.alis_fiyati and urun.alis_fiyati > 0 else (Decimal(str(urun.fiyat)) if urun.fiyat else Decimal('0.00'))
                                else:
                                    kdv_dahil_fiyat = Decimal(str(urun.fiyat)) if urun.fiyat else Decimal('0.00')
                                
                                if kdv_dahil_fiyat and kdv_dahil_fiyat > 0:
                                    # KDV dahil fiyattan KDV hariç fiyatı hesapla
                                    birim_fiyat = kdv_dahil_fiyat / (Decimal('1') + Decimal('20') / Decimal('100'))
                                    birim_fiyat = birim_fiyat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                                else:
                                    birim_fiyat = Decimal('0.00')
                            
                            # Kalem oluştur - Basitleştirilmiş
                            try:
                                # Ürün adını al (max 200 karakter)
                                urun_adi = str(urun.ad)[:200]
                                
                                # Ara toplam hesapla (miktar * birim_fiyat) - KDV hariç
                                # 2 ondalık basamağa yuvarla
                                from decimal import ROUND_HALF_UP
                                ara_toplam = Decimal(str(miktar)) * birim_fiyat
                                ara_toplam = ara_toplam.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                                
                                # KDV tutarını hesapla - 2 ondalık basamağa yuvarla
                                kdv_tutari = (ara_toplam * (Decimal(str(kdv_orani)) / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                                
                                # Toplam tutar (Model'de ara_toplam olarak kaydediliyor, yani KDV hariç)
                                toplam_tutar = ara_toplam
                                
                                # FaturaKalem oluştur
                                kalem = FaturaKalem(
                                    fatura=fatura,
                                    urun=urun,
                                    urun_adi=urun_adi,
                                    miktar=miktar,
                                    birim_fiyat=birim_fiyat,
                                    kdv_orani=kdv_orani,
                                    kdv_tutari=kdv_tutari,
                                    toplam_tutar=toplam_tutar,
                                    sira_no=kalem_sayisi + 1
                                )
                                
                                # Model validation
                                kalem.full_clean()
                                kalem.save()
                                
                                kalem_sayisi += 1
                                logger.info(f"Kalem başarıyla oluşturuldu: Ürün={urun.ad}, Miktar={miktar}, Fiyat={birim_fiyat}, KDV={kdv_orani}, Toplam={toplam_tutar}")
                            except Exception as create_error:
                                error_detail = f"{type(create_error).__name__}: {str(create_error)}"
                                logger.error(f"FaturaKalem oluşturulurken hata: {error_detail}", exc_info=True)
                                hata_sayisi += 1
                                # İlk hatayı kullanıcıya göster
                                if hata_sayisi == 1:
                                    messages.error(request, f'Ürün eklenirken hata: {error_detail}')
                                continue
                            
                        except Exception as e:
                            hata_sayisi += 1
                            error_detail = f"{type(e).__name__}: {str(e)}"
                            logger.error(f"Fatura kalem eklenirken beklenmeyen hata: {error_detail}", exc_info=True)
                            # Hata detayını mesaj olarak ekle
                            if hata_sayisi == 1:  # İlk hatayı göster
                                messages.error(request, f'Ürün eklenirken hata: {error_detail}')
                                continue
                    
                    # En az bir kalem olmalı
                    if kalem_sayisi == 0:
                        fatura.delete()  # Transaction rollback için
                        # Daha detaylı hata mesajı
                        if len(gecerli_kalemler) == 0:
                            messages.error(request, 'Lütfen en az bir ürün seçiniz ve miktar giriniz!')
                        else:
                            # Hata detaylarını logla
                            logger.error(f"Fatura ekleme hatası: {len(gecerli_kalemler)} geçerli kalem var ama hiçbiri eklenemedi. Hata sayısı: {hata_sayisi}")
                            logger.error(f"POST verileri - urun_ids: {urun_ids}, miktarlar: {miktarlar}")
                            messages.error(request, 
                                f'Ürün eklenirken hata oluştu. Lütfen şunları kontrol ediniz:\n'
                                f'- Ürün seçildiğinden emin olun (boş "Seçiniz" seçeneği değil)\n'
                                f'- Miktar 1 veya daha büyük olmalı\n'
                                f'- Fiyat bilgileri geçerli olmalı (otomatik doldurulur)\n'
                                f'(Hata sayısı: {hata_sayisi}, Geçerli kalem sayısı: {len(gecerli_kalemler)})')
                        urunler = Urun.objects.all().order_by('ad')
                        title = 'Yeni Alış Faturası' if tip == 'Alis' else 'Yeni Satış Faturası'
                        return render(request, 'fatura/fatura_form.html', {
                            'form': fatura_form,
                            'title': title,
                            'tip': tip,
                            'urunler': urunler
                        })
                    
                    # Başarı mesajı
                    if hata_sayisi > 0:
                        messages.warning(request, 
                                        f'Fatura oluşturuldu ancak {hata_sayisi} ürün eklenemedi.')
                    
                    messages.success(request, f'Fatura {fatura.fatura_no} başarıyla oluşturuldu.')
                    return redirect('fatura:detay', pk=fatura.pk)
            else:
                # Form validation hataları - detaylı hata mesajları göster
                error_messages = []
                for field, errors in fatura_form.errors.items():
                    for error in errors:
                        field_label = fatura_form.fields[field].label if field in fatura_form.fields else field
                        error_messages.append(f"{field_label}: {error}")
                
                if error_messages:
                    messages.error(request, 'Form hataları:\n' + '\n'.join(error_messages))
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
                
                # Form hatalarıyla birlikte formu tekrar göster
                urunler = Urun.objects.all().order_by('ad')
                title = 'Yeni Alış Faturası' if tip == 'Alis' else 'Yeni Satış Faturası'
                return render(request, 'fatura/fatura_form.html', {
                    'form': fatura_form,
                    'title': title,
                    'tip': tip,
                    'urunler': urunler
                })
                
        except Exception as e:
            logger.error(f"Fatura ekleme hatası: {str(e)}", exc_info=True)
            # Daha detaylı hata mesajı
            error_detail = f"{type(e).__name__}: {str(e)}"
            messages.error(request, f'Fatura oluşturulurken bir hata oluştu: {error_detail}')
            # Formu tekrar göster
            try:
                # Eğer fatura_form tanımlıysa onu kullan, değilse yeni form oluştur
                if 'fatura_form' in locals() and fatura_form is not None:
                    form_to_show = fatura_form
                else:
                    bugun = timezone.now().date()
                    form_to_show = FaturaForm(initial={
                        'fatura_tipi': tip,
                        'fatura_tarihi': bugun,
                        'durum': 'AcikHesap',
                        'iskonto_orani': 0
                    })
            except:
                bugun = timezone.now().date()
                form_to_show = FaturaForm(initial={
                    'fatura_tipi': tip,
                    'fatura_tarihi': bugun,
                    'durum': 'AcikHesap',
                    'iskonto_orani': 0
                })
            
            urunler = Urun.objects.all().order_by('ad')
            title = 'Yeni Alış Faturası' if tip == 'Alis' else 'Yeni Satış Faturası'
            return render(request, 'fatura/fatura_form.html', {
                'form': form_to_show,
                'title': title,
                'tip': tip,
                'urunler': urunler
            })
    else:
        bugun = timezone.now().date()
        fatura_form = FaturaForm(initial={
            'fatura_tipi': tip,
            'fatura_tarihi': bugun,
            'durum': 'AcikHesap',
            'iskonto_orani': 0
        })
    
    urunler = Urun.objects.all().order_by('ad')
    title = 'Yeni Alış Faturası' if tip == 'Alis' else 'Yeni Satış Faturası'
    
    if request.method == 'POST' and not fatura_form.is_valid():
        messages.error(request, 'Lütfen form hatalarını düzeltin.')
    
    return render(request, 'fatura/fatura_form.html', {
        'form': fatura_form,
        'title': title,
        'tip': tip,
        'urunler': urunler
    })


@handle_view_errors(error_message="Fatura detayı yüklenirken bir hata oluştu.")
@login_required
def fatura_detay(request: Any, pk: int) -> Any:
    """
    Fatura detay sayfası.
    
    Satış yetkisi gerektirir. Fatura bilgilerini ve kalemlerini gösterir.
    """
    try:
        fatura = get_object_or_404(Fatura, pk=pk)
        kalemler = fatura.kalemler.select_related('urun').all().order_by('sira_no')
        
        context = {
            'fatura': fatura,
            'kalemler': kalemler,
        }
        return render(request, 'fatura/fatura_detay.html', context)
    except Exception as e:
        logger.error(f"Fatura detay hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Fatura güncellenirken bir hata oluştu.",
    redirect_url="fatura:index"
)
@login_required
def fatura_duzenle(request: Any, pk: int) -> Any:
    """
    Fatura düzenler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    from django.core.exceptions import ValidationError
    
    try:
        fatura = get_object_or_404(Fatura, pk=pk)
        
        if request.method == 'POST':
            try:
                form = FaturaForm(request.POST, instance=fatura)
                if form.is_valid():
                    # Önce mevcut tüm kalemleri sil (fatura düzenleme için)
                    fatura.kalemler.all().delete()
                    
                    # POST'tan gelen kalemleri servis katmanı ile ekle
                    try:
                        kalem_sayisi, hata_sayisi = add_fatura_kalemler_from_post_data(
                            fatura, request.POST, request.user, request
                        )
                    except ValidationError as ve:
                        messages.error(request, str(ve))
                        raise
                    
                    # Servis katmanını kullanarak faturayı güncelle
                    # (Stok ve cari hareketleri servis içinde yönetilir)
                    update_fatura(fatura, form, request.user, request)
                    
                    if hata_sayisi > 0:
                        messages.warning(request, f'{hata_sayisi} ürün eklenemedi.')
                    
                    messages.success(request, 'Fatura başarıyla güncellendi.')
                    return redirect('fatura:detay', pk=fatura.pk)
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Fatura düzenleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = FaturaForm(instance=fatura)
        
        # Ürün listesini context'e ekle
        urunler = Urun.objects.all().order_by('ad')
        
        # Mevcut kalemleri context'e ekle ve KDV dahil fiyatları hesapla
        from decimal import Decimal, ROUND_HALF_UP
        kalemler = fatura.kalemler.select_related('urun').all().order_by('sira_no')
        kalemler_with_kdv_dahil = []
        for kalem in kalemler:
            # KDV oranı 0 ise veya yoksa, 20 yap
            kdv_orani = kalem.kdv_orani if kalem.kdv_orani and kalem.kdv_orani > 0 else 20
            # KDV dahil fiyat = birim_fiyat * (1 + kdv_orani / 100)
            kdv_dahil_fiyat = kalem.birim_fiyat * (Decimal('1') + Decimal(str(kdv_orani)) / Decimal('100'))
            kdv_dahil_fiyat = kdv_dahil_fiyat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Eğer kalem.kdv_orani 0 ise, KDV tutarını yeniden hesapla
            if kalem.kdv_orani == 0 or not kalem.kdv_orani:
                ara_toplam = kalem.birim_fiyat * Decimal(str(kalem.miktar))
                ara_toplam = ara_toplam.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                kdv_tutari = (ara_toplam * (Decimal('20') / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                kdv_tutari = kalem.kdv_tutari
            
            kalemler_with_kdv_dahil.append({
                'kalem': kalem,
                'kdv_dahil_fiyat': kdv_dahil_fiyat,
                # Decimal değerlerini string'e çevir (template'de doğru gösterilmesi için)
                'birim_fiyat_str': str(kalem.birim_fiyat),
                'kdv_tutari_str': str(kdv_tutari),
                'toplam_tutar_str': str(kalem.toplam_tutar),
                'kdv_dahil_fiyat_str': str(kdv_dahil_fiyat),
                'kdv_orani': kdv_orani  # Template'de kullanmak için
            })
        
        return render(request, 'fatura/fatura_form.html', {
            'form': form, 
            'title': 'Fatura Düzenle', 
            'fatura': fatura,
            'urunler': urunler,
            'kalemler': kalemler,
            'kalemler_with_kdv_dahil': kalemler_with_kdv_dahil
        })
    except Exception as e:
        logger.error(f"Fatura düzenleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Fatura silinirken bir hata oluştu.",
    redirect_url="fatura:index"
)
@login_required
def fatura_sil(request: Any, pk: int) -> Any:
    """
    Fatura siler.
    
    Servis katmanı kullanarak faturayı ve ilişkili kayıtları siler.
    """
    try:
        fatura = get_object_or_404(Fatura, pk=pk)
        
        if request.method == 'POST':
            fatura_no = fatura.fatura_no or f"ID:{fatura.pk}"
            
            # Servis katmanını kullanarak sil
            delete_fatura(fatura, request.user, request)
            
            messages.success(request, f'Fatura {fatura_no} ve ilişkili kayıtlar başarıyla silindi.')
            return redirect('fatura:index')
        else:
            return render(request, 'fatura/fatura_sil.html', {'fatura': fatura})
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect('fatura:detay', pk=pk)
    except Exception as e:
        logger.error(f"Fatura silme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Fatura kalemi eklenirken bir hata oluştu.",
    redirect_url="fatura:index"
)
@login_required
def kalem_ekle(request: Any, fatura_pk: int) -> Any:
    """
    Fatura kalemi ekler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    """
    from django.core.exceptions import ValidationError
    from decimal import Decimal, ROUND_HALF_UP
    
    try:
        fatura = get_object_or_404(Fatura, pk=fatura_pk)
        
        if request.method == 'POST':
            try:
                form = FaturaKalemForm(request.POST)
                if form.is_valid():
                    # Servis katmanını kullanarak kalemi ekle
                    add_fatura_kalem(fatura, form, request.user, request)
                    
                    messages.success(request, 'Fatura kalemi başarıyla eklendi.')
                    return redirect('fatura:detay', pk=fatura_pk)
                else:
                    # Form hatalarını göster
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label if field in form.fields else field
                            error_messages.append(f"{field_label}: {error}")
                    
                    if error_messages:
                        messages.error(request, 'Form hataları:\n' + '\n'.join(error_messages))
                    else:
                        messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Fatura kalem ekleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = FaturaKalemForm()
        
        return render(request, 'fatura/kalem_form.html', {'form': form, 'fatura': fatura, 'title': 'Yeni Kalem Ekle'})
    except Exception as e:
        logger.error(f"Fatura kalem ekleme hatası: {str(e)}", exc_info=True)
        raise


@handle_api_errors(error_message="Ürün bilgisi alınamadı", status_code=400)
@login_required
def urun_bilgi_api(request: Any, urun_id: int) -> JsonResponse:
    """
    Ürün bilgilerini JSON formatında döndürür.
    
    Args:
        request: HTTP request
        urun_id: Ürün ID'si
    
    Returns:
        JSON response with product information
    """
    from django.core.exceptions import ValidationError
    
    try:
        # Input validation
        urun_id = sanitize_integer(urun_id, min_value=1)
        urun = Urun.objects.get(pk=urun_id)
        
        return JsonResponse({
            'success': True,
            'urun_adi': urun.ad,
            'birim_fiyat': str(urun.fiyat),
            'birim': urun.birim,
            'mevcut_stok': urun.mevcut_stok
        })
    except Urun.DoesNotExist:
        logger.warning(f"Ürün bulunamadı: {urun_id}")
        return JsonResponse({'success': False, 'error': 'Ürün bulunamadı'}, status=404)
    except ValidationError as e:
        logger.warning(f"Geçersiz ürün ID: {urun_id}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@handle_view_errors(
    error_message="Fatura kalemi güncellenirken bir hata oluştu.",
    redirect_url="fatura:index"
)
@login_required
def kalem_duzenle(request: Any, pk: int) -> Any:
    """
    Fatura kalemi düzenler.
    """
    from django.core.exceptions import ValidationError
    
    try:
        kalem = get_object_or_404(FaturaKalem, pk=pk)
        fatura = kalem.fatura
        
        if request.method == 'POST':
            try:
                form = FaturaKalemForm(request.POST, instance=kalem)
                if form.is_valid():
                    # Servis katmanını kullanarak kalemi güncelle
                    update_fatura_kalem(kalem, form, request.user, request)
                    
                    messages.success(request, 'Fatura kalemi başarıyla güncellendi.')
                    return redirect('fatura:detay', pk=fatura.pk)
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Fatura kalem düzenleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = FaturaKalemForm(instance=kalem)
        
        return render(request, 'fatura/kalem_form.html', {'form': form, 'fatura': fatura, 'kalem': kalem, 'title': 'Kalem Düzenle'})
    except Exception as e:
        logger.error(f"Fatura kalem düzenleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Fatura kalemi silinirken bir hata oluştu.",
    redirect_url="fatura:index"
)
@login_required
def kalem_sil(request: Any, pk: int) -> Any:
    """
    Fatura kalemi siler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    """
    try:
        kalem = get_object_or_404(FaturaKalem, pk=pk)
        fatura_pk = kalem.fatura.pk
        
        if request.method == 'POST':
            # Servis katmanını kullanarak kalemi sil
            delete_fatura_kalem(kalem, request.user, request)
            
            messages.success(request, 'Fatura kalemi başarıyla silindi.')
            return redirect('fatura:detay', pk=fatura_pk)
        else:
            return render(request, 'fatura/kalem_sil.html', {'kalem': kalem})
    except Exception as e:
        logger.error(f"Fatura kalem silme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Fatura kopyalanırken bir hata oluştu.",
    redirect_url="fatura:index"
)
@login_required
def fatura_kopyala(request: Any, pk: int) -> Any:
    """
    Fatura kopyalar.
    
    Servis katmanı kullanarak faturayı ve kalemlerini kopyalar.
    """
    try:
        orijinal_fatura = get_object_or_404(Fatura, pk=pk)
        
        # Servis katmanını kullanarak kopyala
        yeni_fatura = copy_fatura(orijinal_fatura, request.user, request)
        
        messages.success(request, f'Fatura başarıyla kopyalandı. Yeni fatura no: {yeni_fatura.fatura_no}')
        return redirect('fatura:detay', pk=yeni_fatura.pk)
    except Exception as e:
        logger.error(f"Fatura kopyalama hatası: {str(e)}", exc_info=True)
        raise
