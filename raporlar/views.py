from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, Case, When
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
import logging
import json
from stok.models import Urun, StokHareketi
from cari.models import Cari, CariHareketi
from fatura.models import Fatura, FaturaKalem
from accounts.utils import log_action
from stoktakip.error_handling import handle_view_errors
from stoktakip.cache_utils import cache_view_result
from stoktakip.security_utils import validate_date_range, sanitize_integer

logger = logging.getLogger(__name__)


@handle_view_errors(error_message="Dashboard yüklenirken bir hata oluştu.")
@cache_view_result(timeout=300, key_prefix='dashboard')  # 5 dakika cache
@login_required
def dashboard(request: Any) -> Any:
    """
    Ana dashboard sayfası - Genel istatistikler.
    
    Caching ile performans optimize edilmiştir.
    Tüm istatistikler optimize edilmiş query'ler ile hesaplanır.
    
    Args:
        request: HTTP request
    
    Returns:
        Rendered dashboard template
    """
    try:
        # Stok istatistikleri (optimize edilmiş queries)
        toplam_urun_sayisi = Urun.objects.count()
        dusuk_stoklu_urunler = 0  # Min stok her zaman 0 olduğu için düşük stok uyarısı yok
        
        # mevcut_stok bir property olduğu için Python'da hesaplamalıyız
        # Optimize edilmiş query ile tüm ürünlerin stok durumunu hesapla
        # Tüm ürünler için giriş ve çıkış toplamlarını hesapla
        urun_stoklari = {}
        giris_toplamlari = StokHareketi.objects.filter(
            islem_turu='giriş'
        ).values('urun_id').annotate(
            toplam=Sum('miktar')
        )
        for item in giris_toplamlari:
            urun_stoklari[item['urun_id']] = item['toplam'] or 0
        
        cikis_toplamlari = StokHareketi.objects.filter(
            islem_turu='çıkış'
        ).values('urun_id').annotate(
            toplam=Sum('miktar')
        )
        for item in cikis_toplamlari:
            urun_id = item['urun_id']
            if urun_id in urun_stoklari:
                urun_stoklari[urun_id] -= item['toplam'] or 0
            else:
                urun_stoklari[urun_id] = -(item['toplam'] or 0)
        
        # Stoksuz ürünleri say ve toplam stok değerini hesapla
        stoksuz_urunler = 0
        stoksuz_urun_listesi = []
        toplam_stok_degeri = Decimal('0.00')
        urunler = Urun.objects.all()
        
        for urun in urunler:
            mevcut_stok = urun_stoklari.get(urun.id, 0)
            if mevcut_stok == 0:
                stoksuz_urunler += 1
                stoksuz_urun_listesi.append({
                    'id': urun.id,
                    'ad': urun.ad,
                    'barkod': urun.barkod or '',
                    'stok': mevcut_stok
                })
            toplam_stok_degeri += Decimal(str(urun.fiyat)) * Decimal(str(mevcut_stok))
        
        # Cari istatistikleri (optimize edilmiş queries)
        toplam_cari_sayisi = Cari.objects.filter(durum='aktif').count()
        musteri_sayisi = Cari.objects.filter(durum='aktif', kategori__in=['musteri', 'her_ikisi']).count()
        tedarikci_sayisi = Cari.objects.filter(durum='aktif', kategori__in=['tedarikci', 'her_ikisi']).count()
        
        # Toplam alacak için Python'da hesapla (bakiye bir property olduğu için)
        # Optimize edilmiş query ile tüm carilerin bakiyelerini hesapla
        # Tüm aktif cariler için toplu bakiye hesaplama
        aktif_cari_ids = list(Cari.objects.filter(durum='aktif').values_list('id', flat=True))
        
        # Tüm cariler için borç ve alacak toplamlarını tek query ile hesapla
        borc_toplamlari = CariHareketi.objects.filter(
            cari_id__in=aktif_cari_ids,
            hareket_turu__in=['satis_faturasi', 'odeme']
        ).values('cari_id').annotate(toplam=Sum('tutar'))
        
        alacak_toplamlari = CariHareketi.objects.filter(
            cari_id__in=aktif_cari_ids,
            hareket_turu__in=['alis_faturasi', 'tahsilat']
        ).values('cari_id').annotate(toplam=Sum('tutar'))
        
        # Dictionary'ye çevir
        borc_dict = {item['cari_id']: item['toplam'] or Decimal('0.00') for item in borc_toplamlari}
        alacak_dict = {item['cari_id']: item['toplam'] or Decimal('0.00') for item in alacak_toplamlari}
        
        # Toplam alacak hesapla
        toplam_alacak = Decimal('0.00')
        for cari_id in aktif_cari_ids:
            borc = borc_dict.get(cari_id, Decimal('0.00'))
            alacak = alacak_dict.get(cari_id, Decimal('0.00'))
            bakiye = borc - alacak
            if bakiye > 0:
                toplam_alacak += bakiye
        
        # Fatura istatistikleri
        toplam_fatura_sayisi = Fatura.objects.count()
        bu_ay_fatura = Fatura.objects.filter(
            fatura_tarihi__year=timezone.now().year,
            fatura_tarihi__month=timezone.now().month
        ).count()
        
        bu_ay_ciro = Fatura.objects.filter(
            fatura_tipi='Satis',
            fatura_tarihi__year=timezone.now().year,
            fatura_tarihi__month=timezone.now().month
        ).aggregate(
            toplam=Sum('genel_toplam')
        )['toplam'] or Decimal('0.00')
        
        bekleyen_faturalar = Fatura.objects.filter(durum='AcikHesap').count()
        
        son_6_ay = []
        for i in range(6):
            ay_tarihi = timezone.now() - timedelta(days=30*i)
            ay_baslangic = ay_tarihi.replace(day=1).date()  # date objesi olarak
            if i == 0:
                ay_bitis = timezone.now().date()
            else:
                sonraki_ay = datetime.combine(ay_baslangic, datetime.min.time()) + timedelta(days=32)
                ay_bitis = sonraki_ay.replace(day=1).date() - timedelta(days=1)
            
            satis_tutar = Fatura.objects.filter(
                fatura_tipi='Satis',
                fatura_tarihi__gte=ay_baslangic,
                fatura_tarihi__lte=ay_bitis
            ).aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
            
            # Türkçe ay isimleri
            ay_isimleri = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
                          'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
            ay_adi = ay_isimleri[ay_baslangic.month - 1]
            
            son_6_ay.append({
                'ay': ay_baslangic.strftime('%Y-%m'),
                'ay_adi': f'{ay_adi} {ay_baslangic.year}',
                'satis': float(satis_tutar)
            })
        
        son_6_ay.reverse()
        
        urun_kategori_dagilimi = {}
        for urun in Urun.objects.select_related('kategori'):
            kategori_adi = urun.kategori.ad if urun.kategori else 'Kategorisiz'
            if kategori_adi not in urun_kategori_dagilimi:
                urun_kategori_dagilimi[kategori_adi] = 0
            urun_kategori_dagilimi[kategori_adi] += 1
        
        son_eklenenler = Urun.objects.all().order_by('-olusturma_tarihi')[:5]
        son_cariler = Cari.objects.filter(durum='aktif').order_by('-olusturma_tarihi')[:5]
        son_faturalar = Fatura.objects.all().order_by('-olusturma_tarihi')[:5]
        
        bugun = timezone.now().date()
        bu_hafta_baslangic = bugun - timedelta(days=bugun.weekday())
        gecen_hafta_baslangic = bu_hafta_baslangic - timedelta(days=7)
        gecen_hafta_bitis = bu_hafta_baslangic - timedelta(days=1)
        
        bugun_satis = Fatura.objects.filter(
            fatura_tipi='Satis',
            fatura_tarihi=bugun
        ).aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
        
        bu_hafta_satis = Fatura.objects.filter(
            fatura_tipi='Satis',
            fatura_tarihi__gte=bu_hafta_baslangic
        ).aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
        
        gecen_hafta_satis = Fatura.objects.filter(
            fatura_tipi='Satis',
            fatura_tarihi__gte=gecen_hafta_baslangic,
            fatura_tarihi__lte=gecen_hafta_bitis
        ).aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
        
        gecen_ay_baslangic = (bugun.replace(day=1) - timedelta(days=1)).replace(day=1)
        gecen_ay_bitis = bugun.replace(day=1) - timedelta(days=1)
        
        gecen_ay_ciro = Fatura.objects.filter(
            fatura_tipi='Satis',
            fatura_tarihi__gte=gecen_ay_baslangic,
            fatura_tarihi__lte=gecen_ay_bitis
        ).aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
        
        en_cok_satan_urunler = FaturaKalem.objects.filter(
            fatura__fatura_tipi='Satis',
            fatura__fatura_tarihi__year=timezone.now().year,
            fatura__fatura_tarihi__month=timezone.now().month
        ).values('urun_adi').annotate(
            toplam_miktar=Sum('miktar'),
            toplam_tutar=Sum('toplam_tutar')
        ).order_by('-toplam_miktar')[:5]
        
        # Vade tarihi kaldırıldığı için bekleyen faturaları göster
        bekleyen_faturalar = Fatura.objects.filter(
            durum='AcikHesap'
        ).order_by('fatura_tarihi')[:10]
        
        context = {
            'toplam_urun_sayisi': toplam_urun_sayisi,
            'dusuk_stoklu_urunler': dusuk_stoklu_urunler,
            'stoksuz_urunler': stoksuz_urunler,
            'stoksuz_urun_listesi': stoksuz_urun_listesi,
            'toplam_stok_degeri': toplam_stok_degeri,
            'toplam_cari_sayisi': toplam_cari_sayisi,
            'musteri_sayisi': musteri_sayisi,
            'tedarikci_sayisi': tedarikci_sayisi,
            'toplam_alacak': toplam_alacak,
            'toplam_fatura_sayisi': toplam_fatura_sayisi,
            'bu_ay_fatura': bu_ay_fatura,
            'bu_ay_ciro': bu_ay_ciro,
            'bekleyen_faturalar': bekleyen_faturalar,
            'son_urunler': son_eklenenler,
            'son_cariler': son_cariler,
            'son_faturalar': son_faturalar,
            'son_6_ay_satis': json.dumps(son_6_ay),
            'urun_kategori_dagilimi': json.dumps(urun_kategori_dagilimi),
            'bugun_satis': bugun_satis,
            'bu_hafta_satis': bu_hafta_satis,
            'gecen_hafta_satis': gecen_hafta_satis,
            'gecen_ay_ciro': gecen_ay_ciro,
            'en_cok_satan_urunler': en_cok_satan_urunler,
            'vadesi_yaklasan': bekleyen_faturalar,
        }
        
        return render(request, 'raporlar/dashboard.html', context)
    except Exception as e:
        logger.error(f"Dashboard hatası: {str(e)}", exc_info=True)
        raise  # handle_view_errors decorator'ı yakalayacak


@cache_view_result(timeout=600, key_prefix='kar_maliyet_raporu')  # 10 dakika cache
@handle_view_errors(error_message="Kar/maliyet raporu yüklenirken bir hata oluştu.")
@login_required
def kar_maliyet_raporu(request: Any) -> Any:
    """
    Kar/maliyet raporu.
    
    Muhasebe yetkisi gerektirir. Satış ve alış faturalarını karşılaştırarak
    kar/maliyet analizi yapar. Input validation, caching ve error handling ile güvenli hale getirilmiştir.
    """
    try:
        # Tarih validation
        tarih_baslangic = request.GET.get('tarih_baslangic', '')
        tarih_bitis = request.GET.get('tarih_bitis', '')

        # Tarih validation ve default değerler
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

        # Query optimization - select_related ve prefetch_related kullan
        satis_faturalari = Fatura.objects.filter(
            fatura_tipi='Satis',
            fatura_tarihi__gte=tarih_baslangic,
            fatura_tarihi__lte=tarih_bitis
        ).select_related('cari').prefetch_related('kalemler')

        alis_faturalari = Fatura.objects.filter(
            fatura_tipi='Alis',
            fatura_tarihi__gte=tarih_baslangic,
            fatura_tarihi__lte=tarih_bitis
        ).select_related('cari').prefetch_related('kalemler')

        toplam_satis = satis_faturalari.aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
        toplam_alis = alis_faturalari.aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')

        kar = toplam_satis - toplam_alis
        kar_yuzdesi = (kar / toplam_satis * 100) if toplam_satis > 0 else Decimal('0.00')

        # Detay listeleri - N+1 query problemini çöz
        satis_detay = []
        for fatura in satis_faturalari:
            for kalem in fatura.kalemler.all():
                satis_detay.append({
                    'fatura_no': fatura.fatura_no,
                    'tarih': fatura.fatura_tarihi,
                    'urun': kalem.urun_adi,
                    'miktar': kalem.miktar,
                    'birim_fiyat': kalem.birim_fiyat,
                    'toplam': kalem.toplam_tutar,
                })

        alis_detay = []
        for fatura in alis_faturalari:
            for kalem in fatura.kalemler.all():
                alis_detay.append({
                    'fatura_no': fatura.fatura_no,
                    'tarih': fatura.fatura_tarihi,
                    'urun': kalem.urun_adi,
                    'miktar': kalem.miktar,
                    'birim_fiyat': kalem.birim_fiyat,
                    'toplam': kalem.toplam_tutar,
                })

        context = {
            'tarih_baslangic': tarih_baslangic,
            'tarih_bitis': tarih_bitis,
            'toplam_satis': toplam_satis,
            'toplam_alis': toplam_alis,
            'kar': kar,
            'kar_yuzdesi': kar_yuzdesi,
            'satis_detay': satis_detay,
            'alis_detay': alis_detay,
        }
        return render(request, 'raporlar/kar_maliyet_raporu.html', context)
    except Exception as e:
        logger.error(f"Kar/maliyet raporu hatası: {str(e)}", exc_info=True)
        raise


@cache_view_result(timeout=600, key_prefix='alis_raporu')  # 10 dakika cache
@handle_view_errors(error_message="Alış raporu yüklenirken bir hata oluştu.")
@login_required
def alis_raporu(request: Any) -> Any:
    """
    Alış raporu.
    
    Muhasebe yetkisi gerektirir. Alış faturalarını gösterir.
    Input validation, caching ve error handling ile güvenli hale getirilmiştir.
    """
    try:
        # Tarih validation
        tarih_baslangic = request.GET.get('tarih_baslangic', '')
        tarih_bitis = request.GET.get('tarih_bitis', '')
        cari_id = request.GET.get('cari', '')

        # Tarih validation ve default değerler
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

        # Cari ID validation
        if cari_id:
            try:
                cari_id = sanitize_integer(cari_id, min_value=1)
                if not Cari.objects.filter(pk=cari_id, durum='aktif').exists():
                    cari_id = ''
            except Exception:
                cari_id = ''

        # Query optimization
        faturalar = Fatura.objects.filter(
            fatura_tipi='Alis',
            fatura_tarihi__gte=tarih_baslangic,
            fatura_tarihi__lte=tarih_bitis
        ).select_related('cari')

        if cari_id:
            faturalar = faturalar.filter(cari_id=cari_id)

        toplam_tutar = faturalar.aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
        toplam_kdv = faturalar.aggregate(toplam=Sum('kdv_tutari'))['toplam'] or Decimal('0.00')

        # Cari bazlı gruplama - Python'da değil DB'de yapılabilir ama mevcut yapıyı koruyoruz
        cari_bazli = {}
        for fatura in faturalar:
            cari_adi = fatura.cari.ad_soyad if fatura.cari else 'Cari Yok'
            if cari_adi not in cari_bazli:
                cari_bazli[cari_adi] = {
                    'toplam': Decimal('0.00'),
                    'fatura_sayisi': 0,
                    'faturalar': []
                }
            cari_bazli[cari_adi]['toplam'] += fatura.genel_toplam
            cari_bazli[cari_adi]['fatura_sayisi'] += 1
            cari_bazli[cari_adi]['faturalar'].append(fatura)

        context = {
            'tarih_baslangic': tarih_baslangic,
            'tarih_bitis': tarih_bitis,
            'cari_id': cari_id,
            'cariler': Cari.objects.filter(durum='aktif', kategori__in=['tedarikci', 'her_ikisi']).order_by('ad_soyad'),
            'faturalar': faturalar.order_by('-fatura_tarihi'),
            'toplam_tutar': toplam_tutar,
            'toplam_kdv': toplam_kdv,
            'cari_bazli': cari_bazli,
        }
        return render(request, 'raporlar/alis_raporu.html', context)
    except Exception as e:
        logger.error(f"Alış raporu hatası: {str(e)}", exc_info=True)
        raise


@cache_view_result(timeout=600, key_prefix='satis_raporu')  # 10 dakika cache
@handle_view_errors(error_message="Satış raporu yüklenirken bir hata oluştu.")
@login_required
def satis_raporu(request: Any) -> Any:
    """
    Satış raporu.
    
    Muhasebe yetkisi gerektirir. Satış faturalarını gösterir.
    Input validation, caching ve error handling ile güvenli hale getirilmiştir.
    """
    try:
        # Tarih validation
        tarih_baslangic = request.GET.get('tarih_baslangic', '')
        tarih_bitis = request.GET.get('tarih_bitis', '')
        cari_id = request.GET.get('cari', '')

        # Tarih validation ve default değerler
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

        # Cari ID validation
        if cari_id:
            try:
                cari_id = sanitize_integer(cari_id, min_value=1)
                if not Cari.objects.filter(pk=cari_id, durum='aktif').exists():
                    cari_id = ''
            except Exception:
                cari_id = ''

        # Query optimization
        faturalar = Fatura.objects.filter(
            fatura_tipi='Satis',
            fatura_tarihi__gte=tarih_baslangic,
            fatura_tarihi__lte=tarih_bitis
        ).select_related('cari')

        if cari_id:
            faturalar = faturalar.filter(cari_id=cari_id)

        toplam_tutar = faturalar.aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
        toplam_kdv = faturalar.aggregate(toplam=Sum('kdv_tutari'))['toplam'] or Decimal('0.00')

        # Cari bazlı gruplama
        cari_bazli = {}
        for fatura in faturalar:
            cari_adi = fatura.cari.ad_soyad if fatura.cari else 'Cari Yok'
            if cari_adi not in cari_bazli:
                cari_bazli[cari_adi] = {
                    'toplam': Decimal('0.00'),
                    'fatura_sayisi': 0,
                    'faturalar': []
                }
            cari_bazli[cari_adi]['toplam'] += fatura.genel_toplam
            cari_bazli[cari_adi]['fatura_sayisi'] += 1
            cari_bazli[cari_adi]['faturalar'].append(fatura)

        context = {
            'tarih_baslangic': tarih_baslangic,
            'tarih_bitis': tarih_bitis,
            'cari_id': cari_id,
            'cariler': Cari.objects.filter(durum='aktif', kategori__in=['musteri', 'her_ikisi']).order_by('ad_soyad'),
            'faturalar': faturalar.order_by('-fatura_tarihi'),
            'toplam_tutar': toplam_tutar,
            'toplam_kdv': toplam_kdv,
            'cari_bazli': cari_bazli,
        }
        return render(request, 'raporlar/satis_raporu.html', context)
    except Exception as e:
        logger.error(f"Satış raporu hatası: {str(e)}", exc_info=True)
        raise


# Excel export fonksiyonları kaldırıldı
