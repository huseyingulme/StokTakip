"""
Fatura işlemleri için servis katmanı (wrapper).

Bu modül, fatura oluşturma, güncelleme ve silme işlemleri için
iş mantığını içerir. View katmanından bağımsızdır.
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from fatura.models import Fatura
from fatura.forms import FaturaForm
from stoktakip.services.stok_service import create_stok_hareketleri_from_fatura, delete_stok_hareketleri_for_fatura
from stoktakip.services.cari_service import create_or_update_cari_hareketi_from_fatura, delete_cari_hareketi_for_fatura
from accounts.utils import log_action
from typing import Optional
from django.contrib.auth.models import User
from django.http import HttpRequest


@transaction.atomic
def create_fatura(
    form: FaturaForm,
    user: User,
    request: Optional[HttpRequest] = None
) -> Fatura:
    """
    Yeni fatura oluşturur.
    
    Bu fonksiyon:
    - Faturayı oluşturur
    - Fatura numarasını otomatik atar
    - Toplamları hesaplar
    - Stok ve cari hareketlerini oluşturur (kalemler eklendikten sonra)
    - Audit log kaydı tutar
    
    Args:
        form: Geçerli FaturaForm objesi
        user: İşlemi yapan kullanıcı
        request: HTTP request (audit log için opsiyonel)
    
    Returns:
        Oluşturulan Fatura objesi
    
    Raises:
        ValidationError: Form geçersizse veya iş kuralı ihlal edilirse
    """
    if not form.is_valid():
        raise ValidationError(form.errors)
    
    # Faturayı oluştur
    fatura = form.save(commit=False)
    fatura.olusturan = user
    
    # Fatura numarası yoksa otomatik oluştur
    if not fatura.fatura_no:
        fatura.fatura_no = fatura.olustur_fatura_no()
    
    fatura.save()
    
    # Toplamları hesapla (kalemler eklendikten sonra view'da çağrılacak)
    # Burada sadece fatura kaydedilir, kalemler sonra eklenecek
    
    # Audit log
    log_action(
        user,
        'create',
        fatura,
        f'Fatura oluşturuldu: {fatura.fatura_no}',
        request
    )
    
    return fatura


@transaction.atomic
def update_fatura(
    fatura: Fatura,
    form: FaturaForm,
    user: User,
    request: Optional[HttpRequest] = None
) -> Fatura:
    """
    Mevcut faturayı günceller.
    
    Bu fonksiyon:
    - Faturayı günceller
    - Toplamları yeniden hesaplar
    - Stok hareketlerini günceller
    - Cari hareketini günceller
    - Audit log kaydı tutar
    
    Args:
        fatura: Güncellenecek Fatura objesi
        form: Geçerli FaturaForm objesi
        user: İşlemi yapan kullanıcı
        request: HTTP request (audit log için opsiyonel)
    
    Returns:
        Güncellenen Fatura objesi
    
    Raises:
        ValidationError: Form geçersizse veya iş kuralı ihlal edilirse
    """
    if not form.is_valid():
        raise ValidationError(form.errors)
    
    # Faturayı güncelle
    fatura = form.save()
    
    # Toplamları yeniden hesapla
    fatura.hesapla_toplamlar()
    fatura.refresh_from_db()
    
    # Stok hareketlerini güncelle
    create_stok_hareketleri_from_fatura(fatura, user)
    
    # Cari hareketini güncelle
    create_or_update_cari_hareketi_from_fatura(fatura, user)
    
    # Audit log
    log_action(
        user,
        'update',
        fatura,
        f'Fatura güncellendi: {fatura.fatura_no}',
        request
    )
    
    return fatura


@transaction.atomic
def delete_fatura(
    fatura: Fatura,
    user: User,
    request: Optional[HttpRequest] = None
) -> None:
    """
    Faturayı siler.
    
    Bu fonksiyon:
    - İlişkili stok hareketlerini siler
    - İlişkili cari hareketini siler
    - Faturayı siler
    - Audit log kaydı tutar
    
    Args:
        fatura: Silinecek Fatura objesi
        user: İşlemi yapan kullanıcı
        request: HTTP request (audit log için opsiyonel)
    
    Returns:
        None
    
    Raises:
        ValidationError: Faturada kalemler varsa silinemez
    """
    # Kalemler varsa silinemez kontrolü
    if fatura.kalemler.exists():
        raise ValidationError("Faturaların kalemleri varken silinemez.")
    
    fatura_no = fatura.fatura_no
    
    # İlişkili hareketleri sil
    if fatura_no:
        delete_stok_hareketleri_for_fatura(fatura_no)
        delete_cari_hareketi_for_fatura(fatura_no)
    
    # Faturayı sil
    fatura.delete()
    
    # Audit log
    log_action(
        user,
        'delete',
        None,
        f'Fatura silindi: {fatura_no}',
        request
    )


def recalculate_fatura_totals(fatura: Fatura) -> None:
    """
    Fatura toplamlarını yeniden hesaplar.
    
    Args:
        fatura: Toplamları hesaplanacak Fatura objesi
    
    Returns:
        None
    """
    fatura.hesapla_toplamlar()
    fatura.refresh_from_db()


@transaction.atomic
def copy_fatura(
    fatura: Fatura,
    user: User,
    request: Optional[HttpRequest] = None
) -> Fatura:
    """
    Faturayı kopyalar.
    
    Bu fonksiyon:
    - Yeni bir fatura oluşturur
    - Tüm kalemlerini kopyalar
    - Toplamları hesaplar
    - Audit log kaydı tutar
    
    Args:
        fatura: Kopyalanacak Fatura objesi
        user: İşlemi yapan kullanıcı
        request: HTTP request (audit log için opsiyonel)
    
    Returns:
        Oluşturulan yeni Fatura objesi
    """
    from django.utils import timezone
    from fatura.models import FaturaKalem
    
    # Yeni fatura oluştur
    yeni_fatura = Fatura.objects.create(
        fatura_no=None,  # Otomatik oluşturulacak
        cari=fatura.cari,
        fatura_tarihi=timezone.now().date(),
        fatura_tipi=fatura.fatura_tipi,
        durum='AcikHesap',
        iskonto_orani=fatura.iskonto_orani,
        aciklama=f"Kopya: {fatura.fatura_no}",
        olusturan=user
    )
    
    # Kalemleri kopyala
    for kalem in fatura.kalemler.all():
        FaturaKalem.objects.create(
            fatura=yeni_fatura,
            urun=kalem.urun,
            urun_adi=kalem.urun_adi,
            miktar=kalem.miktar,
            birim_fiyat=kalem.birim_fiyat,
            kdv_orani=kalem.kdv_orani,
            kdv_tutari=kalem.kdv_tutari,
            toplam_tutar=kalem.toplam_tutar,
            sira_no=kalem.sira_no
        )
    
    # Toplamları hesapla
    yeni_fatura.hesapla_toplamlar()
    yeni_fatura.refresh_from_db()
    
    # Audit log
    log_action(
        user,
        'create',
        yeni_fatura,
        f'Fatura kopyalandı: {fatura.fatura_no} -> {yeni_fatura.fatura_no}',
        request
    )
    
    return yeni_fatura
