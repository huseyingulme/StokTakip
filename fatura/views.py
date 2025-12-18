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
from django.contrib.auth.decorators import login_required
from typing import Any
import logging

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
    Yeni fatura ve bağlı kalemlerini servis katmanı üzerinden oluşturur.
    Hata durumunda veritabanı bütünlüğünü korumak için gerekli temizlikleri yapar.
    """
    # 1. Fatura tipini belirle (URL parametresinden veya varsayılan)
    try:
        tip = sanitize_string(request.GET.get('tip', 'Satis'), max_length=10)
        if tip not in ['Satis', 'Alis']:
            tip = 'Satis'
    except Exception:
        tip = 'Satis'

    # Ürün listesi (Formda dropdown için her durumda gerekli)
    urunler = Urun.objects.all().order_by('ad')
    title = 'Yeni Alış Faturası' if tip == 'Alis' else 'Yeni Satış Faturası'

    if request.method == 'POST':
        post_data = request.POST.copy()
        if 'fatura_tipi' not in post_data:
            post_data['fatura_tipi'] = tip
        
        fatura_form = FaturaForm(post_data)
        
        if fatura_form.is_valid():
            fatura = None
            try:
                # 2. Servis katmanını kullanarak ana faturayı oluştur
                # Bu işlem genellikle stok/cari hareketlerini de tetikler
                fatura = create_fatura(fatura_form, request.user, request)
                
                # 3. Servis katmanını kullanarak POST verisindeki kalemleri işle
                # add_fatura_kalemler_from_post_data fonksiyonu miktar ve fiyat validasyonlarını yapar
                kalem_sayisi, hata_sayisi = add_fatura_kalemler_from_post_data(
                    fatura, request.POST, request.user, request
                )
                
                # 4. İş kuralı: En az bir kalem eklenmiş olmalı
                if kalem_sayisi == 0:
                    if fatura:
                        fatura.delete()
                    messages.error(request, 'Lütfen en az bir geçerli ürün seçiniz ve miktar giriniz.')
                    return render(request, 'fatura/fatura_form.html', {
                        'form': fatura_form,
                        'title': title,
                        'tip': tip,
                        'urunler': urunler
                    })

                # Başarı durumu
                if hata_sayisi > 0:
                    messages.warning(request, f'Fatura oluşturuldu ancak {hata_sayisi} satırda hata nedeniyle ekleme yapılamadı.')
                else:
                    messages.success(request, f'Fatura {fatura.fatura_no} başarıyla oluşturuldu.')
                
                return redirect('fatura:detay', pk=fatura.pk)

            except ValidationError as ve:
                if fatura:
                    fatura.delete()
                messages.error(request, f"Doğrulama Hatası: {str(ve)}")
            except Exception as e:
                if fatura:
                    fatura.delete()
                logger.error(f"Fatura ekleme işlemi sırasında kritik hata: {str(e)}", exc_info=True)
                messages.error(request, "Beklenmedik bir hata oluştu. Veriler kaydedilemedi.")
        else:
            # Form validasyon hatalarını kullanıcıya göster
            for field, errors in fatura_form.errors.items():
                for error in errors:
                    messages.error(request, f"{fatura_form.fields[field].label}: {error}")
    else:
        # GET isteği: Boş form oluştur
        bugun = timezone.now().date()
        fatura_form = FaturaForm(initial={
            'fatura_tipi': tip,
            'fatura_tarihi': bugun,
            'durum': 'AcikHesap',
            'iskonto_orani': 0
        })

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



