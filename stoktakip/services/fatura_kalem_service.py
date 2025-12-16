"""
Fatura kalem işlemleri için servis katmanı (wrapper).

Bu modül, fatura kalemlerinin eklenmesi, güncellenmesi ve silinmesi için
iş mantığını içerir. View katmanından bağımsızdır.
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from fatura.models import Fatura, FaturaKalem
from fatura.forms import FaturaKalemForm
from stok.models import Urun
from stoktakip.services.stok_service import create_stok_hareketleri_from_fatura
from stoktakip.services.cari_service import create_or_update_cari_hareketi_from_fatura
from accounts.utils import log_action
from stoktakip.security_utils import sanitize_decimal, sanitize_string
from typing import Optional, List, Dict
from django.contrib.auth.models import User
from django.http import HttpRequest
from decimal import Decimal, ROUND_HALF_UP
import logging

logger = logging.getLogger(__name__)


@transaction.atomic
def add_fatura_kalem(
    fatura: Fatura,
    form: FaturaKalemForm,
    user: User,
    request: Optional[HttpRequest] = None
) -> FaturaKalem:
    """
    Faturaya yeni kalem ekler.
    
    Bu fonksiyon:
    - Kalemi oluşturur
    - Fatura toplamlarını yeniden hesaplar
    - Stok hareketlerini günceller
    - Cari hareketini günceller
    - Audit log kaydı tutar
    
    Args:
        fatura: Kalem eklenecek Fatura objesi
        form: Geçerli FaturaKalemForm objesi
        user: İşlemi yapan kullanıcı
        request: HTTP request (audit log için opsiyonel)
    
    Returns:
        Oluşturulan FaturaKalem objesi
    
    Raises:
        ValidationError: Form geçersizse veya iş kuralı ihlal edilirse
    """
    if not form.is_valid():
        raise ValidationError(form.errors)
    
    # Kalemi oluştur
    kalem = form.save(commit=False)
    kalem.fatura = fatura
    
    # Ürün adını ayarla
    if kalem.urun:
        kalem.urun_adi = str(kalem.urun.ad)[:200]
    
    kalem.save()
    
    # Fatura toplamlarını yeniden hesapla
    fatura.hesapla_toplamlar()
    fatura.refresh_from_db()
    
    # Stok hareketlerini güncelle
    create_stok_hareketleri_from_fatura(fatura, user)
    
    # Cari hareketini güncelle (sadece açık hesap ise)
    if fatura.durum == 'AcikHesap':
        create_or_update_cari_hareketi_from_fatura(fatura, user)
    
    # Audit log
    log_action(
        user,
        'create',
        kalem,
        f'Fatura kalemi eklendi: {fatura.fatura_no} - {kalem.urun_adi}',
        request
    )
    
    return kalem


@transaction.atomic
def update_fatura_kalem(
    kalem: FaturaKalem,
    form: FaturaKalemForm,
    user: User,
    request: Optional[HttpRequest] = None
) -> FaturaKalem:
    """
    Mevcut fatura kalemini günceller.
    
    Bu fonksiyon:
    - Kalemi günceller
    - Fatura toplamlarını yeniden hesaplar
    - Stok hareketlerini günceller
    - Cari hareketini günceller
    - Audit log kaydı tutar
    
    Args:
        kalem: Güncellenecek FaturaKalem objesi
        form: Geçerli FaturaKalemForm objesi
        user: İşlemi yapan kullanıcı
        request: HTTP request (audit log için opsiyonel)
    
    Returns:
        Güncellenen FaturaKalem objesi
    
    Raises:
        ValidationError: Form geçersizse veya iş kuralı ihlal edilirse
    """
    if not form.is_valid():
        raise ValidationError(form.errors)
    
    # Kalemi güncelle
    kalem = form.save()
    
    # Fatura toplamlarını yeniden hesapla
    kalem.fatura.hesapla_toplamlar()
    kalem.fatura.refresh_from_db()
    
    # Stok hareketlerini güncelle
    create_stok_hareketleri_from_fatura(kalem.fatura, user)
    
    # Cari hareketini güncelle (sadece açık hesap ise)
    if kalem.fatura.durum == 'AcikHesap':
        create_or_update_cari_hareketi_from_fatura(kalem.fatura, user)
    
    # Audit log
    log_action(
        user,
        'update',
        kalem,
        f'Fatura kalemi güncellendi: {kalem.fatura.fatura_no} - {kalem.urun_adi}',
        request
    )
    
    return kalem


@transaction.atomic
def delete_fatura_kalem(
    kalem: FaturaKalem,
    user: User,
    request: Optional[HttpRequest] = None
) -> None:
    """
    Fatura kalemini siler.
    
    Bu fonksiyon:
    - Kalemi siler
    - Fatura toplamlarını yeniden hesaplar
    - Stok hareketlerini günceller
    - Cari hareketini günceller
    - Audit log kaydı tutar
    
    Args:
        kalem: Silinecek FaturaKalem objesi
        user: İşlemi yapan kullanıcı
        request: HTTP request (audit log için opsiyonel)
    
    Returns:
        None
    """
    fatura = kalem.fatura
    kalem_adi = kalem.urun_adi
    
    # Kalemi sil
    kalem.delete()
    
    # Fatura toplamlarını yeniden hesapla
    fatura.hesapla_toplamlar()
    fatura.refresh_from_db()
    
    # Stok hareketlerini güncelle
    create_stok_hareketleri_from_fatura(fatura, user)
    
    # Cari hareketini güncelle (sadece açık hesap ise)
    if fatura.durum == 'AcikHesap':
        create_or_update_cari_hareketi_from_fatura(fatura, user)
    
    # Audit log
    log_action(
        user,
        'delete',
        None,
        f'Fatura kalemi silindi: {fatura.fatura_no} - {kalem_adi}',
        request
    )


@transaction.atomic
def add_fatura_kalemler_from_post_data(
    fatura: Fatura,
    post_data: Dict,
    user: User,
    request: Optional[HttpRequest] = None
) -> tuple[int, int]:
    """
    POST verilerinden fatura kalemlerini oluşturur.
    
    Bu fonksiyon, fatura ekleme formundan gelen POST verilerini işler
    ve kalemleri oluşturur.
    
    Args:
        fatura: Kalemlerin ekleneceği Fatura objesi
        post_data: POST verileri dictionary'si
        user: İşlemi yapan kullanıcı
        request: HTTP request (audit log için opsiyonel)
    
    Returns:
        (kalem_sayisi, hata_sayisi) tuple
    
    Raises:
        ValidationError: En az bir kalem eklenemezse
    """
    urun_ids = post_data.getlist('urun_id[]', [])
    miktarlar = post_data.getlist('miktar[]', [])
    birim_fiyatlar = post_data.getlist('birim_fiyat[]', [])
    kdv_oranlari = post_data.getlist('kdv_orani[]', [])
    kdv_dahil_fiyatlar = post_data.getlist('kdv_dahil_fiyat[]', [])
    
    # Geçerli kalemleri filtrele
    gecerli_kalemler = []
    for i in range(len(urun_ids)):
        urun_id = urun_ids[i] if i < len(urun_ids) else ''
        miktar_str = miktarlar[i] if i < len(miktarlar) else ''
        
        if urun_id and urun_id.strip() and miktar_str and miktar_str.strip():
            try:
                miktar_float = float(str(miktar_str).replace(',', '.'))
                if miktar_float > 0:
                    gecerli_kalemler.append({
                        'urun_id': urun_id.strip(),
                        'miktar': str(miktar_str).strip(),
                        'birim_fiyat': str(birim_fiyatlar[i]).strip() if i < len(birim_fiyatlar) and birim_fiyatlar[i] else '',
                        'kdv_orani': str(kdv_oranlari[i]).strip() if i < len(kdv_oranlari) and kdv_oranlari[i] else '20',
                        'kdv_dahil_fiyat': str(kdv_dahil_fiyatlar[i]).strip() if i < len(kdv_dahil_fiyatlar) and kdv_dahil_fiyatlar[i] else ''
                    })
            except (ValueError, TypeError, IndexError):
                continue
    
    kalem_sayisi = 0
    hata_sayisi = 0
    
    for kalem_data in gecerli_kalemler:
        try:
            # Ürün ID kontrolü
            try:
                urun_id = int(str(kalem_data['urun_id']).strip())
                if urun_id <= 0:
                    raise ValueError("Ürün ID pozitif olmalı")
            except (ValueError, TypeError):
                hata_sayisi += 1
                continue
            
            # Ürün kontrolü
            try:
                urun = Urun.objects.get(pk=urun_id)
            except Urun.DoesNotExist:
                hata_sayisi += 1
                continue
            
            # Miktar kontrolü
            try:
                miktar_str = str(kalem_data['miktar']).replace(',', '.').strip()
                miktar_float = float(miktar_str)
                miktar = int(miktar_float)
                if miktar <= 0:
                    raise ValueError("Miktar pozitif olmalı")
            except (ValueError, TypeError):
                hata_sayisi += 1
                continue
            
            # KDV oranı
            kdv_orani = 20
            
            # Fiyat hesaplama
            birim_fiyat = None
            
            # Önce KDV dahil fiyat kontrolü
            kdv_dahil_str = str(kalem_data.get('kdv_dahil_fiyat', '')).strip().replace(',', '.')
            if kdv_dahil_str and kdv_dahil_str != '0' and kdv_dahil_str != '0.00':
                try:
                    kdv_dahil_float = float(kdv_dahil_str)
                    if kdv_dahil_float > 0:
                        kdv_dahil = Decimal(str(kdv_dahil_float))
                        if kdv_orani == 0:
                            birim_fiyat = kdv_dahil
                        else:
                            birim_fiyat = kdv_dahil / (Decimal('1') + Decimal(str(kdv_orani)) / Decimal('100'))
                        birim_fiyat = birim_fiyat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                except (ValueError, TypeError, ValidationError):
                    pass
            
            # Eğer KDV dahil fiyat yoksa, birim fiyat kontrolü
            if birim_fiyat is None:
                birim_fiyat_str = str(kalem_data.get('birim_fiyat', '')).strip().replace(',', '.')
                if birim_fiyat_str and birim_fiyat_str != '0' and birim_fiyat_str != '0.00':
                    try:
                        birim_fiyat_float = float(birim_fiyat_str)
                        if birim_fiyat_float > 0:
                            birim_fiyat = Decimal(str(birim_fiyat_float))
                    except (ValueError, TypeError, ValidationError):
                        pass
            
            # Eğer hala fiyat yoksa, varsayılan fiyat
            if birim_fiyat is None:
                if fatura.fatura_tipi == 'Alis':
                    kdv_dahil_fiyat = Decimal(str(urun.alis_fiyati)) if urun.alis_fiyati and urun.alis_fiyati > 0 else (Decimal(str(urun.fiyat)) if urun.fiyat else Decimal('0.00'))
                else:
                    kdv_dahil_fiyat = Decimal(str(urun.fiyat)) if urun.fiyat else Decimal('0.00')
                
                if kdv_dahil_fiyat and kdv_dahil_fiyat > 0:
                    birim_fiyat = kdv_dahil_fiyat / (Decimal('1') + Decimal('20') / Decimal('100'))
                    birim_fiyat = birim_fiyat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    birim_fiyat = Decimal('0.00')
            
            # Kalem oluştur
            urun_adi = str(urun.ad)[:200]
            ara_toplam = Decimal(str(miktar)) * birim_fiyat
            ara_toplam = ara_toplam.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            kdv_tutari = (ara_toplam * (Decimal(str(kdv_orani)) / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            toplam_tutar = ara_toplam
            
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
            
            kalem.full_clean()
            kalem.save()
            
            kalem_sayisi += 1
            
        except Exception as e:
            hata_sayisi += 1
            logger.error(f"Fatura kalem eklenirken hata: {str(e)}", exc_info=True)
            continue
    
    # En az bir kalem kontrolü
    if kalem_sayisi == 0:
        raise ValidationError("En az bir kalem eklenmelidir.")
    
    # Fatura toplamlarını hesapla
    fatura.hesapla_toplamlar()
    fatura.refresh_from_db()
    
    # Stok ve cari hareketlerini oluştur
    create_stok_hareketleri_from_fatura(fatura, user)
    if fatura.durum == 'AcikHesap':
        create_or_update_cari_hareketi_from_fatura(fatura, user)
    
    return kalem_sayisi, hata_sayisi
