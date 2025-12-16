"""
Stok hareketleri için servis katmanı (wrapper).

Bu modül, stok hareketlerinin oluşturulması ve yönetimi için
iş mantığını içerir. View ve Model katmanlarından bağımsızdır.
"""
from django.db import transaction
from stok.models import StokHareketi
from fatura.models import Fatura
from typing import Optional
from django.contrib.auth.models import User


def create_stok_hareketleri_from_fatura(fatura: Fatura, user: Optional[User] = None) -> None:
    """
    Fatura'dan stok hareketleri oluşturur.
    
    Alış faturası → Stok girişi
    Satış faturası → Stok çıkışı
    
    Args:
        fatura: Fatura objesi
        user: İşlemi yapan kullanıcı (opsiyonel)
    
    Returns:
        None
    """
    if not fatura.fatura_no:
        raise ValueError("Fatura numarası olmadan stok hareketi oluşturulamaz.")
    
    # Mevcut stok hareketlerini sil (güncelleme durumu için)
    StokHareketi.objects.filter(
        aciklama__startswith=f"Fatura: {fatura.fatura_no}"
    ).delete()
    
    # Her kalem için stok hareketi oluştur
    for kalem in fatura.kalemler.all():
        if not kalem.urun:
            continue
        
        # İşlem türünü belirle
        islem_turu = 'giriş' if fatura.fatura_tipi == 'Alis' else 'çıkış'
        
        # Stok hareketi oluştur
        StokHareketi.objects.create(
            urun=kalem.urun,
            islem_turu=islem_turu,
            miktar=kalem.miktar,
            aciklama=f"Fatura: {fatura.fatura_no}",
            olusturan=user or fatura.olusturan
        )


def delete_stok_hareketleri_for_fatura(fatura_no: str) -> None:
    """
    Belirli bir fatura için stok hareketlerini siler.
    
    Args:
        fatura_no: Fatura numarası
    
    Returns:
        None
    """
    StokHareketi.objects.filter(
        aciklama__startswith=f"Fatura: {fatura_no}"
    ).delete()


def create_stok_hareketi(
    urun,
    islem_turu: str,
    miktar: int,
    aciklama: str,
    user: Optional[User] = None
) -> StokHareketi:
    """
    Tek bir stok hareketi oluşturur.
    
    Args:
        urun: Urun objesi
        islem_turu: 'giriş' veya 'çıkış'
        miktar: Miktar
        aciklama: Açıklama
        user: İşlemi yapan kullanıcı (opsiyonel)
    
    Returns:
        Oluşturulan StokHareketi objesi
    """
    if islem_turu not in ['giriş', 'çıkış']:
        raise ValueError("İşlem türü 'giriş' veya 'çıkış' olmalıdır.")
    
    if miktar <= 0:
        raise ValueError("Miktar 0'dan büyük olmalıdır.")
    
    return StokHareketi.objects.create(
        urun=urun,
        islem_turu=islem_turu,
        miktar=miktar,
        aciklama=aciklama,
        olusturan=user
    )
