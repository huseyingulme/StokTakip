"""
Cari hareketleri için servis katmanı (wrapper).

Bu modül, cari hareketlerinin oluşturulması ve yönetimi için
iş mantığını içerir. View ve Model katmanlarından bağımsızdır.
"""
from django.db import transaction
from django.utils import timezone
from datetime import datetime, time
from cari.models import CariHareketi
from fatura.models import Fatura
from typing import Optional
from django.contrib.auth.models import User


def create_or_update_cari_hareketi_from_fatura(
    fatura: Fatura,
    user: Optional[User] = None
) -> Optional[CariHareketi]:
    """
    Fatura'dan cari hareketi oluşturur veya günceller.
    
    Sadece 'AcikHesap' durumundaki faturalar için cari hareketi oluşturulur.
    'KasadanKapanacak' durumundaki faturalar için cari hareketi silinir.
    
    Args:
        fatura: Fatura objesi
        user: İşlemi yapan kullanıcı (opsiyonel)
    
    Returns:
        Oluşturulan veya güncellenen CariHareketi objesi, yoksa None
    """
    if not fatura.cari:
        return None
    
    if not fatura.fatura_no:
        raise ValueError("Fatura numarası olmadan cari hareketi oluşturulamaz.")
    
    # Mevcut cari hareketini bul
    cari_hareket = CariHareketi.objects.filter(belge_no=fatura.fatura_no).first()
    
    # Hareket türünü belirle
    hareket_turu = 'satis_faturasi' if fatura.fatura_tipi == 'Satis' else 'alis_faturasi'
    
    # Timezone-aware datetime oluştur
    tarih_naive = datetime.combine(fatura.fatura_tarihi, time.min)
    tarih = timezone.make_aware(tarih_naive)
    
    if fatura.durum == 'AcikHesap':
        # Açık hesap - cari hareketi oluştur veya güncelle
        if cari_hareket:
            # Mevcut hareketi güncelle
            cari_hareket.tutar = fatura.genel_toplam
            cari_hareket.tarih = tarih
            cari_hareket.aciklama = f"Fatura: {fatura.fatura_no}"
            cari_hareket.hareket_turu = hareket_turu
            cari_hareket.save()
            return cari_hareket
        else:
            # Yeni hareket oluştur
            return CariHareketi.objects.create(
                cari=fatura.cari,
                hareket_turu=hareket_turu,
                tutar=fatura.genel_toplam,
                aciklama=f"Fatura: {fatura.fatura_no}",
                belge_no=fatura.fatura_no,
                tarih=tarih,
                olusturan=user or fatura.olusturan
            )
    elif fatura.durum == 'KasadanKapanacak':
        # Kasadan kapanacak - cari hareketi sil (ödendi gibi)
        if cari_hareket:
            cari_hareket.delete()
        return None
    
    return None


def delete_cari_hareketi_for_fatura(fatura_no: str) -> None:
    """
    Belirli bir fatura için cari hareketini siler.
    
    Args:
        fatura_no: Fatura numarası
    
    Returns:
        None
    """
    CariHareketi.objects.filter(belge_no=fatura_no).delete()


def create_cari_hareketi(
    cari,
    hareket_turu: str,
    tutar,
    belge_no: str = '',
    aciklama: str = '',
    tarih=None,
    user: Optional[User] = None
) -> CariHareketi:
    """
    Tek bir cari hareketi oluşturur.
    
    Args:
        cari: Cari objesi
        hareket_turu: Hareket türü ('satis_faturasi', 'alis_faturasi', vb.)
        tutar: Tutar
        belge_no: Belge numarası (opsiyonel)
        aciklama: Açıklama (opsiyonel)
        tarih: Tarih (opsiyonel, varsayılan: şimdi)
        user: İşlemi yapan kullanıcı (opsiyonel)
    
    Returns:
        Oluşturulan CariHareketi objesi
    """
    if tarih is None:
        tarih = timezone.now()
    
    return CariHareketi.objects.create(
        cari=cari,
        hareket_turu=hareket_turu,
        tutar=tutar,
        belge_no=belge_no,
        aciklama=aciklama,
        tarih=tarih,
        olusturan=user
    )
