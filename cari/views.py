from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Case, When, F
from django.db import models, transaction
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
import logging
from .models import Cari, CariHareketi, CariNotu, TahsilatMakbuzu, TediyeMakbuzu
from .forms import CariForm, CariHareketiForm, CariNotuForm, TahsilatMakbuzuForm, TediyeMakbuzuForm
from stoktakip.template_helpers import (
    generate_pagination_html, prepare_cari_table_data, generate_table_html
)
from stoktakip.error_handling import handle_view_errors, database_transaction
from stoktakip.security_utils import (
    sanitize_string, sanitize_integer, sanitize_decimal, validate_date_range, validate_search_query
)
from stoktakip.cache_utils import cache_view_result
from accounts.utils import log_action

logger = logging.getLogger(__name__)


@cache_view_result(timeout=300, key_prefix='cari_index')
@handle_view_errors(error_message="Cari listesi yüklenirken bir hata oluştu.")
@login_required
def index(request: Any) -> Any:
    """
    Cari listesi sayfası.
    
    Satış yetkisi gerektirir. Filtreleme, arama ve sayfalama desteği ile
    cari listesini gösterir. Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    cari_list = Cari.objects.filter(durum='aktif').select_related().order_by('ad_soyad')

    search_query = request.GET.get('search', '')
    if search_query:
        cari_list = cari_list.filter(
            Q(ad_soyad__icontains=search_query) |
            Q(vergi_no__icontains=search_query) |
            Q(tc_vkn__icontains=search_query) |
            Q(telefon__icontains=search_query)
        )

    kategori_filter = request.GET.get('kategori', '')
    if kategori_filter:
        cari_list = cari_list.filter(kategori=kategori_filter)

    paginator = Paginator(cari_list, 20)
    page_number = request.GET.get('page')
    cariler = paginator.get_page(page_number)
    
    # Prepare table data in Python instead of template
    table_data = prepare_cari_table_data(cariler)
    headers = ['ID', 'Ad Soyad / Firma', 'Kategori', 'TC/Vergi No', 'Telefon', 'E-posta', 'Bakiye', 'Son İşlem', 'İşlemler']
    rows = [[
        data['id'], data['ad_soyad'], data['kategori'], data['tc_vkn'],
        data['telefon'], data['email'], data['bakiye'], data['son_islem'], data['actions']
    ] for data in table_data]
    table_html = generate_table_html(headers, rows) if rows else None
    
    # Generate pagination HTML
    request_params = {'search': search_query, 'kategori': kategori_filter}
    pagination_html = generate_pagination_html(cariler, request_params, request.path) if cariler.has_other_pages() else None

    context = {
        'cariler': cariler,
        'search_query': search_query,
        'kategori_filter': kategori_filter,
        'table_html': table_html,
        'pagination_html': pagination_html,
        'has_data': len(table_data) > 0,
    }
    return render(request, 'cari/index.html', context)


@handle_view_errors(
    error_message="Cari eklenirken bir hata oluştu.",
    redirect_url="cari:index"
)
@database_transaction
@login_required
def cari_ekle(request: Any) -> Any:
    """
    Yeni cari ekler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    from django.core.exceptions import ValidationError
    
    try:
        if request.method == 'POST':
            try:
                form = CariForm(request.POST)
                if form.is_valid():
                    with transaction.atomic():
                        cari = form.save()
                        
                        log_action(request.user, 'create', cari, 
                                 f'Cari eklendi: {cari.ad_soyad}', request)
                        messages.success(request, 'Cari başarıyla eklendi.')
                        return redirect('cari:index')
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Cari ekleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = CariForm()

        return render(request, 'cari/cari_form.html', {'form': form, 'title': 'Yeni Cari Ekle'})
    except Exception as e:
        logger.error(f"Cari ekleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Cari güncellenirken bir hata oluştu.",
    redirect_url="cari:index"
)
@login_required
def cari_duzenle(request: Any, pk: int) -> Any:
    """
    Cari düzenler.
    
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    from django.core.exceptions import ValidationError
    
    try:
        cari = get_object_or_404(Cari, pk=pk)

        if request.method == 'POST':
            try:
                form = CariForm(request.POST, instance=cari)
                if form.is_valid():
                    form.save()
                    
                    log_action(request.user, 'update', cari, 
                             f'Cari güncellendi: {cari.ad_soyad}', request)
                    messages.success(request, 'Cari başarıyla güncellendi.')
                    return redirect('cari:detay', pk=pk)
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Cari düzenleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = CariForm(instance=cari)

        return render(request, 'cari/cari_form.html', {'form': form, 'title': 'Cari Düzenle', 'cari': cari})
    except Exception as e:
        logger.error(f"Cari düzenleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Cari silinirken bir hata oluştu.",
    redirect_url="cari:index"
)
@database_transaction
@login_required
def cari_sil(request: Any, pk: int) -> Any:
    """
    Cari siler veya pasif duruma getirir.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Eğer cari'nin hareketleri varsa sadece pasif duruma getirilir.
    """
    try:
        cari = get_object_or_404(Cari, pk=pk)

        if cari.hareketler.exists():
            if request.method == 'POST':
                try:
                    with transaction.atomic():
                        cari.durum = 'pasif'
                        cari.save()
                        
                        log_action(request.user, 'update', cari, 
                                 f'Cari pasif duruma getirildi: {cari.ad_soyad}', request)
                        messages.success(request, 'Cari pasif duruma getirildi.')
                        return redirect('cari:index')
                except Exception as e:
                    logger.error(f"Cari pasif duruma getirme hatası: {str(e)}", exc_info=True)
                    raise
            return render(request, 'cari/cari_sil.html', {'cari': cari})
        else:
            if request.method == 'POST':
                try:
                    with transaction.atomic():
                        cari_ad = cari.ad_soyad
                        cari.delete()
                        
                        log_action(request.user, 'delete', None, 
                                 f'Cari silindi: {cari_ad}', request)
                        messages.success(request, 'Cari başarıyla silindi.')
                        return redirect('cari:index')
                except Exception as e:
                    logger.error(f"Cari silme hatası: {str(e)}", exc_info=True)
                    raise
            return render(request, 'cari/cari_sil.html', {'cari': cari})
    except Exception as e:
        logger.error(f"Cari silme hatası: {str(e)}", exc_info=True)
        raise


@cache_view_result(timeout=300, key_prefix='cari_detay')
@handle_view_errors(error_message="Cari detayı yüklenirken bir hata oluştu.")
@login_required
def cari_detay(request: Any, pk: int) -> Any:
    """
    Cari detay sayfası.
    
    Satış yetkisi gerektirir. Cari bilgilerini, hareketlerini ve notlarını gösterir.
    Caching ve error handling ile optimize edilmiştir.
    """
    try:
        cari = get_object_or_404(Cari, pk=pk)
        hareketler = cari.hareketler.select_related('olusturan').all()[:50]
        notlar = cari.notlar.select_related('olusturan').all()[:10]

        # Bakiye mutlak değeri
        bakiye_abs = abs(cari.bakiye) if cari.bakiye else 0
        
        context = {
            'cari': cari,
            'hareketler': hareketler,
            'notlar': notlar,
            'bakiye_abs': bakiye_abs,
        }
        return render(request, 'cari/cari_detay.html', context)
    except Exception as e:
        logger.error(f"Cari detay hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Cari hareketi eklenirken bir hata oluştu.",
    redirect_url="cari:index"
)
@database_transaction
@login_required
@handle_view_errors(
    error_message="Cari hareketi eklenirken bir hata oluştu.",
    redirect_url="cari:index"
)
@database_transaction
@login_required
def hareket_ekle(request: Any, cari_pk: int = None) -> Any:
    """
    Cari hareketi ekler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    from django.core.exceptions import ValidationError
    
    try:
        if cari_pk:
            cari = get_object_or_404(Cari, pk=cari_pk)
        else:
            cari = None

        if request.method == 'POST':
            try:
                form = CariHareketiForm(request.POST)
                if form.is_valid():
                    with transaction.atomic():
                        hareket = form.save(commit=False)
                        if not hareket.olusturan:
                            hareket.olusturan = request.user
                        
                        # Tutar validation
                        if hareket.tutar <= 0:
                            raise ValidationError("Tutar 0'dan büyük olmalıdır.")
                        
                        hareket.save()

                        if cari and cari.risk_limiti > 0 and cari.bakiye > cari.risk_limiti:
                            messages.warning(request, f'UYARI: Cari risk limitini aştı! Mevcut bakiye: {cari.bakiye:,.2f} ₺')

                        log_action(request.user, 'create', hareket, 
                                 f'Cari hareketi eklendi: {hareket.cari.ad_soyad}', request)
                        messages.success(request, 'Hareket başarıyla eklendi.')
                        if cari:
                            return redirect('cari:detay', pk=cari_pk)
                        return redirect('cari:hareket_listesi')
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Cari hareket ekleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = CariHareketiForm(initial={'cari': cari, 'tarih': timezone.now()})

        return render(request, 'cari/hareket_form.html', {'form': form, 'title': 'Yeni Hareket Ekle', 'cari': cari})
    except Exception as e:
        logger.error(f"Cari hareket ekleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Cari hareketi güncellenirken bir hata oluştu.",
    redirect_url="cari:index"
)
@login_required
def hareket_duzenle(request: Any, pk: int) -> Any:
    """
    Cari hareketi düzenler.
    
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    from django.core.exceptions import ValidationError
    
    try:
        hareket = get_object_or_404(CariHareketi, pk=pk)

        if request.method == 'POST':
            try:
                form = CariHareketiForm(request.POST, instance=hareket)
                if form.is_valid():
                    # Tutar validation
                    if form.cleaned_data.get('tutar', 0) <= 0:
                        raise ValidationError("Tutar 0'dan büyük olmalıdır.")
                    
                    form.save()
                    
                    log_action(request.user, 'update', hareket, 
                             f'Cari hareketi güncellendi: {hareket.cari.ad_soyad}', request)
                    messages.success(request, 'Hareket başarıyla güncellendi.')
                    return redirect('cari:detay', pk=hareket.cari.pk)
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Cari hareket düzenleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = CariHareketiForm(instance=hareket)

        return render(request, 'cari/hareket_form.html', {'form': form, 'title': 'Hareket Düzenle', 'hareket': hareket})
    except Exception as e:
        logger.error(f"Cari hareket düzenleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Cari hareketi silinirken bir hata oluştu.",
    redirect_url="cari:index"
)
@database_transaction
@login_required
def hareket_sil(request: Any, pk: int) -> Any:
    """
    Cari hareketi siler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    """
    try:
        hareket = get_object_or_404(CariHareketi, pk=pk)
        cari_pk = hareket.cari.pk

        if request.method == 'POST':
            try:
                with transaction.atomic():
                    cari_ad = hareket.cari.ad_soyad
                    hareket.delete()
                    
                    log_action(request.user, 'delete', None, 
                             f'Cari hareketi silindi: {cari_ad}', request)
                    messages.success(request, 'Hareket başarıyla silindi.')
                    return redirect('cari:detay', pk=cari_pk)
            except Exception as e:
                logger.error(f"Cari hareket silme hatası: {str(e)}", exc_info=True)
                raise

        return render(request, 'cari/hareket_sil.html', {'hareket': hareket})
    except Exception as e:
        logger.error(f"Cari hareket silme hatası: {str(e)}", exc_info=True)
        raise


@cache_view_result(timeout=300, key_prefix='hareket_listesi')
@handle_view_errors(error_message="Hareket listesi yüklenirken bir hata oluştu.")
@login_required
def hareket_listesi(request: Any) -> Any:
    """
    Cari hareket listesi.
    
    Muhasebe yetkisi gerektirir. Filtreleme, arama ve sayfalama desteği ile
    hareket listesini gösterir. Input validation, caching ve error handling ile güvenli hale getirilmiştir.
    """
    try:
        hareket_list = CariHareketi.objects.select_related('cari', 'olusturan').all().order_by('-tarih', '-id')

        # Cari filtresi - Input validation
        cari_filter = request.GET.get('cari', '')
        if cari_filter:
            try:
                cari_filter = sanitize_integer(cari_filter, min_value=1)
                if not Cari.objects.filter(pk=cari_filter, durum='aktif').exists():
                    cari_filter = ''
            except Exception:
                cari_filter = ''
            if cari_filter:
                hareket_list = hareket_list.filter(cari_id=cari_filter)

        # Hareket türü filtresi - Input validation
        hareket_turu_filter = request.GET.get('hareket_turu', '')
        if hareket_turu_filter:
            valid_turler = ['satis_faturasi', 'alis_faturasi', 'tahsilat', 'odeme', 'iade']
            if hareket_turu_filter not in valid_turler:
                hareket_turu_filter = ''
            else:
                hareket_list = hareket_list.filter(hareket_turu=hareket_turu_filter)

        # Tarih filtreleri - Input validation
        tarih_baslangic = request.GET.get('tarih_baslangic', '')
        tarih_bitis = request.GET.get('tarih_bitis', '')
        if tarih_baslangic and tarih_bitis:
            try:
                tarih_baslangic, tarih_bitis = validate_date_range(tarih_baslangic, tarih_bitis)
                hareket_list = hareket_list.filter(tarih__gte=tarih_baslangic, tarih__lte=tarih_bitis)
            except Exception as e:
                logger.warning(f"Geçersiz tarih aralığı: {str(e)}")
                tarih_baslangic = ''
                tarih_bitis = ''
        elif tarih_baslangic:
            try:
                from datetime import datetime
                datetime.strptime(tarih_baslangic, '%Y-%m-%d')
                hareket_list = hareket_list.filter(tarih__gte=tarih_baslangic)
            except Exception:
                tarih_baslangic = ''
        elif tarih_bitis:
            try:
                from datetime import datetime
                datetime.strptime(tarih_bitis, '%Y-%m-%d')
                hareket_list = hareket_list.filter(tarih__lte=tarih_bitis)
            except Exception:
                tarih_bitis = ''

        paginator = Paginator(hareket_list, 50)
        page_number = request.GET.get('page')
        hareketler = paginator.get_page(page_number)

        # Fatura lookup - N+1 query problemini çöz (prefetch_related kullanılamaz çünkü belge_no ile lookup yapılıyor)
        from fatura.models import Fatura
        
        fatura_nolari = {}
        belge_nolari = [h.belge_no for h in hareketler if h.belge_no and h.hareket_turu in ['satis_faturasi', 'alis_faturasi']]
        if belge_nolari:
            faturalar = Fatura.objects.filter(fatura_no__in=belge_nolari).values_list('fatura_no', 'pk')
            fatura_nolari = dict(faturalar)
        
        # Her hareket için fatura_id'yi hazırla (template'de kolay erişim için)
        hareketler_with_fatura = []
        for hareket in hareketler:
            fatura_id = None
            if hareket.belge_no and hareket.hareket_turu in ['satis_faturasi', 'alis_faturasi']:
                fatura_id = fatura_nolari.get(hareket.belge_no)
            hareketler_with_fatura.append({
                'hareket': hareket,
                'fatura_id': fatura_id
            })

        context = {
            'hareketler': hareketler,
            'hareketler_with_fatura': hareketler_with_fatura,
            'cariler': Cari.objects.filter(durum='aktif').order_by('ad_soyad'),
            'cari_filter': cari_filter,
            'hareket_turu_filter': hareket_turu_filter,
            'tarih_baslangic': tarih_baslangic,
            'tarih_bitis': tarih_bitis,
            'fatura_nolari': fatura_nolari,
        }
        return render(request, 'cari/hareket_listesi.html', context)
    except Exception as e:
        logger.error(f"Hareket listesi hatası: {str(e)}", exc_info=True)
        raise


@cache_view_result(timeout=300, key_prefix='cari_ekstre')
@handle_view_errors(error_message="Cari ekstre yüklenirken bir hata oluştu.")
@login_required
def cari_ekstre(request: Any, pk: int) -> Any:
    """
    Cari ekstre sayfası.
    
    Muhasebe yetkisi gerektirir. Cari ekstre bilgilerini gösterir.
    Input validation, caching ve error handling ile güvenli hale getirilmiştir.
    """
    try:
        cari = get_object_or_404(Cari, pk=pk)

        # Tarih validation
        tarih_baslangic = request.GET.get('tarih_baslangic', '')
        tarih_bitis = request.GET.get('tarih_bitis', '')

        if not tarih_baslangic:
            tarih_baslangic = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not tarih_bitis:
            tarih_bitis = timezone.now().strftime('%Y-%m-%d')
        
        # Tarih aralığı validation
        if tarih_baslangic and tarih_bitis:
            try:
                tarih_baslangic, tarih_bitis = validate_date_range(tarih_baslangic, tarih_bitis)
            except Exception as e:
                logger.warning(f"Geçersiz tarih aralığı: {str(e)}")
                messages.warning(request, "Geçersiz tarih aralığı. Son 30 gün kullanılıyor.")
                tarih_baslangic = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                tarih_bitis = timezone.now().strftime('%Y-%m-%d')

        hareketler = cari.hareketler.filter(
            tarih__gte=tarih_baslangic,
            tarih__lte=tarih_bitis
        ).order_by('tarih', 'id')

        acilis_bakiye = Decimal('0.00')
        onceki_hareketler = cari.hareketler.filter(tarih__lt=tarih_baslangic)
        if onceki_hareketler.exists():
            onceki_borc = onceki_hareketler.filter(
                hareket_turu__in=['satis_faturasi', 'odeme']
            ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
            onceki_alacak = onceki_hareketler.filter(
                hareket_turu__in=['alis_faturasi', 'tahsilat']
            ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
            acilis_bakiye = onceki_borc - onceki_alacak

        bakiye = acilis_bakiye
        ekstre_satirlari = []

        for hareket in hareketler:
            if hareket.hareket_turu in ['satis_faturasi', 'odeme']:
                bakiye += hareket.tutar
                borc = hareket.tutar
                alacak = Decimal('0.00')
            else:
                bakiye -= hareket.tutar
                borc = Decimal('0.00')
                alacak = hareket.tutar

            ekstre_satirlari.append({
                'tarih': hareket.tarih,
                'aciklama': hareket.aciklama or hareket.get_hareket_turu_display(),
                'belge': hareket.belge_no or '',
                'borc': borc,
                'alacak': alacak,
                'bakiye': bakiye,
            })

        kapanis_bakiye = bakiye

        context = {
            'cari': cari,
            'tarih_baslangic': tarih_baslangic,
            'tarih_bitis': tarih_bitis,
            'acilis_bakiye': acilis_bakiye,
            'kapanis_bakiye': kapanis_bakiye,
            'ekstre_satirlari': ekstre_satirlari,
        }
        return render(request, 'cari/cari_ekstre.html', context)
    except Exception as e:
        logger.error(f"Cari ekstre hatası: {str(e)}", exc_info=True)
        raise


# PDF export kaldırıldı


@handle_view_errors(
    error_message="Not eklenirken bir hata oluştu.",
    redirect_url="cari:index"
)
@database_transaction
@login_required
def not_ekle(request: Any, cari_pk: int) -> Any:
    """
    Cari notu ekler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    """
    from django.core.exceptions import ValidationError
    
    try:
        cari = get_object_or_404(Cari, pk=cari_pk)

        if request.method == 'POST':
            try:
                form = CariNotuForm(request.POST)
                if form.is_valid():
                    with transaction.atomic():
                        notu = form.save(commit=False)
                        notu.cari = cari
                        notu.olusturan = request.user
                        notu.save()
                        
                        log_action(request.user, 'create', notu, 
                                 f'Cari notu eklendi: {cari.ad_soyad}', request)
                        messages.success(request, 'Not başarıyla eklendi.')
                        return redirect('cari:detay', pk=cari_pk)
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Cari not ekleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = CariNotuForm()

        return render(request, 'cari/not_form.html', {'form': form, 'title': 'Yeni Not Ekle', 'cari': cari})
    except Exception as e:
        logger.error(f"Cari not ekleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Not güncellenirken bir hata oluştu.",
    redirect_url="cari:index"
)
@login_required
def not_duzenle(request: Any, pk: int) -> Any:
    """
    Cari notu düzenler.
    """
    from django.core.exceptions import ValidationError
    
    try:
        notu = get_object_or_404(CariNotu, pk=pk)

        if request.method == 'POST':
            try:
                form = CariNotuForm(request.POST, instance=notu)
                if form.is_valid():
                    form.save()
                    
                    log_action(request.user, 'update', notu, 
                             f'Cari notu güncellendi: {notu.cari.ad_soyad}', request)
                    messages.success(request, 'Not başarıyla güncellendi.')
                    return redirect('cari:detay', pk=notu.cari.pk)
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Cari not düzenleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = CariNotuForm(instance=notu)

        return render(request, 'cari/not_form.html', {'form': form, 'title': 'Not Düzenle', 'notu': notu, 'cari': notu.cari})
    except Exception as e:
        logger.error(f"Cari not düzenleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Not silinirken bir hata oluştu.",
    redirect_url="cari:index"
)
@database_transaction
@login_required
def not_sil(request: Any, pk: int) -> Any:
    """
    Cari notu siler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    """
    try:
        notu = get_object_or_404(CariNotu, pk=pk)
        cari_pk = notu.cari.pk

        if request.method == 'POST':
            try:
                with transaction.atomic():
                    cari_ad = notu.cari.ad_soyad
                    notu.delete()
                    
                    log_action(request.user, 'delete', None, 
                             f'Cari notu silindi: {cari_ad}', request)
                    messages.success(request, 'Not başarıyla silindi.')
                    return redirect('cari:detay', pk=cari_pk)
            except Exception as e:
                logger.error(f"Cari not silme hatası: {str(e)}", exc_info=True)
                raise
        else:
            return render(request, 'cari/not_sil.html', {'notu': notu})
    except Exception as e:
        logger.error(f"Cari not silme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Tahsilat makbuzu eklenirken bir hata oluştu.",
    redirect_url="cari:index"
)
@database_transaction
@login_required
def tahsilat_makbuzu_ekle(request: Any, cari_pk: int = None) -> Any:
    """
    Tahsilat makbuzu ekler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    from django.core.exceptions import ValidationError
    
    try:
        if cari_pk:
            cari = get_object_or_404(Cari, pk=cari_pk)
        else:
            cari = None

        if request.method == 'POST':
            try:
                form = TahsilatMakbuzuForm(request.POST)
                if form.is_valid():
                    with transaction.atomic():
                        makbuz = form.save(commit=False)
                        if not makbuz.olusturan:
                            makbuz.olusturan = request.user
                        
                        # Tutar validation
                        if makbuz.tutar <= 0:
                            raise ValidationError("Tutar 0'dan büyük olmalıdır.")
                        
                        makbuz.save()
                        
                        log_action(request.user, 'create', makbuz, 
                                 f'Tahsilat makbuzu eklendi: {makbuz.cari.ad_soyad}', request)
                        messages.success(request, 'Tahsilat makbuzu başarıyla oluşturuldu.')
                        if cari:
                            return redirect('cari:detay', pk=cari_pk)
                        return redirect('cari:tahsilat_listesi')
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Tahsilat makbuzu ekleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = TahsilatMakbuzuForm(initial={'cari': cari})

        return render(request, 'cari/tahsilat_makbuzu_form.html', {'form': form, 'title': 'Yeni Tahsilat Makbuzu', 'cari': cari})
    except Exception as e:
        logger.error(f"Tahsilat makbuzu ekleme hatası: {str(e)}", exc_info=True)
        raise


@cache_view_result(timeout=300, key_prefix='tahsilat_listesi')
@handle_view_errors(error_message="Tahsilat makbuzu listesi yüklenirken bir hata oluştu.")
@login_required
def tahsilat_makbuzu_listesi(request: Any) -> Any:
    """
    Tahsilat makbuzu listesi.
    
    Muhasebe yetkisi gerektirir. Filtreleme ve sayfalama desteği ile
    tahsilat makbuzu listesini gösterir. Input validation, caching ve error handling ile güvenli hale getirilmiştir.
    """
    try:
        makbuz_list = TahsilatMakbuzu.objects.select_related('cari', 'olusturan').all().order_by('-tarih', '-id')

        # Cari filtresi - Input validation
        cari_filter = request.GET.get('cari', '')
        if cari_filter:
            try:
                cari_filter = sanitize_integer(cari_filter, min_value=1)
                if not Cari.objects.filter(pk=cari_filter, durum='aktif').exists():
                    cari_filter = ''
            except Exception:
                cari_filter = ''
            if cari_filter:
                makbuz_list = makbuz_list.filter(cari_id=cari_filter)

        # Tarih filtreleri - Input validation
        tarih_baslangic = request.GET.get('tarih_baslangic', '')
        tarih_bitis = request.GET.get('tarih_bitis', '')
        if tarih_baslangic and tarih_bitis:
            try:
                tarih_baslangic, tarih_bitis = validate_date_range(tarih_baslangic, tarih_bitis)
                makbuz_list = makbuz_list.filter(tarih__gte=tarih_baslangic, tarih__lte=tarih_bitis)
            except Exception as e:
                logger.warning(f"Geçersiz tarih aralığı: {str(e)}")
                tarih_baslangic = ''
                tarih_bitis = ''
        elif tarih_baslangic:
            try:
                from datetime import datetime
                datetime.strptime(tarih_baslangic, '%Y-%m-%d')
                makbuz_list = makbuz_list.filter(tarih__gte=tarih_baslangic)
            except Exception:
                tarih_baslangic = ''
        elif tarih_bitis:
            try:
                from datetime import datetime
                datetime.strptime(tarih_bitis, '%Y-%m-%d')
                makbuz_list = makbuz_list.filter(tarih__lte=tarih_bitis)
            except Exception:
                tarih_bitis = ''

        paginator = Paginator(makbuz_list, 50)
        page_number = request.GET.get('page')
        makbuzlar = paginator.get_page(page_number)

        context = {
            'makbuzlar': makbuzlar,
            'cariler': Cari.objects.filter(durum='aktif').order_by('ad_soyad'),
            'cari_filter': cari_filter,
            'tarih_baslangic': tarih_baslangic,
            'tarih_bitis': tarih_bitis,
        }
        return render(request, 'cari/tahsilat_makbuzu_listesi.html', context)
    except Exception as e:
        logger.error(f"Tahsilat makbuzu listesi hatası: {str(e)}", exc_info=True)
        raise


@login_required
@handle_view_errors(
    error_message="Tediye makbuzu eklenirken bir hata oluştu.",
    redirect_url="cari:index"
)
@database_transaction
@login_required
def tediye_makbuzu_ekle(request: Any, cari_pk: int = None) -> Any:
    """
    Tediye makbuzu ekler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    from django.core.exceptions import ValidationError
    
    try:
        if cari_pk:
            cari = get_object_or_404(Cari, pk=cari_pk)
        else:
            cari = None

        if request.method == 'POST':
            try:
                form = TediyeMakbuzuForm(request.POST)
                if form.is_valid():
                    with transaction.atomic():
                        makbuz = form.save(commit=False)
                        if not makbuz.olusturan:
                            makbuz.olusturan = request.user
                        
                        # Tutar validation
                        if makbuz.tutar <= 0:
                            raise ValidationError("Tutar 0'dan büyük olmalıdır.")
                        
                        makbuz.save()
                        
                        log_action(request.user, 'create', makbuz, 
                                 f'Tediye makbuzu eklendi: {makbuz.cari.ad_soyad}', request)
                        messages.success(request, 'Tediye makbuzu başarıyla oluşturuldu.')
                        if cari:
                            return redirect('cari:detay', pk=cari_pk)
                        return redirect('cari:tediye_listesi')
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Tediye makbuzu ekleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = TediyeMakbuzuForm(initial={'cari': cari})

        return render(request, 'cari/tediye_makbuzu_form.html', {'form': form, 'title': 'Yeni Tediye Makbuzu', 'cari': cari})
    except Exception as e:
        logger.error(f"Tediye makbuzu ekleme hatası: {str(e)}", exc_info=True)
        raise


@cache_view_result(timeout=300, key_prefix='tediye_listesi')
@handle_view_errors(error_message="Tediye makbuzu listesi yüklenirken bir hata oluştu.")
@login_required
def tediye_makbuzu_listesi(request: Any) -> Any:
    """
    Tediye makbuzu listesi.
    
    Muhasebe yetkisi gerektirir. Filtreleme ve sayfalama desteği ile
    tediye makbuzu listesini gösterir. Input validation, caching ve error handling ile güvenli hale getirilmiştir.
    """
    try:
        makbuz_list = TediyeMakbuzu.objects.select_related('cari', 'olusturan').all().order_by('-tarih', '-id')

        # Cari filtresi - Input validation
        cari_filter = request.GET.get('cari', '')
        if cari_filter:
            try:
                cari_filter = sanitize_integer(cari_filter, min_value=1)
                if not Cari.objects.filter(pk=cari_filter, durum='aktif').exists():
                    cari_filter = ''
            except Exception:
                cari_filter = ''
            if cari_filter:
                makbuz_list = makbuz_list.filter(cari_id=cari_filter)

        # Tarih filtreleri - Input validation
        tarih_baslangic = request.GET.get('tarih_baslangic', '')
        tarih_bitis = request.GET.get('tarih_bitis', '')
        if tarih_baslangic and tarih_bitis:
            try:
                tarih_baslangic, tarih_bitis = validate_date_range(tarih_baslangic, tarih_bitis)
                makbuz_list = makbuz_list.filter(tarih__gte=tarih_baslangic, tarih__lte=tarih_bitis)
            except Exception as e:
                logger.warning(f"Geçersiz tarih aralığı: {str(e)}")
                tarih_baslangic = ''
                tarih_bitis = ''
        elif tarih_baslangic:
            try:
                from datetime import datetime
                datetime.strptime(tarih_baslangic, '%Y-%m-%d')
                makbuz_list = makbuz_list.filter(tarih__gte=tarih_baslangic)
            except Exception:
                tarih_baslangic = ''
        elif tarih_bitis:
            try:
                from datetime import datetime
                datetime.strptime(tarih_bitis, '%Y-%m-%d')
                makbuz_list = makbuz_list.filter(tarih__lte=tarih_bitis)
            except Exception:
                tarih_bitis = ''

        paginator = Paginator(makbuz_list, 50)
        page_number = request.GET.get('page')
        makbuzlar = paginator.get_page(page_number)

        context = {
            'makbuzlar': makbuzlar,
            'cariler': Cari.objects.filter(durum='aktif').order_by('ad_soyad'),
            'cari_filter': cari_filter,
            'tarih_baslangic': tarih_baslangic,
            'tarih_bitis': tarih_bitis,
        }
        return render(request, 'cari/tediye_makbuzu_listesi.html', context)
    except Exception as e:
        logger.error(f"Tediye makbuzu listesi hatası: {str(e)}", exc_info=True)
        raise


# Yaşlandırma raporu kaldırıldı
