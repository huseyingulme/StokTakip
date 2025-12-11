from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from typing import Any
import logging
from .models import HesapKart, FinansHareketi
from .forms import HesapKartForm, FinansHareketiForm
from accounts.utils import log_action
from stoktakip.error_handling import handle_view_errors, database_transaction
from stoktakip.security_utils import (
    sanitize_integer, sanitize_decimal, validate_date_range, validate_search_query
)
from stoktakip.cache_utils import cache_view_result

logger = logging.getLogger(__name__)


@cache_view_result(timeout=300, key_prefix='finans_index')
@handle_view_errors(error_message="Finans listesi yüklenirken bir hata oluştu.")
@login_required
def index(request: Any) -> Any:
    """
    Finans listesi sayfası.
    
    Muhasebe yetkisi gerektirir. Hesap kartları ve finans hareketlerini gösterir.
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    try:
        hesaplar = HesapKart.objects.filter(durum=True)
        hareketler = FinansHareketi.objects.select_related('hesap', 'olusturan').order_by('-tarih', '-id')
        
        # Filtreleme - Input validation ile
        hesap_filter = request.GET.get('hesap', '')
        if hesap_filter:
            try:
                hesap_id = sanitize_integer(hesap_filter, min_value=1)
                if HesapKart.objects.filter(pk=hesap_id, durum=True).exists():
                    hareketler = hareketler.filter(hesap_id=hesap_id)
                else:
                    hesap_filter = ''
            except Exception:
                hesap_filter = ''
        
        # Hareket tipi filtresi - Input validation
        hareket_tipi_filter = request.GET.get('hareket_tipi', '')
        if hareket_tipi_filter:
            if hareket_tipi_filter in ['gelir', 'gider', 'transfer']:
                hareketler = hareketler.filter(hareket_tipi=hareket_tipi_filter)
            else:
                hareket_tipi_filter = ''
        
        # Tarih aralığı filtresi - Input validation
        tarih_baslangic = request.GET.get('tarih_baslangic', '')
        tarih_bitis = request.GET.get('tarih_bitis', '')
        if tarih_baslangic and tarih_bitis:
            try:
                tarih_baslangic, tarih_bitis = validate_date_range(tarih_baslangic, tarih_bitis)
                hareketler = hareketler.filter(
                    tarih__gte=tarih_baslangic,
                    tarih__lte=tarih_bitis
                )
            except Exception as e:
                logger.warning(f"Geçersiz tarih aralığı: {str(e)}")
                messages.warning(request, "Geçersiz tarih aralığı.")
                tarih_baslangic = ''
                tarih_bitis = ''
        elif tarih_baslangic:
            hareketler = hareketler.filter(tarih__gte=tarih_baslangic)
        elif tarih_bitis:
            hareketler = hareketler.filter(tarih__lte=tarih_bitis)
    
        # Toplamlar - Aggregate kullan
        toplam_gelir = hareketler.filter(hareket_tipi='gelir').aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
        toplam_gider = hareketler.filter(hareket_tipi='gider').aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
        toplam_transfer = hareketler.filter(hareket_tipi='transfer').aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
        net_bakiye = toplam_gelir - toplam_gider
        
        # Sayfalama - Input validation
        try:
            page_number = request.GET.get('page', '1')
            page_number = sanitize_integer(page_number, min_value=1)
        except Exception:
            page_number = 1
        
        paginator = Paginator(hareketler, 20)
        hareketler_page = paginator.get_page(page_number)
        
        # Her hesap için bakiye hesapla (hareketlere göre)
        hesaplar_with_bakiye = []
        for hesap in hesaplar:
            # Bu hesaba ait tüm hareketleri hesapla
            hesap_hareketleri = FinansHareketi.objects.filter(hesap=hesap)
            
            # Gelir hareketleri (sadece gelir tipi)
            gelir_toplam = hesap_hareketleri.filter(
                hareket_tipi='gelir'
            ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
            
            # Gider hareketleri
            gider_toplam = hesap_hareketleri.filter(
                hareket_tipi='gider'
            ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
            
            # Bu hesaba transfer olarak gelen hareketler (hedef_hesap olarak)
            transfer_giris = FinansHareketi.objects.filter(
                hedef_hesap=hesap,
                hareket_tipi='transfer'
            ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
            
            # Bu hesaptan transfer olarak çıkan hareketler (hesap olarak transfer tipi)
            transfer_cikis = hesap_hareketleri.filter(
                hareket_tipi='transfer'
            ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
            
            # Bakiye = Gelir + Transfer Giriş - Gider - Transfer Çıkış
            hesap_bakiye = gelir_toplam + transfer_giris - gider_toplam - transfer_cikis
            
            # Hesap objesine bakiye ekle (property olarak)
            hesap.hesaplanan_bakiye = hesap_bakiye
            hesaplar_with_bakiye.append(hesap)
        
        context = {
            'hesaplar': hesaplar_with_bakiye,
            'hareketler': hareketler_page,
            'toplam_gelir': toplam_gelir,
            'toplam_gider': toplam_gider,
            'toplam_transfer': toplam_transfer,
            'net_bakiye': net_bakiye,
            'hesap_filter': hesap_filter,
            'hareket_tipi_filter': hareket_tipi_filter,
            'tarih_baslangic': tarih_baslangic,
            'tarih_bitis': tarih_bitis,
        }
        return render(request, 'finans/index.html', context)
    except Exception as e:
        logger.error(f"Finans index hatası: {str(e)}", exc_info=True)
        raise  # handle_view_errors decorator'ı yakalayacak


@handle_view_errors(
    error_message="Hesap eklenirken bir hata oluştu.",
    redirect_url="finans:index"
)
@database_transaction
@login_required
def hesap_ekle(request: Any) -> Any:
    """
    Yeni hesap kartı ekler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    """
    from django.core.exceptions import ValidationError
    
    if request.method == 'POST':
        try:
            form = HesapKartForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    hesap = form.save()
                    
                    log_action(request.user, 'create', hesap, 
                             f'Hesap kartı eklendi: {hesap.ad}', request)
                    messages.success(request, 'Hesap kartı başarıyla eklendi.')
                    return redirect('finans:index')
            else:
                messages.error(request, 'Lütfen form hatalarını düzeltin.')
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Hesap ekleme hatası: {str(e)}", exc_info=True)
            raise
    else:
        form = HesapKartForm()
    
    return render(request, 'finans/hesap_form.html', {'form': form, 'title': 'Yeni Hesap Ekle'})


@handle_view_errors(
    error_message="Hesap güncellenirken bir hata oluştu.",
    redirect_url="finans:index"
)
@login_required
def hesap_duzenle(request: Any, pk: int) -> Any:
    """
    Hesap kartı düzenler.
    """
    try:
        hesap = get_object_or_404(HesapKart, pk=pk)
        
        if request.method == 'POST':
            try:
                form = HesapKartForm(request.POST, instance=hesap)
                if form.is_valid():
                    form.save()
                    
                    log_action(request.user, 'update', hesap, 
                             f'Hesap kartı güncellendi: {hesap.ad}', request)
                    messages.success(request, 'Hesap kartı başarıyla güncellendi.')
                    return redirect('finans:index')
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except Exception as e:
                logger.error(f"Hesap düzenleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = HesapKartForm(instance=hesap)
        
        return render(request, 'finans/hesap_form.html', {'form': form, 'title': 'Hesap Düzenle', 'hesap': hesap})
    except Exception as e:
        logger.error(f"Hesap düzenleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Hesap silinirken bir hata oluştu.",
    redirect_url="finans:index"
)
@database_transaction
@login_required
def hesap_sil(request: Any, pk: int) -> Any:
    """
    Hesap kartı siler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    """
    try:
        hesap = get_object_or_404(HesapKart, pk=pk)
        
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    hesap_ad = hesap.ad
                    hesap.delete()
                    
                    log_action(request.user, 'delete', None, 
                             f'Hesap kartı silindi: {hesap_ad}', request)
                    messages.success(request, 'Hesap kartı başarıyla silindi.')
                    return redirect('finans:index')
            except Exception as e:
                logger.error(f"Hesap silme hatası: {str(e)}", exc_info=True)
                raise
        else:
            return render(request, 'finans/hesap_sil.html', {'hesap': hesap})
    except Exception as e:
        logger.error(f"Hesap silme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Finans hareketi eklenirken bir hata oluştu.",
    redirect_url="finans:index"
)
@database_transaction
@login_required
def hareket_ekle(request: Any) -> Any:
    """
    Yeni finans hareketi ekler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    """
    from django.core.exceptions import ValidationError
    
    if request.method == 'POST':
        try:
            form = FinansHareketiForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    hareket = form.save(commit=False)
                    if not hareket.olusturan:
                        hareket.olusturan = request.user
                    
                    # Tutar validation
                    if hareket.tutar and hareket.tutar < 0:
                        raise ValidationError("Tutar negatif olamaz.")
                    
                    hareket.save()
                    
                    log_action(request.user, 'create', hareket, 
                             f'Finans hareketi eklendi: {hareket.aciklama[:50]}', request)
                    messages.success(request, 'Finans hareketi başarıyla eklendi.')
                    return redirect('finans:index')
            else:
                messages.error(request, 'Lütfen form hatalarını düzeltin.')
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Finans hareketi ekleme hatası: {str(e)}", exc_info=True)
            raise
    else:
        form = FinansHareketiForm()
    
    return render(request, 'finans/hareket_form.html', {'form': form, 'title': 'Yeni Finans Hareketi Ekle'})


@handle_view_errors(
    error_message="Finans hareketi güncellenirken bir hata oluştu.",
    redirect_url="finans:index"
)
@login_required
def hareket_duzenle(request: Any, pk: int) -> Any:
    """
    Finans hareketi düzenler.
    """
    from django.core.exceptions import ValidationError
    
    try:
        hareket = get_object_or_404(FinansHareketi, pk=pk)
        
        if request.method == 'POST':
            try:
                form = FinansHareketiForm(request.POST, instance=hareket)
                if form.is_valid():
                    # Tutar validation
                    if form.cleaned_data.get('tutar', 0) < 0:
                        raise ValidationError("Tutar negatif olamaz.")
                    
                    form.save()
                    
                    log_action(request.user, 'update', hareket, 
                             f'Finans hareketi güncellendi: {hareket.aciklama[:50]}', request)
                    messages.success(request, 'Finans hareketi başarıyla güncellendi.')
                    return redirect('finans:index')
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Finans hareketi düzenleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = FinansHareketiForm(instance=hareket)
        
        return render(request, 'finans/hareket_form.html', {'form': form, 'title': 'Finans Hareketi Düzenle', 'hareket': hareket})
    except Exception as e:
        logger.error(f"Finans hareketi düzenleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Finans hareketi silinirken bir hata oluştu.",
    redirect_url="finans:index"
)
@database_transaction
@login_required
def hareket_sil(request: Any, pk: int) -> Any:
    """
    Finans hareketi siler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    """
    try:
        hareket = get_object_or_404(FinansHareketi, pk=pk)
        
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    hareket_aciklama = hareket.aciklama[:50] if hareket.aciklama else 'Finans hareketi'
                    hareket.delete()
                    
                    log_action(request.user, 'delete', None, 
                             f'Finans hareketi silindi: {hareket_aciklama}', request)
                    messages.success(request, 'Finans hareketi başarıyla silindi.')
                    return redirect('finans:index')
            except Exception as e:
                logger.error(f"Finans hareketi silme hatası: {str(e)}", exc_info=True)
                raise
        else:
            return render(request, 'finans/hareket_sil.html', {'hareket': hareket})
    except Exception as e:
        logger.error(f"Finans hareketi silme hatası: {str(e)}", exc_info=True)
        raise
